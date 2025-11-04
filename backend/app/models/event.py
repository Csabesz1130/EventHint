"""Event and Task models."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.db import Base


class EventType(str, enum.Enum):
    """Event type enumeration."""
    EVENT = "event"
    TASK = "task"


class EventStatus(str, enum.Enum):
    """Event processing status."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SYNCED = "synced"
    ERROR = "error"


class Event(Base):
    """Event/Task model (draft and final)."""
    
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Event data
    type = Column(Enum(EventType), default=EventType.EVENT, nullable=False)
    title = Column(String(500), nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True))
    allday = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Budapest")
    
    location = Column(String(500))
    online_url = Column(Text)
    notes = Column(Text)
    
    # JSONB fields for complex data
    attendees = Column(JSONB, default=list)  # [{"name": "", "email": ""}]
    reminders = Column(JSONB, default=list)  # [{"method": "popup", "minutes": 30}]
    labels = Column(JSONB, default=list)  # ["exam", "deadline", ...]
    
    # Recurrence
    recurrence = Column(String(500))  # RRULE format
    
    # Source tracking
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
    provider = Column(String(50), default="gmail")  # gmail, outlook, upload
    confidence = Column(Float, default=0.0)
    extraction_method = Column(String(50))  # deterministic, llm, hybrid
    
    # Status
    status = Column(Enum(EventStatus), default=EventStatus.PENDING_APPROVAL, index=True)
    
    # Calendar sync
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id"))
    external_event_id = Column(String(255))  # ID in Google Calendar, etc.
    synced_at = Column(DateTime)
    
    # Audit
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="events")
    message = relationship("Message", back_populates="events")
    calendar = relationship("Calendar", back_populates="events")

