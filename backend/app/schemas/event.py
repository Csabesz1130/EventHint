"""Event/Task Pydantic schemas - the canonical contract."""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
from datetime import datetime
from uuid import UUID


class Reminder(BaseModel):
    """Event reminder configuration."""
    method: Literal["popup", "email"]
    minutes: int = Field(ge=0, description="Minutes before event")


class Attendee(BaseModel):
    """Event attendee information."""
    name: str
    email: str


class EventSource(BaseModel):
    """Source tracking for extracted events."""
    message_id: Optional[str] = None
    provider: Literal["gmail", "outlook", "upload"]
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class EventBase(BaseModel):
    """Base event schema with common fields."""
    type: Literal["event", "task"] = "event"
    title: str = Field(min_length=1, max_length=500)
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    timezone: str = "Europe/Budapest"
    location: Optional[str] = Field(None, max_length=500)
    online_url: Optional[str] = None
    notes: Optional[str] = None
    attendees: List[Attendee] = []
    reminders: List[Reminder] = []
    recurrence: Optional[str] = None  # RRULE format
    labels: List[str] = []

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Ensure end is after start if provided."""
        if v and info.data.get("start") and v < info.data["start"]:
            raise ValueError("end must be after start")
        return v


class EventCreate(EventBase):
    """Schema for creating a new event."""
    source: Optional[EventSource] = None


class EventUpdate(BaseModel):
    """Schema for updating an event (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    allday: Optional[bool] = None
    timezone: Optional[str] = None
    location: Optional[str] = None
    online_url: Optional[str] = None
    notes: Optional[str] = None
    attendees: Optional[List[Attendee]] = None
    reminders: Optional[List[Reminder]] = None
    recurrence: Optional[str] = None
    labels: Optional[List[str]] = None


class EventSchema(EventBase):
    """Complete event schema for responses (includes DB fields)."""
    id: UUID
    user_id: UUID
    status: str
    confidence: float
    extraction_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    external_event_id: Optional[str] = None

    class Config:
        from_attributes = True


class EventApprovalRequest(BaseModel):
    """Request to approve an event with optional modifications."""
    modifications: Optional[EventUpdate] = None
    calendar_id: Optional[UUID] = None  # Which calendar to sync to


class EventApprovalResponse(BaseModel):
    """Response after approving an event."""
    success: bool
    event_id: UUID
    calendar_event_id: Optional[str] = None
    message: str

