"""Forum: question CRUD, answers, search, filtering, sorting, pagination."""
from __future__ import annotations

from tests.conftest import login, make_user

VALID_QUESTION = {
    "title": "How does hostel room allotment work?",
    "body": "I am joining this year and want to understand the process properly.",
    "categoryId": "hostel",
    "tags": ["hostel"],
}


def create_question(client, **overrides):
    payload = {**VALID_QUESTION, **overrides}
    resp = client.post("/api/questions", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_question_requires_authentication(client, categories):
    assert client.post("/api/questions", json=VALID_QUESTION).status_code == 401


def test_create_question(auth_client, categories):
    body = create_question(auth_client)
    assert body["title"] == VALID_QUESTION["title"]
    assert body["categoryId"] == "hostel"
    assert body["tags"] == ["hostel"]
    # Server-computed fields start at zero regardless of what a client sends.
    assert body["upvotes"] == 0
    assert body["answerCount"] == 0
    assert body["isAnswered"] is False


def test_client_cannot_set_vote_counts_on_creation(auth_client, categories):
    body = create_question(auth_client, upvotes=9999, answerCount=50, isAnswered=True)
    assert body["upvotes"] == 0
    assert body["answerCount"] == 0
    assert body["isAnswered"] is False


def test_question_validation_rejects_short_content(auth_client, categories):
    assert auth_client.post("/api/questions", json={**VALID_QUESTION, "title": "short"}).status_code == 422
    assert auth_client.post("/api/questions", json={**VALID_QUESTION, "body": "tiny"}).status_code == 422


def test_unknown_tags_are_dropped_not_created(auth_client, categories, db):
    from app.models.category import Tag

    body = create_question(auth_client, tags=["hostel", "made-up-tag"])
    assert body["tags"] == ["hostel"]
    assert db.query(Tag).filter(Tag.id == "made-up-tag").first() is None


def test_list_and_get_question(client, auth_client, categories):
    created = create_question(auth_client)

    listing = client.get("/api/questions").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == created["id"]
    # The author is embedded so the frontend can render cards in one request.
    assert listing["items"][0]["author"]["username"]

    detail = client.get(f"/api/questions/{created['id']}").json()
    assert detail["id"] == created["id"]


def test_get_question_increments_views(client, auth_client, categories):
    created = create_question(auth_client)
    first = client.get(f"/api/questions/{created['id']}").json()["views"]
    second = client.get(f"/api/questions/{created['id']}").json()["views"]
    assert second == first + 1


def test_missing_question_returns_clean_404(client):
    resp = client.get("/api/questions/nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "QUESTION_NOT_FOUND"


def test_author_can_edit_own_question(auth_client, categories):
    created = create_question(auth_client)
    resp = auth_client.patch(
        f"/api/questions/{created['id']}",
        json={"title": "An edited title that is long enough"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "An edited title that is long enough"


def test_non_author_cannot_edit_question(client, db, user, other_user, categories):
    login(client, user.email)
    created = create_question(client)
    client.post("/api/auth/logout")

    login(client, other_user.email)
    resp = client.patch(
        f"/api/questions/{created['id']}", json={"title": "Hijacked title, long enough"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_author_can_delete_own_question(client, auth_client, categories):
    created = create_question(auth_client)
    assert auth_client.delete(f"/api/questions/{created['id']}").status_code == 204
    assert client.get(f"/api/questions/{created['id']}").status_code == 404
    assert client.get("/api/questions").json()["total"] == 0


def test_non_author_cannot_delete_question(client, user, other_user, categories):
    login(client, user.email)
    created = create_question(client)
    client.post("/api/auth/logout")
    login(client, other_user.email)
    assert client.delete(f"/api/questions/{created['id']}").status_code == 403


def test_closing_a_question_blocks_new_answers(client, user, other_user, categories):
    login(client, user.email)
    created = create_question(client)
    client.patch(f"/api/questions/{created['id']}", json={"status": "closed"})
    client.post("/api/auth/logout")

    login(client, other_user.email)
    resp = client.post(
        f"/api/questions/{created['id']}/answers",
        json={"body": "Trying to answer a closed question."},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "QUESTION_CLOSED"


# ── Answers ─────────────────────────────────────────────────────────────


def test_create_answer_and_question_becomes_answered(client, user, other_user, categories):
    login(client, user.email)
    q = create_question(client)
    client.post("/api/auth/logout")

    login(client, other_user.email)
    resp = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "Here is a genuinely useful answer."}
    )
    assert resp.status_code == 201
    assert resp.json()["questionId"] == q["id"]

    detail = client.get(f"/api/questions/{q['id']}").json()
    assert detail["answerCount"] == 1
    assert detail["isAnswered"] is True


def test_create_answer_requires_authentication(client, auth_client, categories):
    q = create_question(auth_client)
    auth_client.post("/api/auth/logout")
    resp = client.post(f"/api/questions/{q['id']}/answers", json={"body": "Anonymous answer here."})
    assert resp.status_code == 401


def test_author_can_edit_and_delete_own_answer(client, user, other_user, categories):
    login(client, user.email)
    q = create_question(client)
    client.post("/api/auth/logout")

    login(client, other_user.email)
    a = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "An answer that will be edited."}
    ).json()

    edited = client.patch(f"/api/answers/{a['id']}", json={"body": "The edited answer body."})
    assert edited.status_code == 200
    assert edited.json()["body"] == "The edited answer body."

    assert client.delete(f"/api/answers/{a['id']}").status_code == 204
    assert client.get(f"/api/questions/{q['id']}").json()["answerCount"] == 0


def test_non_author_cannot_edit_answer(client, db, user, other_user, categories):
    third = make_user(db, full_name="Third Person", email="third@example.com")

    login(client, user.email)
    q = create_question(client)
    client.post("/api/auth/logout")

    login(client, other_user.email)
    a = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "The original answer body."}
    ).json()
    client.post("/api/auth/logout")

    login(client, third.email)
    resp = client.patch(f"/api/answers/{a['id']}", json={"body": "Someone else's edit attempt."})
    assert resp.status_code == 403


def test_answers_are_ordered_by_net_votes_by_default(client, db, user, other_user, categories):
    voter = make_user(db, full_name="Voter Person", email="voter@example.com")

    login(client, user.email)
    q = create_question(client)
    low = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "The less popular answer here."}
    ).json()
    high = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "The more popular answer here."}
    ).json()
    client.post("/api/auth/logout")

    login(client, voter.email)
    client.post("/api/votes", json={"targetType": "answer", "targetId": high["id"], "value": 1})
    client.post("/api/auth/logout")
    login(client, other_user.email)
    client.post("/api/votes", json={"targetType": "answer", "targetId": low["id"], "value": -1})

    ordered = client.get(f"/api/questions/{q['id']}/answers").json()
    assert [a["id"] for a in ordered] == [high["id"], low["id"]]

    newest = client.get(f"/api/questions/{q['id']}/answers?sort=newest").json()
    assert newest[0]["id"] == high["id"]  # created second


# ── Search / filter / sort / pagination ─────────────────────────────────


def test_search_matches_title(client, auth_client, categories):
    create_question(auth_client, title="How does hostel room allotment work?")
    create_question(
        auth_client,
        title="Where can I find good vegetarian food nearby?",
        categoryId="food",
        tags=["mess"],
    )

    results = client.get("/api/questions?search=hostel").json()
    assert results["total"] == 1
    assert "hostel" in results["items"][0]["title"].lower()


def test_search_matches_body(client, auth_client, categories):
    create_question(auth_client, body="The cafeteria menu rotation is what I want to know about.")
    assert client.get("/api/questions?search=cafeteria").json()["total"] == 1


def test_search_matches_tags(client, auth_client, categories):
    create_question(
        auth_client,
        title="My laptop keeps disconnecting from the network",
        body="It asks me to log in again every single hour, which is annoying.",
        categoryId="hostel",
        tags=["wifi"],
    )
    # "wi-fi" appears nowhere in the title or body — only as a tag name.
    assert client.get("/api/questions?search=wi-fi").json()["total"] == 1


def test_filter_by_category(client, auth_client, categories):
    create_question(auth_client, categoryId="hostel")
    create_question(auth_client, categoryId="food", title="A question about the food on campus")

    assert client.get("/api/questions?categoryId=hostel").json()["total"] == 1
    assert client.get("/api/questions?categoryId=food").json()["total"] == 1


def test_filter_by_tag(client, auth_client, categories):
    create_question(auth_client, tags=["hostel"])
    create_question(auth_client, title="A second question about the mess", tags=["mess"])
    assert client.get("/api/questions?tags=mess").json()["total"] == 1


def test_filter_by_answered_state(client, user, other_user, categories):
    login(client, user.email)
    answered = create_question(client)
    create_question(client, title="An unanswered question about campus life")
    client.post("/api/auth/logout")

    login(client, other_user.email)
    client.post(f"/api/questions/{answered['id']}/answers", json={"body": "An answer to this one."})

    assert client.get("/api/questions?answered=answered").json()["total"] == 1
    assert client.get("/api/questions?answered=unanswered").json()["total"] == 1
    assert client.get("/api/questions?answered=all").json()["total"] == 2


def test_filter_by_course(client, auth_client, categories):
    # The author's course is denormalised onto the question at creation time.
    create_question(auth_client)
    assert client.get("/api/questions?course=B.Tech").json()["total"] == 1
    assert client.get("/api/questions?course=MBA").json()["total"] == 0


def test_sort_by_latest_is_newest_first(client, auth_client, categories):
    first = create_question(auth_client, title="The first question that was asked")
    second = create_question(auth_client, title="The second question that was asked")
    items = client.get("/api/questions?sortBy=latest").json()["items"]
    assert items[0]["id"] == second["id"]
    assert items[1]["id"] == first["id"]


def test_sort_by_most_upvoted(client, db, user, other_user, categories):
    login(client, user.email)
    unpopular = create_question(client, title="A question nobody upvoted at all")
    popular = create_question(client, title="A question that people did upvote")
    client.post("/api/auth/logout")

    login(client, other_user.email)
    client.post("/api/votes", json={"targetType": "question", "targetId": popular["id"], "value": 1})

    items = client.get("/api/questions?sortBy=most-upvoted").json()["items"]
    assert items[0]["id"] == popular["id"]


def test_sort_by_most_answered(client, user, other_user, categories):
    login(client, user.email)
    quiet = create_question(client, title="A question with no answers at all here")
    busy = create_question(client, title="A question with several answers on it")
    client.post("/api/auth/logout")

    login(client, other_user.email)
    client.post(f"/api/questions/{busy['id']}/answers", json={"body": "The first answer given."})
    client.post(f"/api/questions/{busy['id']}/answers", json={"body": "The second answer given."})

    items = client.get("/api/questions?sortBy=most-answered").json()["items"]
    assert items[0]["id"] == busy["id"]


def test_pagination(client, auth_client, categories):
    for i in range(7):
        create_question(auth_client, title=f"Paginated demo question number {i} here")

    page1 = client.get("/api/questions?page=1&pageSize=3").json()
    page2 = client.get("/api/questions?page=2&pageSize=3").json()
    page3 = client.get("/api/questions?page=3&pageSize=3").json()

    assert page1["total"] == page2["total"] == 7
    assert len(page1["items"]) == 3
    assert len(page2["items"]) == 3
    assert len(page3["items"]) == 1
    # Pages must not overlap.
    ids = [q["id"] for q in page1["items"] + page2["items"] + page3["items"]]
    assert len(set(ids)) == 7


def test_categories_and_tags_endpoints(client, categories):
    cats = client.get("/api/categories").json()
    assert {c["id"] for c in cats} >= {"hostel", "btech", "food"}

    tags = client.get("/api/categories/tags").json()
    assert {t["id"] for t in tags} >= {"hostel", "wifi", "mess"}

    courses = client.get("/api/courses").json()
    assert {c["id"] for c in courses} == {"btech"}
