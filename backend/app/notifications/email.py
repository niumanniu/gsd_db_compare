"""SMTP email service for sending comparison notifications."""

import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.db.models import NotificationSetting


class EmailService:
    """Service for sending email notifications via SMTP."""

    def __init__(self, settings: NotificationSetting):
        """Initialize email service.

        Args:
            settings: NotificationSetting with SMTP configuration
        """
        self.settings = settings
        self._smtp_host = settings.smtp_host
        self._smtp_port = settings.smtp_port
        self._use_tls = settings.use_tls
        self._sender_email = settings.sender_email
        self._sender_name = settings.sender_name

    async def send_alert(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
    ) -> bool:
        """Send an alert email.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_content: HTML email content

        Returns:
            True if sent successfully, False otherwise
        """
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self._sender_name} <{self._sender_email}>"
        message["To"] = ", ".join(recipients)

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send with retry
        return await self.send_with_retry(message)

    async def send_with_retry(
        self,
        message: MIMEMultipart,
        max_retries: int = 3,
        delay: int = 5,
    ) -> bool:
        """Send email with retry logic.

        Args:
            message: Email message to send
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds

        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                await aiosmtplib.send(
                    message,
                    hostname=self._smtp_host,
                    port=self._smtp_port,
                    start_tls=self._use_tls,
                )
                return True
            except Exception as e:
                print(f"Email send attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service(settings: NotificationSetting) -> EmailService:
    """Get or create email service instance.

    Args:
        settings: NotificationSetting with SMTP configuration

    Returns:
        EmailService instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService(settings)
    return _email_service
