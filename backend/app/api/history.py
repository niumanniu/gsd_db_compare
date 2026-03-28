"""API endpoints for comparison history."""

import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import aliased

from app.db.session import get_db_session
from app.db.models import ComparisonHistory
from app.schemas.history import (
    HistoryRecord,
    TrendResponse,
    TrendDataPoint,
    HistoryStats,
)

router = APIRouter(prefix="/api/comparison-history", tags=["history"])


@router.get("", response_model=List[HistoryRecord])
async def list_comparison_history(
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> List[HistoryRecord]:
    """List comparison history records with pagination.

    Args:
        task_id: Optional task ID filter
        status: Optional status filter
        page: Page number
        limit: Page size
        db: Database session

    Returns:
        List of history records
    """
    query = select(ComparisonHistory)

    if task_id is not None:
        query = query.where(ComparisonHistory.task_id == task_id)

    if status:
        query = query.where(ComparisonHistory.status == status)

    query = query.order_by(ComparisonHistory.created_at.desc())

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{history_id}", response_model=HistoryRecord)
async def get_comparison_history(
    history_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> HistoryRecord:
    """Get a specific comparison history record.

    Args:
        history_id: History record ID
        db: Database session

    Returns:
        History record details
    """
    result = await db.execute(
        select(ComparisonHistory).where(ComparisonHistory.id == history_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record {history_id} not found",
        )

    return record


@router.get("/trend", response_model=TrendResponse)
async def get_comparison_trend(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    task_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> TrendResponse:
    """Get trend analysis data for comparison history.

    Args:
        period: Aggregation period (daily, weekly, monthly)
        days: Number of days to analyze
        task_id: Optional task ID filter
        db: Database session

    Returns:
        Trend data with data points and statistics
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Build base query
    query = select(
        func.date(ComparisonHistory.completed_at).label('date'),
        func.count().label('completed_count'),
        func.sum(ComparisonHistory.diff_count).label('diff_count'),
    ).where(
        and_(
            ComparisonHistory.status == 'completed',
            ComparisonHistory.completed_at >= start_date,
            ComparisonHistory.completed_at <= end_date,
        )
    )

    if task_id is not None:
        query = query.where(ComparisonHistory.task_id == task_id)

    query = query.group_by(func.date(ComparisonHistory.completed_at))
    query = query.order_by(func.date(ComparisonHistory.completed_at))

    result = await db.execute(query)
    rows = result.fetchall()

    # Format data points
    data_points = [
        TrendDataPoint(
            date=row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
            diff_count=row.diff_count or 0,
            completed_count=row.completed_count,
        )
        for row in rows
    ]

    # Calculate totals
    total_comparisons = sum(dp.completed_count for dp in data_points)
    total_diffs = sum(dp.diff_count for dp in data_points)
    avg_diff_count = total_diffs / total_comparisons if total_comparisons > 0 else 0.0

    return TrendResponse(
        period=period,
        data_points=data_points,
        total_comparisons=total_comparisons,
        total_diffs=total_diffs,
        avg_diff_count=avg_diff_count,
    )


@router.get("/stats", response_model=HistoryStats)
async def get_comparison_stats(
    task_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> HistoryStats:
    """Get statistical summary of comparison history.

    Args:
        task_id: Optional task ID filter
        db: Database session

    Returns:
        Statistical summary
    """
    # Base conditions
    base_conditions = []
    if task_id is not None:
        base_conditions.append(ComparisonHistory.task_id == task_id)

    # Total comparisons
    total_query = select(func.count()).select_from(ComparisonHistory)
    if base_conditions:
        total_query = total_query.where(and_(*base_conditions))
    total_result = await db.execute(total_query)
    total_comparisons = total_result.scalar() or 0

    # Completed count
    completed_query = select(func.count()).where(
        ComparisonHistory.status == 'completed'
    )
    if base_conditions:
        completed_query = completed_query.where(and_(*base_conditions))
    completed_result = await db.execute(completed_query)
    completed = completed_result.scalar() or 0

    # Failed count
    failed_query = select(func.count()).where(
        ComparisonHistory.status == 'failed'
    )
    if base_conditions:
        failed_query = failed_query.where(and_(*base_conditions))
    failed_result = await db.execute(failed_query)
    failed = failed_result.scalar() or 0

    # Average diff count (completed only)
    avg_query = select(func.avg(ComparisonHistory.diff_count)).where(
        and_(
            ComparisonHistory.status == 'completed',
            ComparisonHistory.diff_count > 0,
        )
    )
    if task_id is not None:
        avg_query = avg_query.where(ComparisonHistory.task_id == task_id)
    avg_result = await db.execute(avg_query)
    avg_diff_count = float(avg_result.scalar() or 0)

    # Max diff count
    max_query = select(func.max(ComparisonHistory.diff_count)).where(
        ComparisonHistory.status == 'completed'
    )
    if task_id is not None:
        max_query = max_query.where(ComparisonHistory.task_id == task_id)
    max_result = await db.execute(max_query)
    max_diff_count = max_result.scalar() or 0

    # Last 24h comparisons
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_24h_query = select(func.count()).where(
        and_(
            ComparisonHistory.created_at >= last_24h,
        )
    )
    if task_id is not None:
        last_24h_query = last_24h_query.where(ComparisonHistory.task_id == task_id)
    last_24h_result = await db.execute(last_24h_query)
    last_24h_comparisons = last_24h_result.scalar() or 0

    # Last 7d comparisons
    last_7d = now - timedelta(days=7)
    last_7d_query = select(func.count()).where(
        and_(
            ComparisonHistory.created_at >= last_7d,
        )
    )
    if task_id is not None:
        last_7d_query = last_7d_query.where(ComparisonHistory.task_id == task_id)
    last_7d_result = await db.execute(last_7d_query)
    last_7d_comparisons = last_7d_result.scalar() or 0

    return HistoryStats(
        total_comparisons=total_comparisons,
        completed=completed,
        failed=failed,
        avg_diff_count=avg_diff_count,
        max_diff_count=max_diff_count,
        last_24h_comparisons=last_24h_comparisons,
        last_7d_comparisons=last_7d_comparisons,
    )
