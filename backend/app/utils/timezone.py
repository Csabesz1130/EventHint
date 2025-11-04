"""Timezone utilities and resolution."""

import pytz
from datetime import datetime
from typing import Optional
import re


# Common timezone mappings
TIMEZONE_ALIASES = {
    "budapest": "Europe/Budapest",
    "hungary": "Europe/Budapest",
    "hungarian": "Europe/Budapest",
    "cet": "Europe/Budapest",
    "cest": "Europe/Budapest",
    "utc": "UTC",
    "gmt": "GMT",
    "est": "America/New_York",
    "pst": "America/Los_Angeles",
}


def normalize_timezone(tz_string: str) -> str:
    """
    Normalize a timezone string to IANA format.
    
    Args:
        tz_string: Timezone string (e.g., "CET", "Budapest", "Europe/Budapest")
    
    Returns:
        IANA timezone string (e.g., "Europe/Budapest")
    """
    tz_lower = tz_string.lower().strip()
    
    # Check aliases
    if tz_lower in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[tz_lower]
    
    # Validate if it's already a valid IANA timezone
    try:
        pytz.timezone(tz_string)
        return tz_string
    except pytz.exceptions.UnknownTimeZoneError:
        pass
    
    # Default fallback
    return "Europe/Budapest"


def localize_datetime(dt: datetime, timezone_str: str) -> datetime:
    """
    Localize a naive datetime to a specific timezone.
    
    Args:
        dt: Naive datetime object
        timezone_str: IANA timezone string
    
    Returns:
        Timezone-aware datetime
    """
    tz = pytz.timezone(normalize_timezone(timezone_str))
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt.astimezone(tz)


def detect_timezone_from_text(text: str) -> Optional[str]:
    """
    Try to detect timezone from text content.
    
    Args:
        text: Text content
    
    Returns:
        IANA timezone string or None
    """
    text_lower = text.lower()
    
    # Check for timezone keywords
    for keyword, tz in TIMEZONE_ALIASES.items():
        if keyword in text_lower:
            return tz
    
    # Check for explicit timezone formats
    tz_pattern = r"(?:GMT|UTC)([+-]\d{1,2}):?(\d{2})?"
    match = re.search(tz_pattern, text, re.IGNORECASE)
    if match:
        # For now, just return UTC; could implement offset-based lookup
        return "UTC"
    
    return None


def get_user_timezone(user) -> str:
    """
    Get user's preferred timezone.
    
    Args:
        user: User model instance
    
    Returns:
        IANA timezone string
    """
    return user.default_timezone or "Europe/Budapest"

