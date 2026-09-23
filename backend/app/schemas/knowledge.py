"""University knowledge-base schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.common import CamelModel


class KnowledgeEntryOut(CamelModel):
    id: str
    question: str
    answer: str
    keywords: List[str] = Field(default_factory=list)
    category: str
    source_type: str
    # True for anything created by backend/seed.py. Surfaced in the API so a
    # caller can always tell demo content from verified university content
    # (brief section 21).
    is_demo: bool
    created_at: datetime
    updated_at: datetime


class KnowledgeEntryCreate(CamelModel):
    question: str = Field(min_length=5, max_length=400)
    answer: str = Field(min_length=10, max_length=20000)
    keywords: List[str] = Field(default_factory=list, max_length=40)
    category: str = Field(default="General", max_length=150)
    # Defaults to False: anything ingested through the API is assumed to be
    # real documentation you have verified. Only the seed script sets True.
    is_demo: bool = False


class KnowledgeEntryUpdate(CamelModel):
    question: Optional[str] = Field(default=None, min_length=5, max_length=400)
    answer: Optional[str] = Field(default=None, min_length=10, max_length=20000)
    keywords: Optional[List[str]] = Field(default=None, max_length=40)
    category: Optional[str] = Field(default=None, max_length=150)
    is_demo: Optional[bool] = None


class KnowledgeSearchHit(CamelModel):
    """A retrieval result, with the relevance score that produced it.

    Exposed so you can tune KB_RELEVANCE_THRESHOLD against real queries
    instead of guessing (see services/retrieval_service.py).
    """

    id: Optional[str] = None
    title: Optional[str] = None
    content: str
    relevance: float
    source_type: str
    is_demo: bool = False
