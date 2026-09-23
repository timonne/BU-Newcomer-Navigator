"""Question model.

`upvotes` / `downvotes` / `answer_count` / `is_answered` are NOT stored here.
They are derived server-side from the votes and answers tables every time a
question is serialized (see services/forum_service.py), which is what makes
"never trust vote counts supplied by the frontend" true by construction
rather than by discipline — there is no column for a client to overwrite.

`views` IS stored, because it is a genuine counter with no source of truth
elsewhere.
"""
from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.category import question_tags
from app.models.mixins import TimestampMixin, UUIDPKMixin


class QuestionStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    deleted = "deleted"


class Question(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Slug FK into `categories` — the same id values the frontend already uses
    # as constants in figma uiux/src/data/categories.ts ("btech", "hostel", ...).
    category_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Denormalised copy of the author's course/programme at posting time, so
    # "filter by course/programme" (brief section 14) keeps working even if the
    # author later changes their own programme.
    course: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)

    status: Mapped[QuestionStatus] = mapped_column(
        Enum(QuestionStatus, native_enum=False, length=20), nullable=False, default=QuestionStatus.open
    )
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    author: Mapped["User"] = relationship(back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    category: Mapped[Optional["Category"]] = relationship()
    tags: Mapped[List["Tag"]] = relationship(secondary=question_tags, lazy="selectin")
