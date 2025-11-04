"""Celery tasks for processing emails and extracting events."""

from celery import Task
from datetime import datetime, timedelta
import logging

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.models.message import Message
from app.models.event import Event, EventStatus

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
def process_message_task(self, message_id: str):
    """
    Process an email message or uploaded file.
    
    Pipeline:
    1. Load message from DB
    2. Extract attachments and perform OCR
    3. Run deterministic + LLM extraction
    4. Create draft events
    5. Mark message as processed
    """
    db = self.db
    
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        
        if not message:
            logger.error(f"Message {message_id} not found")
            return
        
        if message.processed:
            logger.info(f"Message {message_id} already processed")
            return
        
        logger.info(f"Processing message {message_id}")
        
        # Handle website scraping if provider is "website"
        if message.provider == "website":
            from app.services.web.scraper import scrape_url
            
            url = message.body_text
            scrape_result = scrape_url(url)
            
            if not scrape_result.get("success"):
                error_msg = scrape_result.get("error", "Unknown scraping error")
                logger.error(f"Failed to scrape URL {url}: {error_msg}")
                message.processing_error = f"Scraping failed: {error_msg}"
                message.processed = True
                message.processed_at = datetime.utcnow()
                db.commit()
                return
            
            # Update message with scraped content
            message.subject = scrape_result.get("title", message.subject)
            message.body_text = scrape_result.get("text", "")
            message.body_html = scrape_result.get("html", "")
            
            # Store links in attachments for reference
            links = scrape_result.get("links", [])
            if links:
                message.attachments = [{
                    "type": "links",
                    "links": links[:50],  # Limit to first 50 links
                }]
            
            logger.info(f"Successfully scraped URL {url}: {len(message.body_text)} chars")
        
        # 1. OCR on attachments (if any)
        from app.services.ocr import extract_text_smart
        import os
        
        full_text = message.body_text or ""
        
        for attachment in message.attachments:
            if 'path' in attachment and os.path.exists(attachment['path']):
                try:
                    with open(attachment['path'], 'rb') as f:
                        file_bytes = f.read()
                    
                    ocr_result = extract_text_smart(file_bytes)
                    attachment['ocr_text'] = ocr_result.text
                    attachment['ocr_confidence'] = ocr_result.confidence
                    
                    # Append OCR text to full text
                    full_text += f"\n\n--- {attachment['filename']} ---\n{ocr_result.text}"
                    
                    logger.info(
                        f"OCR completed for {attachment['filename']} "
                        f"with confidence {ocr_result.confidence:.2f}"
                    )
                except Exception as e:
                    logger.error(f"OCR failed for {attachment['filename']}: {str(e)}")
        
        # Get user for personalization
        from app.models.user import User
        user = db.query(User).filter(User.id == message.user_id).first()
        
        # 2. Extract events (deterministic + LLM)
        from app.services.extraction.deterministic import extract_events_deterministic
        from app.services.extraction.llm import extract_events_llm
        from app.services.extraction.merger import merge_and_validate_events
        
        deterministic_events = extract_events_deterministic(
            full_text,
            timezone=user.default_timezone if user else "Europe/Budapest",
            user_name=user.preferred_name or user.full_name if user else None,
            neptun_id=user.neptun_id if user else None,
        )
        
        llm_events = extract_events_llm(
            full_text,
            timezone=user.default_timezone if user else "Europe/Budapest",
            context={
                "source": message.provider,
                "sender": message.sender_email,
            }
        )
        
        # 3. Merge and validate
        merged_events = merge_and_validate_events(
            deterministic_events,
            llm_events,
            context={
                "ocr_confidence": min(
                    (att.get('ocr_confidence', 1.0) for att in message.attachments),
                    default=1.0
                ),
            }
        )
        
        # 4. Create draft events
        from app.utils.confidence import should_auto_approve
        
        for event_data in merged_events:
            # Determine status
            if should_auto_approve(event_data, user, {"confidence": event_data.get("confidence", 0.0)}):
                status = EventStatus.APPROVED
                approved_at = datetime.utcnow()
            else:
                status = EventStatus.PENDING_APPROVAL
                approved_at = None
            
            event = Event(
                user_id=message.user_id,
                message_id=message.id,
                type=event_data.get("type", "event"),
                title=event_data["title"],
                start=datetime.fromisoformat(event_data["start"].replace('Z', '+00:00')),
                end=datetime.fromisoformat(event_data["end"].replace('Z', '+00:00')) if event_data.get("end") else None,
                allday=event_data.get("allday", False),
                timezone=event_data.get("timezone", "Europe/Budapest"),
                location=event_data.get("location"),
                online_url=event_data.get("online_url"),
                notes=event_data.get("notes"),
                attendees=event_data.get("attendees", []),
                reminders=event_data.get("reminders", []),
                labels=event_data.get("labels", []),
                recurrence=event_data.get("recurrence"),
                provider=message.provider,
                confidence=event_data.get("confidence", 0.0),
                extraction_method=event_data.get("_source", "hybrid"),
                status=status,
                approved_at=approved_at,
            )
            db.add(event)
        
        message.processed = True
        message.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            f"Message {message_id} processed successfully: "
            f"extracted {len(merged_events)} events "
            f"({len([e for e in merged_events if should_auto_approve(e, user, {})])} auto-approved)"
        )
        
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {str(e)}")
        message.processing_error = str(e)
        db.commit()
        raise


@celery_app.task
def cleanup_old_drafts():
    """
    Periodic task to clean up old rejected/pending events.
    Runs hourly via Celery Beat.
    """
    db = SessionLocal()
    
    try:
        # Delete rejected events older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted = (
            db.query(Event)
            .filter(
                Event.status == EventStatus.REJECTED,
                Event.rejected_at < cutoff_date,
            )
            .delete()
        )
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old rejected events")
        
    except Exception as e:
        logger.error(f"Error cleaning up old drafts: {str(e)}")
    finally:
        db.close()

