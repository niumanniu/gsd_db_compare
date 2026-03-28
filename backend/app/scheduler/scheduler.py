"""APScheduler service management."""

import os
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScheduledTask


class SchedulerService:
    """Service for managing scheduled comparison tasks."""

    def __init__(self, session_factory):
        """Initialize scheduler service.

        Args:
            session_factory: Async session factory for database access
        """
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.session_factory = session_factory
        self.db_url = os.environ.get(
            "DATABASE_URL", "postgresql+asyncpg://localhost/gsd_db_compare"
        )
        # Convert async URL to sync for APScheduler
        self.sync_db_url = self.db_url.replace("postgresql+asyncpg://", "postgresql://")

    def start(self) -> None:
        """Initialize and start the scheduler."""
        jobstores = {
            "default": SQLAlchemyJobStore(url=self.sync_db_url)
        }
        executors = {
            "default": AsyncIOExecutor()
        }
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone="UTC",
        )
        self.scheduler.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()

    def add_job(self, task_id: int, task_name: str, cron_expr: str) -> None:
        """Add a scheduled comparison job.

        Args:
            task_id: ScheduledTask ID
            task_name: Task name for logging
            cron_expr: Cron expression (e.g., "0 */2 * * *")
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not started")

        from app.scheduler.jobs import execute_scheduled_comparison

        # Parse cron expression: minute hour day month day_of_week
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")

        minute, hour, day, month, day_of_week = parts

        self.scheduler.add_job(
            execute_scheduled_comparison,
            trigger="cron",
            args=[task_id],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=f"scheduled_task_{task_id}",
            name=f"Scheduled comparison: {task_name}",
            replace_existing=True,
            misfire_grace_time=60,  # Allow 1 minute grace for missed runs
        )

    def remove_job(self, task_id: int) -> None:
        """Remove a scheduled job.

        Args:
            task_id: ScheduledTask ID
        """
        if not self.scheduler:
            return

        job_id = f"scheduled_task_{task_id}"
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass  # Job may not exist

    def pause_job(self, task_id: int) -> None:
        """Pause a scheduled job.

        Args:
            task_id: ScheduledTask ID
        """
        if not self.scheduler:
            return

        job_id = f"scheduled_task_{task_id}"
        try:
            self.scheduler.pause_job(job_id)
        except Exception:
            pass

    def resume_job(self, task_id: int) -> None:
        """Resume a paused job.

        Args:
            task_id: ScheduledTask ID
        """
        if not self.scheduler:
            return

        job_id = f"scheduled_task_{task_id}"
        try:
            self.scheduler.resume_job(job_id)
        except Exception:
            pass

    async def load_persisted_tasks(self) -> None:
        """Load all enabled tasks from database and add to scheduler."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ScheduledTask).where(ScheduledTask.enabled == True)
            )
            tasks = result.scalars().all()

            for task in tasks:
                try:
                    self.add_job(task.id, task.name, task.cron_expression)
                except Exception as e:
                    print(f"Failed to load task {task.id}: {e}")

    async def update_task_run_time(
        self, task_id: int, last_run_at: datetime, next_run_at: datetime
    ) -> None:
        """Update task run times in database.

        Args:
            task_id: ScheduledTask ID
            last_run_at: Last run timestamp
            next_run_at: Next scheduled run timestamp
        """
        async with self.session_factory() as session:
            await session.execute(
                update(ScheduledTask)
                .where(ScheduledTask.id == task_id)
                .values(last_run_at=last_run_at, next_run_at=next_run_at)
            )
            await session.commit()


# Global scheduler instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service(session_factory=None) -> SchedulerService:
    """Get or create scheduler service instance.

    Args:
        session_factory: Async session factory

    Returns:
        SchedulerService instance
    """
    global _scheduler_service
    if _scheduler_service is None:
        if session_factory is None:
            from app.db.session import get_session_factory
            session_factory = get_session_factory()
        _scheduler_service = SchedulerService(session_factory)
    return _scheduler_service
