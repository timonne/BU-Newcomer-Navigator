"""
Shared pytest fixtures.

Each test gets a fresh in-memory SQLite database (via a StaticPool so the
same connection is reused across the app's sessions), so tests never touch
the development database and never depend on each other's data.

Rate limiting is disabled for the test app — the auth tests would otherwise
trip the 20/minute login limit.
"""
from __future__ import annotations

import os

# Must be set before app.config is first imported, since Settings is cached.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-used-anywhere-real")
os.environ.setdefault("AI_PROVIDER", "")
os.environ.setdefault("AI_API_KEY", "")
os.environ.setdefault("STUDENT_EMAIL_DOMAINS", "")
os.environ.setdefault("STAFF_EMAIL_DOMAINS", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.models.category import Category, CategoryType, Tag
from app.models.knowledge import KnowledgeBaseEntry
from app.models.user import AccountStatus, AccountType, User, VerificationStatus
from app.services.security import hash_password

TEST_PASSWORD = "TestPassword123"


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine, db):
    app = create_app()
    # slowapi is left in place but its limits are neutralised, so the
    # middleware path is still exercised without throttling the tests.
    app.state.limiter.enabled = False

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def categories(db):
    db.add(Category(id="hostel", name="Hostel", type=CategoryType.non_academic))
    db.add(Category(id="btech", name="B.Tech", type=CategoryType.academic, subcategories=["CSE"]))
    db.add(Category(id="food", name="Food & Cafeteria", type=CategoryType.non_academic))
    db.add(Tag(id="hostel", name="Hostel", color="#7C3AED"))
    db.add(Tag(id="wifi", name="Wi-Fi", color="#EA580C"))
    db.add(Tag(id="mess", name="Mess", color="#B45309"))
    db.commit()


def make_user(
    db,
    full_name="Test User",
    email="test.user@example.com",
    username=None,
    account_type=AccountType.student,
    verification=VerificationStatus.verified,
    password=TEST_PASSWORD,
):
    from app.services.username_service import generate_username

    user = User(
        full_name=full_name,
        username=username or generate_username(db, full_name),
        email=email.lower(),
        phone="+91 90000 00000",
        account_type=account_type,
        verification_status=verification,
        account_status=AccountStatus.active,
        password_hash=hash_password(password),
        course="B.Tech",
        department="CSE",
        bio="",
        avatar_color="#1E3A8A",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user(db):
    return make_user(db, full_name="Timonne Choudhury", email="timonne@example.com")


@pytest.fixture
def other_user(db):
    return make_user(db, full_name="Arjun Mehta", email="arjun@example.com")


def login(client, identifier, password=TEST_PASSWORD):
    """Signs in and leaves the auth cookie on the client's cookie jar."""
    resp = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["user"]


@pytest.fixture
def auth_client(client, user):
    login(client, user.email)
    return client


def add_kb_entry(db, question, answer, keywords, category="General", is_demo=True):
    entry = KnowledgeBaseEntry(
        question=question,
        answer=answer,
        keywords=keywords,
        category=category,
        source_type="university",
        is_demo=is_demo,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
