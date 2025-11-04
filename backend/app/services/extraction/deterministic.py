"""Deterministic event extraction using dateparser and regex."""

import re
import dateparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import logging

from app.services.extraction.patterns.hungarian import extract_hungarian_patterns
from app.services.extraction.patterns.english import extract_english_patterns

logger = logging.getLogger(__name__)


def extract_events_deterministic(
    text: str,
    timezone: str = "Europe/Budapest",
    user_name: Optional[str] = None,
    neptun_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Extract events using deterministic patterns (regex + dateparser).
    
    Args:
        text: Text to extract events from
        timezone: Target timezone for extracted dates
        user_name: User's name for personalized matching
        neptun_id: User's Neptun ID for matching in Hungarian schedules
    
    Returns:
        List of extracted event dictionaries
    """
    events = []
    
    # Try Hungarian patterns first (if text contains Hungarian-specific markers)
    if _is_likely_hungarian(text):
        logger.info("Detected Hungarian text, trying Hungarian patterns")
        hungarian_events = extract_hungarian_patterns(
            text, timezone, user_name=user_name, neptun_id=neptun_id
        )
        events.extend(hungarian_events)
    
    # Try English/international patterns
    english_events = extract_english_patterns(text, timezone)
    events.extend(english_events)
    
    # Generic date extraction fallback
    if not events:
        generic_events = _extract_generic_dates(text, timezone)
        events.extend(generic_events)
    
    # Deduplicate and enrich
    events = _deduplicate_events(events)
    
    logger.info(f"Extracted {len(events)} events using deterministic methods")
    return events


def _is_likely_hungarian(text: str) -> bool:
    """Check if text contains Hungarian-specific markers."""
    hungarian_markers = [
        "óra",
        "perc",
        "neptun",
        "vizsga",
        "évfolyam",
        "terem",
        "hallgató",
    ]
    text_lower = text.lower()
    return any(marker in text_lower for marker in hungarian_markers)


def _extract_generic_dates(text: str, timezone: str) -> List[Dict[str, Any]]:
    """
    Extract dates using generic dateparser.
    
    This is a fallback that tries to find any date-like strings.
    """
    events = []
    
    # dateparser settings
    settings = {
        "TIMEZONE": timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    
    # Split text into lines
    lines = text.split('\n')
    
    for line in lines:
        # Skip very short lines
        if len(line.strip()) < 10:
            continue
        
        # Try to parse date from line
        date = dateparser.parse(line, settings=settings)
        
        if date:
            # Extract a title (first 50 chars or until punctuation)
            title_match = re.match(r'^([^:;,\.]{5,50})', line.strip())
            title = title_match.group(1).strip() if title_match else "Event"
            
            events.append({
                "title": title,
                "start": date.isoformat(),
                "end": (date + timedelta(hours=1)).isoformat(),
                "timezone": timezone,
                "notes": line.strip(),
            })
    
    return events


def _deduplicate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate events based on start time and title similarity.
    """
    if not events:
        return events
    
    seen = set()
    unique_events = []
    
    for event in events:
        # Create a signature
        start = event.get("start", "")
        title = event.get("title", "").lower().strip()
        signature = f"{start}:{title[:20]}"
        
        if signature not in seen:
            seen.add(signature)
            unique_events.append(event)
    
    return unique_events


def extract_location(text: str) -> Optional[str]:
    """
    Extract location/room information from text.
    
    Patterns:
    - Room 123, Rm 123
    - Building A, Wing B
    - 1234 Main St
    """
    # Room patterns
    room_patterns = [
        r"(?i)(?:room|rm|terem|sz[oó]ba)\s*:?\s*([A-Z0-9\-]+)",
        r"(?i)(?:building|épület)\s*:?\s*([A-Z0-9\-]+)",
        r"\b([A-Z]{1,2}\s*\d{3,4})\b",  # A101, B-204, etc.
    ]
    
    for pattern in room_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return None


def extract_online_url(text: str) -> Optional[str]:
    """
    Extract online meeting URLs (Zoom, Meet, Teams, etc.).
    """
    # Common meeting URL patterns
    url_patterns = [
        r"https?://[a-zA-Z0-9\-\.]+\.zoom\.us/j/[0-9]+[^\s]*",
        r"https?://meet\.google\.com/[a-z\-]+",
        r"https?://teams\.microsoft\.com/l/meetup-join/[^\s]+",
        r"https?://[a-zA-Z0-9\-\.]+/meeting/[^\s]+",
    ]
    
    for pattern in url_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

