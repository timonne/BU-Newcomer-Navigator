"""
Password hashing (bcrypt via passlib) and JWT creation/verification.

Passwords are never stored or logged in plaintext. JWTs are short-lived,
signed with HS256, and delivered to the browser as an httpOnly cookie
(see app/api/auth.py) rather than being exposed to JavaScript -- this
keeps them out of reach of XSS-based token theft.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except ValueError:
        return False


def create_access_token(user_id: str, expires_minutes: Optional[int] = None) -> str:
    expire_minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Returns the user id (sub claim) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


def generate_raw_token(n_bytes: int = 32) -> str:
    """A URL-safe random token for email verification links / password reset."""
    return secrets.token_urlsafe(n_bytes)


def generate_numeric_code(length: int = 6) -> str:
    """A short numeric code for email verification (easy to type/paste)."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_token(raw_token: str) -> str:
    """One-way hash for storing tokens/codes at rest (SHA-256 is fine here --
    these are high-entropy random values, not low-entropy passwords, so a
    slow KDF like bcrypt is unnecessary)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()