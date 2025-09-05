"""Main document ingestion orchestrator service"""

import logging
import asyncio
from typing import Optional, List, Tuple
from uuid import UUID
from pathlib import Path

from .extraction import extract_text_from_file, ExtractedContent
from .chunking import create_chunks, ChunkData
from .embeddings import generate_embeddings

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when document ingestion fails"""
    pass


class IngestionResult:
    """Result of document ingestion process"""
    
    def __init__(
        self,
        document_id: str,
        success: bool,
        chunks_created: int = 0,
        embeddings_created: int = 0,
        page_count: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_time_seconds: float = 0.0
    ):
        self.document_id = document_id
        self.success = success
        self.chunks_created = chunks_created
        self.embeddings_created = embeddings_created
        self.page_count = page_count
        self.error_message = error_message
        self.processing_time_seconds = processing_time_seconds


async def ingest_document(
    document_id: str,
    file_path: str,
    mime_type: str,
    user_id: str,
    chunk_size: int = 500,
    overlap_ratio: float = 0.15
) -> IngestionResult:
    """
    Complete document ingestion pipeline.
    
    Process:
    1. Extract text from file (PDF/DOCX → structured text)
    2. Create chunks (text → 300-800 token chunks with overlap)
    3. Generate embeddings (chunks → vectors)
    4. Return processing results
    
    Args:
        document_id: Unique document identifier
        file_path: Path to the document file
        mime_type: MIME type of the document
        user_id: ID of the user who owns the document
        chunk_size: Target tokens per chunk
        overlap_ratio: Overlap between chunks (0.0-1.0)
        
    Returns:
        IngestionResult: Results of the ingestion process
        
    Raises:
        IngestionError: If ingestion fails
    """
    import time
    start_time = time.time()
    
    logger.info(
        "Document ingestion started",
        extra={
            "document_id": document_id,
            "file_path": file_path,
            "mime_type": mime_type,
            "user_id": user_id,
            "chunk_size": chunk_size,
            "overlap_ratio": overlap_ratio
        }
    )
    
    try:
        # Step 1: Extract text from document
        logger.info("Starting text extraction", extra={"document_id": document_id})
        extracted_content = await extract_text_from_file(file_path, mime_type)
        
        if not extracted_content.sections:
            raise IngestionError("No content could be extracted from the document")
        
        logger.info(
            "Text extraction completed",
            extra={
                "document_id": document_id,
                "section_count": len(extracted_content.sections),
                "page_count": extracted_content.page_count,
                "title": extracted_content.title
            }
        )
        
        # Step 2: Create chunks
        logger.info("Starting text chunking", extra={"document_id": document_id})
        chunks = create_chunks(
            extracted_content,
            chunk_size=chunk_size,
            overlap_ratio=overlap_ratio
        )
        
        if not chunks:
            raise IngestionError("No chunks could be created from the extracted content")
        
        logger.info(
            "Text chunking completed",
            extra={
                "document_id": document_id,
                "chunk_count": len(chunks),
                "avg_chunk_size": sum(c.token_count for c in chunks) / len(chunks),
                "total_tokens": sum(c.token_count for c in chunks)
            }
        )
        
        # Step 3: Generate embeddings
        logger.info("Starting embedding generation", extra={"document_id": document_id})
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await generate_embeddings(chunk_texts)
        
        if len(embeddings) != len(chunks):
            raise IngestionError(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)} chunks")
        
        logger.info(
            "Embedding generation completed",
            extra={
                "document_id": document_id,
                "embedding_count": len(embeddings),
                "embedding_dimension": len(embeddings[0]) if embeddings else 0
            }
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create successful result
        result = IngestionResult(
            document_id=document_id,
            success=True,
            chunks_created=len(chunks),
            embeddings_created=len(embeddings),
            page_count=extracted_content.page_count,
            processing_time_seconds=processing_time
        )
        
        logger.info(
            "Document ingestion completed successfully",
            extra={
                "document_id": document_id,
                "chunks_created": result.chunks_created,
                "embeddings_created": result.embeddings_created,
                "page_count": result.page_count,
                "processing_time_seconds": result.processing_time_seconds
            }
        )
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = str(e)
        
        logger.error(
            "Document ingestion failed",
            extra={
                "document_id": document_id,
                "error": error_message,
                "error_type": type(e).__name__,
                "processing_time_seconds": processing_time
            }
        )
        
        # Create failed result
        result = IngestionResult(
            document_id=document_id,
            success=False,
            error_message=error_message,
            processing_time_seconds=processing_time
        )
        
        raise IngestionError(f"Document ingestion failed: {error_message}") from e


async def ingest_document_with_storage(
    document_id: str,
    file_path: str,
    mime_type: str,
    user_id: str,
    store_chunks_func,
    store_embeddings_func,
    update_status_func,
    chunk_size: int = 500,
    overlap_ratio: float = 0.15
) -> IngestionResult:
    """
    Complete document ingestion with database storage.
    
    This version includes database storage operations and is meant to be used
    by the background processing worker.
    
    Args:
        document_id: Unique document identifier
        file_path: Path to the document file
        mime_type: MIME type of the document
        user_id: ID of the user who owns the document
        store_chunks_func: Async function to store chunks in database
        store_embeddings_func: Async function to store embeddings in database
        update_status_func: Async function to update document status
        chunk_size: Target tokens per chunk
        overlap_ratio: Overlap between chunks
        
    Returns:
        IngestionResult: Results of the ingestion process
    """
    try:
        # Update status to processing
        await update_status_func(document_id, "processing", None)
        
        # Run the core ingestion pipeline
        result = await ingest_document(
            document_id=document_id,
            file_path=file_path,
            mime_type=mime_type,
            user_id=user_id,
            chunk_size=chunk_size,
            overlap_ratio=overlap_ratio
        )
        
        if result.success:
            # Re-extract chunks and embeddings for storage
            # (In production, you'd pass these through or refactor)
            extracted_content = await extract_text_from_file(file_path, mime_type)
            chunks = create_chunks(extracted_content, chunk_size, overlap_ratio)
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await generate_embeddings(chunk_texts)
            
            # Store in database
            chunk_ids = await store_chunks_func(document_id, chunks)
            await store_embeddings_func(chunk_ids, embeddings)
            
            # Update status to completed
            await update_status_func(
                document_id,
                "completed", 
                result.page_count
            )
        
        return result
        
    except Exception as e:
        # Update status to error
        await update_status_func(document_id, "failed", None)
        raise


def validate_file_for_ingestion(file_path: str, mime_type: str) -> bool:
    """
    Validate that a file can be processed for ingestion.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type of the file
        
    Returns:
        bool: True if file can be processed
    """
    # Check file exists
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False
    
    # Check file size (max 100MB)
    file_size = path.stat().st_size
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        logger.error(f"File too large: {file_size} bytes (max: {max_size})")
        return False
    
    # Check MIME type
    supported_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown"
    ]
    
    if mime_type not in supported_types:
        logger.error(f"Unsupported MIME type: {mime_type}")
        return False
    
    return True