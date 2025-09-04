"""Document management endpoints"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

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
    
    # DUMMY: Return success without actual processing
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    return IngestResponse(
        status="started",
        document_id=request.document_id,
        job_id=job_id,
        trace_id=trace_id
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
    
    # DUMMY: Always return completed status
    return DocumentStatusResponse(
        document_id=document_id,
        status="completed",
        progress=100.0,
        chunks_created=25,
        embeddings_created=25,
        trace_id=trace_id
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
    
    # DUMMY: Return sample document list
    sample_docs = [
        DocumentListItem(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            filename="research_paper.pdf",
            title="Machine Learning Research Paper",
            contentType="application/pdf",
            fileSizeBytes=1024 * 1024 * 2,  # 2MB
            status="completed",
            chunksCount=25,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        ),
        DocumentListItem(
            id=UUID("550e8400-e29b-41d4-a716-446655440001"),
            filename="textbook_chapter.pdf",
            title="Introduction to Algorithms",
            contentType="application/pdf", 
            fileSizeBytes=1024 * 1024 * 5,  # 5MB
            status="processing",
            chunksCount=None,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
    ]
    
    # Apply pagination
    paginated_docs = sample_docs[offset:offset + limit]
    
    return DocumentListResponse(
        documents=paginated_docs,
        totalCount=len(sample_docs),
        trace_id=trace_id
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
    
    # DUMMY: Always return success
    return {
        "message": f"Document {document_id} deleted successfully",
        "trace_id": trace_id
    }