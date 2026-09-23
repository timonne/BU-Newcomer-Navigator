"""
/api/answers/* — editing and deleting an individual answer.

Creating an answer lives on the question thread route
(`POST /api/questions/{id}/answers`) because an answer only exists in the
context of a question.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.user import User
from app.schemas.question import AnswerOut, AnswerUpdate
from app.services import forum_service

router = APIRouter(prefix="/api/answers", tags=["forum"])


@router.get("/{answer_id}", response_model=AnswerOut)
def get_answer(
    answer_id: str,
    db: Session = Depends(get_db),
    viewer: User = Depends(get_current_user_optional),
):
    answer = forum_service.get_answer_or_404(db, answer_id)
    return forum_service.serialize_answers(db, [answer], viewer=viewer)[0]


@router.patch("/{answer_id}", response_model=AnswerOut)
def update_answer(
    answer_id: str,
    payload: AnswerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Only the answer's author may edit it — enforced in
    forum_service.require_owner, not by the UI hiding a button."""
    answer = forum_service.get_answer_or_404(db, answer_id)
    updated = forum_service.update_answer(db, answer, user, payload)
    return forum_service.serialize_answers(db, [updated], viewer=user)[0]


@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_answer(
    answer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    answer = forum_service.get_answer_or_404(db, answer_id)
    forum_service.delete_answer(db, answer, user)
    return None
