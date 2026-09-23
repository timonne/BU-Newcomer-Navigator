"""Basic logging configuration.

Deliberately simple: logs to stdout with a readable format, and never
logs request bodies, passwords, tokens, or full stack traces to anything
the client can see (see app/core/errors.py for the client-facing side).
"""
from __future__ import annotations

import logging
import sys

from app.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on reload.
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        root.addHandler(handler)

    # Quiet down noisy third-party loggers a little.
    logging.getLogger("passlib").setLevel(logging.WARNING)