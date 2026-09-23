"""Schemas for email verification and password reset flows."""
from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel


class SendVerificationRequest(CamelModel):
    email: EmailStr


class SendVerificationResponse(CamelModel):
    success: bool
    message: str


class VerifyCodeRequest(CamelModel):
    user_id: str
    code: str = Field(min_length=4, max_length=10)


class VerifyCodeResponse(CamelModel):
    success: bool
    message: str


class PasswordResetRequest(CamelModel):
    email: EmailStr


class PasswordResetConfirm(CamelModel):
    token: str
    new_password: str = Field(min_length=6, max_length=200)


class GenericMessageResponse(CamelModel):
    success: bool
    message: str