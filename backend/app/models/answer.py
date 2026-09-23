"""Answer model."""
from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class AnswerStatus(str, enum.Enum):
    visible = "visible"
    deleted = "deleted"


class Answer(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "answers"

    question_id: Mapped[str] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AnswerStatus] = mapped_column(
        Enum(AnswerStatus, native_enum=False, length=20), nullable=False, default=AnswerStatus.visible
    )
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["Question"] = relationship(back_populates="answers")
    author: Mapped["User"] = relationship(back_populates="answers")
