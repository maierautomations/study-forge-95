"""Background document processing worker"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from app.services.ingestion import ingest_document_with_storage, IngestionError
from app.db.operations import (
    insert_chunks, 
    insert_embeddings, 
    update_document_status
)

logger = logging.getLogger(__name__)


async def process_document_background(
    document_id: str,
    file_path: str, 
    mime_type: str,
    user_id: str,
    chunk_size: int = 500,
    overlap_ratio: float = 0.15
) -> None:
    """
    Process a document in the background.
    
    This function handles the complete document ingestion pipeline:
    1. Extract text from file
    2. Create chunks 
    3. Generate embeddings
    4. Store chunks and embeddings in database
    5. Update document status
    
    Args:
        document_id: Document UUID
        file_path: Path to the uploaded file
        mime_type: MIME type of the file
        user_id: User UUID who owns the document
        chunk_size: Target tokens per chunk
        overlap_ratio: Overlap between chunks
    """
    logger.info(
        "Starting background document processing",
        extra={
            "document_id": document_id,
            "file_path": file_path,
            "mime_type": mime_type,
            "user_id": user_id
        }
    )
    
    try:
        # Use the ingestion service with database storage
        result = await ingest_document_with_storage(
            document_id=document_id,
            file_path=file_path,
            mime_type=mime_type,
            user_id=user_id,
            store_chunks_func=insert_chunks,
            store_embeddings_func=insert_embeddings,
            update_status_func=lambda doc_id, status, page_count, chunks_count=None, error_msg=None: 
                update_document_status(doc_id, status, page_count, chunks_count, error_msg),
            chunk_size=chunk_size,
            overlap_ratio=overlap_ratio
        )
        
        # Update final document status with chunk count
        await update_document_status(
            document_id=document_id,
            status="completed",
            page_count=result.page_count,
            chunks_count=result.chunks_created
        )
        
        logger.info(
            "Background document processing completed successfully",
            extra={
                "document_id": document_id,
                "chunks_created": result.chunks_created,
                "embeddings_created": result.embeddings_created,
                "page_count": result.page_count,
                "processing_time_seconds": result.processing_time_seconds
            }
        )
        
        # Clean up uploaded file after successful processing
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(
                "Cleaned up uploaded file",
                extra={"document_id": document_id, "file_path": file_path}
            )
        except Exception as cleanup_error:
            logger.warning(
                "Failed to clean up uploaded file",
                extra={
                    "document_id": document_id, 
                    "file_path": file_path,
                    "error": str(cleanup_error)
                }
            )
        
    except IngestionError as e:
        logger.error(
            "Document ingestion failed",
            extra={
                "document_id": document_id,
                "error": str(e),
                "error_type": "IngestionError"
            }
        )
        
        # Update document status to failed
        await update_document_status(
            document_id=document_id,
            status="failed", 
            error_message=str(e)
        )
        
        # Clean up file even on failure
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass  # Ignore cleanup errors on failure
        
    except Exception as e:
        logger.error(
            "Unexpected error during document processing",
            extra={
                "document_id": document_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        
        # Update document status to failed
        await update_document_status(
            document_id=document_id,
            status="failed",
            error_message=f"Unexpected error: {str(e)}"
        )
        
        # Clean up file even on failure
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass


class DocumentProcessor:
    """Document processing worker class for managing concurrent processing"""
    
    def __init__(self, max_concurrent_jobs: int = 3):
        self.max_concurrent_jobs = max_concurrent_jobs
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._active_jobs: set = set()
    
    async def submit_job(
        self,
        document_id: str,
        file_path: str,
        mime_type: str, 
        user_id: str,
        chunk_size: int = 500,
        overlap_ratio: float = 0.15
    ) -> None:
        """
        Submit a document processing job.
        
        This will run the processing in the background with concurrency limits.
        """
        async with self._semaphore:
            job_task = asyncio.create_task(
                process_document_background(
                    document_id=document_id,
                    file_path=file_path,
                    mime_type=mime_type,
                    user_id=user_id,
                    chunk_size=chunk_size,
                    overlap_ratio=overlap_ratio
                )
            )
            
            self._active_jobs.add(job_task)
            
            try:
                await job_task
            finally:
                self._active_jobs.discard(job_task)
    
    def submit_job_nonblocking(
        self,
        document_id: str,
        file_path: str,
        mime_type: str,
        user_id: str,
        chunk_size: int = 500,
        overlap_ratio: float = 0.15
    ) -> asyncio.Task:
        """
        Submit a job without blocking (fire and forget).
        
        Returns:
            asyncio.Task: The background task
        """
        return asyncio.create_task(
            self.submit_job(
                document_id=document_id,
                file_path=file_path,
                mime_type=mime_type,
                user_id=user_id,
                chunk_size=chunk_size,
                overlap_ratio=overlap_ratio
            )
        )
    
    @property
    def active_job_count(self) -> int:
        """Get the number of currently active jobs"""
        return len(self._active_jobs)
    
    async def wait_for_completion(self) -> None:
        """Wait for all active jobs to complete"""
        if self._active_jobs:
            await asyncio.gather(*self._active_jobs, return_exceptions=True)


# Global processor instance
_document_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get the global document processor instance"""
    global _document_processor
    
    if _document_processor is None:
        _document_processor = DocumentProcessor(max_concurrent_jobs=3)
    
    return _document_processor