"""Profiles: public view, own view, editing, ownership, statistics."""
from __future__ import annotations

from tests.conftest import login


def test_public_profile_is_readable_without_auth(client, user):
    resp = client.get(f"/api/users/{user.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["fullName"] == user.full_name
    assert body["username"] == user.username
    assert body["accountType"] == "student"
    assert body["verificationStatus"] == "verified"
    assert body["course"] == "B.Tech"
    assert "joinedAt" in body


def test_public_profile_hides_contact_details(client, user):
    body = client.get(f"/api/users/{user.id}").json()
    assert body["email"] == ""
    assert body["phone"] == ""


def test_own_profile_includes_contact_details(client, user):
    login(client, user.email)
    body = client.get("/api/auth/me").json()["user"]
    assert body["email"] == user.email
    assert body["phone"] == user.phone


def test_profile_includes_activity_statistics(client, auth_client, user, categories):
    body = client.get(f"/api/users/{user.id}").json()
    assert body["questionsCount"] == 0
    assert body["answersCount"] == 0
    assert body["upvotesReceived"] == 0

    auth_client.post(
        "/api/questions",
        json={
            "title": "A question long enough to pass validation",
            "body": "This body is definitely longer than twenty characters.",
            "categoryId": "hostel",
            "tags": [],
        },
    )
    body = client.get(f"/api/users/{user.id}").json()
    assert body["questionsCount"] == 1


def test_upvotes_received_counts_votes_on_own_content(
    client, db, user, other_user, categories
):
    login(client, user.email)
    q = client.post(
        "/api/questions",
        json={
            "title": "A question that will receive an upvote",
            "body": "This body is definitely longer than twenty characters.",
            "categoryId": "hostel",
            "tags": [],
        },
    ).json()
    client.post("/api/auth/logout")

    login(client, other_user.email)
    client.post("/api/votes", json={"targetType": "question", "targetId": q["id"], "value": 1})

    assert client.get(f"/api/users/{user.id}").json()["upvotesReceived"] == 1


def test_owner_can_edit_their_own_profile(auth_client):
    resp = auth_client.patch(
        "/api/users/me",
        json={"bio": "Updated bio text.", "course": "M.Tech", "department": "CSE"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bio"] == "Updated bio text."
    assert body["course"] == "M.Tech"


def test_profile_editing_requires_authentication(client):
    assert client.patch("/api/users/me", json={"bio": "hacked"}).status_code == 401


def test_verification_status_cannot_be_self_edited(auth_client, db, user):
    """Even if the client sends verificationStatus, it must be ignored — the
    field is not part of UserUpdate, so it cannot reach the ORM."""
    from app.models.user import VerificationStatus

    auth_client.patch(
        "/api/users/me",
        json={"bio": "ok", "verificationStatus": "verified", "accountType": "staff"},
    )
    db.refresh(user)
    assert user.verification_status == VerificationStatus.verified
    assert user.account_type.value == "student"


def test_username_and_email_cannot_be_self_edited(auth_client, db, user):
    original_username, original_email = user.username, user.email
    auth_client.patch(
        "/api/users/me",
        json={"bio": "ok", "username": "someone.else", "email": "new@example.com"},
    )
    db.refresh(user)
    assert user.username == original_username
    assert user.email == original_email


def test_there_is_no_route_to_edit_another_users_profile(client, user, other_user):
    """Ownership is structural: PATCH /api/users/{id} does not exist."""
    login(client, user.email)
    resp = client.patch(f"/api/users/{other_user.id}", json={"bio": "hacked"})
    assert resp.status_code in (404, 405)


def test_unknown_profile_returns_a_clean_404(client):
    resp = client.get("/api/users/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "USER_NOT_FOUND"


def test_batch_user_lookup(client, user, other_user):
    resp = client.get(f"/api/users?ids={user.id},{other_user.id}")
    assert resp.status_code == 200
    assert {u["id"] for u in resp.json()} == {user.id, other_user.id}
