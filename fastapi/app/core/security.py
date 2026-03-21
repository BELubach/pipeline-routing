from datetime import datetime, timedelta
from typing import Optional
import hashlib
from jose import jwt
from app.core.config import settings
import bcrypt
import hashlib
import base64


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ensure 'sub' is a string (JWT spec requires it)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    # Ensure 'role' is a string if present
    if "role" in to_encode and hasattr(to_encode["role"], "value"):
        to_encode["role"] = to_encode["role"].value

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access"
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    # Ensure 'sub' is a string (JWT spec requires it)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    # Ensure 'role' is a string if present
    if "role" in to_encode and hasattr(to_encode["role"], "value"):
        to_encode["role"] = to_encode["role"].value

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def _prehash(password: str) -> bytes:
    """SHA-256 prehash to safely handle passwords > 72 bytes."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    # base64 keeps it bcrypt-safe (no null bytes)
    return base64.b64encode(digest)


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(_prehash(password), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode("utf-8"))
