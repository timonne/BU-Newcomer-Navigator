"""
Central application configuration.

All values are read from environment variables (see `.env.example`).
Nothing here should ever contain a real secret — defaults are safe,
non-functional placeholders for local development only.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/app.db"

    # ── Auth / JWT ───────────────────────────────────────────────────
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h
    auth_cookie_name: str = "nn_access_token"
    cookie_secure: bool = False

    # ── University email verification ───────────────────────────────
    # Comma-separated domain lists. Deliberately empty by default — see
    # `.env.example`. Nothing in this codebase invents an official domain.
    student_email_domains: str = ""
    staff_email_domains: str = ""

    # ── Email delivery ───────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = "no-reply@example.com"
    smtp_use_tls: bool = True

    # ── AI provider ──────────────────────────────────────────────────
    ai_provider: str = ""  # "", "openai", or "anthropic"
    ai_api_key: str = ""
    ai_model: str = ""

    # ── CORS / hosting ───────────────────────────────────────────────
    frontend_url: str = "http://localhost:8443"
    backend_url: str = "http://localhost:8000"

    @property
    def cors_origins(self) -> List[str]:
        # Support a comma-separated list in FRONTEND_URL for convenience,
        # while keeping the common single-origin case simple.
        origins = [o.strip() for o in self.frontend_url.split(",") if o.strip()]
        return origins or ["http://localhost:8443"]

    @property
    def student_email_domain_list(self) -> List[str]:
        return [d.strip().lower().lstrip("@") for d in self.student_email_domains.split(",") if d.strip()]

    @property
    def staff_email_domain_list(self) -> List[str]:
        return [d.strip().lower().lstrip("@") for d in self.staff_email_domains.split(",") if d.strip()]

    @property
    def is_ai_enabled(self) -> bool:
        return bool(self.ai_provider and self.ai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
