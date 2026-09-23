"""
Navi — the chatbot orchestrator.

MANDATORY PRIORITY ORDER (brief sections 18 and 22):

    user question
         |
    [1] university knowledge base  -- searched FIRST, always
         |  relevant hit? -> answer, source_type="university"
         |
    [2] forum                      -- only if the KB had nothing relevant
         |  relevant hit? -> highest-rated RELEVANT answer,
         |                   source_type="community"
         |
    [3] general guidance           -- only if neither had anything
            -> source_type="general", explicitly labelled as NOT official
               Bennett University information, with a pointer to contact
               the university directly.

The AI provider is never a source. It is only ever used to rephrase text that
stage 1 or stage 2 already retrieved, or to give general (clearly-labelled)
guidance at stage 3. A question is never sent straight to a model in place of
searching the knowledge base.

Personalisation uses `user.first_name` from the authenticated User row. A
first name supplied in the request body is ignored entirely — the browser is
not a source of identity.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.chat import Conversation, Message, MessageRole
from app.models.user import User
from app.schemas.chat import ChatResponse, ChatSourceRef
from app.services import ai_service, retrieval_service

logger = logging.getLogger("newcomer_navigation.chatbot")

ASSISTANT_NAME = "Navi"

# Appended to every stage-3 answer. Deliberately contains no invented email
# address, phone number, office location or deadline (brief section 18).
GENERAL_DISCLAIMER = (
    "Please note this is general guidance, not official Bennett University "
    "information. For anything authoritative — admissions, fees, hostel "
    "allotment, academic policy or deadlines — please contact Bennett "
    "University, Greater Noida directly, or ask at the relevant campus office."
)

DEMO_KB_NOTICE = (
    "(This answer came from a demo knowledge-base entry, not from verified "
    "official university documentation.)"
)


def _greeting(first_name: Optional[str]) -> str:
    return f"Hi {first_name}! " if first_name else "Hi! "


def _general_answer(question: str, first_name: Optional[str]) -> str:
    """Stage 3. Tries the AI provider for genuinely general help, but the
    deterministic template is always a complete answer on its own."""
    ai_text = ai_service.rephrase_with_context(question, context="", first_name=first_name)
    if ai_text:
        return f"{ai_text}\n\n{GENERAL_DISCLAIMER}"

    return (
        f"{_greeting(first_name)}I couldn't find anything about that in the "
        "university knowledge base or in the community forum yet.\n\n"
        "Two things that usually help: post your question on the forum — "
        "seniors and staff often answer within a day — and check with the "
        "relevant campus office for anything official.\n\n"
        f"{GENERAL_DISCLAIMER}"
    )


def answer_question(
    db: Session, question: str, user: Optional[User] = None
) -> Tuple[ChatResponse, List[retrieval_service.RetrievalCandidate]]:
    """Runs the full priority chain. Returns (response, candidates_considered).

    The candidate list is returned for logging/tests — it is never sent to the
    client.
    """
    first_name = user.first_name if user else None
    query = (question or "").strip()

    # ── Stage 1: university knowledge base ──────────────────────────────
    kb_hits = retrieval_service.search_knowledge_base(db, query)
    if kb_hits:
        best = kb_hits[0]
        context = retrieval_service.build_context_snippets(kb_hits[:2])
        ai_text = ai_service.rephrase_with_context(query, context, first_name)
        content = ai_text or f"{_greeting(first_name)}{best.content}"
        if best.is_demo:
            content = f"{content}\n\n{DEMO_KB_NOTICE}"

        logger.info("chatbot: university hit (relevance=%.2f)", best.relevance)
        return (
            ChatResponse(
                content=content,
                source_type="university",
                source_ref=ChatSourceRef(
                    document_id=best.document_id,
                    document_title=best.document_title,
                ),
            ),
            kb_hits,
        )

    # ── Stage 2: forum ──────────────────────────────────────────────────
    forum_hits = retrieval_service.search_forum(db, query)
    if forum_hits:
        best = forum_hits[0]
        context = retrieval_service.build_context_snippets(forum_hits[:2])
        ai_text = ai_service.rephrase_with_context(query, context, first_name)
        # Strip the markdown bold the forum bodies use, matching what the
        # existing frontend mock did (figma uiux/src/services/chatbot.ts).
        raw = best.content.replace("**", "")
        content = ai_text or f"{_greeting(first_name)}here's what the community said:\n\n{raw}"

        logger.info(
            "chatbot: forum hit (relevance=%.2f, net_votes=%d)", best.relevance, best.rating
        )
        return (
            ChatResponse(
                content=content,
                source_type="community",
                source_ref=ChatSourceRef(
                    question_id=best.question_id,
                    question_title=best.question_title,
                    answer_id=best.answer_id,
                    author_name=best.author_name,
                    net_votes=best.rating,
                ),
            ),
            forum_hits,
        )

    # ── Stage 3: general guidance ───────────────────────────────────────
    logger.info("chatbot: no relevant source, using general fallback")
    return (
        ChatResponse(content=_general_answer(query, first_name), source_type="general"),
        [],
    )


# ─────────────────────────────────────────────────────────────────────────
# Conversation persistence (authenticated users only)
# ─────────────────────────────────────────────────────────────────────────


def _title_from(text: str, limit: int = 60) -> str:
    clean = " ".join((text or "").split())
    return clean[: limit - 1] + "…" if len(clean) > limit else clean or "New conversation"


def get_owned_conversation(db: Session, user: User, conversation_id: str) -> Optional[Conversation]:
    """Ownership is part of the query, so one user can never load another
    user's conversation by guessing an id (brief section 23)."""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )


def persist_exchange(
    db: Session,
    user: User,
    conversation_id: Optional[str],
    user_message: str,
    response: ChatResponse,
) -> str:
    """Stores the user message + assistant reply, creating the conversation if
    needed. Returns the conversation id."""
    conversation = None
    if conversation_id:
        conversation = get_owned_conversation(db, user, conversation_id)

    if conversation is None:
        conversation = Conversation(user_id=user.id, title=_title_from(user_message))
        db.add(conversation)
        db.flush()

    db.add(
        Message(
            conversation_id=conversation.id,
            role=MessageRole.user,
            content=user_message,
        )
    )
    ref = response.source_ref
    db.add(
        Message(
            conversation_id=conversation.id,
            role=MessageRole.assistant,
            content=response.content,
            source_type=response.source_type,
            source_question_id=ref.question_id if ref else None,
            source_question_title=ref.question_title if ref else None,
            source_answer_id=ref.answer_id if ref else None,
            source_author_name=ref.author_name if ref else None,
            source_document_id=ref.document_id if ref else None,
            source_document_title=ref.document_title if ref else None,
        )
    )
    db.commit()
    return conversation.id
