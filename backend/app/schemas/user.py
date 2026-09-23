"""User / profile schemas.

`UserOut` mirrors the frontend's `User` interface exactly (camelCase via
CamelModel) and is what every endpoint that embeds an author returns.
It never includes password_hash or any token.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import CamelModel


class UserOut(CamelModel):
    id: str
    full_name: str
    username: str
    email: str
    phone: str
    account_type: str
    verification_status: str
    course: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = ""
    avatar_color: str
    avatar_url: Optional[str] = None
    joined_at: date
    questions_count: int = 0
    answers_count: int = 0
    upvotes_received: int = 0


class UserUpdate(CamelModel):
    """Fields an authenticated user may edit on their own profile.
    Never includes verification_status, account_type, email, or username --
    the backend enforces that these cannot be self-edited (see api/users.py).
    """

    bio: Optional[str] = Field(default=None, max_length=1000)
    course: Optional[str] = Field(default=None, max_length=150)
    department: Optional[str] = Field(default=None, max_length=150)
    avatar_color: Optional[str] = Field(default=None, max_length=9)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class RegisterRequest(CamelModel):
    full_name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=7, max_length=30)
    email: EmailStr
    account_type: str  # "student" | "staff" | "other"
    password: str = Field(min_length=6, max_length=200)
    confirm_password: str = Field(min_length=6, max_length=200)
    course: Optional[str] = Field(default=None, max_length=150)
    department: Optional[str] = Field(default=None, max_length=150)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        if v not in ("student", "staff", "other"):
            raise ValueError("accountType must be one of: student, staff, other")
        return v


class LoginRequest(CamelModel):
    identifier: str = Field(min_length=1, description="Email or generated username")
    password: str = Field(min_length=1)


class AuthResponse(CamelModel):
    user: UserOut