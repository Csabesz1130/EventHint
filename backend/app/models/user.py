"""User model."""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.db import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    
    # Profile info for matching (e.g., Neptun ID, preferred name)
    neptun_id = Column(String(20), index=True)
    preferred_name = Column(String(255))
    
    # OAuth tokens (encrypted)
    google_id = Column(String(255), unique=True, index=True)
    google_access_token = Column(Text)  # Encrypted
    google_refresh_token = Column(Text)  # Encrypted
    google_token_expiry = Column(DateTime)
    
    # Settings
    default_timezone = Column(String(50), default="Europe/Budapest")
    auto_approve_enabled = Column(Boolean, default=False)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    calendars = relationship("Calendar", back_populates="user", cascade="all, delete-orphan")

