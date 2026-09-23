"""
AI provider abstraction.

    ChatbotService -> RetrievalService -> AIProvider

The provider is chosen at runtime from AI_PROVIDER / AI_API_KEY / AI_MODEL in
the environment. No provider name or key appears anywhere else in the
codebase, and none is ever sent to the browser.

If no key is configured, `get_provider()` returns `NullProvider`, whose
`is_available` is False. The chatbot then answers purely from retrieval plus
a deterministic template. It does NOT claim an AI wrote the answer
(brief section 20) — `chatbot_service` only marks a response as
AI-rephrased when `is_available` was True and the call actually succeeded.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional, Protocol

from app.config import get_settings

logger = logging.getLogger("newcomer_navigation.ai")

REQUEST_TIMEOUT_SECONDS = 20

# The provider is only ever asked to rephrase retrieved context. It is
# explicitly forbidden from adding university-specific facts of its own,
# which is what keeps "do not fabricate official information" enforceable
# even when an AI model is in the loop.
SYSTEM_PROMPT = (
    "You are Navi, the Newcomer Navigation assistant for students and staff at "
    "Bennett University, Greater Noida.\n"
    "Rules you must follow exactly:\n"
    "1. Answer ONLY using the CONTEXT provided in the user message. Do not add "
    "university-specific facts (email addresses, phone numbers, fees, dates, "
    "office locations, policies, staff names) that are not present in the CONTEXT.\n"
    "2. If the CONTEXT does not answer the question, say so plainly and advise "
    "contacting Bennett University, Greater Noida directly. Do not guess.\n"
    "3. Be warm, concise and practical. Two or three short paragraphs maximum.\n"
    "4. Do not invent a source or claim something is official policy unless the "
    "CONTEXT says so."
)


class AIProvider(Protocol):
    name: str
    is_available: bool

    def complete(self, prompt: str) -> Optional[str]:
        """Returns generated text, or None if the call failed."""
        ...


class NullProvider:
    """Used when no AI credentials are configured. Always unavailable."""

    name = "none"
    is_available = False

    def complete(self, prompt: str) -> Optional[str]:
        return None


def _post_json(url: str, payload: dict, headers: dict) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Log the status only. The response body can echo back request
        # content, and the Authorization header must never reach the log.
        logger.warning("AI provider returned HTTP %s", exc.code)
    except urllib.error.URLError as exc:
        logger.warning("AI provider unreachable: %s", exc.reason)
    except (ValueError, TimeoutError) as exc:
        logger.warning("AI provider response could not be parsed: %s", type(exc).__name__)
    return None


class OpenAIProvider:
    name = "openai"
    is_available = True

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model or "gpt-4o-mini"

    def complete(self, prompt: str) -> Optional[str]:
        body = _post_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "model": self._model,
                "max_tokens": 700,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )
        if not body:
            return None
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError):
            logger.warning("Unexpected OpenAI response shape")
            return None


class AnthropicProvider:
    name = "anthropic"
    is_available = True

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model or "claude-sonnet-4-5"

    def complete(self, prompt: str) -> Optional[str]:
        body = _post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": self._model,
                "max_tokens": 700,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            {
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        if not body:
            return None
        try:
            blocks = body.get("content") or []
            text = "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            return text.strip() or None
        except AttributeError:
            logger.warning("Unexpected Anthropic response shape")
            return None


def get_provider() -> AIProvider:
    settings = get_settings()
    if not settings.is_ai_enabled:
        return NullProvider()

    provider = settings.ai_provider.strip().lower()
    if provider == "openai":
        return OpenAIProvider(settings.ai_api_key, settings.ai_model)
    if provider == "anthropic":
        return AnthropicProvider(settings.ai_api_key, settings.ai_model)

    logger.warning(
        "AI_PROVIDER=%r is not recognised; running without an AI provider. "
        "Supported values: openai, anthropic.",
        provider,
    )
    return NullProvider()


def rephrase_with_context(question: str, context: str, first_name: Optional[str] = None) -> Optional[str]:
    """Asks the configured provider to rephrase retrieved context.

    Returns None when no provider is configured or the call failed — callers
    must then fall back to returning the retrieved text directly.
    """
    provider = get_provider()
    if not provider.is_available:
        return None

    greeting = f"The user's first name is {first_name}. " if first_name else ""
    prompt = (
        f"{greeting}QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context if context else '(no context retrieved)'}\n\n"
        "Answer the question using only the CONTEXT above."
    )
    return provider.complete(prompt)
