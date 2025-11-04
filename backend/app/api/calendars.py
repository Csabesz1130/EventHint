"""Calendar management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.calendar import Calendar

router = APIRouter()


@router.get("/")
async def list_calendars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List connected calendars for the current user."""
    calendars = (
        db.query(Calendar)
        .filter(Calendar.user_id == current_user.id, Calendar.is_active == True)
        .all()
    )
    
    return [
        {
            "id": str(cal.id),
            "provider": cal.provider,
            "name": cal.name,
            "color": cal.color,
            "is_default": cal.is_default,
            "last_sync": cal.last_sync,
        }
        for cal in calendars
    ]


@router.post("/{calendar_id}/set-default")
async def set_default_calendar(
    calendar_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set a calendar as the default for new events."""
    # Unset all defaults
    db.query(Calendar).filter(Calendar.user_id == current_user.id).update(
        {"is_default": False}
    )
    
    # Set new default
    calendar = (
        db.query(Calendar)
        .filter(Calendar.id == calendar_id, Calendar.user_id == current_user.id)
        .first()
    )
    
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    
    calendar.is_default = True
    db.commit()
    
    return {"success": True, "message": "Default calendar updated"}

