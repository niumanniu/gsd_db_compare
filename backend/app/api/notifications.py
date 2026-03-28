"""API endpoints for notification settings management."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from app.db.session import get_db_session
from app.db.models import NotificationSetting
from app.schemas.notifications import (
    NotificationSettingsCreate,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
)

router = APIRouter(prefix="/api/notification-settings", tags=["notification-settings"])

# Encryption key for password encryption
_ENCRYPTION_KEY = Fernet.generate_key()
_fernet = Fernet(_ENCRYPTION_KEY)


def encrypt_password(password: str) -> bytes:
    """Encrypt password using Fernet."""
    return _fernet.encrypt(password.encode())


def decrypt_password(encrypted: bytes) -> str:
    """Decrypt password using Fernet."""
    return _fernet.decrypt(encrypted).decode()


@router.post("", response_model=NotificationSettingsResponse, status_code=201)
async def create_notification_settings(
    settings_data: NotificationSettingsCreate,
    db: AsyncSession = Depends(get_db_session),
) -> NotificationSettingsResponse:
    """Create notification settings.

    Args:
        settings_data: Settings creation data
        db: Database session

    Returns:
        Created notification settings
    """
    # Check if settings already exist
    result = await db.execute(select(NotificationSetting).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification settings already exist. Use PUT to update.",
        )

    # Create record with encrypted password
    settings = NotificationSetting(
        smtp_host=settings_data.smtp_host,
        smtp_port=settings_data.smtp_port,
        smtp_username=settings_data.smtp_username,
        smtp_password_encrypted=encrypt_password(settings_data.smtp_password),
        use_tls=settings_data.use_tls,
        sender_email=settings_data.sender_email,
        sender_name=settings_data.sender_name,
        default_recipients=str(settings_data.default_recipients),
    )

    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return NotificationSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        use_tls=settings.use_tls,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        default_recipients=settings_data.default_recipients,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.get("", response_model=Optional[NotificationSettingsResponse])
async def get_notification_settings(
    db: AsyncSession = Depends(get_db_session),
) -> Optional[NotificationSettingsResponse]:
    """Get current notification settings.

    Args:
        db: Database session

    Returns:
        Notification settings or None if not configured
    """
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        return None

    # Parse default_recipients JSON string
    import ast
    try:
        recipients = ast.literal_eval(settings.default_recipients or "[]")
    except (ValueError, SyntaxError):
        recipients = []

    return NotificationSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        use_tls=settings.use_tls,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        default_recipients=recipients,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> NotificationSettingsResponse:
    """Update notification settings.

    Args:
        settings_data: Settings update data
        db: Database session

    Returns:
        Updated notification settings
    """
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not found. Create them first.",
        )

    # Update fields
    update_data = settings_data.model_dump(exclude_unset=True)

    if "smtp_password" in update_data and update_data["smtp_password"] is not None:
        settings.smtp_password_encrypted = encrypt_password(update_data.pop("smtp_password"))

    for field, value in update_data.items():
        if value is not None:
            if field == "default_recipients":
                value = str(value)
            setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    # Parse default_recipients for response
    import ast
    try:
        recipients = ast.literal_eval(settings.default_recipients or "[]")
    except (ValueError, SyntaxError):
        recipients = []

    return NotificationSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        use_tls=settings.use_tls,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        default_recipients=recipients,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.delete("", status_code=204)
async def delete_notification_settings(
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete notification settings.

    Args:
        db: Database session
    """
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not found",
        )

    await db.delete(settings)
    await db.commit()


@router.post("/test")
async def test_notification_settings(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Test notification settings by sending a test email.

    Args:
        db: Database session

    Returns:
        Test result
    """
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not found",
        )

    from app.notifications.email import EmailService

    email_service = EmailService(settings)

    # Parse recipients
    import ast
    try:
        recipients = ast.literal_eval(settings.default_recipients or "[]")
    except (ValueError, SyntaxError):
        recipients = []

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients configured",
        )

    subject = "[DB Compare] 测试邮件"
    html_content = """
    <html>
    <body>
        <h2>测试邮件</h2>
        <p>如果您收到这封邮件，说明 SMTP 配置正确。</p>
        <p>DB Compare 系统</p>
    </body>
    </html>
    """

    success = await email_service.send_alert(recipients, subject, html_content)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email",
        )

    return {"status": "success", "message": "Test email sent successfully"}
