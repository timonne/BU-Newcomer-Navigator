"""
User-related read helpers.

`to_user_out` is the single place that turns a `User` ORM row into the
`UserOut` schema the frontend expects, including the three activity
counts (questionsCount, answersCount, upvotesReceived). Those counts are
always computed live from the questions/answers/votes tables rather than
stored as columns, so they can never drift out of sync -- see
forum_service.compute_user_stats for the actual query.

PRIVACY: email and phone are only included when the viewer is the user
themselves. Every other caller gets empty strings. The existing frontend's
profile page never renders either field, so this costs nothing visually --
it just means a public profile endpoint cannot be used to harvest contact
details (brief section 24).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserOut


def to_user_out(db: Session, user: User, viewer: Optional[User] = None) -> UserOut:
    from app.services.forum_service import compute_user_stats

    stats = compute_user_stats(db, user.id)
    is_self = viewer is not None and viewer.id == user.id

    return UserOut(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        email=user.email if is_self else "",
        phone=user.phone if is_self else "",
        account_type=user.account_type.value,
        verification_status=user.verification_status.value,
        course=user.course,
        department=user.department,
        bio=user.bio or "",
        avatar_color=user.avatar_color,
        avatar_url=user.avatar_url,
        joined_at=user.joined_at,
        questions_count=stats["questions_count"],
        answers_count=stats["answers_count"],
        upvotes_received=stats["upvotes_received"],
    )


def update_own_profile(db: Session, user: User, data) -> User:
    """Applies only the whitelisted editable fields.

    This is an explicit field-by-field assignment rather than a loop over the
    request body, which is what makes mass assignment impossible: there is no
    code path here that could write `verification_status`, `account_type`,
    `email`, `username`, `password_hash` or `account_status`, even if a client
    sends them (brief section 12).
    """
    if data.bio is not None:
        user.bio = data.bio.strip()
    if data.course is not None:
        user.course = data.course.strip() or None
    if data.department is not None:
        user.department = data.department.strip() or None
    if data.avatar_color is not None:
        user.avatar_color = data.avatar_color.strip()
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url.strip() or None

    db.commit()
    db.refresh(user)
    return user
