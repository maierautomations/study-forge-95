"""Profile management endpoints"""

import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from app.models.profile import (
    ProfileResponse,
    ProfileUpdateRequest
)
from app.api.deps import get_current_user_id, get_trace_id

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Get user profile
    
    Returns the current user's profile information.
    """
    logger.info(
        "Profile requested",
        extra={
            "trace_id": trace_id,
            "user_id": str(user_id)
        }
    )
    
    # DUMMY: Return sample profile data
    return ProfileResponse(
        id=UUID("770e8400-e29b-41d4-a716-446655440000"),
        userId=user_id,
        displayName="Demo User",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow(),
        trace_id=trace_id
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Update user profile
    
    Updates the current user's profile information.
    """
    logger.info(
        "Profile update requested",
        extra={
            "trace_id": trace_id,
            "user_id": str(user_id),
            "display_name": request.display_name
        }
    )
    
    # DUMMY: Return updated profile data
    return ProfileResponse(
        id=UUID("770e8400-e29b-41d4-a716-446655440000"),
        userId=user_id,
        displayName=request.display_name or "Demo User",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow(),
        trace_id=trace_id
    )