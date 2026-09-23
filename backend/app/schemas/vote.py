"""Vote, Category, and Tag schemas."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field, field_validator

from app.schemas.common import CamelModel


class VoteRequest(CamelModel):
    target_type: Literal["question", "answer"]
    target_id: str
    value: int  # must be 1 or -1

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("value must be 1 (upvote) or -1 (downvote)")
        return v


class VoteResult(CamelModel):
    upvotes: int
    downvotes: int
    user_vote: int  # the caller's resulting vote: 1, -1, or 0 (removed)


class CategoryOut(CamelModel):
    id: str
    name: str
    type: str
    subcategories: Optional[List[str]] = None


class TagOut(CamelModel):
    id: str
    name: str
    color: str