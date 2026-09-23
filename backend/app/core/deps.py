"""
FastAPI dependencies for authentication.

The access token lives in an httpOnly cookie (never readable by frontend
JS), so the backend -- not the frontend -- is the sole enforcer of who is
logged in. `get_current_user` is used on routes that require auth;
`get_current_user_optional` is used on routes (like the chatbot) that
personalize for a logged-in user but also work for anonymous visitors.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import APIError
from app.database import get_db
from app.models.user import AccountStatus, User
from app.services.security import decode_access_token

settings = get_settings()


def _extract_token(request: Request) -> Optional[str]:
    token = request.cookies.get(settings.auth_cookie_name)
    if token:
        return token
    # Also accept a Bearer token, for non-browser API clients / tests.
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return None


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = _extract_token(request)
    if not token:
        return None
    user_id = decode_access_token(token)
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.account_status == AccountStatus.suspended:
        return None
    return user


def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise APIError(
            "NOT_AUTHENTICATED", "Please sign in to continue.", status.HTTP_401_UNAUTHORIZED
        )
    return user


def require_verified_staff(user: User = Depends(get_current_user)) -> User:
    """Gate for knowledge-base writes.

    Deliberately narrow: only a Staff account whose email has actually been
    verified may add or edit university knowledge-base content, so unverified
    or student accounts cannot publish something that the chatbot will then
    present as university information.
    """
    from app.models.user import AccountType, VerificationStatus

    if user.account_type != AccountType.staff or user.verification_status != VerificationStatus.verified:
        raise APIError(
            "STAFF_ONLY",
            "Only verified staff accounts can modify the university knowledge base.",
            status.HTTP_403_FORBIDDEN,
        )
    return user
