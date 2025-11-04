"""Message schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AttachmentInfo(BaseModel):
    """Attachment metadata."""
    filename: str
    mime_type: str
    size: int
    path: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None


class MessageResponse(BaseModel):
    """Email message response schema."""
    id: UUID
    user_id: UUID
    provider: str
    external_id: Optional[str] = None
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    received_at: Optional[datetime] = None
    body_text: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageUpload(BaseModel):
    """Schema for uploading a message/file."""
    content_type: str
    filename: Optional[str] = None


class EventBrief(BaseModel):
    """Brief event info for message listing."""
    id: UUID
    type: str
    title: str
    start: datetime
    end: Optional[datetime] = None
    allday: bool
    timezone: str
    location: Optional[str] = None
    online_url: Optional[str] = None
    notes: Optional[str] = None
    status: str
    confidence: float
    labels: List[str] = []

    class Config:
        from_attributes = True


class MessageWithEvents(BaseModel):
    """Message with its extracted events."""
    id: UUID
    user_id: UUID
    provider: str
    external_id: Optional[str] = None
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    received_at: Optional[datetime] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime
    events: List[EventBrief] = []

    class Config:
        from_attributes = True
