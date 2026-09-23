"""
/api/users/* — public profiles and own-profile editing.

Ownership rule: there is deliberately no `PATCH /api/users/{id}` route at
all. The only way to edit a profile is `PATCH /api/users/me`, which resolves
the target from the auth cookie. That makes "you cannot edit another user's
profile" a structural property of the API rather than a check that could be
forgotten (brief section 12).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional
from app.core.errors import APIError
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import to_user_out, update_own_profile

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    ids: Optional[str] = Query(default=None, description="Comma-separated user ids"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    """Batch profile lookup.

    The existing frontend calls `getUserById(...)` synchronously while
    rendering question and answer cards, so its service layer keeps a local
    user cache. This endpoint is what fills that cache in one request instead
    of one request per author.
    """
    query = db.query(User)
    if ids:
        wanted = [i.strip() for i in ids.split(",") if i.strip()]
        if not wanted:
            return []
        query = query.filter(User.id.in_(wanted[:200]))
    rows = query.limit(limit).all()
    return [to_user_out(db, u, viewer=viewer) for u in rows]


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edits the authenticated user's own profile.

    `UserUpdate` contains only bio / course / department / avatar fields, so
    verification status, account type, email and username cannot be
    self-edited even if they appear in the request body.
    """
    updated = update_own_profile(db, user, payload)
    return to_user_out(db, updated, viewer=updated)


@router.get("/by-username/{username}", response_model=UserOut)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    row = db.query(User).filter(User.username == username.lower()).first()
    if row is None:
        raise APIError("USER_NOT_FOUND", "User not found.", status.HTTP_404_NOT_FOUND)
    return to_user_out(db, row, viewer=viewer)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    """Public profile. Includes the three activity counts the profile page
    shows; excludes email and phone unless the viewer is the profile owner."""
    row = db.query(User).filter(User.id == user_id).first()
    if row is None:
        raise APIError("USER_NOT_FOUND", "User not found.", status.HTTP_404_NOT_FOUND)
    return to_user_out(db, row, viewer=viewer)
