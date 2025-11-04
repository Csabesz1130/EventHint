"""Events API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.event import Event, EventStatus
from app.schemas.event import (
    EventSchema,
    EventCreate,
    EventUpdate,
    EventApprovalRequest,
    EventApprovalResponse,
)

router = APIRouter()


@router.get("/", response_model=List[EventSchema])
async def list_events(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events for the current user."""
    query = db.query(Event).filter(Event.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Event.status == status_filter)
    
    events = query.order_by(Event.start.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=EventSchema)
async def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific event."""
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    return event


@router.post("/", response_model=EventSchema, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new event (usually from extraction pipeline)."""
    event = Event(
        user_id=current_user.id,
        type=event_data.type,
        title=event_data.title,
        start=event_data.start,
        end=event_data.end,
        allday=event_data.allday,
        timezone=event_data.timezone,
        location=event_data.location,
        online_url=event_data.online_url,
        notes=event_data.notes,
        attendees=[att.model_dump() for att in event_data.attendees],
        reminders=[rem.model_dump() for rem in event_data.reminders],
        labels=event_data.labels,
        recurrence=event_data.recurrence,
    )
    
    if event_data.source:
        event.provider = event_data.source.provider
        event.confidence = event_data.source.confidence
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event


@router.patch("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an event."""
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    # Update fields
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "attendees" and value is not None:
            value = [att.model_dump() if hasattr(att, "model_dump") else att for att in value]
        if field == "reminders" and value is not None:
            value = [rem.model_dump() if hasattr(rem, "model_dump") else rem for rem in value]
        setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    
    return event


@router.post("/{event_id}/approve", response_model=EventApprovalResponse)
async def approve_event(
    event_id: UUID,
    approval_data: Optional[EventApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a pending event and sync to calendar.
    Optionally apply inline edits before syncing.
    """
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    if event.status != EventStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event is not pending approval (status: {event.status})",
        )
    
    # Apply modifications if provided
    if approval_data and approval_data.modifications:
        update_data = approval_data.modifications.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "attendees" and value is not None:
                value = [att.model_dump() if hasattr(att, "model_dump") else att for att in value]
            if field == "reminders" and value is not None:
                value = [rem.model_dump() if hasattr(rem, "model_dump") else rem for rem in value]
            setattr(event, field, value)
    
    # Update status
    from datetime import datetime
    event.status = EventStatus.APPROVED
    event.approved_at = datetime.utcnow()
    
    db.commit()
    
    # Trigger calendar sync task
    from app.tasks.sync_calendar import sync_event_to_calendar
    sync_event_to_calendar.delay(str(event.id), str(approval_data.calendar_id) if approval_data and approval_data.calendar_id else None)
    
    return EventApprovalResponse(
        success=True,
        event_id=event.id,
        calendar_event_id=None,  # Will be populated after sync
        message="Event approved successfully",
    )


@router.post("/{event_id}/reject")
async def reject_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending event."""
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    from datetime import datetime
    event.status = EventStatus.REJECTED
    event.rejected_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": "Event rejected"}


@router.delete("/{event_id}")
async def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an event."""
    event = (
        db.query(Event)
        .filter(Event.id == event_id, Event.user_id == current_user.id)
        .first()
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    db.delete(event)
    db.commit()
    
    return {"success": True, "message": "Event deleted"}

