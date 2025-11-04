"""Messages API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.message import Message
from app.schemas.message import MessageResponse, MessageWithEvents

router = APIRouter()


@router.get("/", response_model=List[MessageWithEvents])
async def list_messages(
    skip: int = 0,
    limit: int = 50,
    provider: Optional[str] = Query(None),
    processed_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List messages for the current user with their extracted events.
    
    Args:
        skip: Number of messages to skip
        limit: Maximum number of messages to return
        provider: Filter by provider (gmail, website, upload)
        processed_only: Only return processed messages
    """
    query = db.query(Message).filter(Message.user_id == current_user.id)
    
    if provider:
        query = query.filter(Message.provider == provider)
    
    if processed_only:
        query = query.filter(Message.processed == True)
    
    messages = (
        query
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Build response with events
    result = []
    for message in messages:
        result.append({
            "id": message.id,
            "user_id": message.user_id,
            "provider": message.provider,
            "external_id": message.external_id,
            "subject": message.subject,
            "sender_email": message.sender_email,
            "sender_name": message.sender_name,
            "received_at": message.received_at,
            "body_text": message.body_text,
            "body_html": message.body_html,
            "attachments": message.attachments,
            "processed": message.processed,
            "processed_at": message.processed_at,
            "created_at": message.created_at,
            "events": [
                {
                    "id": event.id,
                    "type": event.type,
                    "title": event.title,
                    "start": event.start,
                    "end": event.end,
                    "allday": event.allday,
                    "timezone": event.timezone,
                    "location": event.location,
                    "online_url": event.online_url,
                    "notes": event.notes,
                    "status": event.status,
                    "confidence": event.confidence,
                    "labels": event.labels,
                }
                for event in message.events
            ],
        })
    
    return result


@router.get("/{message_id}", response_model=MessageWithEvents)
async def get_message(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific message with its events."""
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.user_id == current_user.id)
        .first()
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    return {
        "id": message.id,
        "user_id": message.user_id,
        "provider": message.provider,
        "external_id": message.external_id,
        "subject": message.subject,
        "sender_email": message.sender_email,
        "sender_name": message.sender_name,
        "received_at": message.received_at,
        "body_text": message.body_text,
        "body_html": message.body_html,
        "attachments": message.attachments,
        "processed": message.processed,
        "processed_at": message.processed_at,
        "created_at": message.created_at,
        "events": [
            {
                "id": event.id,
                "type": event.type,
                "title": event.title,
                "start": event.start,
                "end": event.end,
                "allday": event.allday,
                "timezone": event.timezone,
                "location": event.location,
                "online_url": event.online_url,
                "notes": event.notes,
                "status": event.status,
                "confidence": event.confidence,
                "labels": event.labels,
            }
            for event in message.events
        ],
    }

