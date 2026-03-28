"""APScheduler store configuration.

This module provides SQLAlchemy job store configuration for APScheduler.
The job store persists scheduled jobs to the database, allowing tasks
to survive application restarts.
"""

from typing import Optional, Dict

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os


def get_jobstores(database_url: Optional[str] = None) -> Dict[str, SQLAlchemyJobStore]:
    """Get APScheduler job stores configuration.

    Args:
        database_url: Optional database URL. If not provided, uses DATABASE_URL env var.

    Returns:
        Dictionary of job store configurations
    """
    db_url = database_url or os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://localhost/gsd_db_compare"
    )
    # APScheduler's SQLAlchemyJobStore requires sync URL
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    return {
        "default": SQLAlchemyJobStore(url=sync_url)
    }


def get_executors() -> dict:
    """Get APScheduler executor configuration.

    Returns:
        Dictionary of executor configurations
    """
    from apscheduler.executors.asyncio import AsyncIOExecutor

    return {
        "default": AsyncIOExecutor()
    }
