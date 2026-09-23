"""Authentication: registration, username generation, hashing, login,
protected routes, verification, password reset."""
from __future__ import annotations

from app.models.user import User, VerificationStatus
from app.services.security import verify_password
from tests.conftest import TEST_PASSWORD, login, make_user

REGISTRATION = {
    "fullName": "Timonne Choudhury",
    "phone": "+91 90000 11111",
    "email": "timonne.choudhury@example.com",
    "accountType": "student",
    "password": "StrongPass123",
    "confirmPassword": "StrongPass123",
    "course": "B.Tech",
}


def test_register_creates_account_and_signs_in(client, db):
    resp = client.post("/api/auth/register", json=REGISTRATION)
    assert resp.status_code == 201, resp.text
    user = resp.json()["user"]

    assert user["fullName"] == "Timonne Choudhury"
    assert user["accountType"] == "student"
    # Student accounts start as pending, awaiting email verification.
    assert user["verificationStatus"] == "pending"
    # The session cookie was set, so the client is now authenticated.
    assert client.get("/api/auth/me").status_code == 200


def test_username_is_generated_from_full_name(client):
    resp = client.post("/api/auth/register", json=REGISTRATION)
    assert resp.json()["user"]["username"] == "timonne.choudhury"


def test_duplicate_names_get_numeric_suffixes(client, db):
    client.post("/api/auth/register", json=REGISTRATION)
    second = client.post(
        "/api/auth/register",
        json={**REGISTRATION, "email": "timonne2@example.com"},
    )
    third = client.post(
        "/api/auth/register",
        json={**REGISTRATION, "email": "timonne3@example.com"},
    )
    assert second.json()["user"]["username"] == "timonne.choudhury2"
    assert third.json()["user"]["username"] == "timonne.choudhury3"


def test_username_uniqueness_is_enforced_by_the_database(db):
    """A duplicate username must be rejected at the DB level, not just by the
    generator's collision loop."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    from app.services.security import hash_password

    make_user(db, full_name="Sneha Gupta", email="sneha1@example.com")
    clash = User(
        full_name="Sneha Gupta",
        username="sneha.gupta",  # deliberately bypassing generate_username
        email="sneha2@example.com",
        phone="+91 90000 00000",
        password_hash=hash_password("x"),
        avatar_color="#1E3A8A",
    )
    db.add(clash)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_password_is_hashed_not_stored_plaintext(client, db):
    client.post("/api/auth/register", json=REGISTRATION)
    row = db.query(User).filter(User.email == REGISTRATION["email"]).first()

    assert row.password_hash != REGISTRATION["password"]
    assert REGISTRATION["password"] not in row.password_hash
    assert row.password_hash.startswith("$2")  # bcrypt
    assert verify_password(REGISTRATION["password"], row.password_hash)


def test_password_hash_never_appears_in_api_response(client):
    resp = client.post("/api/auth/register", json=REGISTRATION)
    body = resp.text.lower()
    assert "password" not in body
    assert "hash" not in body


def test_register_rejects_mismatched_passwords(client):
    resp = client.post(
        "/api/auth/register",
        json={**REGISTRATION, "confirmPassword": "SomethingElse123"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PASSWORD_MISMATCH"


def test_register_rejects_duplicate_email(client):
    client.post("/api/auth/register", json=REGISTRATION)
    resp = client.post("/api/auth/register", json={**REGISTRATION, "fullName": "Someone Else"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_rejects_invalid_account_type(client):
    resp = client.post("/api/auth/register", json={**REGISTRATION, "accountType": "admin"})
    assert resp.status_code == 422


def test_login_with_email(client, user):
    resp = client.post("/api/auth/login", json={"identifier": user.email, "password": TEST_PASSWORD})
    assert resp.status_code == 200
    assert resp.json()["user"]["id"] == user.id


def test_login_with_generated_username(client, user):
    resp = client.post(
        "/api/auth/login", json={"identifier": user.username, "password": TEST_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["id"] == user.id


def test_login_with_wrong_password_is_rejected(client, user):
    resp = client.post("/api/auth/login", json={"identifier": user.email, "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_error_does_not_reveal_whether_the_account_exists(client, user):
    known = client.post("/api/auth/login", json={"identifier": user.email, "password": "wrong"})
    unknown = client.post(
        "/api/auth/login", json={"identifier": "nobody@example.com", "password": "wrong"}
    )
    assert known.json()["error"] == unknown.json()["error"]


def test_protected_route_requires_authentication(client):
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_the_session(client, user):
    login(client, user.email)
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_verification_flow_marks_the_account_verified(client, db, caplog):
    """The code is only ever delivered by email (or the log, in console mode),
    never returned in the API response — so the test reads it from the log."""
    import logging
    import re

    resp = client.post("/api/auth/register", json=REGISTRATION)
    user_id = resp.json()["user"]["id"]

    with caplog.at_level(logging.INFO, logger="newcomer_navigation.email"):
        send = client.post("/api/auth/verification/send", json={"email": REGISTRATION["email"]})
    assert send.status_code == 200
    assert send.json()["success"] is True

    match = re.search(r"verification code is: (\d{6})", caplog.text)
    assert match, "verification code was not logged in console mode"
    code = match.group(1)

    confirm = client.post(
        "/api/auth/verification/confirm", json={"userId": user_id, "code": code}
    )
    assert confirm.status_code == 200
    assert confirm.json()["success"] is True

    row = db.query(User).filter(User.id == user_id).first()
    assert row.verification_status == VerificationStatus.verified


def test_verification_rejects_a_wrong_code(client):
    resp = client.post("/api/auth/register", json=REGISTRATION)
    user_id = resp.json()["user"]["id"]
    client.post("/api/auth/verification/send", json={"email": REGISTRATION["email"]})

    confirm = client.post(
        "/api/auth/verification/confirm", json={"userId": user_id, "code": "000000"}
    )
    assert confirm.json()["success"] is False


def test_verification_code_is_single_use(client, caplog):
    import logging
    import re

    resp = client.post("/api/auth/register", json=REGISTRATION)
    user_id = resp.json()["user"]["id"]
    with caplog.at_level(logging.INFO, logger="newcomer_navigation.email"):
        client.post("/api/auth/verification/send", json={"email": REGISTRATION["email"]})
    code = re.search(r"verification code is: (\d{6})", caplog.text).group(1)

    first = client.post("/api/auth/verification/confirm", json={"userId": user_id, "code": code})
    second = client.post("/api/auth/verification/confirm", json={"userId": user_id, "code": code})
    assert first.json()["success"] is True
    assert second.json()["success"] is False


def test_verification_tokens_are_not_stored_in_plaintext(client, db, caplog):
    import logging
    import re

    from app.models.verification import EmailVerificationToken

    client.post("/api/auth/register", json=REGISTRATION)
    with caplog.at_level(logging.INFO, logger="newcomer_navigation.email"):
        client.post("/api/auth/verification/send", json={"email": REGISTRATION["email"]})
    code = re.search(r"verification code is: (\d{6})", caplog.text).group(1)

    row = db.query(EmailVerificationToken).first()
    assert row.code_hash != code
    assert len(row.code_hash) == 64  # sha256 hex


def test_password_reset_does_not_reveal_account_existence(client, user):
    known = client.post("/api/auth/password-reset/request", json={"email": user.email})
    unknown = client.post(
        "/api/auth/password-reset/request", json={"email": "nobody@example.com"}
    )
    assert known.status_code == unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]


def test_password_reset_changes_the_password(client, db, user, caplog):
    import logging
    import re

    with caplog.at_level(logging.INFO, logger="newcomer_navigation.email"):
        client.post("/api/auth/password-reset/request", json={"email": user.email})
    match = re.search(r"reset-password\?token=([\w\-_]+)", caplog.text)
    assert match, "reset link was not logged in console mode"
    token = match.group(1)

    resp = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "newPassword": "BrandNewPass456"},
    )
    assert resp.status_code == 200

    assert (
        client.post(
            "/api/auth/login", json={"identifier": user.email, "password": "BrandNewPass456"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login", json={"identifier": user.email, "password": TEST_PASSWORD}
        ).status_code
        == 401
    )


def test_password_reset_token_is_single_use(client, user, caplog):
    import logging
    import re

    with caplog.at_level(logging.INFO, logger="newcomer_navigation.email"):
        client.post("/api/auth/password-reset/request", json={"email": user.email})
    token = re.search(r"reset-password\?token=([\w\-_]+)", caplog.text).group(1)

    client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "newPassword": "FirstChange123"}
    )
    second = client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "newPassword": "SecondChange123"}
    )
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_TOKEN"
