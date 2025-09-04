"""Schema validation endpoints"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.db.validation import validate_schema_complete

logger = logging.getLogger(__name__)
router = APIRouter()


class SchemaValidationResponse(BaseModel):
    """Schema validation response model"""
    overall_status: str
    failed_checks: list
    summary: Dict[str, Any]
    detailed_results: Dict[str, Any]


@router.get("/validate", response_model=SchemaValidationResponse)
async def validate_schema():
    """
    Validate database schema according to P1.1 requirements
    
    Performs comprehensive validation of:
    - Required tables (chunks, embeddings) exist
    - Required indexes (BM25 GIN, Vector IVFFLAT) exist  
    - RLS policies are enabled and configured
    
    Returns detailed validation results for debugging and monitoring.
    """
    try:
        result = await validate_schema_complete()
        
        return SchemaValidationResponse(
            overall_status=result["overall_status"],
            failed_checks=result["failed_checks"],
            summary=result["summary"],
            detailed_results=result["detailed_results"]
        )
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return SchemaValidationResponse(
            overall_status="error",
            failed_checks=["validation_error"],
            summary={
                "tables_exist": False,
                "indexes_exist": False, 
                "rls_enabled": False
            },
            detailed_results={
                "error": {
                    "status": "error",
                    "details": f"Schema validation error: {str(e)}"
                }
            }
        )