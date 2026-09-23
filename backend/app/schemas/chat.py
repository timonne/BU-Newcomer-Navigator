"""Chatbot schemas.

`ChatResponse` mirrors the frontend's `ChatResponse` shape from
figma uiux/src/services/chatbot.ts exactly: {content, sourceType, sourceRef}.
sourceType values are 'university' | 'community' | 'general' -- matching
the frontend's actual type (figma uiux/src/types/index.ts), not the
'forum' label used loosely elsewhere in the project brief.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field

from app.schemas.common import CamelModel


class ChatSourceRef(CamelModel):
    """Superset of the frontend's `ChatMessage['sourceRef']`.

    The four forum fields below are exactly what the existing frontend reads
    (figma uiux/src/types/index.ts) so it can link back to the thread. The
    document/net-vote fields are additive extras the frontend currently
    ignores -- they let it identify a university source document, and show
    vote weight on a forum answer, without any type change being required
    first.
    """

    question_id: Optional[str] = None
    question_title: Optional[str] = None
    answer_id: Optional[str] = None
    author_name: Optional[str] = None
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    net_votes: Optional[int] = None


class ChatMessageRequest(CamelModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResponse(CamelModel):
    content: str
    source_type: Literal["university", "community", "general"]
    source_ref: Optional[ChatSourceRef] = None
    conversation_id: Optional[str] = None


class ChatMessageOut(CamelModel):
    id: str
    role: str
    content: str
    source_type: Optional[str] = None
    source_ref: Optional[ChatSourceRef] = None
    created_at: datetime


class ConversationOut(CamelModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageOut] = Field(default_factory=list)


class ConversationSummary(CamelModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0