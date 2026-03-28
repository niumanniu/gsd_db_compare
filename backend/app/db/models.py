"""SQLAlchemy ORM models for database entities."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, ForeignKey, JSON, Text, Index, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, IdMixin, TimestampMixin


class DbConnection(Base, IdMixin, TimestampMixin):
    """Model for storing database connection configurations."""

    __tablename__ = "db_connections"

    name = Column(String(255), nullable=False, unique=True, index=True)
    db_type = Column(String(50), nullable=False)  # "mysql", "oracle"
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    password_encrypted = Column(LargeBinary, nullable=False)

    # Relationship to comparison tasks
    source_tasks = relationship(
        "ComparisonTask",
        foreign_keys="ComparisonTask.source_connection_id",
        back_populates="source_connection",
    )
    target_tasks = relationship(
        "ComparisonTask",
        foreign_keys="ComparisonTask.target_connection_id",
        back_populates="target_connection",
    )

    def __repr__(self) -> str:
        return f"<DbConnection(id={self.id}, name='{self.name}', db_type='{self.db_type}')>"


class ComparisonTask(Base, IdMixin, TimestampMixin):
    """Model for tracking schema/data comparison tasks."""

    __tablename__ = "comparison_tasks"

    task_type = Column(String(50), nullable=False)  # "schema", "data"
    source_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_table = Column(String(255), nullable=False)
    target_table = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    source_connection = relationship(
        "DbConnection",
        foreign_keys=[source_connection_id],
        back_populates="source_tasks",
    )
    target_connection = relationship(
        "DbConnection",
        foreign_keys=[target_connection_id],
        back_populates="target_tasks",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_comparison_task_status", "status"),
        Index("ix_comparison_task_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ComparisonTask(id={self.id}, type='{self.task_type}', status='{self.status}')>"


class ScheduledTask(Base, IdMixin, TimestampMixin):
    """Model for scheduled comparison tasks."""

    __tablename__ = "scheduled_tasks"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cron_expression = Column(String(100), nullable=False)
    source_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    tables = Column(Text, nullable=False, comment="JSON array of table mappings")
    compare_mode = Column(String(50), nullable=False, server_default="schema")
    notification_enabled = Column(Boolean, nullable=False, server_default="true")
    enabled = Column(Boolean, nullable=False, server_default="true")
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_scheduled_tasks_enabled", "enabled"),
        Index("ix_scheduled_tasks_next_run", "next_run_at"),
    )

    def __repr__(self) -> str:
        return f"<ScheduledTask(id={self.id}, name='{self.name}', cron='{self.cron_expression}')>"


class ComparisonHistory(Base, IdMixin, TimestampMixin):
    """Model for comparison history records."""

    __tablename__ = "comparison_history"

    task_id = Column(Integer, ForeignKey("scheduled_tasks.id", ondelete="SET NULL"), nullable=True)
    source_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_table = Column(String(255), nullable=False)
    target_table = Column(String(255), nullable=False)
    compare_mode = Column(String(50), nullable=False)
    source_row_count = Column(Integer, nullable=True)
    target_row_count = Column(Integer, nullable=True)
    diff_count = Column(Integer, nullable=False, server_default="0")
    diff_percentage = Column(Float, nullable=True)
    has_critical_diffs = Column(Boolean, nullable=False, server_default="false")
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True, comment="JSON summary")

    __table_args__ = (
        Index("ix_history_task_id", "task_id"),
        Index("ix_history_status", "status"),
        Index("ix_history_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ComparisonHistory(id={self.id}, task_id={self.task_id}, status='{self.status}')>"


class CriticalTable(Base, IdMixin, TimestampMixin):
    """Model for critical table markers."""

    __tablename__ = "critical_tables"

    connection_id = Column(
        Integer,
        ForeignKey("db_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_critical_conn_id", "connection_id"),
        UniqueConstraint("connection_id", "table_name", name="uq_critical_connection_table"),
    )

    def __repr__(self) -> str:
        return f"<CriticalTable(id={self.id}, connection_id={self.connection_id}, table='{self.table_name}')>"


class NotificationSetting(Base, IdMixin, TimestampMixin):
    """Model for notification settings."""

    __tablename__ = "notification_settings"

    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, server_default="587")
    smtp_username = Column(String(255), nullable=False)
    smtp_password_encrypted = Column(LargeBinary, nullable=False)
    use_tls = Column(Boolean, nullable=False, server_default="true")
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False, server_default="DB Compare")
    default_recipients = Column(Text, nullable=True, comment="JSON array of emails")

    def __repr__(self) -> str:
        return f"<NotificationSetting(id={self.id}, smtp_host='{self.smtp_host}')>"
