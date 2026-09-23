"""
/api/questions/* — the forum.

Covers listing (with search, filter, sort, pagination), the question thread,
and create/edit/close for the author. Answers hang off the question thread at
`/api/questions/{id}/answers`; editing and deleting an individual answer
lives in api/answers.py.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.question import (
    AnswerCreate,
    AnswerOut,
    PaginatedQuestions,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
)
from app.services import forum_service

router = APIRouter(prefix="/api/questions", tags=["forum"])


@router.get("", response_model=PaginatedQuestions)
def list_questions(
    search: Optional[str] = Query(default=None, max_length=200),
    category_id: Optional[str] = Query(default=None, alias="categoryId"),
    course: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated tag ids"),
    answered: str = Query(default="all", pattern="^(all|answered|unanswered)$"),
    sort_by: str = Query(default="latest", alias="sortBy"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    """`sortBy` accepts latest | most-upvoted | most-answered, matching the
    frontend's `ForumFilters.sortBy` union exactly."""
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    items, total = forum_service.list_questions(
        db,
        search=search,
        category_id=category_id,
        course=course,
        tags=tag_list,
        answered=answered,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        viewer=viewer,
    )
    return PaginatedQuestions(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
def create_question(
    request: Request,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = forum_service.create_question(db, user, payload)
    return forum_service.serialize_questions(db, [question], viewer=user)[0]


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: str,
    count_view: bool = Query(default=True, alias="countView"),
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    """Returns the question with its author embedded and the caller's own
    vote, so the thread page can render without a second round trip."""
    question = forum_service.get_question_or_404(db, question_id)
    if count_view:
        forum_service.increment_views(db, question)
    return forum_service.serialize_questions(db, [question], viewer=viewer)[0]


@router.patch("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: str,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = forum_service.get_question_or_404(db, question_id)
    updated = forum_service.update_question(db, question, user, payload)
    return forum_service.serialize_questions(db, [updated], viewer=user)[0]


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Soft-deletes the author's own question (status -> deleted)."""
    question = forum_service.get_question_or_404(db, question_id)
    forum_service.delete_question(db, question, user)
    return None


# ── Answers within a thread ─────────────────────────────────────────────


@router.get("/{question_id}/answers", response_model=List[AnswerOut])
def list_answers(
    question_id: str,
    sort: str = Query(default="votes", pattern="^(votes|newest)$"),
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    """Default order is highest net vote score first; `sort=newest` switches
    to most recent first (brief section 15)."""
    forum_service.get_question_or_404(db, question_id)
    return forum_service.list_answers(db, question_id, sort=sort, viewer=viewer)


@router.post("/{question_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("40/hour")
def create_answer(
    request: Request,
    question_id: str,
    payload: AnswerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = forum_service.get_question_or_404(db, question_id)
    answer = forum_service.create_answer(db, question, user, payload)
    return forum_service.serialize_answers(db, [answer], viewer=user)[0]
