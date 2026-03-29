"""Data comparison API endpoints."""

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from cryptography.fernet import Fernet

from app.db.session import get_db_session
from app.db.models import DbConnection, ComparisonTask
from app.schemas.api import (
    DataCompareRequest,
    DataCompareResponse,
    DataSummary,
    RowDiffAPI,
    FieldDiffAPI,
    MultiTableDataCompareRequest,
    MultiTableDataCompareResponse,
    TableDataResult as TableDataResultSchema,
    MultiTableDataSummary as MultiTableDataSummarySchema,
    SchemaDataCompareRequest,
    SchemaDataCompareResponse,
    SchemaDataCompareSummary as SchemaDataCompareSummarySchema,
)
from app.comparison.data import DataComparator, DataDiffResult, RowDiff
from app.comparison.multi_table import (
    MultiTableDataComparator,
    SchemaDataComparator,
    TableDataResult,
    MultiTableDataSummary,
    SchemaDataCompareSummary,
)
from app.adapters import get_adapter

router = APIRouter(prefix="/api/compare", tags=["data-compare"])

# Load encryption key from environment variable (same as connections.py)
_ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "").encode()
if not _ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY environment variable not set")
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
                diff_type=fd.diff_type,
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
                        diff_type=fd.get('diff_type', 'value'),
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


# ============= Multi-Table Data Comparison Endpoints =============


@router.post("/multi-table-data", response_model=MultiTableDataCompareResponse)
async def compare_multi_table_data(
    request: MultiTableDataCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MultiTableDataCompareResponse:
    """Compare data across multiple selected tables.

    Args:
        request: Multi-table comparison request with table lists
        db: AsyncSession dependency

    Returns:
        MultiTableDataCompareResponse with aggregated results

    Error handling:
        - 400: Invalid request, connections not found
        - 401: Authentication failed
        - 503: Database connection failed
        - 504: Comparison timeout
    """
    try:
        # Fetch both connections from database
        result = await db.execute(
            select(DbConnection).where(
                DbConnection.id.in_([request.source_connection_id, request.target_connection_id])
            )
        )
        connections = result.scalars().all()

        if len(connections) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both connections not found",
            )

        # Map connections by ID
        conn_map = {conn.id: conn for conn in connections}
        source_conn = conn_map[request.source_connection_id]
        target_conn = conn_map[request.target_connection_id]

        # Create adapters for both connections
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
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to database: {str(e)}",
            )

        try:
            # Build table mappings
            if request.table_mapping:
                # Use provided mapping
                table_mappings = [
                    (src, request.table_mapping.get(src, tgt))
                    for src, tgt in zip(request.source_tables, request.target_tables)
                ]
            else:
                # Match by index (assumes same order)
                table_mappings = list(zip(request.source_tables, request.target_tables))

            # Create comparator and run comparison
            comparator = MultiTableDataComparator(
                source_adapter=source_adapter,
                target_adapter=target_adapter,
                source_schema=request.source_schema,
                target_schema=request.target_schema,
                mode=request.mode,
                threshold=request.threshold,
                sample_size=request.sample_size,
                timeout_per_table=request.timeout_per_table,
            )

            result = comparator.compare(table_mappings)

            # Convert to Pydantic schema
            return MultiTableDataCompareResponse(
                summary=MultiTableDataSummarySchema(
                    total_tables=result.summary.total_tables,
                    compared_tables=result.summary.compared_tables,
                    identical_tables=result.summary.identical_tables,
                    tables_with_diffs=result.summary.tables_with_diffs,
                    error_tables=result.summary.error_tables,
                    total_rows_compared=result.summary.total_rows_compared,
                    total_diffs_found=result.summary.total_diffs_found,
                    elapsed_time_seconds=result.summary.elapsed_time_seconds,
                ),
                table_results=[
                    TableDataResultSchema(
                        source_table=tr.source_table,
                        target_table=tr.target_table,
                        status=tr.status,
                        source_row_count=tr.source_row_count,
                        target_row_count=tr.target_row_count,
                        diff_count=tr.diff_count,
                        diff_percentage=tr.diff_percentage,
                        mode_used=tr.mode_used,
                        is_identical=tr.is_identical,
                        error_message=tr.error_message,
                        source_hash=tr.source_hash,
                        target_hash=tr.target_hash,
                    )
                    for tr in result.table_results
                ],
            )

        finally:
            source_adapter.disconnect()
            target_adapter.disconnect()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-table comparison failed: {str(e)}",
        )


# ============= Schema-Level Data Comparison Endpoints =============


@router.post("/schema-data", response_model=SchemaDataCompareResponse)
async def compare_schema_data(
    request: SchemaDataCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SchemaDataCompareResponse:
    """Compare data across entire schema (all tables).

    Args:
        request: Schema-level comparison request with filter options
        db: AsyncSession dependency

    Returns:
        SchemaDataCompareResponse with complete results

    Error handling:
        - 400: Invalid request, connections not found
        - 401: Authentication failed
        - 503: Database connection failed
        - 504: Comparison timeout
    """
    try:
        # Fetch both connections from database
        result = await db.execute(
            select(DbConnection).where(
                DbConnection.id.in_([request.source_connection_id, request.target_connection_id])
            )
        )
        connections = result.scalars().all()

        if len(connections) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both connections not found",
            )

        # Map connections by ID
        conn_map = {conn.id: conn for conn in connections}
        source_conn = conn_map[request.source_connection_id]
        target_conn = conn_map[request.target_connection_id]

        # Create adapters for both connections
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
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to database: {str(e)}",
            )

        try:
            # Create schema comparator and run comparison
            comparator = SchemaDataComparator(
                source_adapter=source_adapter,
                target_adapter=target_adapter,
                source_schema=request.source_schema,
                target_schema=request.target_schema,
                source_connection_name=source_conn.name,
                target_connection_name=target_conn.name,
                mode=request.mode,
                threshold=request.threshold,
                sample_size=request.sample_size,
                timeout_per_table=request.timeout_per_table,
            )

            result = comparator.compare(
                exclude_patterns=request.exclude_patterns,
                include_patterns=request.include_patterns,
                only_common_tables=request.only_common_tables,
            )

            # Convert to Pydantic schema
            return SchemaDataCompareResponse(
                summary=SchemaDataCompareSummarySchema(
                    source_schema=result.summary.source_schema,
                    target_schema=result.summary.target_schema,
                    source_connection_name=result.summary.source_connection_name,
                    target_connection_name=result.summary.target_connection_name,
                    total_source_tables=result.summary.total_source_tables,
                    total_target_tables=result.summary.total_target_tables,
                    common_tables=result.summary.common_tables,
                    unmatched_source_tables=result.summary.unmatched_source_tables,
                    unmatched_target_tables=result.summary.unmatched_target_tables,
                    compared_tables=result.summary.compared_tables,
                    identical_tables=result.summary.identical_tables,
                    tables_with_diffs=result.summary.tables_with_diffs,
                    error_tables=result.summary.error_tables,
                    total_rows_source=result.summary.total_rows_source,
                    total_rows_target=result.summary.total_rows_target,
                    total_diffs_found=result.summary.total_diffs_found,
                    overall_diff_percentage=result.summary.overall_diff_percentage,
                    elapsed_time_seconds=result.summary.elapsed_time_seconds,
                ),
                table_results=[
                    TableDataResultSchema(
                        source_table=tr.source_table,
                        target_table=tr.target_table,
                        status=tr.status,
                        source_row_count=tr.source_row_count,
                        target_row_count=tr.target_row_count,
                        diff_count=tr.diff_count,
                        diff_percentage=tr.diff_percentage,
                        mode_used=tr.mode_used,
                        is_identical=tr.is_identical,
                        error_message=tr.error_message,
                        source_hash=tr.source_hash,
                        target_hash=tr.target_hash,
                    )
                    for tr in result.table_results
                ],
                unmatched_source_tables=result.unmatched_source_tables,
                unmatched_target_tables=result.unmatched_target_tables,
                excluded_tables=result.excluded_tables,
            )

        finally:
            source_adapter.disconnect()
            target_adapter.disconnect()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema-level comparison failed: {str(e)}",
        )
