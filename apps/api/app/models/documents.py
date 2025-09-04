"""Document-related models"""

from datetime import datetime
from typing import Optional, Literal, List
from uuid import UUID
from pydantic import BaseModel, Field

from .common import BaseResponse


class DocumentBase(BaseModel):
    """Base document model"""
    id: UUID = Field(description="Document unique identifier")
    filename: str = Field(description="Original filename")
    title: Optional[str] = Field(default=None, description="Document title")
    content_type: str = Field(description="MIME type of the document")
    file_size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class IngestRequest(BaseModel):
    """Document ingestion request"""
    document_id: UUID = Field(description="Document ID to ingest", alias="documentId")
    storage_path: str = Field(description="Storage path in Supabase Storage", alias="storagePath")
    mime_type: str = Field(description="MIME type of the document", alias="mime")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "storagePath": "documents/user123/report.pdf",
                "mime": "application/pdf"
            }
        }


class IngestResponse(BaseResponse):
    """Document ingestion response"""
    status: Literal["started"] = Field(description="Ingestion status")
    document_id: UUID = Field(description="Document ID being processed", alias="documentId")
    job_id: str = Field(description="Background job ID for tracking", alias="jobId")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "status": "started",
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "jobId": "job_abc123xyz",
                "timestamp": "2024-01-01T00:00:00Z",
                "trace_id": "trace_123"
            }
        }


class DocumentStatusResponse(BaseResponse):
    """Document processing status response"""
    document_id: UUID = Field(description="Document ID", alias="documentId")
    status: Literal["pending", "processing", "completed", "failed"] = Field(description="Processing status")
    progress: Optional[float] = Field(default=None, description="Progress percentage (0-100)", ge=0, le=100)
    chunks_created: Optional[int] = Field(default=None, description="Number of chunks created", alias="chunksCreated")
    embeddings_created: Optional[int] = Field(default=None, description="Number of embeddings created", alias="embeddingsCreated")
    error_message: Optional[str] = Field(default=None, description="Error message if failed", alias="errorMessage")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "progress": 100.0,
                "chunksCreated": 25,
                "embeddingsCreated": 25,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class DocumentListItem(BaseModel):
    """Document list item for GET /documents"""
    id: UUID = Field(description="Document ID")
    filename: str = Field(description="Original filename")
    title: Optional[str] = Field(default=None, description="Document title")
    content_type: str = Field(description="MIME type", alias="contentType")
    file_size_bytes: Optional[int] = Field(default=None, description="File size", alias="fileSizeBytes")
    status: Literal["pending", "processing", "completed", "failed"] = Field(description="Processing status")
    chunks_count: Optional[int] = Field(default=None, description="Number of chunks", alias="chunksCount")
    created_at: datetime = Field(description="Creation timestamp", alias="createdAt")
    updated_at: datetime = Field(description="Last update timestamp", alias="updatedAt")
    
    class Config:
        populate_by_name = True


class DocumentListResponse(BaseResponse):
    """Document list response"""
    documents: List[DocumentListItem] = Field(description="List of documents")
    total_count: int = Field(description="Total number of documents", alias="totalCount")
    
    class Config:
        populate_by_name = True