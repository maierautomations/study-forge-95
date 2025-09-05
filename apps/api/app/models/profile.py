"""Profile models"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from .common import BaseResponse


class ProfileBase(BaseModel):
    """Base profile model"""
    id: UUID = Field(description="Profile ID")
    user_id: UUID = Field(description="User ID", alias="userId")
    display_name: Optional[str] = Field(default=None, description="Display name", alias="displayName")
    created_at: datetime = Field(description="Creation timestamp", alias="createdAt")
    updated_at: datetime = Field(description="Last update timestamp", alias="updatedAt")
    
    class Config:
        populate_by_name = True


class ProfileResponse(BaseResponse):
    """Profile response"""
    id: UUID = Field(description="Profile ID")
    user_id: UUID = Field(description="User ID", alias="userId")
    display_name: Optional[str] = Field(default=None, description="Display name", alias="displayName")
    created_at: datetime = Field(description="Creation timestamp", alias="createdAt")
    updated_at: datetime = Field(description="Last update timestamp", alias="updatedAt")
    
    class Config:
        populate_by_name = True


class ProfileUpdateRequest(BaseModel):
    """Profile update request"""
    display_name: Optional[str] = Field(default=None, description="Display name", alias="displayName")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "displayName": "John Doe"
            }
        }