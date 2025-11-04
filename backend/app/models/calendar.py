"""Calendar connection model."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.db import Base


class Calendar(Base):
    """Connected calendar (Google, Microsoft, etc.)."""
    
    __tablename__ = "calendars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Calendar info
    provider = Column(String(50), nullable=False)  # google, microsoft, caldav
    external_id = Column(String(255), nullable=False)  # Calendar ID from provider
    name = Column(String(255), nullable=False)
    color = Column(String(20))
    
    # Access credentials (encrypted)
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expiry = Column(DateTime)
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)
    
    # Metadata
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="calendars")
    events = relationship("Event", back_populates="calendar")

