"""
/api/categories/* and /api/courses — the category, tag and programme lists.

These are served from the database (seeded from the same ids the frontend
already uses as constants in figma uiux/src/data/categories.ts) so that
programmes and categories can be updated later without a frontend rebuild
(brief section 6). The existing frontend still reads its local constants for
rendering; these endpoints exist so it can move to server-driven lists
whenever you want, and so the backend validates against the same vocabulary.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category, CategoryType, Tag
from app.schemas.vote import CategoryOut, TagOut

router = APIRouter(tags=["categories"])


@router.get("/api/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Category).order_by(Category.type, Category.name).all()
    return [
        CategoryOut(id=c.id, name=c.name, type=c.type.value, subcategories=c.subcategories)
        for c in rows
    ]


@router.get("/api/categories/tags", response_model=List[TagOut])
def list_tags(db: Session = Depends(get_db)):
    rows = db.query(Tag).order_by(Tag.name).all()
    return [TagOut(id=t.id, name=t.name, color=t.color) for t in rows]


@router.get("/api/courses", response_model=List[CategoryOut])
def list_courses(db: Session = Depends(get_db)):
    """Academic programmes only — the subset used for the course/programme
    filter and the profile 'course' field."""
    rows = (
        db.query(Category)
        .filter(Category.type == CategoryType.academic)
        .order_by(Category.name)
        .all()
    )
    return [
        CategoryOut(id=c.id, name=c.name, type=c.type.value, subcategories=c.subcategories)
        for c in rows
    ]
