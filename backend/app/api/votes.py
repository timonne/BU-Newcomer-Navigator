"""
/api/votes/* — casting and reading votes.

Every response returns freshly-aggregated `upvotes` / `downvotes` computed
from the votes table, so the frontend always renders server-truth rather than
its own optimistic arithmetic (brief section 16).
"""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.models.vote import VoteTargetType
from app.schemas.vote import VoteRequest, VoteResult
from app.services import forum_service, voting_service

router = APIRouter(prefix="/api/votes", tags=["votes"])


@router.post("", response_model=VoteResult)
@limiter.limit("120/minute")
def cast_vote(
    request: Request,
    payload: VoteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Idempotent per (user, target): sending the same value twice removes the
    vote, sending the opposite value switches it."""
    return voting_service.cast_vote(db, user, payload.target_type, payload.target_id, payload.value)


@router.get("/mine", response_model=Dict[str, int])
def my_votes(
    target_type: str = Query(alias="targetType", pattern="^(question|answer)$"),
    target_ids: Optional[str] = Query(default=None, alias="targetIds"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """{targetId: 1 | -1} for the caller.

    Returns an empty object for anonymous visitors rather than 401, because
    the forum is readable without signing in and the vote arrows simply
    render in their neutral state.
    """
    if user is None:
        return {}
    ids = [i.strip() for i in (target_ids or "").split(",") if i.strip()]
    if not ids:
        return {}
    return forum_service.user_votes_for(db, user.id, VoteTargetType(target_type), ids[:200])
