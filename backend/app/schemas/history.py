"""Pydantic schemas for comparison history API."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HistoryRecord(BaseModel):
    """Single comparison history record."""
    id: int
    task_id: Optional[int]
    source_connection_id: int
    target_connection_id: int
    source_table: str
    target_table: str
    compare_mode: str
    source_row_count: Optional[int]
    target_row_count: Optional[int]
    diff_count: int
    diff_percentage: Optional[float]
    has_critical_diffs: bool
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    result_summary: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TrendDataPoint(BaseModel):
    """Data point for trend chart."""
    date: str
    diff_count: int
    completed_count: int


class TrendResponse(BaseModel):
    """Response schema for trend analysis."""
    period: str  # daily, weekly, monthly
    data_points: List[TrendDataPoint]
    total_comparisons: int
    total_diffs: int
    avg_diff_count: float


class HistoryStats(BaseModel):
    """Statistics summary for comparison history."""
    total_comparisons: int
    completed: int
    failed: int
    avg_diff_count: float
    max_diff_count: int
    last_24h_comparisons: int
    last_7d_comparisons: int
