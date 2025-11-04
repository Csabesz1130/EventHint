"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import timedelta
import logging

from app.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, token_encryption
from app.models.user import User
from app.schemas.auth import Token, UserResponse, GoogleOAuthCallback

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth flow.
    Returns the URL to redirect user to Google's consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )
    
    # Google OAuth URL
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile%20"
        f"https://www.googleapis.com/auth/gmail.readonly%20"
        f"https://www.googleapis.com/auth/calendar.events&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"url": oauth_url}


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    Exchange authorization code for tokens and create/update user.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured",
        )
    
    try:
        # Exchange code for tokens
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/calendar.events",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        # Fetch tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Verify ID token and get user info
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        
        google_id = id_info["sub"]
        email = id_info["email"]
        full_name = id_info.get("name", "")
        
        # Find or create user
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                full_name=full_name,
                google_id=google_id,
            )
            db.add(user)
        else:
            user.google_id = google_id
            user.full_name = full_name or user.full_name
        
        # Store encrypted tokens
        user.google_access_token = token_encryption.encrypt(credentials.token)
        if credentials.refresh_token:
            user.google_refresh_token = token_encryption.encrypt(credentials.refresh_token)
        user.google_token_expiry = credentials.expiry
        
        db.commit()
        db.refresh(user)
        
        # Create JWT for our app
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Redirect to frontend with token
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_db),
):
    """Get current user information."""
    from app.api.deps import get_current_user
    user = await get_current_user(db=db)
    return user

