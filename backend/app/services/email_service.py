"""
Email delivery abstraction.

If SMTP_HOST is not configured, the backend runs in "console mode": the
email content is logged instead of sent. This lets registration and
password-reset flows be fully testable locally without any email
provider credentials. Swap in a real provider by filling in the SMTP_*
variables in .env -- no other code changes needed.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("newcomer_navigation.email")


def send_email(to_address: str, subject: str, body: str) -> None:
    settings = get_settings()

    if not settings.smtp_host:
        logger.info(
            "[EMAIL - console mode, SMTP not configured]\nTo: %s\nSubject: %s\n%s",
            to_address,
            subject,
            body,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_address
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
