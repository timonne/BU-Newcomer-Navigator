"""
Forum business logic: questions, answers, listing/filter/sort/pagination,
and the serialization helpers that attach server-computed vote counts.

Design note — why counts are computed, not stored:
`upvotes`, `downvotes`, `answerCount`, `isAnswered` and the three profile
activity counts are all derived with aggregate queries against the votes and
answers tables. Nothing the client sends can influence them, because there is
no column for them to write to. The cost is an extra aggregate per list
request; the benefit is that a count can never be wrong.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from fastapi import status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import APIError
from app.models.answer import Answer, AnswerStatus
from app.models.category import Tag
from app.models.question import Question, QuestionStatus
from app.models.user import User
from app.models.vote import Vote, VoteTargetType
from app.schemas.question import AnswerOut, QuestionOut

# ─────────────────────────────────────────────────────────────────────────
# Vote aggregation helpers
# ─────────────────────────────────────────────────────────────────────────


def vote_counts_for(
    db: Session, target_type: VoteTargetType, target_ids: Sequence[str]
) -> Dict[str, Tuple[int, int]]:
    """{target_id: (upvotes, downvotes)} for many targets in one query."""
    if not target_ids:
        return {}
    rows = (
        db.query(
            Vote.target_id,
            func.sum(case((Vote.value == 1, 1), else_=0)).label("ups"),
            func.sum(case((Vote.value == -1, 1), else_=0)).label("downs"),
        )
        .filter(Vote.target_type == target_type, Vote.target_id.in_(list(target_ids)))
        .group_by(Vote.target_id)
        .all()
    )
    return {r[0]: (int(r[1] or 0), int(r[2] or 0)) for r in rows}


def user_votes_for(
    db: Session,
    user_id: Optional[str],
    target_type: VoteTargetType,
    target_ids: Sequence[str],
) -> Dict[str, int]:
    """{target_id: 1 | -1} for the given user. Empty when anonymous."""
    if not user_id or not target_ids:
        return {}
    rows = (
        db.query(Vote.target_id, Vote.value)
        .filter(
            Vote.user_id == user_id,
            Vote.target_type == target_type,
            Vote.target_id.in_(list(target_ids)),
        )
        .all()
    )
    return {r[0]: int(r[1]) for r in rows}


def answer_counts_for(db: Session, question_ids: Sequence[str]) -> Dict[str, int]:
    if not question_ids:
        return {}
    rows = (
        db.query(Answer.question_id, func.count(Answer.id))
        .filter(
            Answer.question_id.in_(list(question_ids)),
            Answer.status == AnswerStatus.visible,
        )
        .group_by(Answer.question_id)
        .all()
    )
    return {r[0]: int(r[1]) for r in rows}


def compute_user_stats(db: Session, user_id: str) -> Dict[str, int]:
    """questionsCount / answersCount / upvotesReceived for a profile.

    `upvotes_received` counts upvotes on everything the user has authored —
    both their questions and their answers.
    """
    questions_count = (
        db.query(func.count(Question.id))
        .filter(Question.author_id == user_id, Question.status != QuestionStatus.deleted)
        .scalar()
        or 0
    )
    answers_count = (
        db.query(func.count(Answer.id))
        .filter(Answer.author_id == user_id, Answer.status == AnswerStatus.visible)
        .scalar()
        or 0
    )

    own_question_ids = [
        r[0]
        for r in db.query(Question.id).filter(
            Question.author_id == user_id, Question.status != QuestionStatus.deleted
        )
    ]
    own_answer_ids = [
        r[0]
        for r in db.query(Answer.id).filter(
            Answer.author_id == user_id, Answer.status == AnswerStatus.visible
        )
    ]

    upvotes = 0
    if own_question_ids:
        upvotes += (
            db.query(func.count(Vote.id))
            .filter(
                Vote.target_type == VoteTargetType.question,
                Vote.target_id.in_(own_question_ids),
                Vote.value == 1,
            )
            .scalar()
            or 0
        )
    if own_answer_ids:
        upvotes += (
            db.query(func.count(Vote.id))
            .filter(
                Vote.target_type == VoteTargetType.answer,
                Vote.target_id.in_(own_answer_ids),
                Vote.value == 1,
            )
            .scalar()
            or 0
        )

    return {
        "questions_count": int(questions_count),
        "answers_count": int(answers_count),
        "upvotes_received": int(upvotes),
    }


# ─────────────────────────────────────────────────────────────────────────
# Serialization
# ─────────────────────────────────────────────────────────────────────────


def serialize_questions(
    db: Session,
    questions: Sequence[Question],
    viewer: Optional[User] = None,
    include_authors: bool = True,
) -> List[QuestionOut]:
    from app.services.user_service import to_user_out

    ids = [q.id for q in questions]
    counts = vote_counts_for(db, VoteTargetType.question, ids)
    answers = answer_counts_for(db, ids)
    mine = user_votes_for(db, viewer.id if viewer else None, VoteTargetType.question, ids)

    out: List[QuestionOut] = []
    for q in questions:
        ups, downs = counts.get(q.id, (0, 0))
        n_answers = answers.get(q.id, 0)
        out.append(
            QuestionOut(
                id=q.id,
                title=q.title,
                body=q.body,
                author_id=q.author_id,
                category_id=q.category_id,
                tags=[t.id for t in q.tags],
                created_at=q.created_at,
                updated_at=q.updated_at,
                answer_count=n_answers,
                upvotes=ups,
                downvotes=downs,
                is_answered=n_answers > 0,
                views=q.views,
                status=q.status.value,
                author=to_user_out(db, q.author, viewer=viewer) if include_authors and q.author else None,
                user_vote=mine.get(q.id, 0),
            )
        )
    return out


def serialize_answers(
    db: Session,
    answers: Sequence[Answer],
    viewer: Optional[User] = None,
    include_authors: bool = True,
) -> List[AnswerOut]:
    from app.services.user_service import to_user_out

    ids = [a.id for a in answers]
    counts = vote_counts_for(db, VoteTargetType.answer, ids)
    mine = user_votes_for(db, viewer.id if viewer else None, VoteTargetType.answer, ids)

    out: List[AnswerOut] = []
    for a in answers:
        ups, downs = counts.get(a.id, (0, 0))
        out.append(
            AnswerOut(
                id=a.id,
                question_id=a.question_id,
                body=a.body,
                author_id=a.author_id,
                created_at=a.created_at,
                updated_at=a.updated_at,
                upvotes=ups,
                downvotes=downs,
                is_accepted=a.is_accepted,
                author=to_user_out(db, a.author, viewer=viewer) if include_authors and a.author else None,
                user_vote=mine.get(a.id, 0),
            )
        )
    return out


# ─────────────────────────────────────────────────────────────────────────
# Queries
# ─────────────────────────────────────────────────────────────────────────

SORT_LATEST = "latest"
SORT_MOST_UPVOTED = "most-upvoted"
SORT_MOST_ANSWERED = "most-answered"
VALID_SORTS = (SORT_LATEST, SORT_MOST_UPVOTED, SORT_MOST_ANSWERED)


def list_questions(
    db: Session,
    *,
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    course: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    answered: str = "all",
    sort_by: str = SORT_LATEST,
    page: int = 1,
    page_size: int = 20,
    viewer: Optional[User] = None,
) -> Tuple[List[QuestionOut], int]:
    """Returns (questions, total_matching_count).

    Sorting by upvotes/answers is done with correlated subqueries so the
    ordering is applied in SQL across the whole result set — not just within
    the current page, which is the classic bug when counts are computed in
    Python after pagination.
    """
    if sort_by not in VALID_SORTS:
        sort_by = SORT_LATEST
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    q = db.query(Question).filter(Question.status != QuestionStatus.deleted)

    if search:
        needle = f"%{search.strip().lower()}%"
        # Tag matches are folded in via a subquery so searching "hostel" finds
        # questions tagged hostel even if the word is not in the title/body.
        tag_match = (
            select(Question.id).join(Question.tags).where(func.lower(Tag.name).like(needle))
        )
        q = q.filter(
            or_(
                func.lower(Question.title).like(needle),
                func.lower(Question.body).like(needle),
                Question.id.in_(tag_match),
            )
        )

    if category_id:
        q = q.filter(Question.category_id == category_id)
    if course:
        q = q.filter(Question.course == course)

    tag_list = [t for t in (tags or []) if t]
    if tag_list:
        q = q.filter(Question.tags.any(Tag.id.in_(tag_list)))

    answer_count_sq = (
        select(func.count(Answer.id))
        .where(Answer.question_id == Question.id, Answer.status == AnswerStatus.visible)
        .correlate(Question)
        .scalar_subquery()
    )
    if answered == "answered":
        q = q.filter(answer_count_sq > 0)
    elif answered == "unanswered":
        q = q.filter(answer_count_sq == 0)

    total = q.with_entities(func.count(func.distinct(Question.id))).scalar() or 0

    if sort_by == SORT_MOST_UPVOTED:
        score_sq = (
            select(func.coalesce(func.sum(Vote.value), 0))
            .where(Vote.target_type == VoteTargetType.question, Vote.target_id == Question.id)
            .correlate(Question)
            .scalar_subquery()
        )
        q = q.order_by(score_sq.desc(), Question.created_at.desc())
    elif sort_by == SORT_MOST_ANSWERED:
        q = q.order_by(answer_count_sq.desc(), Question.created_at.desc())
    else:
        q = q.order_by(Question.created_at.desc())

    rows = (
        q.options(selectinload(Question.author), selectinload(Question.tags))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return serialize_questions(db, rows, viewer=viewer), int(total)


def get_question_or_404(db: Session, question_id: str, *, allow_deleted: bool = False) -> Question:
    q = db.query(Question).filter(Question.id == question_id).first()
    if q is None or (q.status == QuestionStatus.deleted and not allow_deleted):
        raise APIError("QUESTION_NOT_FOUND", "Question not found.", status.HTTP_404_NOT_FOUND)
    return q


def get_answer_or_404(db: Session, answer_id: str) -> Answer:
    a = db.query(Answer).filter(Answer.id == answer_id).first()
    if a is None or a.status == AnswerStatus.deleted:
        raise APIError("ANSWER_NOT_FOUND", "Answer not found.", status.HTTP_404_NOT_FOUND)
    return a


def list_answers(
    db: Session, question_id: str, *, sort: str = "votes", viewer: Optional[User] = None
) -> List[AnswerOut]:
    """Default ordering is highest net vote score first (brief section 15).

    Net score (upvotes minus downvotes) is computed in SQL; `sort="newest"`
    switches to creation order.
    """
    rows = (
        db.query(Answer)
        .filter(Answer.question_id == question_id, Answer.status == AnswerStatus.visible)
        .options(selectinload(Answer.author))
        .all()
    )
    serialized = serialize_answers(db, rows, viewer=viewer)
    if sort == "newest":
        serialized.sort(key=lambda a: a.created_at, reverse=True)
    else:
        serialized.sort(key=lambda a: (a.upvotes - a.downvotes, a.created_at), reverse=True)
    return serialized


# ─────────────────────────────────────────────────────────────────────────
# Mutations
# ─────────────────────────────────────────────────────────────────────────


def _resolve_tags(db: Session, tag_ids: Iterable[str]) -> List[Tag]:
    """Only tags that exist in the `tags` table are attached.

    Unknown tag ids are silently dropped rather than auto-created, so a
    client cannot inflate the tag vocabulary (mass-assignment protection).
    """
    ids = [t for t in tag_ids if t]
    if not ids:
        return []
    return db.query(Tag).filter(Tag.id.in_(ids)).all()


def create_question(db: Session, author: User, data) -> Question:
    q = Question(
        author_id=author.id,
        title=data.title.strip(),
        body=data.body.strip(),
        category_id=data.category_id,
        course=author.course,
        status=QuestionStatus.open,
        views=0,
    )
    q.tags = _resolve_tags(db, data.tags or [])
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def update_question(db: Session, question: Question, author: User, data) -> Question:
    require_owner(question.author_id, author, "question")
    if data.title is not None:
        question.title = data.title.strip()
    if data.body is not None:
        question.body = data.body.strip()
    if data.category_id is not None:
        question.category_id = data.category_id
    if data.tags is not None:
        question.tags = _resolve_tags(db, data.tags)
    if data.status is not None:
        question.status = QuestionStatus(data.status)
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question: Question, author: User) -> None:
    """Soft delete — the row and its answers stay, so existing links don't 404
    into a confusing state and moderation history is preserved."""
    require_owner(question.author_id, author, "question")
    question.status = QuestionStatus.deleted
    db.commit()


def create_answer(db: Session, question: Question, author: User, data) -> Answer:
    if question.status == QuestionStatus.closed:
        raise APIError(
            "QUESTION_CLOSED", "This question is closed and no longer accepts answers.", status.HTTP_409_CONFLICT
        )
    a = Answer(
        question_id=question.id,
        author_id=author.id,
        body=data.body.strip(),
        status=AnswerStatus.visible,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def update_answer(db: Session, answer: Answer, author: User, data) -> Answer:
    require_owner(answer.author_id, author, "answer")
    answer.body = data.body.strip()
    db.commit()
    db.refresh(answer)
    return answer


def delete_answer(db: Session, answer: Answer, author: User) -> None:
    require_owner(answer.author_id, author, "answer")
    answer.status = AnswerStatus.deleted
    db.commit()


def require_owner(owner_id: str, user: User, noun: str) -> None:
    """Authorization is enforced here, in the backend.

    The frontend hiding an Edit button is a UI affordance, not a security
    control (brief section 12).
    """
    if owner_id != user.id:
        raise APIError(
            "FORBIDDEN", f"You can only modify your own {noun}.", status.HTTP_403_FORBIDDEN
        )


def increment_views(db: Session, question: Question) -> None:
    question.views = (question.views or 0) + 1
    db.commit()
