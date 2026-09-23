"""University knowledge-base entry.

This is intentionally a simple keyword-indexed table rather than a vector
store — there is no verified official Bennett University document corpus
to index yet (see README "Demo limitations"), and a simple, inspectable
retrieval model is easier for a student developer to maintain and debug
than an embeddings pipeline. `retrieval_service.py` documents exactly
where a semantic/embedding-based search could be swapped in later
without changing this table's shape (add a `chunks` table with vector
columns and update the retrieval query — the KnowledgeBaseEntry API
contract would not need to change).

Every row seeded by backend/seed.py has is_demo=True and is clearly
demo content, NOT verified official university information.
"""
from __future__ import annotations

from typing import List

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class KnowledgeBaseEntry(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_base_entries"

    question: Mapped[str] = mapped_column(String(400), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(150), nullable=False, default="General")
    # Always "university" today; kept as a column (not a hardcoded constant)
    # so future non-university verified sources could be added without a
    # schema change.
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="university")
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
