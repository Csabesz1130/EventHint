"""Security utilities: JWT, OAuth, password hashing."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode (typically {"sub": user_id})
        expires_delta: Optional expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


class TokenEncryption:
    """
    Encrypt/decrypt sensitive tokens (OAuth refresh tokens, etc.).
    Uses Fernet symmetric encryption.
    """
    
    def __init__(self):
        # In production, use a proper KMS or key rotation
        self.cipher = Fernet(self._get_or_create_key())
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from settings (base64 encoded)."""
        # For now, derive from SECRET_KEY; in production use dedicated key
        import base64
        import hashlib
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, plain_text: str) -> str:
        """Encrypt a string."""
        return self.cipher.encrypt(plain_text.encode()).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a string."""
        return self.cipher.decrypt(encrypted_text.encode()).decode()


# Global instance
token_encryption = TokenEncryption()

