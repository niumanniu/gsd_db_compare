"""Initial schema - db_connections, comparison_tasks

Revision ID: 001
Revises:
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema with db_connections and comparison_tasks tables."""

    # Create db_connections table (no dependencies)
    op.create_table(
        'db_connections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('db_type', sa.String(50), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('password_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('name', name='uq_db_connections_name'),
    )
    op.create_index('ix_db_connections_name', 'db_connections', ['name'], unique=True)

    # Create comparison_tasks table (depends on db_connections)
    op.create_table(
        'comparison_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('source_connection_id', sa.Integer(), sa.ForeignKey('db_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_connection_id', sa.Integer(), sa.ForeignKey('db_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_table', sa.String(255), nullable=False),
        sa.Column('target_table', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for comparison_tasks
    op.create_index('ix_comparison_task_status', 'comparison_tasks', ['status'])
    op.create_index('ix_comparison_task_created_at', 'comparison_tasks', ['created_at'])
    op.create_index('ix_comparison_task_source_conn', 'comparison_tasks', ['source_connection_id'])
    op.create_index('ix_comparison_task_target_conn', 'comparison_tasks', ['target_connection_id'])


def downgrade() -> None:
    """Drop tables in reverse order."""
    op.drop_index('ix_comparison_task_target_conn', table_name='comparison_tasks')
    op.drop_index('ix_comparison_task_source_conn', table_name='comparison_tasks')
    op.drop_index('ix_comparison_task_created_at', table_name='comparison_tasks')
    op.drop_index('ix_comparison_task_status', table_name='comparison_tasks')
    op.drop_table('comparison_tasks')

    op.drop_index('ix_db_connections_name', table_name='db_connections')
    op.drop_table('db_connections')
