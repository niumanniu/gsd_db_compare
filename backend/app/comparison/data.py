"""Data comparison engine for comparing table data across databases."""

import hashlib
import signal
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, List, Optional

from app.adapters import DatabaseAdapter, get_adapter


class ComparisonTimeoutError(Exception):
    """Raised when comparison exceeds timeout limit."""
    pass


@contextmanager
def timeout_context(seconds: int) -> Generator[None, None, None]:
    """Context manager for timeout protection.

    Args:
        seconds: Timeout in seconds

    Raises:
        ComparisonTimeoutError: When timeout is exceeded
    """
    def timeout_handler(signum, frame):
        raise ComparisonTimeoutError(f"Comparison exceeded {seconds} seconds timeout")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@dataclass
class FieldDiff:
    """Single field difference between source and target rows."""

    field_name: str
    source_value: Any
    target_value: Any
    diff_type: str  # 'value', 'null', 'type', 'length'

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'field_name': self.field_name,
            'source_value': self._serialize_value(self.source_value),
            'target_value': self._serialize_value(self.target_value),
            'diff_type': self.diff_type,
        }

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value for JSON representation."""
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            return f"<binary:{len(value)} bytes>"
        return str(value) if not isinstance(value, (int, float, str)) else value


@dataclass
class RowDiff:
    """Single row difference between source and target tables."""

    primary_key: Any
    diff_type: str  # 'missing_in_target', 'missing_in_source', 'content_diff'
    field_diffs: List[FieldDiff] = field(default_factory=list)
    source_row: Optional[dict] = None
    target_row: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'primary_key': self.primary_key,
            'diff_type': self.diff_type,
            'field_diffs': [fd.to_dict() for fd in self.field_diffs],
            'source_row': self._serialize_row(self.source_row),
            'target_row': self._serialize_row(self.target_row),
        }

    @staticmethod
    def _serialize_row(row: Optional[dict]) -> Optional[dict]:
        """Serialize row for JSON representation."""
        if row is None:
            return None
        return {k: FieldDiff._serialize_value(v) for k, v in row.items()}


@dataclass
class DataDiffResult:
    """Complete data comparison result."""

    source_table: str
    target_table: str
    source_row_count: int
    target_row_count: int
    diff_count: int
    mode_used: str  # 'full', 'hash', 'sample', 'hash+sample'
    diffs: List[RowDiff] = field(default_factory=list)
    has_more: bool = False
    source_hash: Optional[str] = None
    target_hash: Optional[str] = None
    sampled_row_count: Optional[int] = None
    diff_percentage: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {
            'summary': {
                'source_table': self.source_table,
                'target_table': self.target_table,
                'source_row_count': self.source_row_count,
                'target_row_count': self.target_row_count,
                'diff_count': self.diff_count,
                'diff_percentage': self.diff_percentage,
                'mode_used': self.mode_used,
                'has_more': self.has_more,
            },
            'diffs': [d.to_dict() for d in self.diffs],
        }
        if self.source_hash:
            result['summary']['source_hash'] = self.source_hash
        if self.target_hash:
            result['summary']['target_hash'] = self.target_hash
        if self.sampled_row_count is not None:
            result['summary']['sampled_row_count'] = self.sampled_row_count
        return result


class DataComparator:
    """Compares data between two database tables.

    Supports multiple comparison modes:
    - full: Compare all rows (for small tables)
    - hash: Compare MD5 checksums (quick difference detection)
    - sample: Compare sampled rows (for locating differences in large tables)
    - auto: Automatically select mode based on table size

    Key behaviors:
    - NULL = NULL treated as equal (non-SQL standard)
    - BLOB/CLOB/TEXT compared by length only
    - Batch processing for memory efficiency
    - Primary key interval sampling for large tables
    - Timeout protection for long-running comparisons
    - Streaming queries with server-side cursors
    """

    # Default thresholds
    DEFAULT_THRESHOLD = 100_000  # Rows threshold for auto mode
    DEFAULT_BATCH_SIZE = 1000  # Rows per batch
    DEFAULT_SAMPLE_SIZE = 1000  # Rows to sample for large tables
    DEFAULT_TIMEOUT = 300  # Timeout in seconds (5 minutes)
    MAX_ROW_COUNT_FOR_FULL = 1_000_000  # Max rows for full comparison (1M)

    def __init__(
        self,
        source_adapter: DatabaseAdapter,
        target_adapter: DatabaseAdapter,
        threshold: Optional[int] = None,
        batch_size: Optional[int] = None,
        sample_size: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """Initialize DataComparator.

        Args:
            source_adapter: Source database adapter
            target_adapter: Target database adapter
            threshold: Row count threshold for auto mode (default 100,000)
            batch_size: Rows per batch for batched queries (default 1,000)
            sample_size: Rows to sample for large tables (default 1,000)
            timeout: Timeout in seconds for comparison (default 300s / 5 min)
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.threshold = threshold if threshold is not None else self.DEFAULT_THRESHOLD
        self.batch_size = batch_size if batch_size is not None else self.DEFAULT_BATCH_SIZE
        self.sample_size = sample_size if sample_size is not None else self.DEFAULT_SAMPLE_SIZE
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

    def compare(
        self,
        source_table: str,
        target_table: str,
        mode: str = 'auto',
    ) -> DataDiffResult:
        """Main entry point for data comparison.

        Args:
            source_table: Source table name
            target_table: Target table name
            mode: Comparison mode ('auto', 'full', 'hash', 'sample')

        Returns:
            DataDiffResult with comparison summary and differences

        Raises:
            ValueError: If mode is not one of the valid options
            ComparisonTimeoutError: If comparison exceeds timeout limit
        """
        if mode not in ('auto', 'full', 'hash', 'sample'):
            raise ValueError(f"Invalid mode: {mode}. Must be 'auto', 'full', 'hash', or 'sample'")

        # Get row counts
        source_count = self._get_row_count(source_table)
        target_count = self._get_row_count(target_table)

        # Check for very large tables - force hash/sample mode
        if source_count > self.MAX_ROW_COUNT_FOR_FULL or target_count > self.MAX_ROW_COUNT_FOR_FULL:
            if mode == 'full':
                # Override to sample mode for very large tables
                mode = 'sample'

        # Mode selection
        if mode == 'auto':
            if source_count <= self.threshold and target_count <= self.threshold:
                actual_mode = 'full'
            else:
                # For large tables, use hash+sample strategy
                actual_mode = 'hash+sample'
        else:
            actual_mode = mode

        # Execute comparison with timeout protection
        with timeout_context(self.timeout):
            if actual_mode == 'full':
                return self._full_compare(source_table, target_table, source_count, target_count)
            elif actual_mode == 'hash':
                return self._hash_verify(source_table, target_table, source_count, target_count)
            elif actual_mode == 'sample':
                return self._sample_compare(source_table, target_table, source_count, target_count)
            elif actual_mode == 'hash+sample':
                # First try hash verify
                hash_result = self._hash_verify(source_table, target_table, source_count, target_count)
                if hash_result.source_hash == hash_result.target_hash:
                    # Hashes match - tables are identical
                    return hash_result
                # Hashes differ - follow up with sample compare to locate differences
                sample_result = self._sample_compare(source_table, target_table, source_count, target_count)
                # Merge hash info into sample result
                sample_result.source_hash = hash_result.source_hash
                sample_result.target_hash = hash_result.target_hash
                sample_result.mode_used = 'hash+sample'
                return sample_result
            else:
                raise ValueError(f"Unexpected mode: {actual_mode}")

    def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table.

        Args:
            table_name: Table name

        Returns:
            Row count
        """
        # Use COUNT(*) query
        if not self.source_adapter._connection:
            self.source_adapter.connect()
        if not self.target_adapter._connection:
            self.target_adapter.connect()

        # Try source adapter first
        cursor = self.source_adapter._connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
        finally:
            cursor.close()
        return count

    def _get_primary_key_column(self, table_name: str, adapter: DatabaseAdapter) -> Optional[str]:
        """Get primary key column name for a table.

        Args:
            table_name: Table name
            adapter: Database adapter

        Returns:
            Primary key column name or None if no primary key
        """
        metadata = adapter.get_table_metadata(table_name)
        pk = metadata.get('primary_key')
        if pk and pk.get('columns'):
            return pk['columns'][0]
        return None

    def _get_columns(self, table_name: str, adapter: DatabaseAdapter) -> list[str]:
        """Get column names for a table.

        Args:
            table_name: Table name
            adapter: Database adapter

        Returns:
            List of column names
        """
        metadata = adapter.get_table_metadata(table_name)
        return [col['name'] for col in metadata.get('columns', [])]

    def _get_column_types(self, table_name: str, adapter: DatabaseAdapter) -> dict[str, str]:
        """Get column type mappings for a table.

        Args:
            table_name: Table name
            adapter: Database adapter

        Returns:
            Dict mapping column name to type string
        """
        metadata = adapter.get_table_metadata(table_name)
        return {col['name']: col['type'].lower() for col in metadata.get('columns', [])}

    def _is_lob_type(self, type_str: str) -> bool:
        """Check if type is a BLOB/CLOB/TEXT type.

        Args:
            type_str: Type string

        Returns:
            True if LOB type
        """
        lob_types = {
            'blob', 'tinyblob', 'mediumblob', 'longblob',
            'text', 'tinytext', 'mediumtext', 'longtext',
            'clob', 'nclob',
        }
        return type_str in lob_types

    def _compare_field(
        self,
        field_name: str,
        source_value: Any,
        target_value: Any,
        field_type: str,
    ) -> Optional[FieldDiff]:
        """Compare two field values.

        Args:
            field_name: Field name
            source_value: Source value
            target_value: Target value
            field_type: Field type string

        Returns:
            FieldDiff if different, None if equal
        """
        # Handle NULL = NULL case
        if source_value is None and target_value is None:
            return None

        # Handle NULL vs non-NULL
        if source_value is None or target_value is None:
            return FieldDiff(
                field_name=field_name,
                source_value=source_value,
                target_value=target_value,
                diff_type='null',
            )

        # Handle LOB types - compare length only
        if self._is_lob_type(field_type):
            source_len = len(source_value) if isinstance(source_value, (bytes, str)) else source_value
            target_len = len(target_value) if isinstance(target_value, (bytes, str)) else target_value
            if source_len != target_len:
                return FieldDiff(
                    field_name=field_name,
                    source_value=source_value,
                    target_value=target_value,
                    diff_type='length',
                )
            return None

        # Normal value comparison
        if source_value != target_value:
            return FieldDiff(
                field_name=field_name,
                source_value=source_value,
                target_value=target_value,
                diff_type='value',
            )

        return None

    def _fetch_rows_batch(
        self,
        table_name: str,
        adapter: DatabaseAdapter,
        offset: int,
        limit: int,
        order_by: Optional[str] = None,
    ) -> List[dict]:
        """Fetch a batch of rows from a table.

        Args:
            table_name: Table name
            adapter: Database adapter
            offset: OFFSET for pagination
            limit: LIMIT for pagination
            order_by: Column to order by (default: first column)

        Returns:
            List of row dicts
        """
        if not adapter._connection:
            adapter.connect()

        columns = self._get_columns(table_name, adapter)
        if not columns:
            return []

        if order_by is None:
            order_by = columns[0]

        cursor = adapter._connection.cursor(dictionary=True)
        try:
            query = f"SELECT * FROM {table_name} ORDER BY {order_by} LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            return cursor.fetchall()
        finally:
            cursor.close()

    def _fetch_all_rows_streaming(
        self,
        table_name: str,
        adapter: DatabaseAdapter,
        order_by: Optional[str] = None,
    ) -> List[dict]:
        """Fetch all rows from a table using streaming.

        Args:
            table_name: Table name
            adapter: Database adapter
            order_by: Column to order by

        Returns:
            List of all row dicts
        """
        all_rows = []
        offset = 0

        while True:
            batch = self._fetch_rows_batch(table_name, adapter, offset, self.batch_size, order_by)
            if not batch:
                break
            all_rows.extend(batch)
            offset += self.batch_size

        return all_rows

    def _full_compare(
        self,
        source_table: str,
        target_table: str,
        source_count: int,
        target_count: int,
    ) -> DataDiffResult:
        """Full compare mode - compare all rows.

        Args:
            source_table: Source table name
            target_table: Target table name
            source_count: Source row count
            target_count: Target row count

        Returns:
            DataDiffResult with all differences
        """
        diffs = []

        # Get primary key for ordering and matching
        pk_column = self._get_primary_key_column(source_table, self.source_adapter)
        if pk_column is None:
            # Fallback to first column
            pk_column = self._get_columns(source_table, self.source_adapter)[0]

        # Get column types for LOB detection
        source_types = self._get_column_types(source_table, self.source_adapter)

        # Fetch all rows
        source_rows = self._fetch_all_rows_streaming(source_table, self.source_adapter, pk_column)
        target_rows = self._fetch_all_rows_streaming(target_table, self.target_adapter, pk_column)

        # Build lookup dict from target rows by primary key
        target_by_pk = {row[pk_column]: row for row in target_rows}
        source_pks = set()

        # Compare each source row
        for source_row in source_rows:
            pk_value = source_row[pk_column]
            source_pks.add(pk_value)

            if pk_value not in target_by_pk:
                # Row missing in target
                diffs.append(RowDiff(
                    primary_key=pk_value,
                    diff_type='missing_in_target',
                    field_diffs=[],
                    source_row=source_row,
                    target_row=None,
                ))
            else:
                # Row exists in both - compare field by field
                target_row = target_by_pk[pk_value]
                field_diffs = []

                for col_name in source_types.keys():
                    if col_name == pk_column:
                        continue  # Skip primary key comparison

                    source_value = source_row.get(col_name)
                    target_value = target_row.get(col_name)
                    field_type = source_types.get(col_name, '')

                    field_diff = self._compare_field(col_name, source_value, target_value, field_type)
                    if field_diff:
                        field_diffs.append(field_diff)

                if field_diffs:
                    diffs.append(RowDiff(
                        primary_key=pk_value,
                        diff_type='content_diff',
                        field_diffs=field_diffs,
                        source_row=source_row,
                        target_row=target_row,
                    ))

        # Find rows missing in source (extra rows in target)
        target_pks = set(target_by_pk.keys())
        for pk_value in target_pks - source_pks:
            diffs.append(RowDiff(
                primary_key=pk_value,
                diff_type='missing_in_source',
                field_diffs=[],
                source_row=None,
                target_row=target_by_pk[pk_value],
            ))

        return DataDiffResult(
            source_table=source_table,
            target_table=target_table,
            source_row_count=source_count,
            target_row_count=target_count,
            diff_count=len(diffs),
            mode_used='full',
            diffs=diffs,
            has_more=False,
        )

    def _compute_row_hash(
        self,
        row: dict,
        column_types: dict[str, str],
        pk_column: str,
    ) -> str:
        """Compute hash string for a single row.

        Args:
            row: Row dict
            column_types: Column type mapping
            pk_column: Primary key column name

        Returns:
            String representation for hashing
        """
        parts = []

        # Start with primary key for determinism
        pk_value = row.get(pk_column)
        parts.append(str(pk_value) if pk_value is not None else '<NULL>')

        # Add other columns in sorted order for consistency
        for col_name in sorted(column_types.keys()):
            if col_name == pk_column:
                continue

            value = row.get(col_name)
            col_type = column_types[col_name]

            if value is None:
                parts.append('<NULL>')
            elif self._is_lob_type(col_type):
                # For LOB types, use length only
                if isinstance(value, (bytes, bytearray)):
                    parts.append(f'<LOB:{len(value)}>')
                else:
                    parts.append(f'<LOB:{len(str(value))}>')
            else:
                parts.append(str(value))

        return '|'.join(parts)

    def _compute_table_hash(
        self,
        table_name: str,
        adapter: DatabaseAdapter,
        row_count: int,
    ) -> str:
        """Compute MD5 hash for entire table.

        Args:
            table_name: Table name
            adapter: Database adapter
            row_count: Table row count

        Returns:
            MD5 hash hex string
        """
        pk_column = self._get_primary_key_column(table_name, adapter)
        if pk_column is None:
            pk_column = self._get_columns(table_name, adapter)[0]

        column_types = self._get_column_types(table_name, adapter)

        # Build concatenated string for all rows
        hash_parts = []
        offset = 0

        while True:
            batch = self._fetch_rows_batch(table_name, adapter, offset, self.batch_size, pk_column)
            if not batch:
                break

            for row in batch:
                row_str = self._compute_row_hash(row, column_types, pk_column)
                hash_parts.append(row_str)

            offset += self.batch_size

        # Compute MD5 of concatenated rows
        full_string = ';'.join(hash_parts)
        return hashlib.md5(full_string.encode('utf-8')).hexdigest()

    def _hash_verify(
        self,
        source_table: str,
        target_table: str,
        source_count: int,
        target_count: int,
    ) -> DataDiffResult:
        """Hash verify mode - compare MD5 checksums.

        Args:
            source_table: Source table name
            target_table: Target table name
            source_count: Source row count
            target_count: Target row count

        Returns:
            DataDiffResult with hash values
        """
        # Compute hashes
        source_hash = self._compute_table_hash(source_table, self.source_adapter, source_count)
        target_hash = self._compute_table_hash(target_table, self.target_adapter, target_count)

        # Compare
        is_identical = source_hash == target_hash

        return DataDiffResult(
            source_table=source_table,
            target_table=target_table,
            source_row_count=source_count,
            target_row_count=target_count,
            diff_count=0 if is_identical else -1,  # -1 means "different but unknown how many"
            mode_used='hash',
            diffs=[],
            has_more=False,
            source_hash=source_hash,
            target_hash=target_hash,
            diff_percentage=0.0 if is_identical else None,
        )

    def _fetch_sampled_rows(
        self,
        table_name: str,
        adapter: DatabaseAdapter,
        pk_column: str,
        total_count: int,
    ) -> list[dict]:
        """Fetch sampled rows using primary key interval.

        Args:
            table_name: Table name
            adapter: Database adapter
            pk_column: Primary key column name
            total_count: Total row count

        Returns:
            List of sampled row dicts
        """
        if total_count <= self.sample_size:
            # Fetch all rows if table is small
            return self._fetch_all_rows_streaming(table_name, adapter, pk_column)

        # Calculate sampling interval
        interval = max(1, total_count // self.sample_size)

        # Use modulo-based sampling for efficiency
        if not adapter._connection:
            adapter.connect()

        columns = self._get_columns(table_name, adapter)
        if not columns:
            return []

        cursor = adapter._connection.cursor(dictionary=True)
        try:
            # MySQL modulo sampling: WHERE pk_column % interval = 0
            # This gives roughly 1 out of every interval rows
            query = f"""
                SELECT * FROM {table_name}
                WHERE MOD({pk_column}, %s) = 0
                ORDER BY {pk_column}
                LIMIT %s
            """
            cursor.execute(query, (interval, self.sample_size))
            return cursor.fetchall()
        finally:
            cursor.close()

    def _sample_compare(
        self,
        source_table: str,
        target_table: str,
        source_count: int,
        target_count: int,
    ) -> DataDiffResult:
        """Sample compare mode - compare sampled rows to locate differences.

        Args:
            source_table: Source table name
            target_table: Target table name
            source_count: Source row count
            target_count: Target row count

        Returns:
            DataDiffResult with sampled differences
        """
        diffs = []

        # Get primary key
        pk_column = self._get_primary_key_column(source_table, self.source_adapter)
        if pk_column is None:
            pk_column = self._get_columns(source_table, self.source_adapter)[0]

        # Get column types
        source_types = self._get_column_types(source_table, self.source_adapter)

        # Fetch sampled rows
        source_sample = self._fetch_sampled_rows(source_table, self.source_adapter, pk_column, source_count)
        target_sample = self._fetch_sampled_rows(target_table, self.target_adapter, pk_column, target_count)

        # Build lookup dict from target sample
        target_by_pk = {row[pk_column]: row for row in target_sample}
        source_pks = set()

        # Compare sampled source rows
        for source_row in source_sample:
            pk_value = source_row[pk_column]
            source_pks.add(pk_value)

            if pk_value not in target_by_pk:
                diffs.append(RowDiff(
                    primary_key=pk_value,
                    diff_type='missing_in_target',
                    field_diffs=[],
                    source_row=source_row,
                    target_row=None,
                ))
            else:
                target_row = target_by_pk[pk_value]
                field_diffs = []

                for col_name in source_types.keys():
                    if col_name == pk_column:
                        continue

                    source_value = source_row.get(col_name)
                    target_value = target_row.get(col_name)
                    field_type = source_types.get(col_name, '')

                    field_diff = self._compare_field(col_name, source_value, target_value, field_type)
                    if field_diff:
                        field_diffs.append(field_diff)

                if field_diffs:
                    diffs.append(RowDiff(
                        primary_key=pk_value,
                        diff_type='content_diff',
                        field_diffs=field_diffs,
                        source_row=source_row,
                        target_row=target_row,
                    ))

        # Check for extra rows in target sample
        target_pks = set(target_by_pk.keys())
        for pk_value in target_pks - source_pks:
            diffs.append(RowDiff(
                primary_key=pk_value,
                diff_type='missing_in_source',
                field_diffs=[],
                source_row=None,
                target_row=target_by_pk[pk_value],
            ))

        # Calculate diff percentage from sample
        sampled_count = len(source_sample)
        diff_percentage = (len(diffs) / sampled_count * 100) if sampled_count > 0 else 0.0

        return DataDiffResult(
            source_table=source_table,
            target_table=target_table,
            source_row_count=source_count,
            target_row_count=target_count,
            diff_count=len(diffs),
            mode_used='sample',
            diffs=diffs,
            has_more=True,  # Sample implies there may be more differences
            sampled_row_count=sampled_count,
            diff_percentage=diff_percentage,
        )
