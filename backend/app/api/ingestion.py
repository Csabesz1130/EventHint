"""Ingestion API endpoints (file upload, webhooks)."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import uuid as uuid_lib

from app.config import settings
from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.message import Message

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image, PDF, or other file for processing.
    Triggers extraction pipeline in background.
    """
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {settings.MAX_UPLOAD_SIZE} bytes)",
        )
    
    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid_lib.uuid4())
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create message record
    message = Message(
        user_id=current_user.id,
        provider="upload",
        subject=file.filename or "Uploaded file",
        attachments=[
            {
                "filename": file.filename,
                "mime_type": file.content_type,
                "size": len(file_content),
                "path": file_path,
            }
        ],
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Trigger processing in background
    from app.tasks.process_message import process_message_task
    background_tasks.add_task(process_message_task.delay, str(message.id))
    
    logger.info(f"File uploaded: {file.filename} ({len(file_content)} bytes) for user {current_user.id}")
    
    return {
        "success": True,
        "message_id": str(message.id),
        "filename": file.filename,
        "size": len(file_content),
    }


@router.post("/webhooks/gmail")
async def gmail_webhook(
    background_tasks: BackgroundTasks,
    notification: dict,
    db: Session = Depends(get_db),
):
    """
    Webhook endpoint for Gmail push notifications.
    
    Gmail sends notifications when new messages arrive.
    We extract the message and trigger processing.
    """
    logger.info(f"Gmail webhook received: {notification}")
    
    # TODO: Implement Gmail notification processing
    # 1. Verify notification authenticity
    # 2. Extract message ID and user email
    # 3. Fetch full message from Gmail API
    # 4. Trigger extraction pipeline
    
    return {"success": True}

