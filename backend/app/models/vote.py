"""Vote model.

The `uq_vote_user_target` unique constraint is what actually prevents a user
from stacking votes on the same question/answer (brief sections 6 and 16).
It is a database constraint, not an application check, so it holds even if two
requests race each other. `services/voting_service.py` handles the four legal
transitions (add / switch / remove / re-add) on top of it.

There is no `target_id` foreign key, because a single column cannot reference
two different tables. `voting_service` validates that the target row exists
before inserting, and deleting a question or answer cleans up its votes (see
`voting_service.delete_votes_for_target`).
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDPKMixin, utcnow


class VoteTargetType(str, enum.Enum):
    question = "question"
    answer = "answer"


class Vote(UUIDPKMixin, Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_vote_user_target"),
        CheckConstraint("value IN (-1, 1)", name="ck_vote_value"),
        Index("ix_votes_target", "target_type", "target_id"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[VoteTargetType] = mapped_column(
        Enum(VoteTargetType, native_enum=False, length=20), nullable=False
    )
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # 1 = upvote, -1 = downvote. Enforced by ck_vote_value above as well as by
    # the Pydantic schema (schemas/vote.py).
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="votes")
