"""Event validation, deduplication, and merging."""

from typing import List, Dict, Any
from datetime import datetime
import logging

from app.utils.confidence import calculate_event_confidence

logger = logging.getLogger(__name__)


def merge_and_validate_events(
    deterministic_events: List[Dict[str, Any]],
    llm_events: List[Dict[str, Any]],
    context: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Merge events from multiple extraction methods and validate.
    
    Strategy:
    1. Deduplicate based on start time + title similarity
    2. Prefer deterministic over LLM when conflicting
    3. Merge complementary info (e.g., LLM adds location to deterministic event)
    4. Calculate confidence scores
    5. Validate required fields
    
    Args:
        deterministic_events: Events from regex/dateparser
        llm_events: Events from GPT-4o
        context: Extraction context
    
    Returns:
        List of merged, validated events with confidence scores
    """
    context = context or {}
    all_events = []
    
    # Tag events with source
    for event in deterministic_events:
        event["_source"] = "deterministic"
        all_events.append(event)
    
    for event in llm_events:
        event["_source"] = "llm"
        all_events.append(event)
    
    # Deduplicate
    unique_events = _deduplicate_by_similarity(all_events)
    
    # Validate and enrich
    validated_events = []
    for event in unique_events:
        if _validate_event(event):
            # Calculate confidence
            event_context = {
                **context,
                "extraction_method": event.get("_source", "unknown"),
            }
            confidence = calculate_event_confidence(event, event_context)
            event["confidence"] = confidence
            
            # Remove internal fields
            event.pop("_source", None)
            
            validated_events.append(event)
        else:
            logger.warning(f"Event failed validation: {event.get('title', 'Untitled')}")
    
    logger.info(
        f"Merged {len(deterministic_events)} deterministic + {len(llm_events)} LLM events "
        f"→ {len(validated_events)} unique validated events"
    )
    
    return validated_events


def _deduplicate_by_similarity(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate events based on start time and title similarity.
    
    If two events have same start time and similar titles:
    - Prefer deterministic over LLM
    - Merge non-conflicting fields
    """
    if not events:
        return []
    
    # Group by start time (rounded to 15 min)
    from collections import defaultdict
    time_groups = defaultdict(list)
    
    for event in events:
        start = event.get("start")
        if start:
            # Round to 15 minutes for grouping
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            rounded = dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0)
            time_groups[rounded.isoformat()].append(event)
    
    unique_events = []
    
    for group in time_groups.values():
        if len(group) == 1:
            unique_events.append(group[0])
        else:
            # Merge similar events in this time group
            merged = _merge_similar_events(group)
            unique_events.extend(merged)
    
    return unique_events


def _merge_similar_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge events with similar titles.
    
    Title similarity threshold: 0.5 (fuzzy match)
    """
    if len(events) == 1:
        return events
    
    merged = []
    processed = set()
    
    for i, event1 in enumerate(events):
        if i in processed:
            continue
        
        # Find similar events
        similar = [event1]
        for j, event2 in enumerate(events[i + 1:], start=i + 1):
            if j in processed:
                continue
            
            if _titles_similar(event1.get("title", ""), event2.get("title", "")):
                similar.append(event2)
                processed.add(j)
        
        # Merge the similar events
        merged_event = _merge_event_group(similar)
        merged.append(merged_event)
        processed.add(i)
    
    return merged


def _titles_similar(title1: str, title2: str, threshold: float = 0.5) -> bool:
    """Check if two titles are similar (simple word overlap)."""
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1 & words2)
    total = len(words1 | words2)
    
    return overlap / total >= threshold


def _merge_event_group(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge a group of similar events.
    
    Strategy:
    - Prefer deterministic for structured fields (start, end)
    - Use LLM for descriptive fields (notes, location) if missing
    - Combine labels and reminders
    """
    # Sort by source preference
    events.sort(key=lambda e: 0 if e.get("_source") == "deterministic" else 1)
    
    base = events[0].copy()
    
    for event in events[1:]:
        # Merge fields that are missing in base
        for key, value in event.items():
            if key.startswith("_"):
                continue
            
            if key not in base or not base.get(key):
                base[key] = value
            elif key == "labels":
                # Combine labels
                base_labels = set(base.get("labels", []))
                base_labels.update(event.get("labels", []))
                base["labels"] = list(base_labels)
            elif key == "reminders":
                # Combine reminders (deduplicate by minutes)
                base_reminders = {r["minutes"]: r for r in base.get("reminders", [])}
                for reminder in event.get("reminders", []):
                    base_reminders[reminder["minutes"]] = reminder
                base["reminders"] = list(base_reminders.values())
            elif key == "notes":
                # Append notes
                if base.get("notes") and event.get("notes"):
                    base["notes"] += f"\n{event['notes']}"
    
    return base


def _validate_event(event: Dict[str, Any]) -> bool:
    """
    Validate that an event has required fields.
    
    Required:
    - title
    - start (valid datetime)
    - type
    """
    # Check title
    if not event.get("title") or len(event["title"].strip()) < 2:
        return False
    
    # Check start datetime
    if not event.get("start"):
        return False
    
    try:
        datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False
    
    # Check type
    if event.get("type") not in ["event", "task", None]:
        event["type"] = "event"  # Default
    
    # Set defaults for optional fields
    event.setdefault("allday", False)
    event.setdefault("timezone", "Europe/Budapest")
    event.setdefault("attendees", [])
    event.setdefault("reminders", [])
    event.setdefault("labels", [])
    
    return True

