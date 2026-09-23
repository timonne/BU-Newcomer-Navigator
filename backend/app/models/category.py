"""Category and Tag models.

Seeded to match figma uiux/src/data/categories.ts exactly (same ids/names)
so the existing frontend — which imports its category/tag lists as static
constants rather than fetching them — stays perfectly in sync with what
the backend accepts and stores. See backend/seed.py.
"""
from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, JSON, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CategoryType(str, enum.Enum):
    academic = "academic"
    non_academic = "non-academic"


class Category(Base):
    __tablename__ = "categories"

    # Slug-style primary key, e.g. "btech", "hostel" — matches the frontend's
    # AcademicCategory.id values directly, so no ID-translation layer is needed.
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[CategoryType] = mapped_column(Enum(CategoryType, native_enum=False, length=20), nullable=False)
    subcategories: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#1E3A8A")


# Many-to-many association between questions and tags.
question_tags = Table(
    "question_tags",
    Base.metadata,
    Column("question_id", String(64), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(60), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
