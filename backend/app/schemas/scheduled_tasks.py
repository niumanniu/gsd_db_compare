"""Pydantic schemas for scheduled tasks API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TableMapping(BaseModel):
    """Table mapping configuration."""
    source: str
    target: str
    critical: bool = False


class ScheduledTaskCreate(BaseModel):
    """Request schema for creating a scheduled task."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cron_expression: str = Field(..., description="Cron expression, e.g., '0 */2 * * *'")
    source_connection_id: int
    target_connection_id: int
    tables: List[TableMapping]
    compare_mode: str = Field(default='schema', pattern='^(schema|data|both)$')
    notification_enabled: bool = True
    enabled: bool = True


class ScheduledTaskUpdate(BaseModel):
    """Request schema for updating a scheduled task."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    tables: Optional[List[TableMapping]] = None
    compare_mode: Optional[str] = Field(None, pattern='^(schema|data|both)$')
    notification_enabled: Optional[bool] = None
    enabled: Optional[bool] = None


class ScheduledTaskResponse(BaseModel):
    """Response schema for scheduled task."""
    id: int
    name: str
    description: Optional[str]
    cron_expression: str
    source_connection_id: int
    target_connection_id: int
    tables: List[TableMapping]
    compare_mode: str
    notification_enabled: bool
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
