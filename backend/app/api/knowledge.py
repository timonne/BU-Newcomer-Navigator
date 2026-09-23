"""
/api/knowledge/* — ingesting and searching the university knowledge base.

This is the mechanism by which verified Bennett University documentation gets
into the system. Nothing here ships with real university content: the project
has none yet (see README "Demo limitations"), and the seed script's entries
are all flagged `isDemo: true`.

WRITE ACCESS is restricted to verified staff accounts. That is a deliberately
simple model for a student project — if you need a proper admin role, add an
`is_admin` column to User and swap the dependency below; no other code
changes.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_verified_staff
from app.core.errors import APIError
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.knowledge import KnowledgeBaseEntry
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeEntryCreate,
    KnowledgeEntryOut,
    KnowledgeEntryUpdate,
    KnowledgeSearchHit,
)
from app.services import retrieval_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=List[KnowledgeEntryOut])
def list_entries(
    include_demo: bool = Query(default=True, alias="includeDemo"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeBaseEntry)
    if not include_demo:
        query = query.filter(KnowledgeBaseEntry.is_demo.is_(False))
    return query.order_by(KnowledgeBaseEntry.category, KnowledgeBaseEntry.question).limit(limit).all()


@router.get("/search", response_model=List[KnowledgeSearchHit])
def search_entries(
    q: str = Query(min_length=2, max_length=400),
    threshold: float = Query(default=retrieval_service.KB_RELEVANCE_THRESHOLD, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """Runs the same retrieval the chatbot uses, exposed for debugging and
    threshold tuning."""
    hits = retrieval_service.search_knowledge_base(db, q, threshold=threshold)
    return [
        KnowledgeSearchHit(
            id=h.document_id,
            title=h.document_title,
            content=h.content,
            relevance=round(h.relevance, 4),
            source_type=h.source_type,
            is_demo=h.is_demo,
        )
        for h in hits
    ]


@router.post("", response_model=KnowledgeEntryOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/hour")
def create_entry(
    request: Request,
    payload: KnowledgeEntryCreate,
    db: Session = Depends(get_db),
    staff: User = Depends(require_verified_staff),
):
    entry = KnowledgeBaseEntry(
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        keywords=[k.strip().lower() for k in payload.keywords if k.strip()],
        category=payload.category.strip() or "General",
        source_type="university",
        is_demo=payload.is_demo,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=KnowledgeEntryOut)
def update_entry(
    entry_id: str,
    payload: KnowledgeEntryUpdate,
    db: Session = Depends(get_db),
    staff: User = Depends(require_verified_staff),
):
    entry = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.id == entry_id).first()
    if entry is None:
        raise APIError("ENTRY_NOT_FOUND", "Knowledge base entry not found.", status.HTTP_404_NOT_FOUND)

    if payload.question is not None:
        entry.question = payload.question.strip()
    if payload.answer is not None:
        entry.answer = payload.answer.strip()
    if payload.keywords is not None:
        entry.keywords = [k.strip().lower() for k in payload.keywords if k.strip()]
    if payload.category is not None:
        entry.category = payload.category.strip() or "General"
    if payload.is_demo is not None:
        entry.is_demo = payload.is_demo

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    staff: User = Depends(require_verified_staff),
):
    entry = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.id == entry_id).first()
    if entry is None:
        raise APIError("ENTRY_NOT_FOUND", "Knowledge base entry not found.", status.HTTP_404_NOT_FOUND)
    db.delete(entry)
    db.commit()
    return None
