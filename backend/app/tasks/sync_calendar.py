"""Celery tasks for syncing events to calendars."""

from celery import Task
from datetime import datetime
import logging

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.models.event import Event, EventStatus
from app.models.calendar import Calendar
from app.models.user import User

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""
    
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def sync_event_to_calendar(self, event_id: str, calendar_id: str = None):
    """
    Sync an approved event to the user's calendar.
    
    Args:
        event_id: UUID of the event to sync
        calendar_id: Optional specific calendar ID; uses default if not provided
    """
    db = self.db
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            logger.error(f"Event {event_id} not found")
            return
        
        if event.status != EventStatus.APPROVED:
            logger.warning(f"Event {event_id} is not approved (status: {event.status})")
            return
        
        # Get calendar
        if calendar_id:
            calendar = db.query(Calendar).filter(Calendar.id == calendar_id).first()
        else:
            calendar = (
                db.query(Calendar)
                .filter(
                    Calendar.user_id == event.user_id,
                    Calendar.is_default == True,
                    Calendar.is_active == True,
                )
                .first()
            )
        
        if not calendar:
            logger.error(f"No calendar found for event {event_id}")
            event.status = EventStatus.ERROR
            db.commit()
            return
        
        logger.info(f"Syncing event {event_id} to calendar {calendar.name}")
        
        # Sync to Google Calendar
        from app.services.calendar.google import GoogleCalendarService
        from app.models.user import User
        
        user = db.query(User).filter(User.id == event.user_id).first()
        if not user:
            logger.error(f"User not found for event {event_id}")
            event.status = EventStatus.ERROR
            db.commit()
            return
        
        calendar_service = GoogleCalendarService(user, calendar)
        
        # Convert event to dict for calendar service
        event_dict = {
            "type": event.type,
            "title": event.title,
            "start": event.start.isoformat(),
            "end": event.end.isoformat() if event.end else None,
            "allday": event.allday,
            "timezone": event.timezone,
            "location": event.location,
            "online_url": event.online_url,
            "notes": event.notes,
            "attendees": event.attendees,
            "reminders": event.reminders,
            "recurrence": event.recurrence,
            "labels": event.labels,
        }
        
        external_id = calendar_service.create_event(event_dict)
        
        # Mark as synced
        event.status = EventStatus.SYNCED
        event.synced_at = datetime.utcnow()
        event.calendar_id = calendar.id
        event.external_event_id = external_id
        
        db.commit()
        logger.info(f"Event {event_id} synced successfully to Google Calendar: {external_id}")
        
    except Exception as e:
        logger.error(f"Error syncing event {event_id}: {str(e)}")
        event.status = EventStatus.ERROR
        db.commit()
        raise


@celery_app.task(base=DatabaseTask, bind=True)
def undo_calendar_event(self, event_id: str):
    """
    Undo/delete a calendar event.
    
    Args:
        event_id: UUID of the event to undo
    """
    db = self.db
    
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            logger.error(f"Event {event_id} not found")
            return
        
        if not event.external_event_id:
            logger.info(f"Event {event_id} not synced to calendar, just deleting")
            db.delete(event)
            db.commit()
            return
        
        # Delete from calendar provider
        from app.services.calendar.google import GoogleCalendarService
        from app.models.user import User
        
        calendar = db.query(Calendar).filter(Calendar.id == event.calendar_id).first()
        if calendar:
            user = db.query(User).filter(User.id == event.user_id).first()
            if user:
                try:
                    calendar_service = GoogleCalendarService(user, calendar)
                    calendar_service.delete_event(event.external_event_id)
                except Exception as e:
                    logger.warning(f"Failed to delete from calendar: {str(e)}")
        
        db.delete(event)
        db.commit()
        
        logger.info(f"Event {event_id} undone and deleted")
        
    except Exception as e:
        logger.error(f"Error undoing event {event_id}: {str(e)}")
        raise

