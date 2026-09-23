"""Chatbot conversation history.

Conversations are always owned by an authenticated user. Anonymous chatbot
use is allowed (see api/chatbot.py) but is not persisted — there is no user
to attribute it to, and inventing a session identity would make one
anonymous visitor's history readable by another.

`source_type` / `source_ref_*` on Message record where an assistant answer
came from, so reopening a past conversation still shows the same university
or forum attribution the user originally saw.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Conversation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Derived from the first user message; purely a display label.
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=20), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # "university" | "community" | "general" — matches the frontend's
    # ChatMessage.sourceType union (figma uiux/src/types/index.ts).
    source_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    source_question_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_question_title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    source_answer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_author_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_document_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_document_title: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
