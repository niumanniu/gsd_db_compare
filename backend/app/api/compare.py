"""Schema comparison API endpoints."""

import os
import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from app.db.session import get_db_session
from app.db.models import DbConnection
from app.schemas.api import (
    SchemaCompareRequest,
    SchemaDiffResponse,
    ColumnDiff,
    IndexDiff,
    ConstraintDiff,
    MultiTableCompareRequest,
    MultiTableCompareResponse,
    DatabaseCompareRequest,
    DatabaseCompareResponse,
    TableCompareSummary,
)
from app.comparison.schema import SchemaComparator
from app.adapters import get_adapter

router = APIRouter(prefix="/api/compare", tags=["compare"])

# Load encryption key from environment variable (same as connections.py)
_ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "").encode()
if not _ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY environment variable not set")
_fernet = Fernet(_ENCRYPTION_KEY)


def decrypt_password(encrypted: bytes) -> str:
    """Decrypt password using Fernet symmetric encryption."""
    return _fernet.decrypt(encrypted).decode()


@router.post("/schema", response_model=SchemaDiffResponse)
async def compare_schemas(
    request: SchemaCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SchemaDiffResponse:
    """Compare schemas of two tables from different database connections.

    Fetches metadata from both tables and identifies all differences.
    """
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

    source_adapter = get_adapter(source_conn.db_type, source_config)
    target_adapter = get_adapter(target_conn.db_type, target_config)

    try:
        # Fetch metadata from both tables
        source_metadata = source_adapter.get_table_metadata(request.source_table)
        target_metadata = target_adapter.get_table_metadata(request.target_table)

        # Get database types for comparison
        source_db_type = source_adapter.get_database_type()
        target_db_type = target_adapter.get_database_type()

        # Run comparison with database-aware comparator
        comparator = SchemaComparator(
            source_db_type=source_db_type,
            target_db_type=target_db_type,
        )
        diff = comparator.compare(source_metadata, target_metadata)

        # Convert to Pydantic response with database type info
        comparison_mode = 'same-database' if source_db_type == target_db_type else 'cross-database'

        return SchemaDiffResponse(
            source_table=diff.source_table,
            target_table=diff.target_table,
            column_diffs=[
                ColumnDiff(
                    column_name=d.column_name,
                    diff_type=d.diff_type,
                    source_definition=d.source_def,
                    target_definition=d.target_def,
                    differences=d.differences,
                )
                for d in diff.column_diffs
            ],
            index_diffs=[
                IndexDiff(
                    index_name=d.index_name,
                    diff_type=d.diff_type,
                    source_definition=d.source_def,
                    target_definition=d.target_def,
                    differences=d.differences,
                )
                for d in diff.index_diffs
            ],
            constraint_diffs=[
                ConstraintDiff(
                    constraint_name=d.constraint_name,
                    diff_type=d.diff_type,
                    constraint_type=d.constraint_type,
                    source_definition=d.source_def,
                    target_definition=d.target_def,
                    differences=d.differences,
                )
                for d in diff.constraint_diffs
            ],
            has_differences=diff.has_differences,
            source_db_type=source_db_type,
            target_db_type=target_db_type,
            comparison_mode=comparison_mode,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare schemas: {str(e)}",
        )
    finally:
        source_adapter.disconnect()
        target_adapter.disconnect()


@router.post("/schema/batch", response_model=MultiTableCompareResponse)
async def compare_schemas_batch(
    request: MultiTableCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MultiTableCompareResponse:
    """Compare multiple tables between two database connections.

    Supports both automatic table name matching and custom table mapping.
    """
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

    source_adapter = get_adapter(source_conn.db_type, source_config)
    target_adapter = get_adapter(target_conn.db_type, target_config)

    try:
        # Build table mapping
        table_mapping = request.table_mapping or {}

        # If no custom mapping, auto-match by table name
        if not table_mapping:
            source_set = set(request.source_tables)
            target_set = set(request.target_tables)
            common_tables = source_set & target_set
            table_mapping = {t: t for t in common_tables}

        # Compare each table pair
        summaries: list[TableCompareSummary] = []
        table_results: dict[str, SchemaDiffResponse] = {}

        comparator = SchemaComparator(
            source_db_type=source_conn.db_type,
            target_db_type=target_conn.db_type,
        )

        for source_table, target_table in table_mapping.items():
            try:
                # Fetch metadata from both tables
                source_metadata = source_adapter.get_table_metadata(source_table)
                target_metadata = target_adapter.get_table_metadata(target_table)

                # Run comparison
                diff = comparator.compare(source_metadata, target_metadata)

                # Build response
                response_diff = SchemaDiffResponse(
                    source_table=source_table,
                    target_table=target_table,
                    column_diffs=[
                        ColumnDiff(
                            column_name=d.column_name,
                            diff_type=d.diff_type,
                            source_definition=d.source_def,
                            target_definition=d.target_def,
                            differences=d.differences,
                        )
                        for d in diff.column_diffs
                    ],
                    index_diffs=[
                        IndexDiff(
                            index_name=d.index_name,
                            diff_type=d.diff_type,
                            source_definition=d.source_def,
                            target_definition=d.target_def,
                            differences=d.differences,
                        )
                        for d in diff.index_diffs
                    ],
                    constraint_diffs=[
                        ConstraintDiff(
                            constraint_name=d.constraint_name,
                            diff_type=d.diff_type,
                            constraint_type=d.constraint_type,
                            source_definition=d.source_def,
                            target_definition=d.target_def,
                            differences=d.differences,
                        )
                        for d in diff.constraint_diffs
                    ],
                    has_differences=diff.has_differences,
                    source_db_type=source_conn.db_type,
                    target_db_type=target_conn.db_type,
                )

                summaries.append(TableCompareSummary(
                    source_table=source_table,
                    target_table=target_table,
                    has_differences=response_diff.has_differences,
                    diff_count=response_diff.diff_count,
                    status='success',
                ))

                table_results[source_table] = response_diff

            except Exception as e:
                summaries.append(TableCompareSummary(
                    source_table=source_table,
                    target_table=target_table,
                    has_differences=False,
                    diff_count=0,
                    status='error',
                    error_message=str(e),
                ))

        return MultiTableCompareResponse(
            summary=summaries,
            table_results=table_results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare schemas: {str(e)}",
        )
    finally:
        source_adapter.disconnect()
        target_adapter.disconnect()


@router.post("/schema/database", response_model=DatabaseCompareResponse)
async def compare_databases(
    request: DatabaseCompareRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DatabaseCompareResponse:
    """Compare all matching tables between two databases.

    Automatically matches tables by name and supports exclusion patterns.
    """
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

    source_adapter = get_adapter(source_conn.db_type, source_config)
    target_adapter = get_adapter(target_conn.db_type, target_config)

    try:
        # Get all tables from both databases using selected schemas
        # Use provided schema parameters or fall back to connection's default database
        source_schema_name = request.source_schema or source_conn.database
        target_schema_name = request.target_schema or target_conn.database

        source_tables_result = source_adapter.get_tables(schema=source_schema_name)
        target_tables_result = target_adapter.get_tables(schema=target_schema_name)

        source_table_names = [t['table_name'] for t in source_tables_result]
        target_table_names = [t['table_name'] for t in target_tables_result]

        # Apply exclusion patterns
        excluded_tables = []
        filtered_source_tables = []
        for table_name in source_table_names:
            if request.should_exclude_table(table_name):
                excluded_tables.append(table_name)
            else:
                filtered_source_tables.append(table_name)

        filtered_target_tables = [t for t in target_table_names if not request.should_exclude_table(t)]

        # Find matching tables (by name)
        source_set = set(filtered_source_tables)
        target_set = set(filtered_target_tables)
        matching_tables = sorted(source_set & target_set)
        unmatched_source = sorted(source_set - target_set)
        unmatched_target = sorted(target_set - source_set)

        # Compare each matching table
        summaries: list[TableCompareSummary] = []
        tables_with_diffs = 0

        comparator = SchemaComparator(
            source_db_type=source_conn.db_type,
            target_db_type=target_conn.db_type,
        )

        for table_name in matching_tables:
            try:
                # Fetch metadata from both tables
                source_metadata = source_adapter.get_table_metadata(table_name)
                target_metadata = target_adapter.get_table_metadata(table_name)

                # Run comparison
                diff = comparator.compare(source_metadata, target_metadata)

                # Build summary
                has_diffs = bool(diff.column_diffs or diff.index_diffs or diff.constraint_diffs)
                if has_diffs:
                    tables_with_diffs += 1

                summaries.append(TableCompareSummary(
                    source_table=table_name,
                    target_table=table_name,
                    has_differences=has_diffs,
                    diff_count=len(diff.column_diffs) + len(diff.index_diffs) + len(diff.constraint_diffs),
                    status='success',
                ))

            except Exception as e:
                summaries.append(TableCompareSummary(
                    source_table=table_name,
                    target_table=table_name,
                    has_differences=False,
                    diff_count=0,
                    status='error',
                    error_message=str(e),
                ))

        return DatabaseCompareResponse(
            source_database=source_schema_name,
            target_database=target_schema_name,
            source_connection_name=source_conn.name,
            target_connection_name=target_conn.name,
            source_connection_id=source_conn.id,
            target_connection_id=target_conn.id,
            total_tables=len(matching_tables),
            compared_tables=len(summaries),
            tables_with_diffs=tables_with_diffs,
            table_summaries=summaries,
            excluded_tables=excluded_tables,
            unmatched_source_tables=unmatched_source,
            unmatched_target_tables=unmatched_target,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare databases: {str(e)}",
        )
    finally:
        source_adapter.disconnect()
        target_adapter.disconnect()
