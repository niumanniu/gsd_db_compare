"""Pydantic schemas for notification settings API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NotificationSettingsCreate(BaseModel):
    """Request schema for creating notification settings."""
    smtp_host: str
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str
    smtp_password: str = Field(..., min_length=1)
    use_tls: bool = True
    sender_email: str
    sender_name: str = "DB Compare"
    default_recipients: List[str] = []


class NotificationSettingsUpdate(BaseModel):
    """Request schema for updating notification settings."""
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = Field(None, min_length=1)
    use_tls: Optional[bool] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    default_recipients: Optional[List[str]] = None


class NotificationSettingsResponse(BaseModel):
    """Response schema for notification settings."""
    id: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    use_tls: bool
    sender_email: str
    sender_name: str
    default_recipients: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
