"""Voting: upvote, downvote, switch, remove, duplicate prevention, counts."""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.vote import Vote, VoteTargetType
from tests.conftest import login, make_user

QUESTION = {
    "title": "A question that will be voted on repeatedly",
    "body": "This body is comfortably longer than twenty characters.",
    "categoryId": "hostel",
    "tags": [],
}


@pytest.fixture
def question_by_other(client, user, other_user, categories):
    """A question authored by `other_user`, with `user` signed in as the voter
    (you cannot vote on your own post)."""
    login(client, other_user.email)
    q = client.post("/api/questions", json=QUESTION).json()
    client.post("/api/auth/logout")
    login(client, user.email)
    return q


def vote(client, target_id, value, target_type="question"):
    resp = client.post(
        "/api/votes", json={"targetType": target_type, "targetId": target_id, "value": value}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_upvote(client, question_by_other):
    result = vote(client, question_by_other["id"], 1)
    assert result == {"upvotes": 1, "downvotes": 0, "userVote": 1}


def test_downvote(client, question_by_other):
    result = vote(client, question_by_other["id"], -1)
    assert result == {"upvotes": 0, "downvotes": 1, "userVote": -1}


def test_switch_upvote_to_downvote(client, question_by_other):
    vote(client, question_by_other["id"], 1)
    result = vote(client, question_by_other["id"], -1)
    assert result == {"upvotes": 0, "downvotes": 1, "userVote": -1}


def test_switch_downvote_to_upvote(client, question_by_other):
    vote(client, question_by_other["id"], -1)
    result = vote(client, question_by_other["id"], 1)
    assert result == {"upvotes": 1, "downvotes": 0, "userVote": 1}


def test_repeating_the_same_vote_removes_it(client, question_by_other):
    vote(client, question_by_other["id"], 1)
    result = vote(client, question_by_other["id"], 1)
    assert result == {"upvotes": 0, "downvotes": 0, "userVote": 0}


def test_vote_can_be_re_added_after_removal(client, question_by_other):
    vote(client, question_by_other["id"], 1)
    vote(client, question_by_other["id"], 1)  # removed
    result = vote(client, question_by_other["id"], 1)
    assert result["userVote"] == 1


def test_duplicate_votes_never_accumulate(client, db, question_by_other):
    for _ in range(6):
        client.post(
            "/api/votes",
            json={"targetType": "question", "targetId": question_by_other["id"], "value": 1},
        )
    rows = (
        db.query(Vote)
        .filter(
            Vote.target_type == VoteTargetType.question,
            Vote.target_id == question_by_other["id"],
        )
        .all()
    )
    # 6 clicks = toggle on/off three times, leaving at most one row.
    assert len(rows) <= 1


def test_duplicate_vote_is_blocked_by_the_database(db, user, other_user, categories):
    """The uniqueness guarantee must hold even when the service layer is
    bypassed entirely."""
    db.add(
        Vote(user_id=user.id, target_type=VoteTargetType.answer, target_id="target-1", value=1)
    )
    db.commit()
    db.add(
        Vote(user_id=user.id, target_type=VoteTargetType.answer, target_id="target-1", value=-1)
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_invalid_vote_value_is_rejected(client, question_by_other):
    resp = client.post(
        "/api/votes",
        json={"targetType": "question", "targetId": question_by_other["id"], "value": 5},
    )
    assert resp.status_code == 422


def test_voting_requires_authentication(client, other_user, categories):
    login(client, other_user.email)
    q = client.post("/api/questions", json=QUESTION).json()
    client.post("/api/auth/logout")

    resp = client.post(
        "/api/votes", json={"targetType": "question", "targetId": q["id"], "value": 1}
    )
    assert resp.status_code == 401


def test_cannot_vote_on_own_post(client, auth_client, categories):
    q = auth_client.post("/api/questions", json=QUESTION).json()
    resp = auth_client.post(
        "/api/votes", json={"targetType": "question", "targetId": q["id"], "value": 1}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "SELF_VOTE_FORBIDDEN"


def test_voting_on_missing_target_404s(client, auth_client):
    resp = auth_client.post(
        "/api/votes", json={"targetType": "answer", "targetId": "nope", "value": 1}
    )
    assert resp.status_code == 404


def test_counts_are_aggregated_across_users(client, db, user, other_user, categories):
    third = make_user(db, full_name="Third Voter", email="third.voter@example.com")

    login(client, user.email)
    q = client.post("/api/questions", json=QUESTION).json()
    client.post("/api/auth/logout")

    login(client, other_user.email)
    vote(client, q["id"], 1)
    client.post("/api/auth/logout")

    login(client, third.email)
    result = vote(client, q["id"], -1)

    assert result["upvotes"] == 1
    assert result["downvotes"] == 1
    # And the question endpoint reports the same server-side figures.
    detail = client.get(f"/api/questions/{q['id']}").json()
    assert detail["upvotes"] == 1 and detail["downvotes"] == 1


def test_my_votes_endpoint(client, question_by_other):
    vote(client, question_by_other["id"], 1)
    mine = client.get(
        f"/api/votes/mine?targetType=question&targetIds={question_by_other['id']}"
    ).json()
    assert mine == {question_by_other["id"]: 1}


def test_my_votes_is_empty_for_anonymous_visitors(client, question_by_other):
    client.post("/api/auth/logout")
    resp = client.get(f"/api/votes/mine?targetType=question&targetIds={question_by_other['id']}")
    assert resp.status_code == 200
    assert resp.json() == {}


def test_user_vote_is_reflected_in_question_response(client, question_by_other):
    vote(client, question_by_other["id"], -1)
    detail = client.get(f"/api/questions/{question_by_other['id']}").json()
    assert detail["userVote"] == -1
