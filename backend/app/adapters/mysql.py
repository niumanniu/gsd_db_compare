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

    def get_tables(self) -> list[dict]:
        """List all tables in the database.

        Queries information_schema.TABLES for table metadata.

        Returns:
            List of dicts with table_name, table_type, row_count, create_time
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor(dictionary=True)
        query = """
            SELECT
                TABLE_NAME as table_name,
                TABLE_TYPE as table_type,
                TABLE_ROWS as row_count,
                CREATE_TIME as create_time
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """
        cursor.execute(query, (self.config['database'],))
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
            table_name: Name of table to inspect

        Returns:
            Dict with columns, indexes, primary_key, foreign_keys, unique_constraints
        """
        engine = self._get_engine()
        insp = inspect(engine)

        metadata = {
            'table_name': table_name,
            'columns': [],
            'indexes': [],
            'primary_key': None,
            'foreign_keys': [],
            'unique_constraints': [],
        }

        # Get columns
        columns = insp.get_columns(table_name)
        for col in columns:
            metadata['columns'].append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'default': col.get('default'),
                'comment': col.get('comment'),
            })

        # Get indexes
        indexes = insp.get_indexes(table_name)
        for idx in indexes:
            metadata['indexes'].append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx.get('unique', False),
                'index_type': idx.get('type', 'BTREE'),
            })

        # Get primary key
        pk_constraint = insp.get_pk_constraint(table_name)
        if pk_constraint and pk_constraint.get('constrained_columns'):
            metadata['primary_key'] = {
                'name': pk_constraint.get('name', 'PRIMARY'),
                'columns': pk_constraint['constrained_columns'],
            }

        # Get foreign keys
        fkeys = insp.get_foreign_keys(table_name)
        for fk in fkeys:
            metadata['foreign_keys'].append({
                'name': fk.get('name'),
                'columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns'],
                'ondelete': fk.get('options', {}).get('ondelete'),
            })

        # Get unique constraints
        unique_constraints = insp.get_unique_constraints(table_name)
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
