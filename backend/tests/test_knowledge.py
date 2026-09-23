"""Knowledge base: ingestion, search, and write authorization."""
from __future__ import annotations

from app.models.user import AccountType, VerificationStatus
from tests.conftest import add_kb_entry, login, make_user

ENTRY = {
    "question": "How do I get my student ID card?",
    "answer": "ID cards are issued by the student services office after enrolment.",
    "keywords": ["id", "card", "student id"],
    "category": "Administration",
}


def test_listing_is_public(client, db):
    add_kb_entry(db, **{k: ENTRY[k] for k in ("question", "answer", "keywords", "category")})
    resp = client.get("/api/knowledge")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["isDemo"] is True


def test_demo_entries_can_be_filtered_out(client, db):
    add_kb_entry(db, question="Demo one", answer="Demo answer here.", keywords=["demo"], is_demo=True)
    add_kb_entry(db, question="Real one", answer="Verified answer here.", keywords=["real"], is_demo=False)

    assert len(client.get("/api/knowledge").json()) == 2
    verified_only = client.get("/api/knowledge?includeDemo=false").json()
    assert len(verified_only) == 1
    assert verified_only[0]["question"] == "Real one"


def test_search_endpoint_returns_relevance_scores(client, db):
    add_kb_entry(db, **{k: ENTRY[k] for k in ("question", "answer", "keywords", "category")})
    hits = client.get("/api/knowledge/search?q=student id card").json()
    assert hits
    assert 0.0 < hits[0]["relevance"] <= 1.0
    assert hits[0]["sourceType"] == "university"


def test_write_requires_authentication(client):
    assert client.post("/api/knowledge", json=ENTRY).status_code == 401


def test_student_cannot_write_to_the_knowledge_base(client, user):
    login(client, user.email)
    resp = client.post("/api/knowledge", json=ENTRY)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "STAFF_ONLY"


def test_unverified_staff_cannot_write(client, db):
    staff = make_user(
        db,
        full_name="Unverified Staff",
        email="unverified.staff@example.com",
        account_type=AccountType.staff,
        verification=VerificationStatus.pending,
    )
    login(client, staff.email)
    assert client.post("/api/knowledge", json=ENTRY).status_code == 403


def test_verified_staff_can_create_update_and_delete(client, db):
    staff = make_user(
        db,
        full_name="Verified Staff",
        email="verified.staff@example.com",
        account_type=AccountType.staff,
        verification=VerificationStatus.verified,
    )
    login(client, staff.email)

    created = client.post("/api/knowledge", json=ENTRY)
    assert created.status_code == 201
    entry = created.json()
    # Content ingested through the API is treated as real, not demo.
    assert entry["isDemo"] is False

    updated = client.patch(f"/api/knowledge/{entry['id']}", json={"category": "Student Services"})
    assert updated.status_code == 200
    assert updated.json()["category"] == "Student Services"

    assert client.delete(f"/api/knowledge/{entry['id']}").status_code == 204
    assert client.get("/api/knowledge").json() == []


def test_newly_ingested_content_is_immediately_retrievable_by_the_chatbot(client, db):
    staff = make_user(
        db,
        full_name="Ingesting Staff",
        email="ingesting.staff@example.com",
        account_type=AccountType.staff,
        verification=VerificationStatus.verified,
    )
    login(client, staff.email)
    client.post("/api/knowledge", json=ENTRY)
    client.post("/api/auth/logout")

    result = client.post("/api/chat/messages", json={"message": "How do I get a student ID card?"})
    assert result.json()["sourceType"] == "university"
