---
phase: 02-multi-database-support
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/adapters/oracle.py
  - backend/pyproject.toml
autonomous: true
requirements:
  - MULTI-DB-01
  - MULTI-DB-02

must_haves:
  truths:
    - "oracledb package added to dependencies"
    - "OracleAdapter inherits from DatabaseAdapter"
    - "OracleAdapter implements all abstract methods"
  artifacts:
    - path: backend/app/adapters/oracle.py
      provides: Oracle database adapter
      contains: "class OracleAdapter", "get_tables", "get_table_metadata"
  key_links:
    - from: backend/app/adapters/oracle.py
      to: backend/app/adapters/base.py
      via: "Inherits DatabaseAdapter"
      pattern: "class OracleAdapter(DatabaseAdapter)"
---

<objective>
Implement Oracle database adapter for metadata extraction.

Purpose: Enable connection to Oracle databases and fetch table/column/index/constraint metadata using oracledb driver.
Output: OracleAdapter implementation matching MySQLAdapter interface.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-multi-database-support/CONTEXT.md
@.planning/phases/01-foundation/1-CONTEXT.md (D-2: Database Adapter Pattern)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add oracledb dependency to project</name>
  <files>backend/pyproject.toml</files>
  <read_first>
    - backend/pyproject.toml (current dependencies)
    - .planning/phases/02-multi-database-support/CONTEXT.md (Technical Implications - Dependencies)
  </read_first>
  <action>
    Update backend/pyproject.toml to add Oracle support:

    1. Add oracledb dependency:
       - oracledb>=2.0 (Oracle's official Python driver)
       - Pure Python implementation, no Oracle Instant Client required for Basic Client mode

    2. Add optional dependencies for report generation (Phase 2 Wave 2):
       - Jinja2>=3.1 (HTML templating)
       - openpyxl>=3.1 (Excel .xlsx writing)

    3. Update dependencies section:
       ```toml
       [tool.poetry.dependencies]
       oracledb = "^2.0"
       Jinja2 = "^3.1"
       openpyxl = "^3.1"
       ```
  </action>
  <acceptance_criteria>
    - backend/pyproject.toml contains oracledb dependency
    - backend/pyproject.toml contains Jinja2 dependency
    - backend/pyproject.toml contains openpyxl dependency
  </acceptance_criteria>
  <verify>
    <automated>grep -E "oracledb|Jinja2|openpyxl" backend/pyproject.toml</automated>
  </verify>
  <done>Oracle and report generation dependencies added</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create OracleAdapter implementation</name>
  <files>backend/app/adapters/oracle.py</files>
  <read_first>
    - backend/app/adapters/base.py (abstract base class)
    - backend/app/adapters/mysql.py (reference implementation)
    - .planning/phases/02-multi-database-support/CONTEXT.md (Oracle metadata queries)
  </read_first>
  <action>
    Create backend/app/adapters/oracle.py with OracleAdapter:

    1. Import oracledb:
       ```python
       import oracledb
       from sqlalchemy import create_engine, inspect
       from app.adapters.base import DatabaseAdapter
       ```

    2. Implement __init__ and connection handling:
       - Support both Thick mode (requires Oracle client) and Thin mode (pure Python)
       - Default to Thin mode for simplicity

    3. Implement _get_connection_string():
       - Build Oracle DSN: host:port/service_name or host:port/SID
       - Return SQLAlchemy-compatible connection string

    4. Implement connect():
       - Use oracledb.connect() with config
       - Support config keys: host, port, database (service_name), username, password

    5. Implement test_connection():
       - Try SELECT 1 FROM DUAL
       - Return True/False

    6. Implement get_tables():
       - Query ALL_TABLES or USER_TABLES
       - Return {table_name, table_type, row_count (NUM_ROWS), create_time}

    7. Implement get_table_metadata():
       - Use SQLAlchemy inspect() for columns, indexes, constraints
       - Oracle-specific metadata queries:
         - Columns: ALL_TAB_COLUMNS
         - Comments: ALL_COL_COMMENTS
         - Indexes: ALL_INDEXES, ALL_IND_COLUMNS
         - Constraints: ALL_CONSTRAINTS, ALL_CONS_COLUMNS
         - Primary keys: ALL_CONSTRAINTS where CONSTRAINT_TYPE='P'
         - Foreign keys: ALL_CONSTRAINTS where CONSTRAINT_TYPE='R'
         - Unique constraints: ALL_CONSTRAINTS where CONSTRAINT_TYPE='U'
  </action>
  <acceptance_criteria>
    - backend/app/adapters/oracle.py exists
    - File contains "class OracleAdapter(DatabaseAdapter)"
    - All abstract methods implemented: connect, disconnect, get_tables, get_table_metadata, test_connection
    - Oracle queries use ALL_* system views
    - Returns same metadata format as MySQLAdapter
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class OracleAdapter|def (connect|get_tables|get_table_metadata|test_connection|disconnect)" backend/app/adapters/oracle.py</automated>
  </verify>
  <done>OracleAdapter implemented with all metadata extraction methods</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Add adapter factory for runtime selection</name>
  <files>backend/app/adapters/__init__.py</files>
  <read_first>
    - backend/app/adapters/__init__.py (current exports)
    - backend/app/adapters/base.py
  </read_first>
  <action>
    Update backend/app/adapters/__init__.py to provide factory function:

    ```python
    from app.adapters.base import DatabaseAdapter
    from app.adapters.mysql import MySQLAdapter
    from app.adapters.oracle import OracleAdapter

    def get_adapter(db_type: str, connection_config: dict) -> DatabaseAdapter:
        """Factory function to get appropriate adapter for database type.

        Args:
            db_type: Database type ('mysql' or 'oracle')
            connection_config: Connection configuration dict

        Returns:
            DatabaseAdapter instance

        Raises:
            ValueError: If db_type not supported
        """
        adapters = {
            'mysql': MySQLAdapter,
            'oracle': OracleAdapter,
        }

        if db_type not in adapters:
            raise ValueError(f"Unsupported database type: {db_type}")

        return adapters[db_type](connection_config)
    ```
  </action>
  <acceptance_criteria>
    - backend/app/adapters/__init__.py exports get_adapter factory
    - Factory returns correct adapter based on db_type
    - Factory raises ValueError for unsupported types
  </acceptance_criteria>
  <verify>
    <automated>grep "def get_adapter" backend/app/adapters/__init__.py</automated>
  </verify>
  <done>Adapter factory created for runtime adapter selection</done>
</task>

</tasks>

<verification>
- OracleAdapter can be instantiated
- OracleAdapter methods match MySQLAdapter interface
- Factory function returns correct adapter type
- pyproject.toml has all required dependencies
</verification>

<success_criteria>
- backend/app/adapters/oracle.py contains working OracleAdapter
- Oracle adapter returns metadata in same format as MySQL
- Adapter factory enables runtime adapter selection
- Dependencies ready for report generation in Wave 2
</success_criteria>

<output>
After completion, create `.planning/phases/02-multi-database-support/02-multi-database-support-01-SUMMARY.md` with:
- OracleAdapter implementation details
- Oracle metadata query mappings used
- Any Oracle-specific considerations discovered
</output>
