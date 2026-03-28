"""Schema comparison API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.db.models import DbConnection
from app.schemas.api import (
    SchemaCompareRequest,
    SchemaDiffResponse,
    ColumnDiff,
    IndexDiff,
    ConstraintDiff,
)
from app.comparison.schema import SchemaComparator
from app.adapters import get_adapter

from cryptography.fernet import Fernet

router = APIRouter(prefix="/api/compare", tags=["compare"])

# Same encryption key as connections.py (in production, use shared secrets)
_ENCRYPTION_KEY = Fernet.generate_key()
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
