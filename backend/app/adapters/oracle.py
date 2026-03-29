"""Oracle database adapter implementation."""

from typing import Any, Optional

import oracledb
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.adapters.base import DatabaseAdapter


class OracleAdapter(DatabaseAdapter):
    """Oracle database adapter for metadata extraction.

    Uses oracledb for connections and SQLAlchemy for metadata reflection.
    Supports both Thin mode (pure Python) and Thick mode (requires Oracle client).
    """

    def __init__(self, connection_config: dict):
        """Initialize Oracle adapter.

        Args:
            connection_config: Dict with host, port, database (service_name), username, password
        """
        super().__init__(connection_config)
        self._engine: Optional[Engine] = None

    def _get_connection_string(self) -> str:
        """Build Oracle connection string.

        Supports service_name (default) or SID format.
        """
        # Oracle DSN format: host:port/service_name or host:port/SID
        dsn = f"{self.config['host']}:{self.config['port']}/{self.config.get('service_name', self.config['database'])}"
        return f"oracle+oracledb://{self.config['username']}:{self.config['password']}@{dsn}"

    def connect(self) -> Any:
        """Establish Oracle connection using oracledb.

        Uses Thin mode by default (pure Python, no Oracle client required).

        Returns:
            oracledb.Connection
        """
        dsn = f"{self.config['host']}:{self.config['port']}/{self.config.get('service_name', self.config['database'])}"
        self._connection = oracledb.connect(
            user=self.config['username'],
            password=self.config['password'],
            dsn=dsn,
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
        """Test if Oracle connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False
        finally:
            self.disconnect()

    def get_tables(self) -> list[dict]:
        """List all tables in the database.

        Queries ALL_TABLES for table metadata.

        Returns:
            List of dicts with table_name, table_type, row_count, create_time, schema
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        # Use ALL_TABLES for all accessible tables, or USER_TABLES for current schema
        query = """
            SELECT
                TABLE_NAME as table_name,
                'TABLE' as table_type,
                NUM_ROWS as row_count,
                CREATED as create_time,
                OWNER as schema
            FROM ALL_TABLES
            WHERE OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            ORDER BY TABLE_NAME
        """
        cursor.execute(query)
        columns = ['table_name', 'table_type', 'row_count', 'create_time', 'schema']
        tables = []
        for row in cursor.fetchall():
            table_dict = {}
            for i, col in enumerate(columns):
                table_dict[col] = row[i]
            tables.append(table_dict)
        cursor.close()
        return tables

    def get_schemas(self) -> list[dict]:
        """List all schemas (users) accessible to the current user.

        Queries ALL_USERS view.

        Returns:
            List of dicts with schema_name, account_status, created_time
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        query = """
            SELECT
                USERNAME as schema_name,
                CREATED as created_time,
                ACCOUNT_STATUS as account_status
            FROM ALL_USERS
            ORDER BY USERNAME
        """
        cursor.execute(query)
        columns = ['schema_name', 'created_time', 'account_status']
        schemas = []
        for row in cursor.fetchall():
            schema_dict = {}
            for i, col in enumerate(columns):
                schema_dict[col] = row[i]
            schemas.append(schema_dict)
        cursor.close()
        return schemas

    def get_table_metadata(self, table_name: str) -> dict:
        """Get complete metadata for a specific table.

        Uses SQLAlchemy inspect() for columns, indexes, constraints.
        Falls back to Oracle system views for additional metadata.

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

        # Get columns using SQLAlchemy inspect
        try:
            columns = insp.get_columns(table_name)
            for col in columns:
                metadata['columns'].append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True),
                    'default': col.get('default'),
                    'comment': col.get('comment'),
                })
        except Exception:
            # Fallback to Oracle system views
            metadata['columns'] = self._get_columns_from_oracle(table_name)

        # Get indexes
        try:
            indexes = insp.get_indexes(table_name)
            for idx in indexes:
                metadata['indexes'].append({
                    'name': idx['name'],
                    'columns': idx['column_names'],
                    'unique': idx.get('unique', False),
                    'index_type': idx.get('type', 'BTREE'),
                })
        except Exception:
            metadata['indexes'] = self._get_indexes_from_oracle(table_name)

        # Get primary key
        try:
            pk_constraint = insp.get_pk_constraint(table_name)
            if pk_constraint and pk_constraint.get('constrained_columns'):
                metadata['primary_key'] = {
                    'name': pk_constraint.get('name', 'SYS_C0000000'),
                    'columns': pk_constraint['constrained_columns'],
                }
        except Exception:
            metadata['primary_key'] = self._get_primary_key_from_oracle(table_name)

        # Get foreign keys
        try:
            fkeys = insp.get_foreign_keys(table_name)
            for fk in fkeys:
                metadata['foreign_keys'].append({
                    'name': fk.get('name'),
                    'columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns'],
                    'ondelete': fk.get('options', {}).get('ondelete'),
                })
        except Exception:
            metadata['foreign_keys'] = self._get_foreign_keys_from_oracle(table_name)

        # Get unique constraints
        try:
            unique_constraints = insp.get_unique_constraints(table_name)
            for uc in unique_constraints:
                metadata['unique_constraints'].append({
                    'name': uc.get('name'),
                    'columns': uc.get('column_names', []),
                })
        except Exception:
            metadata['unique_constraints'] = self._get_unique_constraints_from_oracle(table_name)

        return metadata

    def _get_columns_from_oracle(self, table_name: str) -> list[dict]:
        """Get column metadata from Oracle system views."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        query = """
            SELECT
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.DATA_LENGTH,
                c.DATA_PRECISION,
                c.DATA_SCALE,
                c.NULLABLE,
                c.DATA_DEFAULT,
                cm.COMMENTS
            FROM ALL_TAB_COLUMNS c
            LEFT JOIN ALL_COL_COMMENTS cm ON c.OWNER = cm.OWNER
                AND c.TABLE_NAME = cm.TABLE_NAME
                AND c.COLUMN_NAME = cm.COLUMN_NAME
            WHERE c.OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND c.TABLE_NAME = :table_name
            ORDER BY c.COLUMN_ID
        """
        cursor.execute(query, {'table_name': table_name.upper()})
        columns = []
        for row in cursor.fetchall():
            # Build type string with precision/scale where applicable
            data_type = row[1]
            if data_type in ('NUMBER', 'NUMERIC'):
                if row[3] and row[4]:  # precision and scale
                    data_type = f"NUMBER({row[3]}, {row[4]})"
                elif row[3]:  # precision only
                    data_type = f"NUMBER({row[3]})"
            elif data_type in ('VARCHAR2', 'NVARCHAR2', 'CHAR', 'NCHAR'):
                data_type = f"{data_type}({row[2]})"
            elif data_type in ('FLOAT', 'BINARY_FLOAT', 'BINARY_DOUBLE'):
                if row[3]:
                    data_type = f"{data_type}({row[3]})"

            columns.append({
                'name': row[0],
                'type': data_type,
                'nullable': row[5] == 'Y',
                'default': row[6],
                'comment': row[7],
            })
        cursor.close()
        return columns

    def _get_indexes_from_oracle(self, table_name: str) -> list[dict]:
        """Get index metadata from Oracle system views."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()

        # Get indexes
        idx_query = """
            SELECT
                INDEX_NAME,
                UNIQUENESS,
                INDEX_TYPE
            FROM ALL_INDEXES
            WHERE OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND TABLE_NAME = :table_name
            ORDER BY INDEX_NAME
        """
        cursor.execute(idx_query, {'table_name': table_name.upper()})
        indexes_map = {}
        for row in cursor.fetchall():
            indexes_map[row[0]] = {
                'name': row[0],
                'columns': [],
                'unique': row[1] == 'UNIQUE',
                'index_type': row[2],
            }

        # Get index columns
        col_query = """
            SELECT
                INDEX_NAME,
                COLUMN_NAME,
                COLUMN_POSITION
            FROM ALL_IND_COLUMNS
            WHERE INDEX_OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND TABLE_NAME = :table_name
            ORDER BY INDEX_NAME, COLUMN_POSITION
        """
        cursor.execute(col_query, {'table_name': table_name.upper()})
        for row in cursor.fetchall():
            if row[0] in indexes_map:
                indexes_map[row[0]]['columns'].append(row[1])

        cursor.close()
        return list(indexes_map.values())

    def _get_primary_key_from_oracle(self, table_name: str) -> Optional[dict]:
        """Get primary key metadata from Oracle system views."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        query = """
            SELECT
                c.CONSTRAINT_NAME,
                cc.COLUMN_NAME,
                cc.POSITION
            FROM ALL_CONSTRAINTS c
            JOIN ALL_CONS_COLUMNS cc ON c.OWNER = cc.OWNER
                AND c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            WHERE c.OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND c.TABLE_NAME = :table_name
            AND c.CONSTRAINT_TYPE = 'P'
            ORDER BY cc.POSITION
        """
        cursor.execute(query, {'table_name': table_name.upper()})
        pk_info = None
        columns = []
        for row in cursor.fetchall():
            if pk_info is None:
                pk_info = {'name': row[0], 'columns': []}
            columns.append(row[1])
        if pk_info:
            pk_info['columns'] = columns
        cursor.close()
        return pk_info

    def _get_foreign_keys_from_oracle(self, table_name: str) -> list[dict]:
        """Get foreign key metadata from Oracle system views."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()

        # Get constraints
        fk_query = """
            SELECT
                c.CONSTRAINT_NAME,
                c.R_OWNER,
                c.R_CONSTRAINT_NAME,
                c.DELETE_RULE
            FROM ALL_CONSTRAINTS c
            WHERE c.OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND c.TABLE_NAME = :table_name
            AND c.CONSTRAINT_TYPE = 'R'
            ORDER BY c.CONSTRAINT_NAME
        """
        cursor.execute(fk_query, {'table_name': table_name.upper()})
        fks = []
        for row in cursor.fetchall():
            fk = {
                'name': row[0],
                'columns': [],
                'referred_table': None,
                'referred_columns': [],
                'ondelete': row[3],
            }

            # Get referred table info
            ref_query = """
                SELECT TABLE_NAME, CONSTRAINT_NAME
                FROM ALL_CONSTRAINTS
                WHERE OWNER = :owner
                AND CONSTRAINT_NAME = :constraint_name
            """
            cursor.execute(ref_query, {
                'owner': row[1],
                'constraint_name': row[2]
            })
            ref_row = cursor.fetchone()
            if ref_row:
                fk['referred_table'] = ref_row[0]

            # Get columns
            col_query = """
                SELECT COLUMN_NAME, POSITION
                FROM ALL_CONS_COLUMNS
                WHERE OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
                AND CONSTRAINT_NAME = :constraint_name
                ORDER BY POSITION
            """
            cursor.execute(col_query, {'constraint_name': row[0]})
            for col_row in cursor.fetchall():
                fk['columns'].append(col_row[0])

            # Get referred columns
            ref_col_query = """
                SELECT COLUMN_NAME, POSITION
                FROM ALL_CONS_COLUMNS
                WHERE OWNER = :owner
                AND CONSTRAINT_NAME = :constraint_name
                ORDER BY POSITION
            """
            cursor.execute(ref_col_query, {
                'owner': row[1],
                'constraint_name': row[2]
            })
            for col_row in cursor.fetchall():
                fk['referred_columns'].append(col_row[0])

            fks.append(fk)

        cursor.close()
        return fks

    def _get_unique_constraints_from_oracle(self, table_name: str) -> list[dict]:
        """Get unique constraint metadata from Oracle system views."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()

        # Get constraints
        uc_query = """
            SELECT
                c.CONSTRAINT_NAME,
                cc.COLUMN_NAME,
                cc.POSITION
            FROM ALL_CONSTRAINTS c
            JOIN ALL_CONS_COLUMNS cc ON c.OWNER = cc.OWNER
                AND c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            WHERE c.OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
            AND c.TABLE_NAME = :table_name
            AND c.CONSTRAINT_TYPE = 'U'
            ORDER BY c.CONSTRAINT_NAME, cc.POSITION
        """
        cursor.execute(uc_query, {'table_name': table_name.upper()})
        uc_map = {}
        for row in cursor.fetchall():
            if row[0] not in uc_map:
                uc_map[row[0]] = {'name': row[0], 'columns': []}
            uc_map[row[0]]['columns'].append(row[1])

        cursor.close()
        return list(uc_map.values())

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
