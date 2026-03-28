---
phase: 02-multi-database-support
plan: 03
type: execute
wave: 2
depends_on: ["01-PLAN"]
files_modified:
  - backend/app/comparison/schema.py
  - backend/app/adapters/mysql.py
  - backend/app/adapters/oracle.py
autonomous: true
requirements:
  - COMPARE-01
  - COMPARE-02

must_haves:
  truths:
    - "SchemaComparator handles database-specific type normalization"
    - "MySQL vs MySQL comparison works correctly"
    - "Oracle vs Oracle comparison works correctly"
    - "Type mapping infrastructure exists for future cross-database comparison"
  artifacts:
    - path: backend/app/comparison/schema.py
      provides: Enhanced schema comparison
      contains: "class SchemaComparator", "_normalize_type"
    - path: backend/app/comparison/type_mapping.py
      provides: Cross-database type mapping
      contains: "DATABASE_TYPE_MAP", "normalize_database_type"
  key_links:
    - from: backend/app/comparison/schema.py
      to: backend/app/comparison/type_mapping.py
      via: "Type normalization utilities"
      pattern: "import type_mapping"
---

<objective>
Enhance MySQL comparison and prepare for cross-database comparison.

Purpose: Improve comparison accuracy and add type mapping infrastructure for future MySQL vs Oracle comparison.
Output: Enhanced SchemaComparator with database-aware type handling.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-multi-database-support/CONTEXT.md (Key Decisions - Comparison Scenarios)
@.planning/phases/01-foundation/1-CONTEXT.md (D-4: Schema Comparison Algorithm)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create database type mapping module</name>
  <files>backend/app/comparison/type_mapping.py</files>
  <read_first>
    - .planning/phases/02-multi-database-support/CONTEXT.md (Cross-database type mapping research need)
  </read_first>
  <action>
    Create backend/app/comparison/type_mapping.py for future cross-database comparison:

    ```python
    """Database type mappings for cross-database comparison.

    Note: Full cross-database comparison deferred to later phase.
    This module provides infrastructure for type normalization.
    """

    # MySQL base types
    MYSQL_TYPES = {
        'tinyint', 'smallint', 'mediumint', 'int', 'integer', 'bigint',
        'bit', 'decimal', 'numeric', 'float', 'double', 'real',
        'date', 'time', 'datetime', 'timestamp', 'year',
        'char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext',
        'binary', 'varbinary', 'tinyblob', 'blob', 'mediumblob', 'longblob',
        'enum', 'set', 'json', 'geometry', 'point', 'linestring', 'polygon',
    }

    # Oracle base types
    ORACLE_TYPES = {
        'char', 'nchar', 'varchar2', 'nvarchar2',
        'number', 'float', 'binary_float', 'binary_double',
        'date', 'timestamp', 'timestamp with time zone', 'timestamp with local time zone',
        'interval year to month', 'interval day to second',
        'clob', 'nclob', 'blob', 'bfile', 'long', 'long raw', 'raw', 'rowid', 'urowid', 'xmltype',
    }

    # Common canonical types for comparison
    CANONICAL_TYPES = {
        # Integer types
        'tinyint': 'integer', 'smallint': 'integer', 'mediumint': 'integer',
        'int': 'integer', 'integer': 'integer', 'bigint': 'integer',
        'number': 'integer',  # Oracle NUMBER without precision/scale

        # Decimal/numeric types
        'decimal': 'decimal', 'numeric': 'decimal',
        'float': 'float', 'double': 'float', 'real': 'float',
        'binary_float': 'float', 'binary_double': 'float',

        # String types
        'char': 'char', 'nchar': 'char', 'varchar': 'string', 'varchar2': 'string',
        'nvarchar2': 'string', 'tinytext': 'string', 'text': 'string',
        'mediumtext': 'string', 'longtext': 'string', 'clob': 'string', 'nclob': 'string',

        # Date/time types
        'date': 'datetime', 'datetime': 'datetime', 'timestamp': 'datetime',
        'time': 'datetime', 'year': 'datetime',

        # Binary types
        'binary': 'binary', 'varbinary': 'binary', 'blob': 'binary',
        'tinyblob': 'binary', 'mediumblob': 'binary', 'longblob': 'binary',
        'bfile': 'binary', 'long': 'binary', 'raw': 'binary',

        # Special types
        'json': 'json', 'xmltype': 'json', 'enum': 'enum', 'set': 'set',
        'geometry': 'spatial', 'point': 'spatial', 'linestring': 'spatial',
    }

    def normalize_database_type(type_str: str, db_type: str = 'mysql') -> str:
        """Normalize database type to canonical form.

        Args:
            type_str: Database-specific type string (e.g., 'VARCHAR(255)', 'NUMBER(10,2)')
            db_type: Database type ('mysql' or 'oracle')

        Returns:
            Canonical type string for comparison
        """
        if not type_str:
            return 'unknown'

        # Extract base type (remove precision/scale)
        type_str = type_str.lower().strip()
        if '(' in type_str:
            base_type = type_str.split('(')[0]
        else:
            base_type = type_str

        # Map to canonical type
        return CANONICAL_TYPES.get(base_type, base_type)
    ```
  </action>
  <acceptance_criteria>
    - backend/app/comparison/type_mapping.py exists
    - File contains MYSQL_TYPES set
    - File contains ORACLE_TYPES set
    - File contains CANONICAL_TYPES mapping
    - normalize_database_type() function works correctly
  </acceptance_criteria>
  <verify>
    <automated>grep -E "MYSQL_TYPES|ORACLE_TYPES|CANONICAL_TYPES|def normalize_database_type" backend/app/comparison/type_mapping.py</automated>
  </verify>
  <done>Database type mapping module created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Enhance SchemaComparator with database awareness</name>
  <files>backend/app/comparison/schema.py</files>
  <read_first>
    - backend/app/comparison/schema.py (current implementation)
    - backend/app/comparison/type_mapping.py (created in Task 1)
  </read_first>
  <action>
    Enhance backend/app/comparison/schema.py:

    1. Add database type parameters to SchemaComparator:
       ```python
       class SchemaComparator:
           def __init__(
               self,
               source_db_type: str = 'mysql',
               target_db_type: str = 'mysql',
           ):
               self.source_db_type = source_db_type
               self.target_db_type = target_db_type
               self.same_db_type = source_db_type == target_db_type
       ```

    2. Update compare() method to accept database types:
       ```python
       def compare(
           self,
           source_metadata: dict,
           target_metadata: dict,
           source_db_type: str | None = None,
           target_db_type: str | None = None,
       ) -> SchemaDiff:
           # Use instance defaults or provided values
           source_db_type = source_db_type or self.source_db_type
           target_db_type = target_db_type or self.target_db_type
       ```

    3. Update _compare_column_definitions() for same-database comparison:
       - When source_db_type == target_db_type: Use strict comparison (current behavior)
       - When different: Use canonical type comparison (for future cross-database)

    4. Add database-specific normalization in _normalize_type():
       ```python
       def _normalize_type(self, type_str: str, db_type: str = 'mysql') -> str:
           from app.comparison.type_mapping import normalize_database_type
           return normalize_database_type(type_str, db_type)
       ```
  </action>
  <acceptance_criteria>
    - SchemaComparator accepts source_db_type and target_db_type parameters
    - compare() method can handle different database types
    - _normalize_type() uses type_mapping module
    - Same-database comparison uses strict type matching
    - Different-database comparison uses canonical type matching
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class SchemaComparator|def compare\(|def _normalize_type" backend/app/comparison/schema.py</automated>
  </verify>
  <done>SchemaComparator enhanced with database awareness</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Update MySQL and Oracle adapters to return database type</name>
  <files>backend/app/adapters/mysql.py, backend/app/adapters/oracle.py</files>
  <read_first>
    - backend/app/adapters/mysql.py
    - backend/app/adapters/oracle.py
  </read_first>
  <action>
    Add get_database_type() method to both adapters:

    1. Update backend/app/adapters/mysql.py:
       ```python
       def get_database_type(self) -> str:
           """Return database type identifier."""
           return 'mysql'

       def get_database_version(self) -> str:
           """Return database version string."""
           if not self._connection:
               self.connect()
           cursor = self._connection.cursor()
           cursor.execute("SELECT VERSION()")
           version = cursor.fetchone()[0]
           cursor.close()
           return version
       ```

    2. Update backend/app/adapters/oracle.py:
       ```python
       def get_database_type(self) -> str:
           """Return database type identifier."""
           return 'oracle'

       def get_database_version(self) -> str:
           """Return database version string."""
           if not self._connection:
               self.connect()
           cursor = self._connection.cursor()
           cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
           version = cursor.fetchone()[0]
           cursor.close()
           return version
       ```

    3. Add get_database_type() to DatabaseAdapter base class as abstract method
  </action>
  <acceptance_criteria>
    - MySQLAdapter has get_database_type() returning 'mysql'
    - MySQLAdapter has get_database_version() method
    - OracleAdapter has get_database_type() returning 'oracle'
    - OracleAdapter has get_database_version() method
    - DatabaseAdapter base class includes abstract get_database_type()
  </acceptance_criteria>
  <verify>
    <automated>grep -E "def get_database_type|def get_database_version" backend/app/adapters/mysql.py backend/app/adapters/oracle.py backend/app/adapters/base.py</automated>
  </verify>
  <done>Adapters return database type and version information</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Update comparison API to use enhanced comparator</name>
  <files>backend/app/api/compare.py, backend/app/worker.py</files>
  <read_first>
    - backend/app/api/compare.py (current implementation)
    - backend/app/worker.py (current implementation)
  </read_first>
  <action>
    Update both comparison entry points to use enhanced SchemaComparator:

    1. Update backend/app/api/compare.py:
       - Get database types from adapters before comparison
       - Pass database types to SchemaComparator
       ```python
       source_adapter = get_adapter(source_conn.db_type, source_config)
       target_adapter = get_adapter(target_conn.db_type, target_config)

       comparator = SchemaComparator(
           source_db_type=source_conn.db_type,
           target_db_type=target_conn.db_type,
       )
       ```

    2. Update backend/app/worker.py:
       - Same changes for Celery task
       - Pass database types from connection records

    3. Update SchemaDiffResponse to include database type info:
       - Add source_db_type, target_db_type fields
       - Add comparison_mode field ('same-database' or 'cross-database')
  </action>
  <acceptance_criteria>
    - compare.py uses database-aware SchemaComparator
    - worker.py uses database-aware SchemaComparator
    - SchemaDiffResponse includes database type information
    - API returns comparison_mode in response
  </acceptance_criteria>
  <verify>
    <automated>grep -E "SchemaComparator|source_db_type|target_db_type" backend/app/api/compare.py backend/app/worker.py</automated>
  </verify>
  <done>Comparison API updated for database-aware comparison</done>
</task>

</tasks>

<verification>
- SchemaComparator correctly handles same-database comparison
- Type mapping module ready for cross-database comparison
- Adapters return correct database type identifiers
- API responses include database type metadata
</verification>

<success_criteria>
- MySQL vs MySQL comparison works with strict type matching
- Oracle vs Oracle comparison works with strict type matching
- Cross-database comparison infrastructure in place (activated in future phase)
- Type mapping module provides accurate canonical type conversions
</success_criteria>

<output>
After completion, create `.planning/phases/02-multi-database-support/02-multi-database-support-03-SUMMARY.md` with:
- Type mapping decisions made
- Comparison mode behavior
- Any type normalization edge cases discovered
</output>
