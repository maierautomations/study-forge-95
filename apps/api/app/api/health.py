"""Health check endpoints"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app import __version__
from app.core.config import get_settings
from app.db.session import test_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    checks: Dict[str, Any]


# Track startup time for uptime calculation
_startup_time = time.time()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # Check if database is configured
        if not settings.database_url or settings.database_url.startswith("postgresql://postgres:password@"):
            return {
                "status": "skipped",
                "response_time_ms": 0,
                "details": "Database not configured"
            }
            
        start_time = time.time()
        is_connected = await test_db_connection()
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "response_time_ms": response_time,
            "details": "Database connection successful" if is_connected else "Database connection failed"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "response_time_ms": 0,
            "details": f"Database health check error: {str(e)}"
        }


async def check_dependencies() -> Dict[str, Any]:
    """Check external dependencies"""
    checks = {}
    
    # Check database
    checks["database"] = await check_database()
    
    # Could add more checks here:
    # - OpenAI API connectivity
    # - Supabase API connectivity
    # - Storage bucket access
    
    return checks


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns API status, version, uptime and dependency checks
    """
    try:
        # Run dependency checks
        checks = await check_dependencies()
        
        # Determine overall status
        overall_status = "healthy"
        for check_name, check_result in checks.items():
            if check_result.get("status") != "healthy":
                overall_status = "degraded"
                break
        
        # Calculate uptime
        uptime = time.time() - _startup_time
        
        return HealthResponse(
            status=overall_status,
            version=__version__,
            timestamp=datetime.utcnow(),
            uptime_seconds=round(uptime, 2),
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=__version__,
            timestamp=datetime.utcnow(),
            uptime_seconds=round(time.time() - _startup_time, 2),
            checks={"error": {"status": "unhealthy", "details": str(e)}}
        )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic availability check
    """
    return {"message": "pong", "timestamp": datetime.utcnow()}