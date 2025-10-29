"""Authentication service for user signup, login, and verification."""
import secrets
import random
import os
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt

# JWT settings
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Demo mode configuration
SKIP_AUTH = os.getenv("SKIP_AUTH", "false").lower() == "true"
DEMO_FAMILY_ID = int(os.getenv("DEMO_FAMILY_ID", "1"))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Note: bcrypt has a 72 byte limit. Passwords are truncated if necessary.
    """
    # Truncate to 72 bytes if necessary (bcrypt limitation)
    password_bytes = password.encode('utf-8')[:72]

    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Note: Applies same 72 byte truncation as hash_password for consistency.
    """
    # Truncate to 72 bytes if necessary (bcrypt limitation)
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token.

    If SKIP_AUTH is enabled, returns a mock payload with demo family_id.
    """
    if SKIP_AUTH:
        # Return mock payload for demo mode
        return {
            "sub": "demo@cooai.test",
            "family_id": DEMO_FAMILY_ID,
            "exp": (datetime.utcnow() + timedelta(days=365)).timestamp()
        }

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_verification_code() -> str:
    """Generate a 6-digit verification code for phone verification."""
    return str(random.randint(100000, 999999))


def generate_email_verification_token() -> str:
    """Generate a secure token for email verification."""
    return secrets.token_urlsafe(32)


def is_verification_code_expired(expires_at: datetime) -> bool:
    """Check if a verification code has expired."""
    return datetime.utcnow() > expires_at
