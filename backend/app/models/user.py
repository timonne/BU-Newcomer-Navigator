"""User model.

Mirrors the fields the existing frontend's `User` interface expects
(figma uiux/src/types/index.ts) plus the server-only columns it must never
see: `password_hash`, `account_status`.

The three activity counts the frontend shows (questionsCount, answersCount,
upvotesReceived) are deliberately NOT columns here — they are computed live
from the questions/answers/votes tables in
`services/forum_service.compute_user_stats`, so they can never drift out of
sync with reality.
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Date, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin, utcnow

# Kept in sync with the AVATAR_COLORS list in figma uiux/src/services/auth.ts
# so backend-created users look identical to the frontend's demo users.
AVATAR_COLORS = [
    "#1E3A8A",
    "#7C3AED",
    "#059669",
    "#D97706",
    "#DB2777",
    "#0891B2",
    "#EA580C",
    "#9333EA",
    "#16A34A",
    "#DC2626",
]


class AccountType(str, enum.Enum):
    student = "student"
    staff = "staff"
    other = "other"


class VerificationStatus(str, enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"


class AccountStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Generated from full_name by services/username_service.py — users never
    # choose it. Uniqueness is enforced by the database, not just in code.
    username: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")

    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, native_enum=False, length=20), nullable=False, default=AccountType.other
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=20),
        nullable=False,
        default=VerificationStatus.unverified,
    )
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, native_enum=False, length=20), nullable=False, default=AccountStatus.active
    )

    # Never returned by any endpoint — see schemas/user.py (UserOut has no
    # password field at all, so it cannot leak by accident).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    course: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")

    # The frontend renders initials on a coloured circle rather than an image
    # (figma uiux/src/components/common/Avatar.tsx), so `avatar_color` is what
    # it actually uses. `avatar_url` is stored for when real uploads are added.
    avatar_color: Mapped[str] = mapped_column(String(9), nullable=False, default="#1E3A8A")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    joined_at: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: utcnow().date())

    # Marks rows created by backend/seed.py so demo content is always
    # distinguishable from real accounts.
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    questions: Mapped[List["Question"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    votes: Mapped[List["Vote"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def first_name(self) -> str:
        """Used by the chatbot to greet the user ("Hi Timonne!").

        Derived from the authenticated user's stored full name — never from a
        value supplied by the browser.
        """
        return (self.full_name or "").strip().split(" ")[0]
