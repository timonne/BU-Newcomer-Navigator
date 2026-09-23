"""
Voting logic.

The four legal transitions, all on top of the `uq_vote_user_target` unique
constraint in models/vote.py:

    no vote  + value      -> insert (upvote or downvote)
    existing + same value -> delete  (toggle off / remove vote)
    existing + other value-> update  (upvote <-> downvote)

An IntegrityError from a concurrent duplicate insert is caught and retried as
an update, so two simultaneous clicks can never produce two rows.
"""
from __future__ import annotations

from typing import Tuple

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.models.answer import Answer, AnswerStatus
from app.models.mixins import utcnow
from app.models.question import Question, QuestionStatus
from app.models.user import User
from app.models.vote import Vote, VoteTargetType
from app.schemas.vote import VoteResult
from app.services.forum_service import vote_counts_for


def _assert_target_exists(db: Session, target_type: VoteTargetType, target_id: str) -> str:
    """Returns the target's author id, so self-voting can be blocked."""
    if target_type == VoteTargetType.question:
        row = db.query(Question).filter(Question.id == target_id).first()
        if row is None or row.status == QuestionStatus.deleted:
            raise APIError("QUESTION_NOT_FOUND", "Question not found.", status.HTTP_404_NOT_FOUND)
        return row.author_id
    row = db.query(Answer).filter(Answer.id == target_id).first()
    if row is None or row.status == AnswerStatus.deleted:
        raise APIError("ANSWER_NOT_FOUND", "Answer not found.", status.HTTP_404_NOT_FOUND)
    return row.author_id


def cast_vote(db: Session, user: User, target_type_raw: str, target_id: str, value: int) -> VoteResult:
    if value not in (1, -1):
        raise APIError("INVALID_VOTE", "Vote value must be 1 or -1.", status.HTTP_400_BAD_REQUEST)

    target_type = VoteTargetType(target_type_raw)
    author_id = _assert_target_exists(db, target_type, target_id)

    if author_id == user.id:
        raise APIError(
            "SELF_VOTE_FORBIDDEN", "You cannot vote on your own post.", status.HTTP_403_FORBIDDEN
        )

    existing = (
        db.query(Vote)
        .filter(
            Vote.user_id == user.id,
            Vote.target_type == target_type,
            Vote.target_id == target_id,
        )
        .first()
    )

    resulting_vote = 0
    if existing is None:
        vote = Vote(user_id=user.id, target_type=target_type, target_id=target_id, value=value)
        db.add(vote)
        try:
            db.commit()
            resulting_vote = value
        except IntegrityError:
            # A concurrent request inserted first — fall back to updating it.
            db.rollback()
            existing = (
                db.query(Vote)
                .filter(
                    Vote.user_id == user.id,
                    Vote.target_type == target_type,
                    Vote.target_id == target_id,
                )
                .first()
            )
            if existing is not None:
                existing.value = value
                existing.updated_at = utcnow()
                db.commit()
                resulting_vote = value
    elif existing.value == value:
        db.delete(existing)
        db.commit()
        resulting_vote = 0
    else:
        existing.value = value
        existing.updated_at = utcnow()
        db.commit()
        resulting_vote = value

    counts = vote_counts_for(db, target_type, [target_id])
    ups, downs = counts.get(target_id, (0, 0))
    return VoteResult(upvotes=ups, downvotes=downs, user_vote=resulting_vote)


def get_user_vote(db: Session, user_id: str, target_type_raw: str, target_id: str) -> int:
    row = (
        db.query(Vote.value)
        .filter(
            Vote.user_id == user_id,
            Vote.target_type == VoteTargetType(target_type_raw),
            Vote.target_id == target_id,
        )
        .first()
    )
    return int(row[0]) if row else 0


def delete_votes_for_target(db: Session, target_type_raw: str, target_id: str) -> None:
    """Called when a target is hard-deleted. Votes have no FK to their target
    (one column cannot reference two tables), so cleanup is explicit."""
    db.query(Vote).filter(
        Vote.target_type == VoteTargetType(target_type_raw),
        Vote.target_id == target_id,
    ).delete(synchronize_session=False)
    db.commit()
