"""Base calendar provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class CalendarProvider(ABC):
    """
    Abstract base class for calendar providers.
    
    Implementations:
    - GoogleCalendarService: Google Calendar
    - OutlookCalendarService: Microsoft Outlook/365 (future)
    - CalDAVService: Apple Calendar via CalDAV (future)
    """
    
    @abstractmethod
    def create_event(self, event_data: Dict[str, Any]) -> str:
        """
        Create a calendar event.
        
        Args:
            event_data: Event dictionary matching our schema
        
        Returns:
            External event ID from calendar provider
        """
        pass
    
    @abstractmethod
    def update_event(self, external_id: str, event_data: Dict[str, Any]) -> None:
        """
        Update an existing calendar event.
        
        Args:
            external_id: Event ID in the calendar provider
            event_data: Updated event data
        """
        pass
    
    @abstractmethod
    def delete_event(self, external_id: str) -> None:
        """
        Delete a calendar event.
        
        Args:
            external_id: Event ID in the calendar provider
        """
        pass
    
    @abstractmethod
    def get_event(self, external_id: str) -> Dict[str, Any]:
        """
        Fetch an event from the calendar.
        
        Args:
            external_id: Event ID in the calendar provider
        
        Returns:
            Event data dictionary
        """
        pass
    
    @abstractmethod
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List available calendars for the user.
        
        Returns:
            List of calendar dictionaries
        """
        pass

