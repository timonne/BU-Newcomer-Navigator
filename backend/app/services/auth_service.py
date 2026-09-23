"""
Authentication business logic: registration, login, email verification,
and password reset. Routes in app/api/auth.py stay thin and delegate here.
"""
from __future__ import annotations

import random
from datetime import timedelta
from typing import Optional

from fastapi import status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import APIError
from app.models.mixins import utcnow
from app.models.user import AVATAR_COLORS, AccountStatus, AccountType, User, VerificationStatus
from app.models.verification import EmailVerificationToken, PasswordResetToken
from app.schemas.user import RegisterRequest
from app.services import security
from app.services.email_service import send_email
from app.services.username_service import generate_username

settings = get_settings()

VERIFICATION_CODE_TTL_MINUTES = 15
PASSWORD_RESET_TTL_MINUTES = 60
# Generic message used for both "email not found" and "email found" cases
# on password reset requests, so the API never reveals which emails have
# accounts.
GENERIC_RESET_MESSAGE = (
    "If an account exists for that email address, a password reset link has been sent."
)


def _email_domain_allowed(email: str, account_type: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    if account_type == "student":
        allowed = settings.student_email_domain_list
    elif account_type == "staff":
        allowed = settings.staff_email_domain_list
    else:
        return True
    if not allowed:
        # No domain restriction has been configured yet -- see .env.example.
        # Fail open rather than blocking every registration on an
        # unconfigured system.
        return True
    return domain in allowed


def register_user(db: Session, data: RegisterRequest) -> User:
    if data.password != data.confirm_password:
        raise APIError("PASSWORD_MISMATCH", "Passwords do not match.", status.HTTP_400_BAD_REQUEST)

    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing is not None:
        raise APIError(
            "EMAIL_TAKEN", "An account with this email already exists.", status.HTTP_409_CONFLICT
        )

    username = generate_username(db, data.full_name)

    verification_status = (
        VerificationStatus.unverified if data.account_type == "other" else VerificationStatus.pending
    )

    user = User(
        full_name=data.full_name.strip(),
        username=username,
        email=data.email.lower(),
        phone=data.phone.strip(),
        account_type=AccountType(data.account_type),
        password_hash=security.hash_password(data.password),
        verification_status=verification_status,
        account_status=AccountStatus.active,
        course=data.course,
        department=data.department,
        bio="",
        avatar_color=random.choice(AVATAR_COLORS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    user = (
        db.query(User)
        .filter(or_(User.email == identifier.lower(), User.username == identifier.lower()))
        .first()
    )
    if user is None or not security.verify_password(password, user.password_hash):
        raise APIError(
            "INVALID_CREDENTIALS",
            "The email/username or password is incorrect.",
            status.HTTP_401_UNAUTHORIZED,
        )
    if user.account_status == AccountStatus.suspended:
        raise APIError(
            "ACCOUNT_SUSPENDED", "This account has been suspended.", status.HTTP_403_FORBIDDEN
        )
    return user


def send_verification_code(db: Session, email: str) -> tuple[bool, str]:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        # Deliberately vague to avoid confirming/denying account existence
        # in a way that's inconsistent with the password-reset flow.
        return False, "No account found with that email address."

    if user.verification_status == VerificationStatus.verified:
        return True, "This account is already verified."

    if not _email_domain_allowed(user.email, user.account_type.value):
        return (
            False,
            f"Please use your official {user.account_type.value} email address for verification.",
        )

    code = security.generate_numeric_code(6)
    raw_token = security.generate_raw_token()
    token_row = EmailVerificationToken(
        user_id=user.id,
        token_hash=security.hash_token(raw_token),
        code_hash=security.hash_token(code),
        expires_at=utcnow() + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES),
    )
    db.add(token_row)
    db.commit()

    send_email(
        user.email,
        "Verify your Newcomer Navigation account",
        f"Hi {user.full_name.split(' ')[0]},\n\n"
        f"Your verification code is: {code}\n"
        f"This code expires in {VERIFICATION_CODE_TTL_MINUTES} minutes.\n\n"
        "If you didn't request this, you can ignore this email.",
    )
    return True, f"A verification code has been sent to {user.email}."


def confirm_verification_code(db: Session, user_id: str, code: str) -> tuple[bool, str]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise APIError("USER_NOT_FOUND", "User not found.", status.HTTP_404_NOT_FOUND)

    code_hash = security.hash_token(code)
    token_row = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.code_hash == code_hash,
        )
        .order_by(EmailVerificationToken.created_at.desc())
        .first()
    )

    if token_row is None or not token_row.is_valid():
        return False, "That code is invalid or has expired. Please request a new one."

    token_row.used_at = utcnow()
    user.verification_status = VerificationStatus.verified
    db.commit()
    return True, "Email verified successfully!"


def request_password_reset(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is not None:
        raw_token = security.generate_raw_token()
        token_row = PasswordResetToken(
            user_id=user.id,
            token_hash=security.hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
        )
        db.add(token_row)
        db.commit()

        reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
        send_email(
            user.email,
            "Reset your Newcomer Navigation password",
            f"Hi {user.full_name.split(' ')[0]},\n\n"
            f"Use this link to reset your password (expires in {PASSWORD_RESET_TTL_MINUTES} minutes):\n"
            f"{reset_link}\n\n"
            "If you didn't request this, you can ignore this email.",
        )
    # Always return the same message whether or not the account exists.
    return GENERIC_RESET_MESSAGE


def confirm_password_reset(db: Session, raw_token: str, new_password: str) -> None:
    token_hash = security.hash_token(raw_token)
    token_row = (
        db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    )
    if token_row is None or not token_row.is_valid():
        raise APIError(
            "INVALID_TOKEN", "This reset link is invalid or has expired.", status.HTTP_400_BAD_REQUEST
        )

    user = db.query(User).filter(User.id == token_row.user_id).first()
    if user is None:
        raise APIError("USER_NOT_FOUND", "User not found.", status.HTTP_404_NOT_FOUND)

    user.password_hash = security.hash_password(new_password)
    token_row.used_at = utcnow()
    db.commit()
