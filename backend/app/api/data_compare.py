"""Data comparison API endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session
from app.db.models import DbConnection, ComparisonTask
from app.schemas.api import (
    DataCompareRequest,
    DataCompareResponse,
    DataSummary,
    RowDiffAPI,
    FieldDiffAPI,
)
from app.comparison.data import DataComparator, DataDiffResult, RowDiff
from app.adapters import get_adapter

from cryptography.fernet import Fernet

router = APIRouter(prefix="/api/compare", tags=["data-compare"])

# Same encryption key as connections.py (in production, use shared secrets)
_ENCRYPTION_KEY = Fernet.generate_key()
_fernet = Fernet(_ENCRYPTION_KEY)


# Error message templates
ERROR_MESSAGES = {
    "connection_not_found": "One or both connections not found",
    "connection_failed": "Failed to connect to database. Please check connection settings.",
    "table_not_found": "Table '{table}' not found in database",
    "authentication_failed": "Database authentication failed. Please check username/password.",
    "timeout": "Comparison timed out. Try using hash or sample mode for large tables.",
    "memory_limit": "Memory limit exceeded. Try using hash mode or reduce sample size.",
    "type_mismatch": "Cannot compare columns with incompatible types",
    "generic": "An unexpected error occurred",
}


def decrypt_password(encrypted: bytes) -> str:
    """Decrypt password using Fernet symmetric encryption."""
    return _fernet.decrypt(encrypted).decode()


def convert_row_diff(row_diff: RowDiff) -> RowDiffAPI:
    """Convert internal RowDiff to API RowDiffAPI."""
    return RowDiffAPI(
        primary_key_value=row_diff.primary_key,
        diff_type=row_diff.diff_type,
        field_diffs=[
            FieldDiffAPI(
                field_name=fd.field_name,
                source_value=fd.source_value,
                target_value=fd.target_value,
                difference_type=fd.diff_type,
            )
            for fd in row_diff.field_diffs
        ],
        source_row=row_diff.source_row,
        target_row=row_diff.target_row,
    )


def convert_result_to_response(result: DataDiffResult, max_diffs: int = 100) -> DataCompareResponse:
    """Convert DataDiffResult to DataCompareResponse."""
    # Truncate diffs if too many
    truncated = len(result.diffs) > max_diffs
    diffs = result.diffs[:max_diffs] if truncated else result.diffs

    return DataCompareResponse(
        summary=DataSummary(
            source_row_count=result.source_row_count,
            target_row_count=result.target_row_count,
            diff_count=result.diff_count,
            diff_percentage=result.diff_percentage,
            mode_used=result.mode_used,
            hash_source=result.source_hash,
            hash_target=result.target_hash,
            sampled_row_count=result.sampled_row_count,
        ),
        diffs=[convert_row_diff(d) for d in diffs],
        has_more=result.has_more,
        truncated=truncated,
    )


async def create_task_record(
    db: AsyncSession,
    request: DataCompareRequest,
) -> ComparisonTask:
    """Create a comparison task record."""
    task = ComparisonTask(
        task_type="data",
        source_connection_id=request.source_connection_id,
        target_connection_id=request.target_connection_id,
        source_table=request.source_table,
        target_table=request.target_table,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task_completed(
    db: AsyncSession,
    task: ComparisonTask,
    result: DataDiffResult,
) -> None:
    """Update task as completed with result."""
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    task.result = result.to_dict()
    await db.commit()


async def update_task_failed(
    db: AsyncSession,
    task: ComparisonTask,
    error_message: str,
) -> None:
    """Update task as failed with error message."""
    task.status = "failed"
    task.completed_at = datetime.utcnow()
    task.error_message = error_message
    await db.commit()


@router.post("/data", response_model=DataCompareResponse)
async def compare_data(
    request: DataCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DataCompareResponse:
    """Compare data between two tables from different database connections.

    Supports multiple comparison modes:
    - auto: Automatically select mode based on table size
    - full: Compare all rows (for small tables)
    - hash: Compare MD5 checksums only
    - sample: Compare sampled rows (for large tables)

    Error handling:
    - 400: Invalid request, connections not found, table not found
    - 401: Authentication failed
    - 404: Table not found
    - 503: Database connection failed
    - 504: Comparison timeout
    - 413: Memory limit exceeded
    - 500: Internal server error
    """
    # Create task record for tracking
    task = await create_task_record(db, request)

    try:
        # Fetch both connections from database
        result = await db.execute(
            select(DbConnection).where(
                DbConnection.id.in_([request.source_connection_id, request.target_connection_id])
            )
        )
        connections = result.scalars().all()

        if len(connections) < 2:
            error_msg = ERROR_MESSAGES["connection_not_found"]
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Map connections by ID
        conn_map = {conn.id: conn for conn in connections}
        source_conn = conn_map[request.source_connection_id]
        target_conn = conn_map[request.target_connection_id]

        # Create adapters for both connections using factory
        source_config = {
            'host': source_conn.host,
            'port': source_conn.port,
            'database': source_conn.database,
            'username': source_conn.username,
            'password': decrypt_password(source_conn.password_encrypted),
        }

        target_config = {
            'host': target_conn.host,
            'port': target_conn.port,
            'database': target_conn.database,
            'username': target_conn.username,
            'password': decrypt_password(target_conn.password_encrypted),
        }

        try:
            source_adapter = get_adapter(source_conn.db_type, source_config)
            target_adapter = get_adapter(target_conn.db_type, target_config)
        except Exception as e:
            error_msg = f"{ERROR_MESSAGES['connection_failed']} {str(e)}"
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg,
            )

        try:
            # Create comparator with custom settings
            comparator = DataComparator(
                source_adapter=source_adapter,
                target_adapter=target_adapter,
                threshold=request.threshold,
                batch_size=request.batch_size,
                sample_size=request.sample_size,
                timeout=request.timeout,
            )

            # Run comparison
            comparison_result = comparator.compare(
                source_table=request.source_table,
                target_table=request.target_table,
                mode=request.mode,
            )

            # Update task as completed
            await update_task_completed(db, task, comparison_result)

            # Convert result to API response
            return convert_result_to_response(comparison_result)

        except ValueError as e:
            # Table not found or invalid configuration
            error_msg = str(e)
            if "not found" in error_msg.lower() or "no such table" in error_msg.lower():
                error_msg = ERROR_MESSAGES["table_not_found"].format(
                    table=request.source_table
                )
                await update_task_failed(db, task, error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        except TimeoutError as e:
            error_msg = ERROR_MESSAGES["timeout"]
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=error_msg,
            )
        except MemoryError as e:
            error_msg = ERROR_MESSAGES["memory_limit"]
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail=error_msg,
            )
        except Exception as e:
            # Comparison error
            error_msg = f"{ERROR_MESSAGES['generic']}: {str(e)}"
            await update_task_failed(db, task, error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
        finally:
            source_adapter.disconnect()
            target_adapter.disconnect()

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        # Database error
        error_msg = f"Database error: {str(e)}"
        try:
            await update_task_failed(db, task, error_msg)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_msg,
        )
    except Exception as e:
        # Generic error
        error_msg = f"{ERROR_MESSAGES['generic']}: {str(e)}"
        # Try to update task if it was created
        try:
            await update_task_failed(db, task, error_msg)
        except Exception:
            pass  # Ignore errors in error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.get("/data/{task_id}", response_model=DataCompareResponse)
async def get_comparison_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> DataCompareResponse:
    """Get comparison task status and result by ID."""
    result = await db.execute(
        select(ComparisonTask).where(ComparisonTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if task.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task not yet started",
        )

    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task still in progress",
        )

    if task.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=task.error_message or "Task failed",
        )

    # Task completed - reconstruct response from stored result
    if task.result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task completed but no result stored",
        )

    result_data = task.result
    summary_data = result_data.get('summary', {})

    return DataCompareResponse(
        summary=DataSummary(
            source_row_count=summary_data.get('source_row_count', 0),
            target_row_count=summary_data.get('target_row_count', 0),
            diff_count=summary_data.get('diff_count', 0),
            diff_percentage=summary_data.get('diff_percentage'),
            mode_used=summary_data.get('mode_used', 'unknown'),
            hash_source=summary_data.get('source_hash'),
            hash_target=summary_data.get('target_hash'),
            sampled_row_count=summary_data.get('sampled_row_count'),
        ),
        diffs=[
            RowDiffAPI(
                primary_key_value=d.get('primary_key'),
                diff_type=d.get('diff_type', 'unknown'),
                field_diffs=[
                    FieldDiffAPI(
                        field_name=fd.get('field_name', ''),
                        source_value=fd.get('source_value'),
                        target_value=fd.get('target_value'),
                        difference_type=fd.get('diff_type', 'value'),
                    )
                    for fd in d.get('field_diffs', [])
                ],
                source_row=d.get('source_row'),
                target_row=d.get('target_row'),
            )
            for d in result_data.get('diffs', [])
        ],
        has_more=summary_data.get('has_more', False),
        truncated=False,
    )
