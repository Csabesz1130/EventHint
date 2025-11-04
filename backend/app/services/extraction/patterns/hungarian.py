"""Hungarian-specific extraction patterns (exam schedules, etc.)."""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import logging

logger = logging.getLogger(__name__)

# Hungarian date pattern: 2025.11.04.
DATE_HEADER_PATTERN = r"(?P<y>\d{4})\.(?P<m>\d{2})\.(?P<d>\d{2})\."

# Hungarian time pattern: 8 óra 50 perc
TIME_PATTERN = r"(?P<h>\d{1,2})\s*óra\s*(?P<m>\d{1,2})\s*perc"

# Alternative time pattern: 08:50 or 8:50
TIME_PATTERN_ALT = r"(?P<h>\d{1,2}):(?P<m>\d{2})"


def extract_hungarian_patterns(
    text: str,
    timezone: str = "Europe/Budapest",
    user_name: Optional[str] = None,
    neptun_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract events from Hungarian text (especially exam schedules).
    
    Args:
        text: Text to extract from
        timezone: Target timezone
        user_name: User's name for personalized matching
        neptun_id: User's Neptun ID
    
    Returns:
        List of extracted events
    """
    events = []
    
    # Try exam schedule pattern
    exam_events = extract_hungarian_exam_schedule(text, timezone, user_name, neptun_id)
    events.extend(exam_events)
    
    return events


def extract_hungarian_exam_schedule(
    text: str,
    timezone: str = "Europe/Budapest",
    user_name: Optional[str] = None,
    neptun_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract exam appointments from Hungarian schedule table.
    
    Expected format:
        2025.11.04.
        Balogh Csaba — 8 óra 50 perc
        [Other names] — [Other times]
    
    Args:
        text: Schedule text
        timezone: Target timezone
        user_name: User's name to match
        neptun_id: User's Neptun ID to match
    
    Returns:
        List of exam event dictionaries
    """
    events = []
    
    # Find date header
    date_match = re.search(DATE_HEADER_PATTERN, text)
    if not date_match:
        logger.debug("No Hungarian date header found")
        return events
    
    base_date = datetime(
        int(date_match.group('y')),
        int(date_match.group('m')),
        int(date_match.group('d'))
    )
    
    logger.info(f"Found Hungarian date header: {base_date.date()}")
    
    # Split into lines
    lines = text.split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Check if line matches user
        matches_user = False
        if user_name and user_name.lower() in line.lower():
            matches_user = True
            logger.info(f"Matched user name '{user_name}' in line: {line[:50]}")
        elif neptun_id and neptun_id.upper() in line.upper():
            matches_user = True
            logger.info(f"Matched Neptun ID '{neptun_id}' in line: {line[:50]}")
        
        # If no user filter, extract all times
        if not user_name and not neptun_id:
            matches_user = True
        
        if not matches_user:
            continue
        
        # Try to find time in this line
        time_match = re.search(TIME_PATTERN, line)
        if not time_match:
            # Try alternative time format
            time_match = re.search(TIME_PATTERN_ALT, line)
        
        if time_match:
            hour = int(time_match.group('h'))
            minute = int(time_match.group('m'))
            
            # Create timezone-aware datetime
            tz = pytz.timezone(timezone)
            start = tz.localize(base_date.replace(hour=hour, minute=minute))
            
            # Default duration: 30 minutes for exams
            end = start + timedelta(minutes=30)
            
            # Extract potential room/location from line
            location = _extract_room_from_line(line)
            
            # Extract name from line (before the time)
            name_part = line.split('—')[0].strip() if '—' in line else ""
            
            events.append({
                "type": "event",
                "title": "Exam appointment",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "timezone": timezone,
                "location": location,
                "notes": f"Imported from schedule. {name_part if name_part else 'Matched user.'}",
                "labels": ["exam"],
                "reminders": [
                    {"method": "popup", "minutes": 1440},  # 1 day before
                    {"method": "popup", "minutes": 120},   # 2 hours before
                    {"method": "popup", "minutes": 30},    # 30 minutes before
                ],
            })
            
            logger.info(f"Extracted exam event: {start.isoformat()}")
    
    return events


def _extract_room_from_line(line: str) -> Optional[str]:
    """Extract room/location from a line."""
    # Common patterns: "Terem: A123", "A-123", "1.23"
    room_patterns = [
        r"(?i)terem\s*:?\s*([A-Z0-9\-\.]+)",
        r"\b([A-Z]{1,2}[\-\.]?\d{2,4})\b",
    ]
    
    for pattern in room_patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    
    return None

