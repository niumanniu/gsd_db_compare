"""Database session and engine configuration."""

from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.db.base import Base


class DatabaseSettings:
    """Database configuration."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        self.database_url = database_url or "postgresql+asyncpg://localhost/gsd_db_compare"
        self.pool_size = pool_size
        self.max_overflow = max_overflow


# Global engine and session factory
_engine = None
_async_session_factory = None


def init_database(database_url: str) -> None:
    """Initialize database engine and session factory."""
    global _engine, _async_session_factory

    _engine = create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_engine():
    """Get the SQLAlchemy engine."""
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get the async session factory."""
    return _async_session_factory


async def get_db_session() -> AsyncSession:
    """Dependency for FastAPI - yields async db session."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
