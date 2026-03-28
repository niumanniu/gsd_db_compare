"""Add advanced features - scheduled tasks, history, critical tables, notifications

Revision ID: 002
Revises: 001
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables for advanced features."""

    # 1. scheduled_tasks -定时任务配置
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('source_connection_id', sa.Integer(), nullable=False),
        sa.Column('target_connection_id', sa.Integer(), nullable=False),
        sa.Column('tables', sa.Text(), nullable=False, comment='JSON array: [{"source": "tbl1", "target": "tbl2", "critical": true}]'),
        sa.Column('compare_mode', sa.String(50), nullable=False, server_default='schema', comment='schema, data, both'),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['source_connection_id'], ['db_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_connection_id'], ['db_connections.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_scheduled_tasks_enabled', 'scheduled_tasks', ['enabled'])
    op.create_index('ix_scheduled_tasks_next_run', 'scheduled_tasks', ['next_run_at'])

    # 2. comparison_history - 比对历史记录
    op.create_table(
        'comparison_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Integer(), nullable=True, comment='nullable for ad-hoc comparisons'),
        sa.Column('source_connection_id', sa.Integer(), nullable=False),
        sa.Column('target_connection_id', sa.Integer(), nullable=False),
        sa.Column('source_table', sa.String(255), nullable=False),
        sa.Column('target_table', sa.String(255), nullable=False),
        sa.Column('compare_mode', sa.String(50), nullable=False, comment='schema, data, both'),
        sa.Column('source_row_count', sa.Integer(), nullable=True),
        sa.Column('target_row_count', sa.Integer(), nullable=True),
        sa.Column('diff_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('diff_percentage', sa.Float(), nullable=True),
        sa.Column('has_critical_diffs', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, comment='pending, running, completed, failed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result_summary', sa.Text(), nullable=True, comment='JSON summary'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['task_id'], ['scheduled_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_connection_id'], ['db_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_connection_id'], ['db_connections.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_history_task_id', 'comparison_history', ['task_id'])
    op.create_index('ix_history_status', 'comparison_history', ['status'])
    op.create_index('ix_history_created_at', 'comparison_history', ['created_at'])

    # 3. critical_tables - 关键表标记
    op.create_table(
        'critical_tables',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['connection_id'], ['db_connections.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('connection_id', 'table_name', name='uq_critical_connection_table'),
    )
    op.create_index('ix_critical_conn_id', 'critical_tables', ['connection_id'])

    # 4. notification_settings - 通知配置
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('smtp_host', sa.String(255), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False, server_default='587'),
        sa.Column('smtp_username', sa.String(255), nullable=False),
        sa.Column('smtp_password_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sender_email', sa.String(255), nullable=False),
        sa.Column('sender_name', sa.String(255), nullable=False, server_default='DB Compare'),
        sa.Column('default_recipients', sa.Text(), nullable=True, comment='JSON array of emails'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """Drop tables in reverse order."""
    op.drop_table('notification_settings')

    op.drop_index('ix_critical_conn_id', table_name='critical_tables')
    op.drop_table('critical_tables')

    op.drop_index('ix_history_created_at', table_name='comparison_history')
    op.drop_index('ix_history_status', table_name='comparison_history')
    op.drop_index('ix_history_task_id', table_name='comparison_history')
    op.drop_table('comparison_history')

    op.drop_index('ix_scheduled_tasks_next_run', table_name='scheduled_tasks')
    op.drop_index('ix_scheduled_tasks_enabled', table_name='scheduled_tasks')
    op.drop_table('scheduled_tasks')
