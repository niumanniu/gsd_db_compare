"""Pydantic schemas for critical tables API."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CriticalTableCreate(BaseModel):
    """Request schema for marking a critical table."""
    connection_id: int
    table_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CriticalTableResponse(BaseModel):
    """Response schema for critical table."""
    id: int
    connection_id: int
    table_name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CriticalTableCheckResponse(BaseModel):
    """Response schema for critical table check."""
    is_critical: bool
    table_name: str
    connection_id: int
