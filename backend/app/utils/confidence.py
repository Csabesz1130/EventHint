"""Confidence scoring utilities for extracted events."""

from typing import Dict, Any
from datetime import datetime


def calculate_event_confidence(event_data: Dict[str, Any], context: Dict[str, Any] = None) -> float:
    """
    Calculate confidence score for an extracted event.
    
    Factors:
    - Has clear date/time: +0.3
    - Has title: +0.2
    - Has location: +0.1
    - Deterministic extraction: +0.2
    - LLM extraction with high certainty: +0.15
    - Trusted sender: +0.05
    - OCR confidence: scaled contribution
    
    Args:
        event_data: Extracted event dictionary
        context: Additional context (OCR confidence, sender trust, etc.)
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    context = context or {}
    confidence = 0.0
    
    # Date/time presence
    if event_data.get("start"):
        confidence += 0.3
        if event_data.get("end"):
            confidence += 0.05
    
    # Title quality
    title = event_data.get("title", "")
    if title and len(title) > 3:
        confidence += 0.2
    
    # Location
    if event_data.get("location") or event_data.get("online_url"):
        confidence += 0.1
    
    # Extraction method
    extraction_method = context.get("extraction_method", "")
    if extraction_method == "deterministic":
        confidence += 0.2
    elif extraction_method == "llm":
        confidence += 0.15
    elif extraction_method == "hybrid":
        confidence += 0.25
    
    # Trusted sender
    if context.get("trusted_sender"):
        confidence += 0.05
    
    # OCR confidence (if applicable)
    ocr_confidence = context.get("ocr_confidence", 1.0)
    if ocr_confidence < 1.0:
        confidence *= ocr_confidence
    
    # Cap at 1.0
    return min(confidence, 1.0)


def should_auto_approve(event_data: Dict[str, Any], user, context: Dict[str, Any] = None) -> bool:
    """
    Determine if an event should be auto-approved.
    
    Args:
        event_data: Extracted event dictionary
        user: User model instance
        context: Additional context
    
    Returns:
        True if event should be auto-approved
    """
    if not user.auto_approve_enabled:
        return False
    
    confidence = calculate_event_confidence(event_data, context)
    
    # Auto-approve if confidence is very high
    if confidence >= 0.9:
        return True
    
    # Auto-approve from trusted senders
    if context and context.get("trusted_sender"):
        return confidence >= 0.7
    
    return False

