"""Document management endpoints"""

import logging
import uuid
import os
import tempfile
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.models.documents import (
    IngestRequest, 
    IngestResponse,
    DocumentStatusResponse,
    DocumentListResponse,
    DocumentListItem
)
from app.models.common import ErrorResponse
from app.api.deps import get_current_user_id, get_trace_id
from app.workers.document_processor import get_document_processor
from app.services.ingestion import validate_file_for_ingestion
from app.db.operations import (
    update_document_status,
    get_document_chunks,
    delete_document_chunks,
    count_document_chunks
)
from app.db.session import get_db_pool
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Start document ingestion process
    
    Initiates background processing of uploaded document:
    1. Extract text content from PDF/DOCX 
    2. Create chunks with optimal size/overlap
    3. Generate embeddings via OpenAI
    4. Store in database with RLS protection
    
    Returns job ID for status tracking.
    """
    settings = get_settings()
    logger.info(
        "Document ingestion started",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "mime_type": request.mime_type,
            "storage_path": request.storage_path
        }
    )
    
    try:
        # For now, assume the file is already downloaded from Supabase Storage
        # In production, you'd download from Supabase Storage using the storage_path
        # For testing, we'll create a temporary file path
        temp_file_path = os.path.join(
            tempfile.gettempdir(), 
            f"doc_{request.document_id}_{Path(request.storage_path).name}"
        )
        
        # Validate file for ingestion
        if not validate_file_for_ingestion(temp_file_path, request.mime_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed for {request.mime_type}"
            )
        
        # Update document status to processing
        await update_document_status(
            str(request.document_id), 
            "processing"
        )
        
        # Start background processing
        processor = get_document_processor()
        job_task = processor.submit_job_nonblocking(
            document_id=str(request.document_id),
            file_path=temp_file_path,
            mime_type=request.mime_type,
            user_id=str(user_id)
        )
        
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        logger.info(
            "Document ingestion job started",
            extra={
                "trace_id": trace_id,
                "document_id": str(request.document_id),
                "job_id": job_id,
                "user_id": str(user_id)
            }
        )
        
        return IngestResponse(
            status="started",
            document_id=request.document_id,
            job_id=job_id,
            trace_id=trace_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Document ingestion failed to start",
            extra={
                "trace_id": trace_id,
                "document_id": str(request.document_id),
                "error": str(e)
            }
        )
        await update_document_status(
            str(request.document_id),
            "failed",
            error_message=f"Failed to start ingestion: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start document ingestion"
        )


@router.get("/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID = Query(description="Document ID to check status for", alias="documentId"),
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Get document processing status
    
    Returns current processing state and progress information.
    Possible states: pending, processing, completed, failed
    """
    logger.info(
        "Document status requested",
        extra={
            "trace_id": trace_id,
            "document_id": str(document_id),
            "user_id": str(user_id)
        }
    )
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Set user context for RLS
            await conn.execute("SELECT set_config('request.jwt.claims', $1, true)", f'{{"sub":"{user_id}"}}')
            
            # Get document status from database
            row = await conn.fetchrow(
                """
                SELECT status, page_count, chunks_count, error_message, updated_at
                FROM documents 
                WHERE id = $1
                """,
                str(document_id)
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            # Calculate progress based on status
            progress = None
            if row['status'] == 'completed':
                progress = 100.0
            elif row['status'] == 'processing':
                progress = 50.0  # Rough estimate
            elif row['status'] == 'failed':
                progress = 0.0
            
            # Get actual chunk count
            chunks_count = await count_document_chunks(str(document_id), str(user_id))
            
            return DocumentStatusResponse(
                document_id=document_id,
                status=row['status'],
                progress=progress,
                chunks_created=chunks_count if chunks_count > 0 else row['chunks_count'],
                embeddings_created=chunks_count if chunks_count > 0 else row['chunks_count'],
                error_message=row['error_message'],
                trace_id=trace_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document status",
            extra={
                "trace_id": trace_id,
                "document_id": str(document_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document status"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=20, description="Maximum number of documents to return", ge=1, le=100),
    offset: int = Query(default=0, description="Number of documents to skip", ge=0),
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    List user's documents
    
    Returns paginated list of user's uploaded documents with processing status.
    """
    logger.info(
        "Document list requested",
        extra={
            "trace_id": trace_id,
            "user_id": str(user_id),
            "limit": limit,
            "offset": offset
        }
    )
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Set user context for RLS
            await conn.execute("SELECT set_config('request.jwt.claims', $1, true)", f'{{"sub":"{user_id}"}}')
            
            # Get total count
            count_row = await conn.fetchrow(
                "SELECT COUNT(*) as total FROM documents"
            )
            total_count = count_row['total'] if count_row else 0
            
            # Get paginated documents
            rows = await conn.fetch(
                """
                SELECT id, filename, title, content_type, file_size_bytes, 
                       status, chunks_count, created_at, updated_at
                FROM documents 
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            
            documents = []
            for row in rows:
                # Convert database row to DocumentListItem
                doc = DocumentListItem(
                    id=UUID(row['id']),
                    filename=row['filename'],
                    title=row['title'],
                    content_type=row['content_type'],
                    file_size_bytes=row['file_size_bytes'],
                    status=row['status'],
                    chunks_count=row['chunks_count'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                documents.append(doc)
            
            return DocumentListResponse(
                documents=documents,
                total_count=total_count,
                trace_id=trace_id
            )
            
    except Exception as e:
        logger.error(
            "Failed to list documents",
            extra={
                "trace_id": trace_id,
                "user_id": str(user_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Delete document and all associated data
    
    Removes document, chunks, and embeddings. This action is irreversible.
    """
    logger.info(
        "Document deletion requested", 
        extra={
            "trace_id": trace_id,
            "document_id": str(document_id),
            "user_id": str(user_id)
        }
    )
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Set user context for RLS
                await conn.execute("SELECT set_config('request.jwt.claims', $1, true)", f'{{"sub":"{user_id}"}}')
                
                # Check if document exists
                doc_row = await conn.fetchrow(
                    "SELECT id FROM documents WHERE id = $1",
                    str(document_id)
                )
                
                if not doc_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Document not found"
                    )
                
                # Delete chunks and embeddings
                chunks_deleted = await delete_document_chunks(str(document_id), str(user_id))
                
                # Delete the document itself
                result = await conn.execute(
                    "DELETE FROM documents WHERE id = $1",
                    str(document_id)
                )
                
                logger.info(
                    "Document deleted successfully",
                    extra={
                        "trace_id": trace_id,
                        "document_id": str(document_id),
                        "chunks_deleted": chunks_deleted
                    }
                )
                
                return {
                    "message": f"Document {document_id} deleted successfully",
                    "chunks_deleted": chunks_deleted,
                    "trace_id": trace_id
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete document",
            extra={
                "trace_id": trace_id,
                "document_id": str(document_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )