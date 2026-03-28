---
phase: 01-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/pyproject.toml
  - backend/app/db/base.py
  - backend/app/db/session.py
  - backend/app/db/models.py
  - backend/alembic/versions/001_initial_schema.py
autonomous: true
requirements:
  - CONN-01
  - CONN-02
  - SCHEMA-01
user_setup: []

must_haves:
  truths:
    - "Database tables exist for db_connections, comparison_tasks"
    - "Each table has correct fields per requirements"
    - "Foreign key relationships are properly defined"
  artifacts:
    - path: backend/app/db/models.py
      provides: SQLAlchemy ORM models
      contains: "class DbConnection", "class ComparisonTask"
    - path: backend/alembic/versions/001_initial_schema.py
      provides: Database migration
      contains: "upgrade()", "downgrade()"
  key_links:
    - from: backend/app/db/models.py
      to: backend/app/db/base.py
      via: "SQLAlchemy import"
      pattern: "from sqlalchemy"
---

<objective>
Create database schema and ORM models for Phase 1 core entities.

Purpose: Foundation for all connection management and comparison task tracking.
Output: SQLAlchemy models, Alembic migration, database initialized.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md
@.planning/phases/01-foundation/1-RESEARCH.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Set up backend project dependencies and database foundation</name>
  <files>backend/pyproject.toml, backend/app/db/base.py, backend/app/db/session.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-RESEARCH.md (Standard Stack section)
    - .planning/phases/01-foundation/1-CONTEXT.md (T-3: FastAPI Project Structure)
  </read_first>
  <action>
    Create backend project structure:
    1. Create backend/pyproject.toml with dependencies:
       - fastapi>=0.115,<0.130
       - uvicorn[standard]>=0.30
       - pydantic>=2.0
       - pydantic-settings>=2.0
       - sqlalchemy>=2.0
       - psycopg2-binary>=2.9
       - mysql-connector-python>=8.0
       - alembic>=1.12
       - celery[redis]>=5.4
       - redis>=5.0
       - cryptography>=42.0
       - structlog>=24.0
    2. Create directory structure:
       - backend/app/__init__.py
       - backend/app/db/__init__.py
       - backend/app/db/base.py
       - backend/app/db/session.py
       - backend/alembic/versions/
       - backend/alembic/env.py
       - backend/alembic.ini
    3. Create backend/app/db/base.py with:
       - SQLAlchemy Base = declarative_base()
       - Base class with id, created_at, updated_at mixin
    4. Create backend/app/db/session.py with:
       - create_async_engine for PostgreSQL
       - async_sessionmaker factory
       - get_db_session dependency for FastAPI
    5. Run alembic init to initialize migration structure
  </action>
  <acceptance_criteria>
    - backend/pyproject.toml exists and contains "fastapi", "sqlalchemy", "psycopg2-binary", "alembic", "celery"
    - backend/app/db/base.py exists and contains "declarative_base"
    - backend/app/db/session.py exists and contains "create_async_engine", "async_sessionmaker"
    - backend/alembic.ini exists
    - backend/alembic/env.py exists and contains "target_metadata = Base.metadata"
  </acceptance_criteria>
  <verify>
    <automated>ls backend/pyproject.toml backend/app/db/base.py backend/app/db/session.py backend/alembic.ini backend/alembic/env.py 2>&1 | head -5</automated>
  </verify>
  <done>All database foundation files created, dependencies defined in pyproject.toml</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create SQLAlchemy ORM models for connections and tasks</name>
  <files>backend/app/db/models.py</files>
  <read_first>
    - backend/app/db/base.py (created in Task 1)
    - .planning/research/ARCHITECTURE.md (Application Data Storage section)
    - .planning/phases/01-foundation/1-CONTEXT.md (D-8: Credential Security)
  </read_first>
  <action>
    Create backend/app/db/models.py with two ORM models:

    1. DbConnection model (per ARCHITECTURE.md):
       - id: Integer, primary_key=True
       - name: String(255), nullable=False
       - db_type: String(50), nullable=False (values: "mysql", "oracle")
       - host: String(255), nullable=False
       - port: Integer, nullable=False
       - database: String(255), nullable=False
       - username: String(255), nullable=False
       - password_encrypted: LargeBinary, nullable=False
       - created_at: DateTime, default=datetime.utcnow
       - updated_at: DateTime, onupdate=datetime.utcnow

    2. ComparisonTask model:
       - id: Integer, primary_key=True
       - task_type: String(50), nullable=False (values: "schema", "data")
       - source_connection_id: Integer, ForeignKey("db_connections.id")
       - target_connection_id: Integer, ForeignKey("db_connections.id")
       - source_table: String(255), nullable=False
       - target_table: String(255), nullable=False
       - status: String(50), default="pending" (values: "pending", "running", "completed", "failed")
       - result: JSONB, nullable=True
       - error_message: Text, nullable=True
       - started_at: DateTime, nullable=True
       - completed_at: DateTime, nullable=True
       - created_at: DateTime, default=datetime.utcnow
  </action>
  <acceptance_criteria>
    - backend/app/db/models.py exists
    - File contains "class DbConnection(Base)"
    - File contains "class ComparisonTask(Base)"
    - DbConnection has name, db_type, host, port, database, username, password_encrypted fields
    - ComparisonTask has task_type, source_connection_id, target_connection_id, source_table, target_table, status, result fields
    - ComparisonTask has ForeignKey relationships to DbConnection
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class (DbConnection|ComparisonTask)\(Base\)" backend/app/db/models.py</automated>
  </verify>
  <done>ORM models created with correct fields and relationships</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create Alembic migration for initial schema</name>
  <files>backend/alembic/versions/001_initial_schema.py</files>
  <read_first>
    - backend/app/db/models.py (created in Task 2)
    - backend/alembic/env.py (created in Task 1)
  </read_first>
  <action>
    Create initial database migration:
    1. Create migration file:
       - File path: backend/alembic/versions/001_initial_schema.py
       - Revision: "001" (first migration)
       - Description: "Initial schema - db_connections, comparison_tasks"
    2. In upgrade() function, create tables in order:
       - db_connections (no dependencies)
       - comparison_tasks (depends on db_connections)
    3. Include all indexes:
       - db_connections.name (unique)
       - comparison_task.status (index)
       - comparison_task.created_at (index)
    4. Include foreign keys with ondelete behaviors:
       - comparison_tasks.source_connection_id -> db_connections.id (ondelete="CASCADE")
       - comparison_tasks.target_connection_id -> db_connections.id (ondelete="CASCADE")
    5. In downgrade() function, drop tables in reverse order:
       - comparison_tasks, db_connections
  </action>
  <acceptance_criteria>
    - backend/alembic/versions/001_initial_schema.py exists
    - File contains "def upgrade():" with create_table calls for db_connections, comparison_tasks
    - File contains "def downgrade():" with drop_table calls
    - db_connections table has name column with unique=True
    - db_connections table has db_type, host, port, database, username, password_encrypted columns
    - comparison_tasks table has task_type, status, result columns
    - Foreign keys defined with ondelete="CASCADE"
  </acceptance_criteria>
  <verify>
    <automated>grep -c "op.create_table" backend/alembic/versions/001_initial_schema.py</automated>
  </verify>
  <done>Alembic migration created with both tables, indexes, and foreign keys</done>
</task>

</tasks>

<verification>
- All models importable without errors
- Alembic migration can run upgrade and downgrade without errors
- Database schema matches requirements for connection management and task tracking
</verification>

<success_criteria>
- backend/app/db/models.py contains DbConnection, ComparisonTask models
- backend/alembic/versions/001_initial_schema.py contains migration for both tables
- Running `alembic upgrade head` creates all tables successfully
- All foreign key relationships are correctly defined
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-01-SUMMARY.md` with:
- Models created and their fields
- Migration file path
- Any schema decisions made
</output>
