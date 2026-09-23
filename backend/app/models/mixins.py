"""Shared model mixins: string UUID primary keys and timestamp columns."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def new_uuid() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPKMixin:
    """String UUID primary key, e.g. 'a1b2c3...'.

    String(64) is explicit (rather than a bare Mapped[str]) so that
    `Base.metadata.create_all` produces the same column type as the Alembic
    migration in alembic/versions/0001_initial_schema.py, and so the FK
    columns that reference it (String(64)) match exactly.
    """

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
