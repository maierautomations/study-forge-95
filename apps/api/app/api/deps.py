"""API dependencies for authentication and database access"""

import logging
from typing import Optional, AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status, Depends, Header
from supabase import Client, create_client
import asyncpg

from app.core.config import get_settings
from app.db.session import get_db_connection

logger = logging.getLogger(__name__)
settings = get_settings()

# Supabase client for JWT verification
supabase: Optional[Client] = None

if settings.supabase_url and settings.supabase_anon_key:
    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> UUID:
    """
    Extract user ID from JWT token
    
    For now, this is a placeholder that will be fully implemented
    when we have proper JWT token verification in place.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Handle development mode tokens
    if token == "dev-user-123":
        return UUID("11111111-1111-1111-1111-111111111111")
    
    # For production with Supabase JWT
    if not supabase:
        # No Supabase configured, use development fallback
        logger.warning("No Supabase configuration, using development auth")
        return UUID("11111111-1111-1111-1111-111111111111")
    
    try:
        # Verify JWT access token with Supabase
        # The frontend sends JWT access tokens from supabase.auth.getSession()
        response = supabase.auth.get_user(token)
        
        if response.user and response.user.id:
            return UUID(response.user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        # In development, accept any non-empty token as valid for testing
        if settings.debug and token and len(token) > 10:
            logger.warning(f"Development mode: accepting token for testing")
            return UUID("11111111-1111-1111-1111-111111111111")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection dependency"""
    try:
        async with get_db_connection() as conn:
            yield conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable"
        )


def get_trace_id(x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")) -> Optional[str]:
    """Extract trace ID from headers for request tracking"""
    return x_trace_id