"""
/api/chat/* — Navi, the chatbot.

`POST /api/chat/messages` works for anonymous visitors too (the existing
frontend lets you use the chatbot before signing in). When the caller IS
authenticated, two things change:
  - the reply is personalised with their real first name, taken from the
    User row resolved from the auth cookie — never from the request body
  - the exchange is persisted to their conversation history

Conversation endpoints are authenticated-only and always scoped by owner, so
no user can read or delete another user's history.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional
from app.core.errors import APIError
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.chat import Conversation
from app.models.user import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatMessageRequest,
    ChatResponse,
    ChatSourceRef,
    ConversationOut,
    ConversationSummary,
)
from app.services import chatbot_service

router = APIRouter(prefix="/api/chat", tags=["chatbot"])


@router.post("/messages", response_model=ChatResponse)
@limiter.limit("30/minute")
def send_message(
    request: Request,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Runs the university -> forum -> general priority chain.

    Note the request schema has no `firstName` field: personalisation cannot
    be driven by the client (brief section 13).
    """
    response, _candidates = chatbot_service.answer_question(db, payload.message, user=user)

    if user is not None:
        response.conversation_id = chatbot_service.persist_exchange(
            db, user, payload.conversation_id, payload.message, response
        )
    return response


@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        )
        for c in rows
    ]


def _to_conversation_out(conversation: Conversation) -> ConversationOut:
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ChatMessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                source_type=m.source_type,
                source_ref=ChatSourceRef(
                    question_id=m.source_question_id,
                    question_title=m.source_question_title,
                    answer_id=m.source_answer_id,
                    author_name=m.source_author_name,
                    document_id=m.source_document_id,
                    document_title=m.source_document_title,
                ),
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = chatbot_service.get_owned_conversation(db, user, conversation_id)
    if conversation is None:
        # Deliberately 404 rather than 403: a conversation the caller does not
        # own should be indistinguishable from one that does not exist.
        raise APIError("CONVERSATION_NOT_FOUND", "Conversation not found.", status.HTTP_404_NOT_FOUND)
    return _to_conversation_out(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = chatbot_service.get_owned_conversation(db, user, conversation_id)
    if conversation is None:
        raise APIError("CONVERSATION_NOT_FOUND", "Conversation not found.", status.HTTP_404_NOT_FOUND)
    db.delete(conversation)
    db.commit()
    return None
