"""Google Calendar API integration."""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.calendar.base import CalendarProvider
from app.core.security import token_encryption
from app.models.calendar import Calendar
from app.models.user import User

logger = logging.getLogger(__name__)


class GoogleCalendarService(CalendarProvider):
    """
    Google Calendar API service.
    
    Features:
    - Create events with reminders
    - Update and delete events
    - Handle recurrence rules
    - Support multiple calendars
    """
    
    def __init__(self, user: User, calendar: Optional[Calendar] = None):
        """
        Initialize Google Calendar service.
        
        Args:
            user: User model with Google tokens
            calendar: Specific calendar to use (uses primary if None)
        """
        self.user = user
        self.calendar = calendar
        self.calendar_id = calendar.external_id if calendar else 'primary'
        
        # Decrypt tokens
        access_token = token_encryption.decrypt(user.google_access_token)
        refresh_token = (
            token_encryption.decrypt(user.google_refresh_token)
            if user.google_refresh_token
            else None
        )
        
        # Create credentials
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id="",
            client_secret="",
        )
        
        # Build Calendar API service
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def create_event(self, event_data: Dict[str, Any]) -> str:
        """
        Create a Google Calendar event.
        
        Args:
            event_data: Event dictionary from our schema
        
        Returns:
            Google Calendar event ID
        """
        try:
            # Convert our schema to Google Calendar format
            gcal_event = self._convert_to_gcal_format(event_data)
            
            # Create event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=gcal_event
            ).execute()
            
            logger.info(
                f"Created Google Calendar event: {created_event['id']} "
                f"for user {self.user.id}"
            )
            
            return created_event['id']
            
        except HttpError as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            raise
    
    def update_event(self, external_id: str, event_data: Dict[str, Any]) -> None:
        """Update an existing Google Calendar event."""
        try:
            # Convert to Google Calendar format
            gcal_event = self._convert_to_gcal_format(event_data)
            
            # Update event
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=external_id,
                body=gcal_event
            ).execute()
            
            logger.info(f"Updated Google Calendar event: {external_id}")
            
        except HttpError as e:
            logger.error(f"Error updating Google Calendar event: {str(e)}")
            raise
    
    def delete_event(self, external_id: str) -> None:
        """Delete a Google Calendar event."""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=external_id
            ).execute()
            
            logger.info(f"Deleted Google Calendar event: {external_id}")
            
        except HttpError as e:
            logger.error(f"Error deleting Google Calendar event: {str(e)}")
            raise
    
    def get_event(self, external_id: str) -> Dict[str, Any]:
        """Fetch a Google Calendar event."""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=external_id
            ).execute()
            
            return event
            
        except HttpError as e:
            logger.error(f"Error fetching Google Calendar event: {str(e)}")
            raise
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars for the user."""
        try:
            calendar_list = self.service.calendarList().list().execute()
            
            calendars = []
            for cal in calendar_list.get('items', []):
                calendars.append({
                    'id': cal['id'],
                    'name': cal['summary'],
                    'color': cal.get('backgroundColor', '#000000'),
                    'primary': cal.get('primary', False),
                })
            
            return calendars
            
        except HttpError as e:
            logger.error(f"Error listing Google Calendars: {str(e)}")
            raise
    
    def _convert_to_gcal_format(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert our event schema to Google Calendar API format.
        
        Our schema → Google Calendar schema mapping:
        - title → summary
        - notes → description
        - start/end → start/end with dateTime or date
        - location → location
        - online_url → conferenceData or description
        - reminders → reminders.overrides
        - recurrence → recurrence (RRULE)
        """
        gcal_event = {
            'summary': event_data.get('title', 'Untitled Event'),
            'description': event_data.get('notes', ''),
            'location': event_data.get('location', ''),
        }
        
        # Handle all-day vs timed events
        if event_data.get('allday'):
            # All-day event uses 'date' field (YYYY-MM-DD)
            start_dt = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            gcal_event['start'] = {'date': start_dt.strftime('%Y-%m-%d')}
            
            if event_data.get('end'):
                end_dt = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
                gcal_event['end'] = {'date': end_dt.strftime('%Y-%m-%d')}
            else:
                gcal_event['end'] = gcal_event['start']
        else:
            # Timed event uses 'dateTime' field
            gcal_event['start'] = {
                'dateTime': event_data['start'],
                'timeZone': event_data.get('timezone', 'Europe/Budapest'),
            }
            
            if event_data.get('end'):
                gcal_event['end'] = {
                    'dateTime': event_data['end'],
                    'timeZone': event_data.get('timezone', 'Europe/Budapest'),
                }
            else:
                # Default 1 hour duration
                from datetime import timedelta
                start_dt = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                gcal_event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': event_data.get('timezone', 'Europe/Budapest'),
                }
        
        # Reminders
        if event_data.get('reminders'):
            gcal_event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {
                        'method': 'popup' if r['method'] == 'popup' else 'email',
                        'minutes': r['minutes'],
                    }
                    for r in event_data['reminders']
                ],
            }
        
        # Recurrence
        if event_data.get('recurrence'):
            gcal_event['recurrence'] = [event_data['recurrence']]
        
        # Online URL (add to description if present)
        if event_data.get('online_url'):
            online_note = f"\n\nJoin: {event_data['online_url']}"
            gcal_event['description'] = (gcal_event.get('description', '') + online_note).strip()
        
        # Attendees
        if event_data.get('attendees'):
            gcal_event['attendees'] = [
                {'email': att['email'], 'displayName': att.get('name', '')}
                for att in event_data['attendees']
            ]
        
        # Color (based on labels)
        labels = event_data.get('labels', [])
        if 'exam' in labels:
            gcal_event['colorId'] = '11'  # Red
        elif 'meeting' in labels:
            gcal_event['colorId'] = '9'   # Blue
        elif 'deadline' in labels:
            gcal_event['colorId'] = '6'   # Orange
        
        return gcal_event

