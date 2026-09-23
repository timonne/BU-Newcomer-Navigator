"""
Username generation.

Mirrors figma uiux/src/data/users.ts `generateUsername` exactly:
lowercase full name, spaces -> dots, strip anything that isn't a-z/0-9/dot,
then append an incrementing numeric suffix on collision
(timonne.choudhury, timonne.choudhury2, timonne.choudhury3, ...).
Users never choose their own username (project brief section 8).
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.user import User


def _slugify_name(full_name: str) -> str:
    base = full_name.strip().lower()
    base = re.sub(r"\s+", ".", base)
    base = re.sub(r"[^a-z0-9.]", "", base)
    # Collapse repeated dots and trim leading/trailing dots that can result
    # from names with punctuation (e.g. "Dr. Suresh Kumar" -> "dr..suresh.kumar").
    base = re.sub(r"\.{2,}", ".", base).strip(".")
    return base or "user"


def generate_username(db: Session, full_name: str) -> str:
    base = _slugify_name(full_name)

    existing = db.query(User.username).filter(User.username == base).first()
    if existing is None:
        return base

    i = 2
    while True:
        candidate = f"{base}{i}"
        if db.query(User.username).filter(User.username == candidate).first() is None:
            return candidate
        i += 1
