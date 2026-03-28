---
phase: 01-foundation
plan: 02
type: execute
wave: 1
depends_on: ["01-PLAN"]
files_modified:
  - backend/app/adapters/base.py
  - backend/app/adapters/mysql.py
  - backend/app/schemas/api.py
autonomous: true
requirements:
  - CONN-01
  - CONN-03
user_setup: []

must_haves:
  truths:
    - "MySQL adapter can connect to database"
    - "MySQL adapter can fetch table list"
    - "MySQL adapter can fetch table metadata"
  artifacts:
    - path: backend/app/adapters/mysql.py
      provides: MySQL database adapter
      contains: "class MySQLAdapter", "get_tables", "get_table_metadata"
  key_links:
    - from: backend/app/adapters/mysql.py
      to: backend/app/adapters/base.py
      via: "Inherits DatabaseAdapter"
      pattern: "class MySQLAdapter(DatabaseAdapter)"
---

<objective>
Implement MySQL database adapter for metadata extraction.

Purpose: Enable connection to MySQL databases and fetch table/column/index/constraint metadata.
Output: DatabaseAdapter ABC, MySQLAdapter implementation, connection testing.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-foundation/1-CONTEXT.md
@.planning/phases/01-foundation/1-RESEARCH.md (MySQL Metadata Queries section)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create DatabaseAdapter abstract base class</name>
  <files>backend/app/adapters/base.py</files>
  <read_first>
    - .planning/research/ARCHITECTURE.md (Database Adapter Layer)
    - .planning/phases/01-foundation/1-CONTEXT.md (D-2: Database Adapter Pattern)
  </read_first>
  <action>
    Create backend/app/adapters/base.py with abstract base class:

    ```python
    from abc import ABC, abstractmethod
    from typing import Any

    class DatabaseAdapter(ABC):
        def __init__(self, connection_config: dict):
            self.config = connection_config
            self._connection = None

        @abstractmethod
        def connect(self) -> Any:
            """Establish database connection."""
            pass

        @abstractmethod
        def disconnect(self) -> None:
            """Close database connection."""
            pass

        @abstractmethod
        def get_tables(self) -> list[dict]:
            """List all tables in database."""
            pass

        @abstractmethod
        def get_table_metadata(self, table_name: str) -> dict:
            """Get metadata for a specific table."""
            pass

        @abstractmethod
        def test_connection(self) -> bool:
            """Test if connection is working."""
            pass
    ```
  </action>
  <acceptance_criteria>
    - backend/app/adapters/base.py exists
    - File contains "class DatabaseAdapter(ABC)"
    - File contains abstract methods: connect, disconnect, get_tables, get_table_metadata, test_connection
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class DatabaseAdapter|def (connect|disconnect|get_tables|get_table_metadata|test_connection)" backend/app/adapters/base.py</automated>
  </verify>
  <done>DatabaseAdapter ABC created with all abstract methods</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Implement MySQLAdapter</name>
  <files>backend/app/adapters/mysql.py</files>
  <read_first>
    - backend/app/adapters/base.py (created in Task 1)
    - .planning/phases/01-foundation/1-RESEARCH.md (MySQL Metadata Queries)
    - .planning/phases/01-foundation/1-CONTEXT.md (T-2: SQLAlchemy Metadata Reflection)
  </read_first>
  <action>
    Create backend/app/adapters/mysql.py with MySQLAdapter implementation:

    1. Import mysql-connector-python:
       ```python
       import mysql.connector
       from sqlalchemy import create_engine, inspect
       ```

    2. Implement connect():
       - Use mysql.connector.connect() with config
       - Store connection in self._connection

    3. Implement test_connection():
       - Try to execute SELECT 1
       - Return True on success, False on exception

    4. Implement get_tables():
       - Query information_schema.TABLES
       - Return list of {table_name, table_type, row_count, create_time}

    5. Implement get_table_metadata():
       - Use SQLAlchemy inspect() to get:
         - columns (via get_columns)
         - indexes (via get_indexes)
         - primary key (via get_pk_constraint)
         - foreign keys (via get_foreign_keys)
         - unique constraints (via get_unique_constraints)
       - Return structured metadata dict
  </action>
  <acceptance_criteria>
    - backend/app/adapters/mysql.py exists
    - File contains "class MySQLAdapter(DatabaseAdapter)"
    - MySQLAdapter implements all abstract methods from DatabaseAdapter
    - get_tables() queries information_schema.TABLES
    - get_table_metadata() uses SQLAlchemy inspect()
    - get_table_metadata() returns columns, indexes, primary_key, foreign_keys, unique_constraints
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class MySQLAdapter|def (connect|get_tables|get_table_metadata|test_connection)" backend/app/adapters/mysql.py</automated>
  </verify>
  <done>MySQLAdapter implemented with all metadata extraction methods</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create Pydantic schemas for API</name>
  <files>backend/app/schemas/api.py</files>
  <read_first>
    - .planning/phases/01-foundation/1-CONTEXT.md (D-5: Diff Data Structure)
  </read_first>
  <action>
    Create backend/app/schemas/api.py with Pydantic models:

    1. Connection schemas:
       - ConnectionCreate (name, db_type, host, port, database, username, password)
       - ConnectionResponse (same + id, created_at, updated_at, password hidden)

    2. Table schemas:
       - TableInfo (table_name, table_type, row_count)
       - ColumnInfo (name, type, nullable, default, comment)
       - IndexInfo (name, columns, unique, index_type)
       - ConstraintInfo (name, type, columns, referred_table)

    3. Comparison schemas:
       - SchemaCompareRequest (source_connection_id, source_table, target_connection_id, target_table)
       - ColumnDiff (column_name, diff_type, source_definition, target_definition, differences)
       - IndexDiff (index_name, diff_type, source_definition, target_definition)
       - SchemaDiffResponse (source_table, target_table, column_diffs, index_diffs, constraint_diffs)
  </action>
  <acceptance_criteria>
    - backend/app/schemas/api.py exists
    - File contains ConnectionCreate, ConnectionResponse
    - File contains TableInfo, ColumnInfo, IndexInfo, ConstraintInfo
    - File contains SchemaCompareRequest, SchemaDiffResponse, ColumnDiff, IndexDiff
    - All schemas inherit from BaseModel
  </acceptance_criteria>
  <verify>
    <automated>grep "class.*BaseModel" backend/app/schemas/api.py</automated>
  </verify>
  <done>Pydantic schemas created for API request/response validation</done>
</task>

</tasks>

<verification>
- MySQLAdapter can connect to a test MySQL database
- MySQLAdapter.get_tables() returns table list
- MySQLAdapter.get_table_metadata() returns complete metadata
- Pydantic schemas validate correctly
</verification>

<success_criteria>
- backend/app/adapters/mysql.py contains working MySQLAdapter
- backend/app/schemas/api.py contains all API schemas
- Can fetch table list and metadata from MySQL database
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-foundation-02-SUMMARY.md` with:
- Adapter implementation details
- Any MySQL-specific considerations discovered
- Test results
</output>
