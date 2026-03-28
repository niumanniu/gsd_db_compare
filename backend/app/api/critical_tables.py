"""API endpoints for critical table management."""

from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.db.models import CriticalTable, DbConnection
from app.schemas.critical_tables import (
    CriticalTableCreate,
    CriticalTableResponse,
    CriticalTableCheckResponse,
)

router = APIRouter(prefix="/api/critical-tables", tags=["critical-tables"])


@router.post("", response_model=CriticalTableResponse, status_code=201)
async def mark_critical_table(
    table_data: CriticalTableCreate,
    db: AsyncSession = Depends(get_db_session),
) -> CriticalTableResponse:
    """Mark a table as critical.

    Args:
        table_data: Table marking data
        db: Database session

    Returns:
        Created critical table record
    """
    # Verify connection exists
    result = await db.execute(
        select(DbConnection).where(DbConnection.id == table_data.connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection {table_data.connection_id} not found",
        )

    # Check if already marked
    existing = await db.execute(
        select(CriticalTable).where(
            CriticalTable.connection_id == table_data.connection_id,
            CriticalTable.table_name == table_data.table_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table '{table_data.table_name}' is already marked as critical",
        )

    # Create record
    critical_table = CriticalTable(
        connection_id=table_data.connection_id,
        table_name=table_data.table_name,
        description=table_data.description,
    )

    db.add(critical_table)
    await db.commit()
    await db.refresh(critical_table)

    return critical_table


@router.delete("/{table_id}", status_code=204)
async def unmark_critical_table(
    table_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Remove critical table marker.

    Args:
        table_id: Critical table ID
        db: Database session
    """
    result = await db.execute(
        select(CriticalTable).where(CriticalTable.id == table_id)
    )
    table = result.scalar_one_or_none()

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Critical table {table_id} not found",
        )

    await db.delete(table)
    await db.commit()


@router.get("", response_model=List[CriticalTableResponse])
async def list_critical_tables(
    connection_id: int = Query(..., description="Connection ID to filter by"),
    db: AsyncSession = Depends(get_db_session),
) -> List[CriticalTableResponse]:
    """List critical tables for a connection.

    Args:
        connection_id: Connection ID
        db: Database session

    Returns:
        List of critical tables
    """
    result = await db.execute(
        select(CriticalTable)
        .where(CriticalTable.connection_id == connection_id)
        .order_by(CriticalTable.table_name)
    )
    return result.scalars().all()


@router.get("/check", response_model=CriticalTableCheckResponse)
async def check_critical_table(
    connection_id: int = Query(...),
    table_name: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> CriticalTableCheckResponse:
    """Check if a table is marked as critical.

    Args:
        connection_id: Connection ID
        table_name: Table name
        db: Database session

    Returns:
        Check result
    """
    result = await db.execute(
        select(CriticalTable).where(
            CriticalTable.connection_id == connection_id,
            CriticalTable.table_name == table_name,
        )
    )
    table = result.scalar_one_or_none()

    return CriticalTableCheckResponse(
        is_critical=table is not None,
        table_name=table_name,
        connection_id=connection_id,
    )
