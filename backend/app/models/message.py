"""Email message model."""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.db import Base


class Message(Base):
    """Email message or uploaded file."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Message metadata
    provider = Column(String(50), default="gmail")  # gmail, outlook, upload
    external_id = Column(String(255), index=True)  # Gmail message ID, etc.
    thread_id = Column(String(255), index=True)
    
    # Email fields
    subject = Column(String(500))
    sender_email = Column(String(255), index=True)
    sender_name = Column(String(255))
    received_at = Column(DateTime)
    
    # Content
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Attachments (JSONB array)
    # [{"filename": "", "mime_type": "", "size": 0, "path": "", "ocr_text": ""}]
    attachments = Column(JSONB, default=list)
    
    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)
    processing_error = Column(Text)
    
    # OCR results
    ocr_confidence = Column(Integer)  # 0-100
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    events = relationship("Event", back_populates="message")

