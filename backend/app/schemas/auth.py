"""Authentication schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class Token(BaseModel):
    """OAuth token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data."""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    full_name: Optional[str] = None
    google_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    preferred_name: Optional[str] = None
    neptun_id: Optional[str] = None
    default_timezone: Optional[str] = None
    auto_approve_enabled: Optional[bool] = None
    approval_preview_mode: Optional[str] = None
    link_handling_mode: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    preferred_name: Optional[str] = None
    neptun_id: Optional[str] = None
    default_timezone: str
    auto_approve_enabled: bool
    approval_preview_mode: Optional[str] = "modal"
    link_handling_mode: Optional[str] = "both"
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GoogleOAuthCallback(BaseModel):
    """Google OAuth callback data."""
    code: str
    state: Optional[str] = None

