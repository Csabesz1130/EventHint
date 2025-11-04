"""Gmail API connector for fetching and monitoring emails."""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, Any, List, Optional
import base64
import logging

from app.core.security import token_encryption
from app.models.user import User

logger = logging.getLogger(__name__)


class GmailService:
    """
    Gmail API service wrapper.
    
    Features:
    - Fetch messages
    - Set up push notifications (watch)
    - Extract attachments
    - Parse MIME content
    """
    
    def __init__(self, user: User):
        """
        Initialize Gmail service for a user.
        
        Args:
            user: User model with Google tokens
        """
        self.user = user
        
        # Decrypt tokens
        access_token = token_encryption.decrypt(user.google_access_token)
        refresh_token = (
            token_encryption.decrypt(user.google_refresh_token)
            if user.google_refresh_token
            else None
        )
        
        # Create credentials
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id="",  # Not needed for API calls
            client_secret="",
        )
        
        # Build Gmail API service
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Fetch a full message by ID.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Message dictionary with headers, body, attachments
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
            
        except HttpError as e:
            logger.error(f"Error fetching Gmail message {message_id}: {str(e)}")
            raise
    
    def list_messages(
        self,
        query: str = "",
        max_results: int = 10,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List messages matching a query.
        
        Args:
            query: Gmail search query (e.g., "subject:invoice after:2024/01/01")
            max_results: Number of results to return
            page_token: Token for pagination
        
        Returns:
            Dict with 'messages' list and optional 'nextPageToken'
        """
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                pageToken=page_token,
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Error listing Gmail messages: {str(e)}")
            raise
    
    def setup_push_notifications(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set up Gmail push notifications (watch).
        
        Gmail will send POST requests to webhook_url when new messages arrive.
        
        Args:
            webhook_url: Public HTTPS URL to receive notifications
        
        Returns:
            Watch response with historyId and expiration
        """
        try:
            request_body = {
                'labelIds': ['INBOX'],
                'topicName': 'projects/YOUR_PROJECT/topics/gmail-notifications',
            }
            
            response = self.service.users().watch(
                userId='me',
                body=request_body
            ).execute()
            
            logger.info(f"Gmail watch set up for user {self.user.id}: {response}")
            return response
            
        except HttpError as e:
            logger.error(f"Error setting up Gmail watch: {str(e)}")
            raise
    
    def stop_push_notifications(self) -> None:
        """Stop receiving push notifications."""
        try:
            self.service.users().stop(userId='me').execute()
            logger.info(f"Gmail watch stopped for user {self.user.id}")
        except HttpError as e:
            logger.error(f"Error stopping Gmail watch: {str(e)}")
            raise
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Gmail message into a simplified format.
        
        Returns:
            {
                'id': '...',
                'thread_id': '...',
                'subject': '...',
                'from': '...',
                'to': '...',
                'date': '...',
                'body_text': '...',
                'body_html': '...',
                'attachments': [...]
            }
        """
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Extract body
        body_text = ""
        body_html = ""
        attachments = []
        
        if 'parts' in message['payload']:
            self._extract_parts(message['payload']['parts'], body_text, body_html, attachments)
        else:
            # Simple message without parts
            if 'body' in message['payload'] and 'data' in message['payload']['body']:
                body_text = base64.urlsafe_b64decode(
                    message['payload']['body']['data']
                ).decode('utf-8')
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'body_text': body_text,
            'body_html': body_html,
            'attachments': attachments,
        }
    
    def _extract_parts(
        self,
        parts: List[Dict[str, Any]],
        body_text: str,
        body_html: str,
        attachments: List[Dict[str, Any]],
    ) -> None:
        """Recursively extract text, HTML, and attachments from message parts."""
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                body_text += base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='ignore')
            
            elif mime_type == 'text/html' and 'data' in part.get('body', {}):
                body_html += base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='ignore')
            
            elif 'filename' in part and part['filename']:
                # Attachment
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': mime_type,
                        'size': part['body'].get('size', 0),
                        'attachment_id': attachment_id,
                    })
            
            # Recurse into nested parts
            if 'parts' in part:
                self._extract_parts(part['parts'], body_text, body_html, attachments)
    
    def get_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """
        Download an attachment.
        
        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID from message
        
        Returns:
            Attachment data as bytes
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = base64.urlsafe_b64decode(attachment['data'])
            return data
            
        except HttpError as e:
            logger.error(f"Error downloading attachment: {str(e)}")
            raise

