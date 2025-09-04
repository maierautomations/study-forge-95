"""Common models and base classes"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = Field(default=None, description="Request trace ID for debugging")


class ErrorResponse(BaseResponse):
    """Error response model following RFC 7807 Problem Details"""
    type: str = Field(description="Error type URI")
    title: str = Field(description="Human-readable error title")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable error details")
    instance: Optional[str] = Field(default=None, description="URI reference for this error instance")
    errors: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "The request body contains invalid data",
                "instance": "/api/v1/documents/ingest",
                "errors": {
                    "documentId": ["Field is required"]
                },
                "timestamp": "2024-01-01T00:00:00Z",
                "trace_id": "abc123"
            }
        }


class SuccessResponse(BaseResponse):
    """Success response with message"""
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional response data")