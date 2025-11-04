"""English/international extraction patterns."""

import re
import dateparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_english_patterns(text: str, timezone: str = "UTC") -> List[Dict[str, Any]]:
    """
    Extract events from English text using common patterns.
    
    Patterns:
    - Meeting: [Title] on [Date] at [Time]
    - Flight: [Airline] [Number] from [Origin] to [Dest] on [Date] at [Time]
    - Deadline: [Task] due [Date]
    """
    events = []
    
    # Try meeting patterns
    meeting_events = _extract_meetings(text, timezone)
    events.extend(meeting_events)
    
    # Try flight patterns
    flight_events = _extract_flights(text, timezone)
    events.extend(flight_events)
    
    # Try deadline patterns
    deadline_events = _extract_deadlines(text, timezone)
    events.extend(deadline_events)
    
    return events


def _extract_meetings(text: str, timezone: str) -> List[Dict[str, Any]]:
    """
    Extract meeting events.
    
    Patterns:
    - "Meeting: [Title] on [Date] at [Time]"
    - "[Title] meeting [Date] [Time]"
    """
    events = []
    
    meeting_patterns = [
        r"(?i)meeting[:\s]+([^\.]+?)(?:\s+on\s+|\s+)(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})(?:\s+at\s+|\s+)(\d{1,2}:\d{2}\s*(?:AM|PM)?)",
        r"(?i)(\w+.*?)\s+meeting\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+(?:at\s+)?(\d{1,2}:\d{2}\s*(?:AM|PM)?)",
    ]
    
    for pattern in meeting_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            title = match.group(1).strip()
            date_str = match.group(2)
            time_str = match.group(3)
            
            # Parse datetime
            full_datetime_str = f"{date_str} {time_str}"
            dt = dateparser.parse(
                full_datetime_str,
                settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True}
            )
            
            if dt:
                events.append({
                    "type": "event",
                    "title": f"{title} meeting" if "meeting" not in title.lower() else title,
                    "start": dt.isoformat(),
                    "end": (dt + timedelta(hours=1)).isoformat(),
                    "timezone": timezone,
                    "labels": ["meeting"],
                    "reminders": [
                        {"method": "popup", "minutes": 15},
                    ],
                })
    
    return events


def _extract_flights(text: str, timezone: str) -> List[Dict[str, Any]]:
    """
    Extract flight events.
    
    Patterns:
    - "Flight [Airline] [Number] from [Origin] to [Dest] on [Date] at [Time]"
    - "[Airline] [Number]: [Origin] -> [Dest] [Date] [Time]"
    """
    events = []
    
    flight_pattern = r"(?i)(?:flight\s+)?([A-Z]{2}\s*\d{3,4}).*?(?:from\s+)?([A-Z]{3}).*?(?:to\s+)?([A-Z]{3}).*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+(?:at\s+)?(\d{1,2}:\d{2}\s*(?:AM|PM)?)"
    
    matches = re.finditer(flight_pattern, text)
    for match in matches:
        flight_number = match.group(1).strip()
        origin = match.group(2)
        destination = match.group(3)
        date_str = match.group(4)
        time_str = match.group(5)
        
        # Parse datetime
        full_datetime_str = f"{date_str} {time_str}"
        dt = dateparser.parse(
            full_datetime_str,
            settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True}
        )
        
        if dt:
            events.append({
                "type": "event",
                "title": f"Flight {flight_number}: {origin} → {destination}",
                "start": dt.isoformat(),
                "end": (dt + timedelta(hours=3)).isoformat(),  # Rough flight duration
                "timezone": timezone,
                "notes": f"Flight from {origin} to {destination}",
                "labels": ["flight", "travel"],
                "reminders": [
                    {"method": "popup", "minutes": 1440},  # 1 day: check-in
                    {"method": "popup", "minutes": 180},   # 3 hours
                    {"method": "popup", "minutes": 60},    # 1 hour
                ],
            })
    
    return events


def _extract_deadlines(text: str, timezone: str) -> List[Dict[str, Any]]:
    """
    Extract deadline/task events.
    
    Patterns:
    - "[Task] due [Date]"
    - "Deadline: [Task] [Date]"
    """
    events = []
    
    deadline_patterns = [
        r"(?i)([^\.]+?)\s+due\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        r"(?i)deadline[:\s]+([^\.]+?)\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
    ]
    
    for pattern in deadline_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            task = match.group(1).strip()
            date_str = match.group(2)
            
            # Parse date (end of day)
            dt = dateparser.parse(
                f"{date_str} 23:59",
                settings={"TIMEZONE": timezone, "RETURN_AS_TIMEZONE_AWARE": True}
            )
            
            if dt:
                events.append({
                    "type": "task",
                    "title": task,
                    "start": dt.isoformat(),
                    "timezone": timezone,
                    "allday": True,
                    "labels": ["deadline"],
                    "reminders": [
                        {"method": "popup", "minutes": 1440},  # 1 day before
                        {"method": "popup", "minutes": 360},   # 6 hours before
                    ],
                })
    
    return events

