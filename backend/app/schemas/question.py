"""Question and Answer schemas.

`QuestionOut` / `AnswerOut` mirror the frontend's `Question` / `Answer`
interfaces. `upvotes` / `downvotes` / `answerCount` / `isAnswered` are
always computed server-side (see forum_service.py) -- they are never
accepted as input from the client.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from app.schemas.common import CamelModel
from app.schemas.user import UserOut


class QuestionOut(CamelModel):
    id: str
    title: str
    body: str
    author_id: str
    category_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    answer_count: int = 0
    upvotes: int = 0
    downvotes: int = 0
    is_answered: bool = False
    views: int = 0
    status: str = "open"

    # Optional embedded data -- populated by list/detail endpoints so the
    # frontend service layer can populate its synchronous user cache
    # without a second round trip (see figma uiux/src/services/auth.ts).
    author: Optional[UserOut] = None
    # The authenticated caller's own vote on this question, if any (1, -1, or 0).
    user_vote: int = 0


class AnswerOut(CamelModel):
    id: str
    question_id: str
    body: str
    author_id: str
    created_at: datetime
    updated_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    is_accepted: bool = False

    author: Optional[UserOut] = None
    user_vote: int = 0


class QuestionCreate(CamelModel):
    title: str = Field(min_length=10, max_length=300)
    body: str = Field(min_length=20, max_length=10000)
    category_id: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list, max_length=4)


class QuestionUpdate(CamelModel):
    title: Optional[str] = Field(default=None, min_length=10, max_length=300)
    body: Optional[str] = Field(default=None, min_length=20, max_length=10000)
    category_id: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, max_length=4)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ("open", "closed"):
            raise ValueError("status must be 'open' or 'closed'")
        return v


class AnswerCreate(CamelModel):
    body: str = Field(min_length=10, max_length=10000)


class AnswerUpdate(CamelModel):
    body: str = Field(min_length=10, max_length=10000)


class PaginatedQuestions(CamelModel):
    items: List[QuestionOut]
    total: int
    page: int
    page_size: int