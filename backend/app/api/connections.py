"""Connection management API endpoints."""

import os
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet

from app.db.session import get_db_session
from app.db.models import DbConnection
from app.schemas.api import (
    ConnectionCreate,
    ConnectionResponse,
    TableInfo,
    ConnectionTestRequest,
    ConnectionTestResponse,
    SchemaInfo,
)
from app.adapters.mysql import MySQLAdapter

router = APIRouter(prefix="/api/connections", tags=["connections"])

# Load encryption key from environment variable
_ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "").encode()
if not _ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY environment variable not set")
_fernet = Fernet(_ENCRYPTION_KEY)


def encrypt_password(password: str) -> bytes:
    """Encrypt password using Fernet symmetric encryption."""
    return _fernet.encrypt(password.encode())


def decrypt_password(encrypted: bytes) -> str:
    """Decrypt password using Fernet symmetric encryption."""
    return _fernet.decrypt(encrypted).decode()


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection_data: ConnectionCreate,
    db: AsyncSession = Depends(get_db_session),
) -> DbConnection:
    """Create a new database connection.

    - Tests connection to database
    - Encrypts password before storing
    - Saves connection configuration
    """
    # Test connection first
    test_config = {
        'host': connection_data.host,
        'port': connection_data.port,
        'database': connection_data.database,
        'username': connection_data.username,
        'password': connection_data.password,
    }

    adapter = MySQLAdapter(test_config)
    if not adapter.test_connection():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to database. Please check connection parameters.",
        )

    # Check for duplicate name
    result = await db.execute(
        select(DbConnection).where(DbConnection.name == connection_data.name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection with name '{connection_data.name}' already exists",
        )

    # Create connection with encrypted password
    db_connection = DbConnection(
        name=connection_data.name,
        db_type=connection_data.db_type,
        host=connection_data.host,
        port=connection_data.port,
        database=connection_data.database,
        username=connection_data.username,
        password_encrypted=encrypt_password(connection_data.password),
    )

    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)

    return db_connection


@router.get("", response_model=List[ConnectionResponse])
async def list_connections(
    db: AsyncSession = Depends(get_db_session),
) -> List[DbConnection]:
    """List all saved database connections."""
    result = await db.execute(select(DbConnection).order_by(DbConnection.name))
    connections = result.scalars().all()
    return list(connections)


@router.get("/{conn_id}", response_model=ConnectionResponse)
async def get_connection(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> DbConnection:
    """Get a specific database connection by ID."""
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {conn_id} not found",
        )

    return connection


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a database connection."""
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {conn_id} not found",
        )

    await db.delete(connection)
    await db.commit()


@router.get("/{conn_id}/tables", response_model=List[TableInfo])
async def get_connection_tables(
    conn_id: int,
    schema: str = None,
    db: AsyncSession = Depends(get_db_session),
) -> List[dict]:
    """Fetch table list from a database connection.

    Connects to the database using stored credentials and retrieves table metadata.

    Args:
        conn_id: Connection ID
        schema: Optional schema name to filter tables (for MySQL database/schema).
                If not provided or empty, uses the connection's default database.
        db: AsyncSession dependency
    """
    # Fetch connection from database
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {conn_id} not found",
        )

    # Normalize schema parameter - treat empty strings and 'undefined' as None
    if not schema or schema.lower() == 'undefined':
        schema = None

    # Create adapter with decrypted password
    config = {
        'host': connection.host,
        'port': connection.port,
        'database': connection.database,
        'username': connection.username,
        'password': decrypt_password(connection.password_encrypted),
    }

    adapter = MySQLAdapter(config)

    try:
        tables = adapter.get_tables(schema=schema)
        return tables
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tables: {str(e)}",
        )
    finally:
        adapter.disconnect()


@router.get("/{conn_id}/schemas", response_model=list[SchemaInfo])
async def get_connection_schemas(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Fetch available schemas from a database connection.

    Returns schemas (databases in MySQL, users in Oracle) that the
    connection's credentials have access to.
    """
    # Fetch connection from database
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {conn_id} not found",
        )

    # Create adapter with decrypted password
    config = {
        'host': connection.host,
        'port': connection.port,
        'database': connection.database,
        'username': connection.username,
        'password': decrypt_password(connection.password_encrypted),
    }

    # Use adapter factory
    from app.adapters import get_adapter
    adapter = get_adapter(connection.db_type, config)

    try:
        schemas = adapter.get_schemas()
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch schemas: {str(e)}",
        )
    finally:
        adapter.disconnect()


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    test_data: ConnectionTestRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionTestResponse:
    """Test database connection with provided credentials.

    Attempts to connect to the database and returns success/failure status.
    """
    config = {
        'host': test_data.host,
        'port': test_data.port,
        'database': test_data.database,
        'username': test_data.username,
        'password': test_data.password,
    }

    adapter = MySQLAdapter(config)

    try:
        if adapter.test_connection():
            return ConnectionTestResponse(
                success=True,
                message="Connection successful!"
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message="Failed to connect to database"
            )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )
    finally:
        adapter.disconnect()


@router.get("/{conn_id}/test", response_model=ConnectionTestResponse)
async def test_saved_connection(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionTestResponse:
    """Test a saved database connection using stored credentials.

    Attempts to connect to the database using decrypted credentials and returns success/failure status.
    """
    # Fetch connection from database
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection {conn_id} not found"
        )

    # Create adapter with decrypted password
    config = {
        'host': connection.host,
        'port': connection.port,
        'database': connection.database,
        'username': connection.username,
        'password': decrypt_password(connection.password_encrypted),
    }

    adapter = MySQLAdapter(config)

    try:
        if adapter.test_connection():
            return ConnectionTestResponse(
                success=True,
                message="Connection successful!"
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message="Failed to connect to database"
            )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )
    finally:
        adapter.disconnect()
