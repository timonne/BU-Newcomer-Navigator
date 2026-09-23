"""
Chatbot: the mandatory source priority order, relevance filtering,
personalisation, and source attribution.

The critical tests here are:
  - university data wins when it is relevant
  - forum is used only when the KB has nothing relevant
  - a highly-upvoted but IRRELEVANT forum answer is never selected
  - neither available -> general fallback, clearly labelled
"""
from __future__ import annotations

from app.services import chatbot_service, retrieval_service
from tests.conftest import add_kb_entry, login, make_user

HOSTEL_QUERY = "How does hostel room allotment work?"

KB_HOSTEL = dict(
    question="What is the general process for hostel accommodation?",
    answer="Hostel accommodation is applied for separately and allotted centrally.",
    keywords=["hostel", "accommodation", "room", "allotment"],
    category="Hostel",
)


def ask(client, message, conversation_id=None):
    payload = {"message": message}
    if conversation_id:
        payload["conversationId"] = conversation_id
    resp = client.post("/api/chat/messages", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def seed_forum_thread(client, author_email, title, body, answer_body, voters=()):
    """Creates a question + answer, optionally upvoted by each voter."""
    login(client, author_email)
    q = client.post(
        "/api/questions",
        json={"title": title, "body": body, "categoryId": "hostel", "tags": []},
    ).json()
    a = client.post(f"/api/questions/{q['id']}/answers", json={"body": answer_body}).json()
    client.post("/api/auth/logout")

    for email in voters:
        login(client, email)
        client.post("/api/votes", json={"targetType": "answer", "targetId": a["id"], "value": 1})
        client.post("/api/auth/logout")
    return q, a


# ── Priority 1: university knowledge base ───────────────────────────────


def test_university_source_wins_when_available(client, db):
    add_kb_entry(db, **KB_HOSTEL)
    result = ask(client, HOSTEL_QUERY)
    assert result["sourceType"] == "university"
    assert result["sourceRef"]["documentTitle"] == KB_HOSTEL["question"]


def test_university_wins_even_when_a_relevant_forum_answer_exists(
    client, db, user, other_user, categories
):
    """The KB must be searched first and must take precedence — the forum is a
    fallback, not a competitor."""
    add_kb_entry(db, **KB_HOSTEL)
    seed_forum_thread(
        client,
        user.email,
        "How does hostel room allotment work for first years?",
        "I want to understand the hostel room allotment process before I arrive.",
        "The hostel allotment is done by the office, this is the community view.",
        voters=[other_user.email],
    )
    result = ask(client, HOSTEL_QUERY)
    assert result["sourceType"] == "university"


def test_demo_knowledge_base_answers_are_labelled_as_demo(client, db):
    add_kb_entry(db, **{**KB_HOSTEL, "answer": "DEMO DATA — NOT OFFICIAL UNIVERSITY INFORMATION\n\nDetails."}, is_demo=True)
    result = ask(client, HOSTEL_QUERY)
    assert "demo" in result["content"].lower()


def test_verified_knowledge_base_answers_get_no_demo_notice(client, db):
    add_kb_entry(db, **KB_HOSTEL, is_demo=False)
    result = ask(client, HOSTEL_QUERY)
    assert "demo knowledge-base entry" not in result["content"]


# ── Priority 2: forum ───────────────────────────────────────────────────


def test_forum_source_is_used_when_no_university_data_exists(
    client, db, user, other_user, categories
):
    q, a = seed_forum_thread(
        client,
        user.email,
        "How does hostel room allotment work for first years?",
        "I want to understand the hostel room allotment process before I arrive.",
        "Allotment is handled centrally and you are notified by email.",
        voters=[other_user.email],
    )
    result = ask(client, HOSTEL_QUERY)

    assert result["sourceType"] == "community"
    assert result["sourceRef"]["questionId"] == q["id"]
    assert result["sourceRef"]["answerId"] == a["id"]
    assert result["sourceRef"]["questionTitle"] == q["title"]
    # Enough information for the frontend to link back to the thread.
    assert result["sourceRef"]["authorName"]


def test_highest_rated_relevant_answer_is_chosen(client, db, user, other_user, categories):
    voter = make_user(db, full_name="Extra Voter", email="extra.voter@example.com")

    login(client, user.email)
    q = client.post(
        "/api/questions",
        json={
            "title": "How does hostel room allotment work for first years?",
            "body": "I want to understand the hostel room allotment process before I arrive.",
            "categoryId": "hostel",
            "tags": [],
        },
    ).json()
    weak = client.post(
        f"/api/questions/{q['id']}/answers", json={"body": "Not sure honestly, ask someone else."}
    ).json()
    strong = client.post(
        f"/api/questions/{q['id']}/answers",
        json={"body": "Allotment is central and communicated by email before term starts."},
    ).json()
    client.post("/api/auth/logout")

    for email in (other_user.email, voter.email):
        login(client, email)
        client.post(
            "/api/votes", json={"targetType": "answer", "targetId": strong["id"], "value": 1}
        )
        client.post("/api/auth/logout")

    result = ask(client, HOSTEL_QUERY)
    assert result["sourceRef"]["answerId"] == strong["id"]
    assert result["sourceRef"]["answerId"] != weak["id"]


def test_irrelevant_but_highly_upvoted_answer_is_not_selected(
    client, db, user, other_user, categories
):
    """The headline relevance requirement (brief section 12).

    A wildly popular answer about cafeteria food must not be returned for a
    question about hostel allotment — relevance filtering happens BEFORE
    vote-based ranking.
    """
    voters = [
        make_user(db, full_name=f"Voter Number{i}", email=f"voter{i}@example.com")
        for i in range(4)
    ]

    login(client, user.email)
    q = client.post(
        "/api/questions",
        json={
            "title": "Which cafeteria has the best coffee on campus?",
            "body": "Looking for opinions on where the coffee is actually drinkable.",
            "categoryId": "food",
            "tags": [],
        },
    ).json()
    popular = client.post(
        f"/api/questions/{q['id']}/answers",
        json={"body": "The one near the library is by far the best for coffee."},
    ).json()
    client.post("/api/auth/logout")

    for v in voters + [other_user]:
        login(client, v.email)
        client.post(
            "/api/votes", json={"targetType": "answer", "targetId": popular["id"], "value": 1}
        )
        client.post("/api/auth/logout")

    # Sanity check: that answer really is the highest-rated thing in the forum.
    detail = client.get(f"/api/questions/{q['id']}/answers").json()
    assert detail[0]["upvotes"] == 5

    result = ask(client, HOSTEL_QUERY)
    assert result["sourceType"] == "general"
    assert result["sourceRef"] is None


def test_unanswered_relevant_question_does_not_produce_a_forum_answer(
    client, db, auth_client, categories
):
    """A relevant thread with no answers is not an answer."""
    auth_client.post(
        "/api/questions",
        json={
            "title": "How does hostel room allotment work for first years?",
            "body": "I want to understand the hostel room allotment process before I arrive.",
            "categoryId": "hostel",
            "tags": [],
        },
    )
    result = ask(client, HOSTEL_QUERY)
    assert result["sourceType"] == "general"


# ── Priority 3: general fallback ────────────────────────────────────────


def test_general_fallback_when_nothing_is_available(client):
    result = ask(client, "What is the airspeed velocity of an unladen swallow?")
    assert result["sourceType"] == "general"
    assert result["sourceRef"] is None


def test_general_fallback_is_labelled_and_points_to_the_university(client):
    content = ask(client, "What is the airspeed velocity of an unladen swallow?")["content"]
    assert "general guidance" in content.lower()
    assert "not official" in content.lower()
    assert "bennett university" in content.lower()


def test_fallback_invents_no_contact_details(client):
    """No fabricated email address, phone number or office location
    (brief section 18)."""
    import re

    content = ask(client, "Who exactly do I email about my fee waiver deadline?")["content"]
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", content)
    assert not re.search(r"\+?\d[\d\s\-]{8,}\d", content)


# ── Personalisation ─────────────────────────────────────────────────────


def test_authenticated_user_is_greeted_by_first_name(client, db, user):
    add_kb_entry(db, **KB_HOSTEL)
    login(client, user.email)
    content = ask(client, HOSTEL_QUERY)["content"]
    assert content.startswith("Hi Timonne!")


def test_anonymous_user_gets_a_neutral_greeting(client, db):
    add_kb_entry(db, **KB_HOSTEL)
    content = ask(client, HOSTEL_QUERY)["content"]
    assert content.startswith("Hi!")


def test_first_name_cannot_be_supplied_by_the_client(client, db):
    """Identity comes from the auth cookie, never from the request body."""
    add_kb_entry(db, **KB_HOSTEL)
    resp = client.post(
        "/api/chat/messages",
        json={"message": HOSTEL_QUERY, "firstName": "Administrator", "userId": "someone-else"},
    )
    assert resp.status_code == 200
    assert "Administrator" not in resp.json()["content"]


# ── Chat history ────────────────────────────────────────────────────────


def test_conversation_is_persisted_for_authenticated_users(client, db, user):
    add_kb_entry(db, **KB_HOSTEL)
    login(client, user.email)

    first = ask(client, HOSTEL_QUERY)
    assert first["conversationId"]

    second = ask(client, "And what about the mess timings?", first["conversationId"])
    assert second["conversationId"] == first["conversationId"]

    convo = client.get(f"/api/chat/conversations/{first['conversationId']}").json()
    assert len(convo["messages"]) == 4  # 2 user + 2 assistant
    assert convo["messages"][0]["role"] == "user"
    assert convo["messages"][1]["role"] == "assistant"
    assert convo["messages"][1]["sourceType"] == "university"


def test_anonymous_chat_is_not_persisted(client, db):
    add_kb_entry(db, **KB_HOSTEL)
    result = ask(client, HOSTEL_QUERY)
    assert result.get("conversationId") is None


def test_conversations_require_authentication(client):
    assert client.get("/api/chat/conversations").status_code == 401


def test_one_user_cannot_read_another_users_conversation(client, db, user, other_user):
    add_kb_entry(db, **KB_HOSTEL)
    login(client, user.email)
    convo_id = ask(client, HOSTEL_QUERY)["conversationId"]
    client.post("/api/auth/logout")

    login(client, other_user.email)
    resp = client.get(f"/api/chat/conversations/{convo_id}")
    # 404, not 403 — existence itself is not disclosed.
    assert resp.status_code == 404
    assert client.get("/api/chat/conversations").json() == []


def test_user_can_delete_own_conversation(client, db, user):
    add_kb_entry(db, **KB_HOSTEL)
    login(client, user.email)
    convo_id = ask(client, HOSTEL_QUERY)["conversationId"]

    assert client.delete(f"/api/chat/conversations/{convo_id}").status_code == 204
    assert client.get(f"/api/chat/conversations/{convo_id}").status_code == 404


def test_one_user_cannot_delete_another_users_conversation(client, db, user, other_user):
    add_kb_entry(db, **KB_HOSTEL)
    login(client, user.email)
    convo_id = ask(client, HOSTEL_QUERY)["conversationId"]
    client.post("/api/auth/logout")

    login(client, other_user.email)
    assert client.delete(f"/api/chat/conversations/{convo_id}").status_code == 404


# ── Retrieval internals ─────────────────────────────────────────────────


def test_relevance_threshold_discards_weak_matches(db):
    add_kb_entry(db, **KB_HOSTEL)
    strong = retrieval_service.search_knowledge_base(db, "hostel room allotment")
    weak = retrieval_service.search_knowledge_base(db, "parking permit for motorcycles")

    assert strong and strong[0].relevance >= retrieval_service.KB_RELEVANCE_THRESHOLD
    assert weak == []


def test_empty_query_retrieves_nothing(db):
    add_kb_entry(db, **KB_HOSTEL)
    assert retrieval_service.search_knowledge_base(db, "   ") == []
    assert retrieval_service.search_forum(db, "   ") == []


def test_chatbot_runs_without_an_ai_provider_configured(db):
    """No AI_API_KEY is set in the test environment, so this exercises the
    retrieval-only path end to end."""
    from app.config import get_settings

    assert get_settings().is_ai_enabled is False

    add_kb_entry(db, **KB_HOSTEL)
    response, candidates = chatbot_service.answer_question(db, HOSTEL_QUERY)
    assert response.source_type == "university"
    assert candidates


def test_ai_service_returns_none_without_credentials():
    from app.services import ai_service

    assert ai_service.get_provider().is_available is False
    assert ai_service.rephrase_with_context("q", "context") is None


def test_health_endpoint_does_not_leak_ai_configuration(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["aiProviderConfigured"] is False
    assert "aiApiKey" not in body and "ai_api_key" not in str(body)
