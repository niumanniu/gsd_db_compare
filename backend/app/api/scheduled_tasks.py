"""API endpoints for scheduled task management."""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.db.models import ScheduledTask, DbConnection
from app.scheduler import get_scheduler_service
from app.schemas.scheduled_tasks import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    TableMapping,
)

router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])


def validate_cron_expression(cron_expr: str) -> bool:
    """Validate cron expression format.

    Args:
        cron_expr: Cron expression string (5 parts: minute hour day month day_of_week)

    Returns:
        True if valid, raises ValueError if invalid
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: must have 5 parts, got {len(parts)}")

    # Basic validation ranges
    ranges = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day
        (1, 12),   # month
        (0, 7),    # day of week (0 and 7 are Sunday)
    ]

    for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
        if part != '*' and not part.startswith('*/'):
            try:
                val = int(part)
                if val < min_val or val > max_val:
                    raise ValueError(f"Part {i+1} out of range: {part}")
            except ValueError:
                # Could be a comma-separated list or range
                pass

    return True


@router.post("", response_model=ScheduledTaskResponse, status_code=201)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """Create a new scheduled comparison task.

    Args:
        task_data: Task creation data
        db: Database session

    Returns:
        Created scheduled task
    """
    # 1. Validate cron expression
    try:
        validate_cron_expression(task_data.cron_expression)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 2. Verify connections exist
    result = await db.execute(
        select(DbConnection).where(
            DbConnection.id.in_([task_data.source_connection_id, task_data.target_connection_id])
        )
    )
    connections = result.scalars().all()

    if len(connections) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or both connections not found",
        )

    # 3. Create database record
    tables_json = json.dumps([t.model_dump() for t in task_data.tables])

    task = ScheduledTask(
        name=task_data.name,
        description=task_data.description,
        cron_expression=task_data.cron_expression,
        source_connection_id=task_data.source_connection_id,
        target_connection_id=task_data.target_connection_id,
        tables=tables_json,
        compare_mode=task_data.compare_mode,
        notification_enabled=task_data.notification_enabled,
        enabled=task_data.enabled,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 4. Add to scheduler if enabled
    if task.enabled:
        try:
            scheduler = get_scheduler_service()
            if scheduler.scheduler:
                scheduler.add_job(task.id, task.name, task.cron_expression)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to add task to scheduler: {e}")

    return task


@router.get("", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
) -> List[ScheduledTaskResponse]:
    """List all scheduled tasks.

    Args:
        enabled_only: If True, only return enabled tasks
        db: Database session

    Returns:
        List of scheduled tasks
    """
    query = select(ScheduledTask)
    if enabled_only:
        query = query.where(ScheduledTask.enabled == True)

    result = await db.execute(query.order_by(ScheduledTask.name))
    return result.scalars().all()


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """Get a specific scheduled task by ID.

    Args:
        task_id: Task ID
        db: Database session

    Returns:
        Scheduled task details
    """
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled task {task_id} not found",
        )

    return task


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """Update a scheduled task.

    Args:
        task_id: Task ID
        task_data: Update data
        db: Database session

    Returns:
        Updated scheduled task
    """
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled task {task_id} not found",
        )

    # Validate cron expression if provided
    if task_data.cron_expression:
        try:
            validate_cron_expression(task_data.cron_expression)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)

    # Handle tables conversion to JSON
    if "tables" in update_data and update_data["tables"] is not None:
        update_data["tables"] = json.dumps(
            [t.model_dump() if isinstance(t, TableMapping) else t for t in update_data["tables"]]
        )

    for field, value in update_data.items():
        if value is not None:
            setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    # Update scheduler if cron expression or enabled status changed
    scheduler = get_scheduler_service()
    if scheduler.scheduler:
        if task.enabled:
            scheduler.add_job(task.id, task.name, task.cron_expression)
        else:
            scheduler.remove_job(task.id)

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a scheduled task.

    Args:
        task_id: Task ID
        db: Database session
    """
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled task {task_id} not found",
        )

    # Remove from scheduler
    scheduler = get_scheduler_service()
    if scheduler.scheduler:
        scheduler.remove_job(task.id)

    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/run", response_model=dict)
async def run_scheduled_task_now(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Manually trigger immediate execution of a scheduled task.

    Args:
        task_id: Task ID
        db: Database session

    Returns:
        Execution status
    """
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled task {task_id} not found",
        )

    # Schedule immediate execution
    from app.scheduler.jobs import execute_scheduled_comparison

    scheduler = get_scheduler_service()
    if scheduler.scheduler:
        scheduler.scheduler.add_job(
            execute_scheduled_comparison,
            args=[task_id],
            id=f"adhoc_{task_id}_{int(datetime.utcnow().timestamp())}",
            misfire_grace_time=None,
        )

    return {"status": "started", "message": "Task execution started"}


@router.post("/{task_id}/toggle", response_model=ScheduledTaskResponse)
async def toggle_scheduled_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledTaskResponse:
    """Toggle enabled/disabled state of a scheduled task.

    Args:
        task_id: Task ID
        db: Database session

    Returns:
        Updated scheduled task
    """
    result = await db.execute(
        select(ScheduledTask).where(ScheduledTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled task {task_id} not found",
        )

    # Toggle enabled state
    task.enabled = not task.enabled

    # Update scheduler
    scheduler = get_scheduler_service()
    if scheduler.scheduler:
        if task.enabled:
            scheduler.add_job(task.id, task.name, task.cron_expression)
        else:
            scheduler.remove_job(task.id)

    await db.commit()
    await db.refresh(task)

    return task
