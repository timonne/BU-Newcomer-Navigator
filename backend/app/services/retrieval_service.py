"""
Retrieval for the chatbot: university knowledge base first, forum second.

RELEVANCE METHOD (brief section 12 asks for this to be documented)
──────────────────────────────────────────────────────────────────
This uses **lexical relevance scoring**, not embeddings:

  1. The query is tokenised, lowercased, and stripped of stopwords.
  2. Each candidate (KB entry or forum question) is scored as a weighted
     overlap between query tokens and the candidate's text fields:
       - knowledge base: explicit `keywords` (weight 3), question text
         (weight 2), category (weight 1), answer body (weight 0.5)
       - forum: question title (weight 3), tag names (weight 2),
         question body (weight 0.5)
  3. The raw score is normalised by the number of meaningful query tokens,
     giving a 0.0–1.0 coverage figure — "how much of what the user asked did
     this candidate actually address?"
  4. Candidates below the relevance floor are **discarded entirely** before
     any vote-based ranking happens. This is the step that stops a
     highly-upvoted but unrelated forum answer from being returned
     (brief section 12): votes are only ever used to rank results that have
     already cleared the relevance bar, never to rescue one that hasn't.

Why lexical and not vector search: there is no verified official university
corpus loaded yet (see README "Demo limitations"), the dataset is small
enough that lexical matching is competitive, and it runs with zero extra
services or API keys — important because the chatbot must work with no AI
provider configured at all.

WHERE TO SWAP IN SEMANTIC SEARCH
Replace the bodies of `search_knowledge_base` and `search_forum` only. Both
return the same `RetrievalCandidate` shape, and `chatbot_service` depends on
that shape alone, so a pgvector/embedding implementation can be dropped in
without touching the priority logic or the API contract.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from sqlalchemy.orm import Session, selectinload

from app.models.answer import Answer, AnswerStatus
from app.models.knowledge import KnowledgeBaseEntry
from app.models.question import Question, QuestionStatus
from app.models.vote import VoteTargetType
from app.services.forum_service import vote_counts_for

# Tuned so that a question sharing one incidental word ("the campus") does not
# clear the bar, but one sharing the actual subject ("hostel laundry") does.
# Raise to be stricter (more "contact the university" fallbacks), lower to be
# more willing to answer from partial matches.
KB_RELEVANCE_THRESHOLD = 0.34
FORUM_RELEVANCE_THRESHOLD = 0.40

STOPWORDS: Set[str] = {
    "a", "about", "am", "an", "and", "any", "are", "as", "at", "be", "been",
    "but", "by", "can", "could", "did", "do", "does", "for", "from", "get",
    "getting", "had", "has", "have", "how", "i", "if", "in", "into", "is",
    "it", "its", "just", "know", "me", "my", "need", "of", "on", "or", "our",
    "please", "should", "so", "some", "tell", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "to", "up", "us", "was",
    "we", "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    tokens = _TOKEN_RE.findall((text or "").lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def _overlap(query_tokens: Sequence[str], text: str) -> int:
    """Number of distinct query tokens present in `text`.

    Matching is prefix-tolerant in both directions so "hostels" matches
    "hostel" and "admission" matches "admissions" without a stemmer.
    """
    if not text:
        return 0
    candidate_tokens = set(_TOKEN_RE.findall(text.lower()))
    hits = 0
    for qt in set(query_tokens):
        for ct in candidate_tokens:
            if qt == ct or (len(qt) > 3 and ct.startswith(qt)) or (len(ct) > 3 and qt.startswith(ct)):
                hits += 1
                break
    return hits


@dataclass
class RetrievalCandidate:
    """One retrieval hit, from either source.

    `relevance` is the 0.0-1.0 coverage score; `rating` is the net vote score
    for forum answers (always 0 for knowledge-base entries, which are not
    voted on).
    """

    source_type: str  # "university" | "community"
    relevance: float
    content: str
    rating: int = 0
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    question_id: Optional[str] = None
    question_title: Optional[str] = None
    answer_id: Optional[str] = None
    author_name: Optional[str] = None
    is_demo: bool = False
    debug: Dict[str, float] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────
# Stage 1 — university knowledge base (highest priority)
# ─────────────────────────────────────────────────────────────────────────


def search_knowledge_base(
    db: Session, query: str, *, limit: int = 5, threshold: float = KB_RELEVANCE_THRESHOLD
) -> List[RetrievalCandidate]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    denom = float(len(set(query_tokens)))

    candidates: List[RetrievalCandidate] = []
    for entry in db.query(KnowledgeBaseEntry).all():
        keywords_text = " ".join(entry.keywords or [])
        score = (
            3.0 * _overlap(query_tokens, keywords_text)
            + 2.0 * _overlap(query_tokens, entry.question)
            + 1.0 * _overlap(query_tokens, entry.category or "")
            + 0.5 * _overlap(query_tokens, entry.answer)
        )
        # Normalise against the best score this query could possibly achieve
        # (every token matching every weighted field) to land in 0.0-1.0.
        max_score = denom * (3.0 + 2.0 + 1.0 + 0.5)
        relevance = score / max_score if max_score else 0.0
        # Scale up: full coverage of keywords+question alone should be a
        # strong match, so rebase on the two fields that matter most.
        strong = (3.0 * denom + 2.0 * denom) / max_score
        relevance = min(1.0, relevance / strong) if strong else 0.0

        if relevance >= threshold:
            candidates.append(
                RetrievalCandidate(
                    source_type="university",
                    relevance=relevance,
                    content=entry.answer,
                    document_id=entry.id,
                    document_title=entry.question,
                    is_demo=bool(entry.is_demo),
                    debug={"raw": score, "relevance": relevance},
                )
            )

    candidates.sort(key=lambda c: c.relevance, reverse=True)
    return candidates[:limit]


# ─────────────────────────────────────────────────────────────────────────
# Stage 2 — forum (only reached when the KB has nothing relevant)
# ─────────────────────────────────────────────────────────────────────────


def search_forum(
    db: Session, query: str, *, limit: int = 5, threshold: float = FORUM_RELEVANCE_THRESHOLD
) -> List[RetrievalCandidate]:
    """Relevance-filter questions, then pick each one's best-rated answer.

    Ordering is (relevance cleared) -> highest net votes -> highest relevance.
    A question with no visible answers is skipped: an unanswered thread is not
    an answer.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    denom = float(len(set(query_tokens)))
    max_score = denom * (3.0 + 2.0 + 0.5)

    questions = (
        db.query(Question)
        .filter(Question.status == QuestionStatus.open)
        .options(selectinload(Question.tags), selectinload(Question.author))
        .all()
    )

    relevant: List[tuple[Question, float]] = []
    for q in questions:
        tag_text = " ".join(t.name for t in q.tags)
        score = (
            3.0 * _overlap(query_tokens, q.title)
            + 2.0 * _overlap(query_tokens, tag_text)
            + 0.5 * _overlap(query_tokens, q.body)
        )
        relevance = (score / max_score) if max_score else 0.0
        strong = (3.0 * denom + 2.0 * denom) / max_score if max_score else 0.0
        relevance = min(1.0, relevance / strong) if strong else 0.0
        if relevance >= threshold:
            relevant.append((q, relevance))

    if not relevant:
        return []

    question_ids = [q.id for q, _ in relevant]
    answers = (
        db.query(Answer)
        .filter(
            Answer.question_id.in_(question_ids),
            Answer.status == AnswerStatus.visible,
        )
        .options(selectinload(Answer.author))
        .all()
    )
    if not answers:
        return []

    counts = vote_counts_for(db, VoteTargetType.answer, [a.id for a in answers])

    by_question: Dict[str, List[Answer]] = {}
    for a in answers:
        by_question.setdefault(a.question_id, []).append(a)

    candidates: List[RetrievalCandidate] = []
    for q, relevance in relevant:
        q_answers = by_question.get(q.id)
        if not q_answers:
            continue

        def net(a: Answer) -> int:
            ups, downs = counts.get(a.id, (0, 0))
            return ups - downs

        # Accepted answers win ties; otherwise highest net score.
        best = max(q_answers, key=lambda a: (a.is_accepted, net(a), a.created_at))
        candidates.append(
            RetrievalCandidate(
                source_type="community",
                relevance=relevance,
                content=best.body,
                rating=net(best),
                question_id=q.id,
                question_title=q.title,
                answer_id=best.id,
                author_name=best.author.full_name if best.author else None,
                debug={"relevance": relevance, "net_votes": float(net(best))},
            )
        )

    # Relevance has already been thresholded above, so ranking by rating here
    # can only ever reorder answers that are all genuinely on-topic.
    candidates.sort(key=lambda c: (c.rating, c.relevance), reverse=True)
    return candidates[:limit]


def build_context_snippets(candidates: Sequence[RetrievalCandidate], max_chars: int = 2400) -> str:
    """Flattens candidates into a context block for the AI provider.

    Only retrieved text is included — the AI layer is asked to rephrase this
    context, never to supply university facts from its own training data.
    """
    parts: List[str] = []
    used = 0
    for c in candidates:
        label = "UNIVERSITY KNOWLEDGE BASE" if c.source_type == "university" else "FORUM ANSWER"
        title = c.document_title or c.question_title or ""
        block = f"[{label}] {title}\n{c.content}".strip()
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)
