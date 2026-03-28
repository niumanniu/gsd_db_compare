"""Email notification module for sending comparison alerts."""

from app.notifications.email import EmailService, get_email_service

__all__ = ["EmailService", "get_email_service"]
