"""LLM-based event extraction using OpenAI GPT-4o."""

import openai
from typing import List, Dict, Any, Optional
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY


SYSTEM_PROMPT = """You are an expert at extracting calendar events and tasks from text.

Extract events/tasks and return them as JSON matching this schema:
{
  "events": [
    {
      "type": "event" | "task",
      "title": "string",
      "start": "ISO-8601 datetime",
      "end": "ISO-8601 datetime or null",
      "allday": boolean,
      "timezone": "IANA timezone (default: Europe/Budapest)",
      "location": "string or null",
      "online_url": "string or null",
      "notes": "string or null",
      "attendees": [{"name": "", "email": ""}],
      "reminders": [{"method": "popup", "minutes": 30}],
      "labels": ["exam", "meeting", "deadline", etc.]
    }
  ]
}

Rules:
- Honor locales: if date like "2025.11.04." and time "8 óra 50 perc", use Europe/Budapest timezone
- Extract ALL events you find, not just one
- If time is ambiguous, note it in "notes"
- Never invent locations - only extract if explicitly mentioned
- For exams, add smart reminders: -1 day, -2 hours, -30 minutes
- For flights, add: -24h (check-in), -3h, -1h
- Return empty array if no events found
"""


def extract_events_llm(
    text: str,
    timezone: str = "Europe/Budapest",
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Extract events using GPT-4o with structured output.
    
    Args:
        text: Text to extract from
        timezone: Default timezone
        context: Additional context (OCR source, sender, etc.)
    
    Returns:
        List of extracted event dictionaries
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, skipping LLM extraction")
        return []
    
    if not settings.ENABLE_LLM_FALLBACK:
        logger.info("LLM fallback disabled in settings")
        return []
    
    try:
        # Build user prompt
        user_prompt = f"Extract calendar events from this text:\n\n{text}"
        
        if context:
            user_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"
        
        user_prompt += f"\n\nDefault timezone: {timezone}"
        
        # Call OpenAI with JSON mode
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=settings.OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        
        # Parse response
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        events = result.get("events", [])
        
        logger.info(f"LLM extracted {len(events)} events")
        
        # Add extraction metadata
        for event in events:
            if "notes" not in event:
                event["notes"] = ""
            event["notes"] += "\n[Extracted by AI]"
        
        return events
        
    except Exception as e:
        logger.error(f"LLM extraction error: {str(e)}")
        return []


def enhance_event_with_llm(
    event: Dict[str, Any],
    original_text: str,
) -> Dict[str, Any]:
    """
    Enhance an extracted event with additional details using LLM.
    
    Use this to fill in missing fields or add context.
    
    Args:
        event: Partially extracted event
        original_text: Original text source
    
    Returns:
        Enhanced event dictionary
    """
    if not settings.OPENAI_API_KEY or not settings.ENABLE_LLM_FALLBACK:
        return event
    
    try:
        prompt = f"""Given this partially extracted event:
{json.dumps(event, indent=2)}

And this original text:
{original_text}

Enhance the event by:
1. Adding a better title if current one is generic
2. Extracting location if not present
3. Extracting online meeting URL if not present
4. Adding relevant notes
5. Suggesting appropriate reminders based on event type

Return the enhanced event as JSON with the same schema.
"""
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You enhance calendar events with details from text."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"LLM enhancement error: {str(e)}")
        return event

