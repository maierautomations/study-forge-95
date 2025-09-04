"""Authentication and JWT verification using Supabase"""

import logging
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer()


class User(BaseModel):
    """User model from JWT payload"""
    id: str
    email: Optional[str] = None
    role: str = "authenticated"
    
    
class AuthError(Exception):
    """Authentication error"""
    pass


async def verify_supabase_jwt(token: str) -> dict:
    """Verify Supabase JWT token"""
    try:
        # Use Supabase service to verify JWT
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.supabase_anon_key
                }
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data
            else:
                logger.warning(f"JWT verification failed: {response.status_code}")
                raise AuthError("Invalid token")
                
    except httpx.RequestError as e:
        logger.error(f"JWT verification request failed: {e}")
        raise AuthError("Token verification failed")
    except Exception as e:
        logger.error(f"JWT verification error: {e}")
        raise AuthError("Authentication error")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token"""
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_data = await verify_supabase_jwt(credentials.credentials)
        
        return User(
            id=user_data.get("id"),
            email=user_data.get("email"),
            role=user_data.get("role", "authenticated")
        )
        
    except AuthError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user, but don't require authentication"""
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_auth(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires authentication"""
    return user


# Service role authentication for internal operations
async def get_service_role_headers() -> dict:
    """Get headers for Supabase service role requests"""
    return {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": "application/json"
    }