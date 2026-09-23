"""
FastAPI application entry point.

    main.py -> FastAPI app -> routers -> services -> database

Run from the `backend/` directory:

    uvicorn app.main:app --reload --port 8000

or from the project root via the root-level `main.py` shim.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import answers, auth, categories, chatbot, knowledge, questions, users, votes
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.database import Base, engine

# Importing the models package registers every table on Base.metadata.
from app import models  # noqa: F401

logger = logging.getLogger("newcomer_navigation")

MAX_REQUEST_BYTES = 1_000_000  # 1 MB — generous for JSON, closes off bulk abuse


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title="Newcomer Navigation API",
        description=(
            "Backend for the Newcomer Navigation app (Bennett University, Greater Noida). "
            "Serves the existing Figma Make frontend: authentication, profiles, forum, "
            "voting, and the Navi chatbot."
        ),
        version="1.0.0",
        # Interactive docs are development-only.
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment == "development" else None,
    )

    # ── Rate limiting ───────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests. Please wait a moment and try again.",
                }
            },
        )

    # ── CORS ────────────────────────────────────────────────────────────
    # allow_credentials is required for the httpOnly auth cookie to be sent.
    # That in turn forbids a wildcard origin, so origins come from
    # FRONTEND_URL (comma-separated list supported) -- see config.py.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Request size limit ──────────────────────────────────────────────
    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body is too large."}},
            )
        return await call_next(request)

    # ── Errors ──────────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routes ──────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(questions.router)
    app.include_router(answers.router)
    app.include_router(votes.router)
    app.include_router(categories.router)
    app.include_router(chatbot.router)
    app.include_router(knowledge.router)

    @app.get("/api/health", tags=["meta"])
    def health():
        """Liveness check. Also reports whether an AI provider is configured,
        without ever revealing the key or provider name."""
        return {
            "status": "ok",
            "environment": settings.environment,
            "aiProviderConfigured": settings.is_ai_enabled,
        }

    @app.on_event("startup")
    def on_startup() -> None:
        # Convenience for local SQLite development: create any missing tables
        # so `uvicorn app.main:app` works on a fresh clone with no migration
        # step. Alembic remains the source of truth for schema changes and is
        # what you should use for PostgreSQL (see backend/README.md).
        if settings.database_url.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
            logger.info("SQLite detected — ensured tables exist.")
        logger.info("Newcomer Navigation API ready (env=%s)", settings.environment)
        if not settings.is_ai_enabled:
            logger.info(
                "No AI provider configured — the chatbot will answer from the university "
                "knowledge base, then the forum, then a deterministic general fallback."
            )
        if not settings.student_email_domain_list and not settings.staff_email_domain_list:
            logger.warning(
                "STUDENT_EMAIL_DOMAINS / STAFF_EMAIL_DOMAINS are empty — email-domain "
                "restriction is disabled. Set them in .env once you have the official domains."
            )

    return app


app = create_app()
