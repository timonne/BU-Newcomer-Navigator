"""
SQLAlchemy engine, session factory, and declarative base.

Defaults to a local SQLite file so the project runs with zero database
setup. Swap DATABASE_URL to a PostgreSQL URL when you're ready to move
past local development — no code changes required elsewhere.
"""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    # Needed for SQLite when used with FastAPI's threaded request handling.
    connect_args["check_same_thread"] = False

    # Make sure the directory for a file-based SQLite DB exists.
    if ":///" in settings.database_url and settings.database_url != "sqlite:///:memory:":
        db_path = settings.database_url.split("sqlite:///")[-1]
        if db_path and db_path != ":memory:":
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
