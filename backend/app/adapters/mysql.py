"""MySQL database adapter implementation."""

from typing import Any, Optional

import mysql.connector
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.adapters.base import DatabaseAdapter


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter for metadata extraction.

    Uses mysql-connector-python for connections and SQLAlchemy for metadata reflection.
    """

    def __init__(self, connection_config: dict):
        """Initialize MySQL adapter.

        Args:
            connection_config: Dict with host, port, database, username, password
        """
        super().__init__(connection_config)
        self._engine: Optional[Engine] = None

    def _get_connection_string(self) -> str:
        """Build MySQL connection string."""
        return (
            f"mysql+mysqlconnector://{self.config['username']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )

    def connect(self) -> Any:
        """Establish MySQL connection using mysql-connector.

        Returns:
            mysql.connector.connection.MySQLConnection
        """
        self._connection = mysql.connector.connect(
            host=self.config['host'],
            port=self.config['port'],
            database=self.config['database'],
            user=self.config['username'],
            password=self.config['password'],
        )
        return self._connection

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(self._get_connection_string())
        return self._engine

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def test_connection(self) -> bool:
        """Test if MySQL connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
        finally:
            self.disconnect()

    def get_tables(self, schema: str = None) -> list[dict]:
        """List all tables in the database.

        Queries information_schema.TABLES for table metadata.

        Args:
            schema: Optional schema name to filter tables. If None, uses connection database.

        Returns:
            List of dicts with table_name, table_type, row_count, create_time, schema
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor(dictionary=True)
        query = """
            SELECT
                TABLE_NAME as table_name,
                TABLE_TYPE as table_type,
                TABLE_ROWS as row_count,
                CREATE_TIME as create_time,
                TABLE_SCHEMA as schema_name
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """
        # Use provided schema or fall back to connection database
        schema_name = schema if schema is not None else self.config['database']
        cursor.execute(query, (schema_name,))
        tables = cursor.fetchall()
        cursor.close()
        return tables

    def get_schemas(self) -> list[dict]:
        """List all databases (schemas) accessible to the user.

        Queries information_schema.SCHEMATA.

        Returns:
            List of dicts with schema_name, charset, collation, created_time
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor(dictionary=True)
        query = """
            SELECT
                SCHEMA_NAME as schema_name,
                DEFAULT_CHARACTER_SET_NAME as charset,
                DEFAULT_COLLATION_NAME as collation,
                'N/A' as created_time
            FROM information_schema.SCHEMATA
            ORDER BY SCHEMA_NAME
        """
        cursor.execute(query)
        schemas = cursor.fetchall()
        cursor.close()
        return schemas

    def get_table_metadata(self, table_name: str) -> dict:
        """Get complete metadata for a specific table.

        Uses SQLAlchemy inspect() to reflect table structure.

        Args:
            table_name: Name of table to inspect. Can be simple name (e.g., 'users')
                        or schema-qualified name (e.g., 'db_source1.users').

        Returns:
            Dict with columns, indexes, primary_key, foreign_keys, unique_constraints
        """
        engine = self._get_engine()
        insp = inspect(engine)

        # Handle schema-qualified table names
        # SQLAlchemy's inspect needs the schema parameter for cross-schema reflection
        schema_param = None
        actual_table_name = table_name

        if '.' in table_name:
            parts = table_name.split('.', 1)
            schema_param = parts[0]
            actual_table_name = parts[1]

            # If schema matches connection database, use simple table name
            if schema_param == self.config.get('database', ''):
                schema_param = None

        metadata = {
            'table_name': table_name,
            'columns': [],
            'indexes': [],
            'primary_key': None,
            'foreign_keys': [],
            'unique_constraints': [],
        }

        # Get columns - pass schema parameter separately
        columns = insp.get_columns(actual_table_name, schema=schema_param)
        for col in columns:
            metadata['columns'].append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'default': col.get('default'),
                'comment': col.get('comment'),
            })

        # Get indexes
        indexes = insp.get_indexes(actual_table_name, schema=schema_param)
        for idx in indexes:
            metadata['indexes'].append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx.get('unique', False),
                'index_type': idx.get('type', 'BTREE'),
            })

        # Get primary key
        pk_constraint = insp.get_pk_constraint(actual_table_name, schema=schema_param)
        if pk_constraint and pk_constraint.get('constrained_columns'):
            metadata['primary_key'] = {
                'name': pk_constraint.get('name', 'PRIMARY'),
                'columns': pk_constraint['constrained_columns'],
            }

        # Get foreign keys
        fkeys = insp.get_foreign_keys(actual_table_name, schema=schema_param)
        for fk in fkeys:
            metadata['foreign_keys'].append({
                'name': fk.get('name'),
                'columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns'],
                'ondelete': fk.get('options', {}).get('ondelete'),
            })

        # Get unique constraints
        unique_constraints = insp.get_unique_constraints(actual_table_name, schema=schema_param)
        for uc in unique_constraints:
            metadata['unique_constraints'].append({
                'name': uc.get('name'),
                'columns': uc.get('column_names', []),
            })

        return metadata

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
