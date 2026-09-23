"""
/api/auth/* — registration, login, logout, current user, email
verification, and password reset.

The access token is set as an httpOnly cookie, so frontend JavaScript can
never read it. The existing frontend therefore needs no token-handling code
at all: it calls these endpoints with `credentials: 'include'` and the
browser carries the session.

Rate limits are applied to every endpoint that can be brute-forced or used
to send email.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    GenericMessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    SendVerificationRequest,
    SendVerificationResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.schemas.user import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services import auth_service
from app.services.security import create_access_token
from app.services.user_service import to_user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _set_auth_cookie(response: Response, user_id: str) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Creates the account and signs the user straight in.

    The response carries the backend-generated username (the user never
    chooses it), which is what the existing sign-up UI displays after
    registration.
    """
    user = auth_service.register_user(db, payload)
    _set_auth_cookie(response, user.id)
    return AuthResponse(user=to_user_out(db, user, viewer=user))


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Accepts either the generated username or the email address."""
    user = auth_service.authenticate_user(db, payload.identifier, payload.password)
    _set_auth_cookie(response, user.id)
    return AuthResponse(user=to_user_out(db, user, viewer=user))


@router.post("/logout", response_model=GenericMessageResponse)
def logout(response: Response):
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return GenericMessageResponse(success=True, message="Signed out.")


@router.get("/me", response_model=AuthResponse)
def current_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Used by the frontend on page load to restore the session.

    Returns 401 (not an empty body) when there is no valid cookie, so the
    frontend can distinguish "not signed in" from "request failed".
    """
    return AuthResponse(user=to_user_out(db, user, viewer=user))


@router.post("/verification/send", response_model=SendVerificationResponse)
@limiter.limit("5/hour")
def send_verification(
    request: Request,
    payload: SendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Sends (or, with no SMTP configured, logs) a single-use expiring code.

    Rate-limited to 5/hour per IP so this cannot be used to spam an inbox.
    """
    success, message = auth_service.send_verification_code(db, payload.email)
    return SendVerificationResponse(success=success, message=message)


@router.post("/verification/confirm", response_model=VerifyCodeResponse)
@limiter.limit("20/hour")
def confirm_verification(
    request: Request,
    payload: VerifyCodeRequest,
    db: Session = Depends(get_db),
):
    success, message = auth_service.confirm_verification_code(db, payload.user_id, payload.code)
    return VerifyCodeResponse(success=success, message=message)


@router.post("/password-reset/request", response_model=GenericMessageResponse)
@limiter.limit("5/hour")
def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Always returns the same message whether or not the account exists, so
    this endpoint cannot be used to enumerate registered email addresses
    (brief section 11)."""
    message = auth_service.request_password_reset(db, payload.email)
    return GenericMessageResponse(success=True, message=message)


@router.post("/password-reset/confirm", response_model=GenericMessageResponse)
@limiter.limit("10/hour")
def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    auth_service.confirm_password_reset(db, payload.token, payload.new_password)
    return GenericMessageResponse(success=True, message="Your password has been reset. Please sign in.")
