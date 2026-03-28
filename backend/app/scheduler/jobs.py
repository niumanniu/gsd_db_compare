"""Scheduled comparison job definitions."""

import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScheduledTask, ComparisonHistory, DbConnection
from app.db.session import get_session_factory
from cryptography.fernet import Fernet
import os
import json

# Encryption key for decrypting passwords
_ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().encode())
_fernet = Fernet(_ENCRYPTION_KEY)


def decrypt_password(encrypted: bytes) -> str:
    """Decrypt password using Fernet symmetric encryption."""
    return _fernet.decrypt(encrypted).decode()


async def execute_scheduled_comparison(task_id: int) -> None:
    """Execute a scheduled comparison task.

    Args:
        task_id: ScheduledTask ID to execute
    """
    session_factory = get_session_factory()
    started_at = datetime.utcnow()

    async with session_factory() as session:
        try:
            # 1. Get task configuration
            result = await session.execute(
                select(ScheduledTask).where(ScheduledTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                print(f"ScheduledTask {task_id} not found")
                return

            # 2. Get connection details
            source_conn = session.get(DbConnection, task.source_connection_id)
            target_conn = session.get(DbConnection, task.target_connection_id)

            if not source_conn or not target_conn:
                raise ValueError(f"Connections not found for task {task_id}")

            # 3. Parse table mappings
            tables = json.loads(task.tables)

            # 4. Execute comparison for each table
            for table_mapping in tables:
                source_table = table_mapping["source"]
                target_table = table_mapping["target"]
                is_critical = table_mapping.get("critical", False)

                # Create history record
                history = ComparisonHistory(
                    task_id=task_id,
                    source_connection_id=task.source_connection_id,
                    target_connection_id=task.target_connection_id,
                    source_table=source_table,
                    target_table=target_table,
                    compare_mode=task.compare_mode,
                    started_at=started_at,
                    status="running",
                )
                session.add(history)
                await session.flush()

                try:
                    # 5. Execute comparison (call existing comparison logic)
                    from app.adapters import get_adapter
                    from app.comparison.schema import SchemaComparator

                    source_config = {
                        "host": source_conn.host,
                        "port": source_conn.port,
                        "database": source_conn.database,
                        "username": source_conn.username,
                        "password": decrypt_password(source_conn.password_encrypted),
                    }

                    target_config = {
                        "host": target_conn.host,
                        "port": target_conn.port,
                        "database": target_conn.database,
                        "username": target_conn.username,
                        "password": decrypt_password(target_conn.password_encrypted),
                    }

                    source_adapter = get_adapter(source_conn.db_type, source_config)
                    target_adapter = get_adapter(target_conn.db_type, target_config)

                    try:
                        # Fetch metadata
                        source_metadata = source_adapter.get_table_metadata(source_table)
                        target_metadata = target_adapter.get_table_metadata(target_table)

                        # Compare
                        comparator = SchemaComparator(
                            source_db_type=source_conn.db_type,
                            target_db_type=target_conn.db_type,
                        )
                        diff = comparator.compare(source_metadata, target_metadata)

                        # Update history record
                        history.source_row_count = source_metadata.row_count
                        history.target_row_count = target_metadata.row_count
                        history.diff_count = len(diff.column_diffs) + len(diff.index_diffs) + len(diff.constraint_diffs)
                        history.has_critical_diffs = is_critical and history.diff_count > 0
                        history.status = "completed"
                        history.result_summary = json.dumps(diff.to_dict())

                        # 6. Send notification if there are critical differences
                        if history.has_critical_diffs and task.notification_enabled:
                            await send_comparison_notification(
                                task_name=task.name,
                                source_table=source_table,
                                target_table=target_table,
                                diff_count=history.diff_count,
                                history_id=history.id,
                            )

                    finally:
                        source_adapter.disconnect()
                        target_adapter.disconnect()

                except Exception as e:
                    history.status = "failed"
                    history.error_message = str(e)
                    print(f"Comparison failed for task {task_id}: {e}")

                history.completed_at = datetime.utcnow()

            # Update task run times
            from app.scheduler.scheduler import get_scheduler_service
            scheduler = get_scheduler_service(session_factory)
            if scheduler.scheduler:
                job = scheduler.scheduler.get_job(f"scheduled_task_{task_id}")
                next_run = job.next_run_time if job else None
                await scheduler.update_task_run_time(task_id, started_at, next_run)

            await session.commit()

        except Exception as e:
            print(f"Scheduled comparison failed for task {task_id}: {e}")
            await session.rollback()


async def send_comparison_notification(
    task_name: str,
    source_table: str,
    target_table: str,
    diff_count: int,
    history_id: int,
) -> None:
    """Send email notification for critical differences.

    Args:
        task_name: Scheduled task name
        source_table: Source table name
        target_table: Source table name
        diff_count: Number of differences found
        history_id: ComparisonHistory ID for report link
    """
    from app.notifications.email import get_email_service
    from app.db.session import get_session_factory
    from sqlalchemy import select
    from app.db.models import NotificationSetting

    session_factory = get_session_factory()
    async with session_factory() as session:
        # Get notification settings
        result = await session.execute(select(NotificationSetting).limit(1))
        settings = result.scalar_one_or_none()

        if not settings:
            print("No notification settings configured, skipping email")
            return

        email_service = get_email_service(settings)

        # Generate report URL (configured via environment)
        base_url = os.environ.get("APP_BASE_URL", "http://localhost:5173")
        report_url = f"{base_url}/history/{history_id}"

        # Send alert email
        recipients = json.loads(settings.default_recipients or "[]")
        if not recipients:
            print("No recipients configured, skipping email")
            return

        subject = f"[关键表差异告警] {task_name}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-critical {{ background-color: #ffe6e6; border-left: 4px solid #ff4444; padding: 15px; }}
                .diff-summary {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .btn {{ background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="alert-critical">
                <h2>数据库差异告警</h2>
                <p><strong>任务：</strong>{task_name}</p>
                <p><strong>时间：</strong>{datetime.utcnow().isoformat()}</p>
                <p><strong>严重程度：</strong>关键</p>
            </div>

            <div class="diff-summary">
                <h3>差异摘要</h3>
                <table>
                    <tr><th>源表</th><td>{source_table}</td></tr>
                    <tr><th>目标表</th><td>{target_table}</td></tr>
                    <tr><th>差异数量</th><td>{diff_count}</td></tr>
                </table>
            </div>

            <p>
                <a href="{report_url}" class="btn">查看详细报告</a>
            </p>
        </body>
        </html>
        """

        success = await email_service.send_alert(recipients, subject, html_content)
        if not success:
            print(f"Failed to send notification email for task {task_name}")
