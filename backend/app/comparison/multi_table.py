"""Multi-table and schema-level data comparison engine."""

import re
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from app.adapters import DatabaseAdapter
from app.comparison.data import DataComparator, DataDiffResult


@dataclass
class TableDataResult:
    """Result of single table comparison."""

    source_table: str
    target_table: str
    status: str  # 'success', 'error', 'skipped'
    source_row_count: int
    target_row_count: int
    diff_count: int
    diff_percentage: Optional[float]
    mode_used: str
    is_identical: bool
    error_message: Optional[str] = None
    source_hash: Optional[str] = None
    target_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'source_table': self.source_table,
            'target_table': self.target_table,
            'status': self.status,
            'source_row_count': self.source_row_count,
            'target_row_count': self.target_row_count,
            'diff_count': self.diff_count,
            'diff_percentage': self.diff_percentage,
            'mode_used': self.mode_used,
            'is_identical': self.is_identical,
            'error_message': self.error_message,
            'source_hash': self.source_hash,
            'target_hash': self.target_hash,
        }


@dataclass
class MultiTableDataSummary:
    """Summary statistics for multi-table comparison."""

    total_tables: int
    compared_tables: int
    identical_tables: int
    tables_with_diffs: int
    error_tables: int
    total_rows_compared: int
    total_diffs_found: int
    elapsed_time_seconds: float

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'total_tables': self.total_tables,
            'compared_tables': self.compared_tables,
            'identical_tables': self.identical_tables,
            'tables_with_diffs': self.tables_with_diffs,
            'error_tables': self.error_tables,
            'total_rows_compared': self.total_rows_compared,
            'total_diffs_found': self.total_diffs_found,
            'elapsed_time_seconds': self.elapsed_time_seconds,
        }


@dataclass
class MultiTableDataCompareResponse:
    """Complete multi-table comparison response."""

    summary: MultiTableDataSummary
    table_results: List[TableDataResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'summary': self.summary.to_dict(),
            'table_results': [tr.to_dict() for tr in self.table_results],
        }


@dataclass
class SchemaDataCompareSummary:
    """Summary statistics for schema-level comparison."""

    source_schema: str
    target_schema: str
    source_connection_name: str
    target_connection_name: str

    # Table statistics
    total_source_tables: int
    total_target_tables: int
    common_tables: int
    unmatched_source_tables: int
    unmatched_target_tables: int

    # Comparison results
    compared_tables: int
    identical_tables: int
    tables_with_diffs: int
    error_tables: int

    # Data volume
    total_rows_source: int
    total_rows_target: int
    total_diffs_found: int
    overall_diff_percentage: Optional[float]
    elapsed_time_seconds: float

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'source_schema': self.source_schema,
            'target_schema': self.target_schema,
            'source_connection_name': self.source_connection_name,
            'target_connection_name': self.target_connection_name,
            'total_source_tables': self.total_source_tables,
            'total_target_tables': self.total_target_tables,
            'common_tables': self.common_tables,
            'unmatched_source_tables': self.unmatched_source_tables,
            'unmatched_target_tables': self.unmatched_target_tables,
            'compared_tables': self.compared_tables,
            'identical_tables': self.identical_tables,
            'tables_with_diffs': self.tables_with_diffs,
            'error_tables': self.error_tables,
            'total_rows_source': self.total_rows_source,
            'total_rows_target': self.total_rows_target,
            'total_diffs_found': self.total_diffs_found,
            'overall_diff_percentage': self.overall_diff_percentage,
            'elapsed_time_seconds': self.elapsed_time_seconds,
        }


@dataclass
class SchemaDataCompareResponse:
    """Complete schema-level comparison response."""

    summary: SchemaDataCompareSummary
    table_results: List[TableDataResult] = field(default_factory=list)
    unmatched_source_tables: List[str] = field(default_factory=list)
    unmatched_target_tables: List[str] = field(default_factory=list)
    excluded_tables: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'summary': self.summary.to_dict(),
            'table_results': [tr.to_dict() for tr in self.table_results],
            'unmatched_source_tables': self.unmatched_source_tables,
            'unmatched_target_tables': self.unmatched_target_tables,
            'excluded_tables': self.excluded_tables,
        }


class MultiTableDataComparator:
    """Multi-table data comparator - coordinates multiple single-table comparisons.

    Reuses DataComparator for individual table comparison, provides:
    - Batch coordination for multiple table pairs
    - Progress tracking
    - Result aggregation
    - Error handling per table
    """

    def __init__(
        self,
        source_adapter: DatabaseAdapter,
        target_adapter: DatabaseAdapter,
        source_schema: str,
        target_schema: str,
        mode: str = "auto",
        threshold: int = 100000,
        sample_size: int = 1000,
        timeout_per_table: int = 300,
    ):
        """Initialize MultiTableDataComparator.

        Args:
            source_adapter: Source database adapter
            target_adapter: Target database adapter
            source_schema: Source schema name
            target_schema: Target schema name
            mode: Comparison mode ('auto', 'full', 'hash', 'sample')
            threshold: Row count threshold for auto mode
            sample_size: Sample size for sample mode
            timeout_per_table: Timeout in seconds per table
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.source_schema = source_schema
        self.target_schema = target_schema
        self.mode = mode
        self.threshold = threshold
        self.sample_size = sample_size
        self.timeout_per_table = timeout_per_table

    def compare(
        self,
        table_mappings: List[Tuple[str, str]],
    ) -> MultiTableDataCompareResponse:
        """Compare data across multiple table pairs.

        Args:
            table_mappings: List of (source_table, target_table) tuples

        Returns:
            MultiTableDataCompareResponse with aggregated results
        """
        start_time = time.time()
        results: List[TableDataResult] = []

        for source_table, target_table in table_mappings:
            result = self._compare_single_table(source_table, target_table)
            results.append(result)

        elapsed = time.time() - start_time
        summary = self._build_summary(results, elapsed)

        return MultiTableDataCompareResponse(
            summary=summary,
            table_results=results,
        )

    def _compare_single_table(
        self,
        source_table: str,
        target_table: str,
    ) -> TableDataResult:
        """Compare single table using DataComparator.

        Args:
            source_table: Source table name (without schema prefix)
            target_table: Target table name (without schema prefix)

        Returns:
            TableDataResult with comparison outcome
        """
        try:
            # Build full table names with schema prefix
            full_source_table = f"{self.source_schema}.{source_table}"
            full_target_table = f"{self.target_schema}.{target_table}"

            # Create comparator for single table comparison
            comparator = DataComparator(
                source_adapter=self.source_adapter,
                target_adapter=self.target_adapter,
                threshold=self.threshold,
                sample_size=self.sample_size,
                timeout=self.timeout_per_table,
            )

            # Run comparison
            result = comparator.compare(
                source_table=full_source_table,
                target_table=full_target_table,
                mode=self.mode,
            )

            return TableDataResult(
                source_table=source_table,
                target_table=target_table,
                status="success",
                source_row_count=result.source_row_count,
                target_row_count=result.target_row_count,
                diff_count=result.diff_count,
                diff_percentage=result.diff_percentage,
                mode_used=result.mode_used,
                is_identical=result.diff_count == 0,
                source_hash=result.source_hash,
                target_hash=result.target_hash,
            )

        except Exception as e:
            return TableDataResult(
                source_table=source_table,
                target_table=target_table,
                status="error",
                error_message=str(e),
                source_row_count=0,
                target_row_count=0,
                diff_count=0,
                diff_percentage=None,
                mode_used=self.mode,
                is_identical=False,
            )

    def _build_summary(
        self,
        results: List[TableDataResult],
        elapsed_time: float,
    ) -> MultiTableDataSummary:
        """Build summary statistics from results.

        Args:
            results: List of TableDataResult
            elapsed_time: Total elapsed time in seconds

        Returns:
            MultiTableDataSummary with aggregated statistics
        """
        total_tables = len(results)
        compared_tables = sum(1 for r in results if r.status == "success")
        error_tables = sum(1 for r in results if r.status == "error")
        identical_tables = sum(1 for r in results if r.is_identical and r.status == "success")
        tables_with_diffs = sum(1 for r in results if not r.is_identical and r.status == "success")
        total_rows_compared = sum(r.source_row_count + r.target_row_count for r in results if r.status == "success")
        total_diffs_found = sum(r.diff_count for r in results if r.status == "success")

        return MultiTableDataSummary(
            total_tables=total_tables,
            compared_tables=compared_tables,
            identical_tables=identical_tables,
            tables_with_diffs=tables_with_diffs,
            error_tables=error_tables,
            total_rows_compared=total_rows_compared,
            total_diffs_found=total_diffs_found,
            elapsed_time_seconds=elapsed_time,
        )


class SchemaDataComparator:
    """Schema-level data comparator - compares all tables in a schema.

    Discovers tables in both schemas, applies filtering, and delegates
    to MultiTableDataComparator for actual comparison.
    """

    def __init__(
        self,
        source_adapter: DatabaseAdapter,
        target_adapter: DatabaseAdapter,
        source_schema: str,
        target_schema: str,
        source_connection_name: str = "",
        target_connection_name: str = "",
        mode: str = "hash",
        threshold: int = 100000,
        sample_size: int = 1000,
        timeout_per_table: int = 300,
    ):
        """Initialize SchemaDataComparator.

        Args:
            source_adapter: Source database adapter
            target_adapter: Target database adapter
            source_schema: Source schema name
            target_schema: Target schema name
            source_connection_name: Source connection name for display
            target_connection_name: Target connection name for display
            mode: Comparison mode (default 'hash' for fast screening)
            threshold: Row count threshold for auto mode
            sample_size: Sample size for sample mode
            timeout_per_table: Timeout in seconds per table
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.source_schema = source_schema
        self.target_schema = target_schema
        self.source_connection_name = source_connection_name
        self.target_connection_name = target_connection_name
        self.mode = mode
        self.threshold = threshold
        self.sample_size = sample_size
        self.timeout_per_table = timeout_per_table

    def compare(
        self,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        only_common_tables: bool = True,
    ) -> SchemaDataCompareResponse:
        """Compare data across entire schema.

        Args:
            exclude_patterns: List of wildcard patterns to exclude (e.g., ['sys_*', '*_log'])
            include_patterns: List of wildcard patterns to include (if provided, only these match)
            only_common_tables: If True, only compare tables present in both schemas

        Returns:
            SchemaDataCompareResponse with complete results
        """
        start_time = time.time()

        # 1. Discover tables in both schemas
        source_tables = self._get_schema_tables(self.source_adapter, self.source_schema)
        target_tables = self._get_schema_tables(self.target_adapter, self.target_schema)

        # 2. Apply filters
        filtered_source = self._apply_filters(
            source_tables,
            exclude_patterns or [],
            include_patterns or [],
        )
        filtered_target = self._apply_filters(
            target_tables,
            exclude_patterns or [],
            include_patterns or [],
        )

        # 3. Determine comparison scope
        if only_common_tables:
            common = set(filtered_source) & set(filtered_target)
            table_mappings = [(t, t) for t in sorted(common)]
            unmatched_source = sorted(set(filtered_source) - set(filtered_target))
            unmatched_target = sorted(set(filtered_target) - set(filtered_source))
        else:
            # Include all tables, match by name where possible
            table_mappings, unmatched_source, unmatched_target = self._build_table_mappings(
                filtered_source,
                filtered_target,
            )

        # 4. Execute comparison using MultiTableDataComparator
        multi_comparator = MultiTableDataComparator(
            source_adapter=self.source_adapter,
            target_adapter=self.target_adapter,
            source_schema=self.source_schema,
            target_schema=self.target_schema,
            mode=self.mode,
            threshold=self.threshold,
            sample_size=self.sample_size,
            timeout_per_table=self.timeout_per_table,
        )

        multi_result = multi_comparator.compare(table_mappings)

        # 5. Calculate excluded tables
        excluded_source = set(source_tables) - set(filtered_source)
        excluded_target = set(target_tables) - set(filtered_target)
        excluded_tables = sorted(excluded_source | excluded_target)

        # 6. Build schema-level summary
        elapsed = time.time() - start_time
        summary = self._build_schema_summary(
            multi_result.summary,
            source_tables,
            target_tables,
            filtered_source,
            filtered_target,
            unmatched_source,
            unmatched_target,
            elapsed,
        )

        return SchemaDataCompareResponse(
            summary=summary,
            table_results=multi_result.table_results,
            unmatched_source_tables=unmatched_source,
            unmatched_target_tables=unmatched_target,
            excluded_tables=excluded_tables,
        )

    def _get_schema_tables(
        self,
        adapter: DatabaseAdapter,
        schema: str,
    ) -> List[str]:
        """Get list of tables in a schema.

        Args:
            adapter: Database adapter
            schema: Schema name

        Returns:
            List of table names
        """
        # Use adapter's get_tables method
        # Note: adapter may need schema parameter
        tables = adapter.get_tables()
        # Filter by schema if needed
        return [t['table_name'] for t in tables if t.get('schema') == schema or schema is None]

    def _apply_filters(
        self,
        tables: List[str],
        exclude_patterns: List[str],
        include_patterns: List[str],
    ) -> List[str]:
        """Apply include/exclude patterns to table list.

        Args:
            tables: List of table names
            exclude_patterns: Patterns to exclude (wildcards supported)
            include_patterns: Patterns to include (if provided, only these match)

        Returns:
            Filtered list of table names
        """
        result = tables

        # Apply include filter first (if provided, only include matching)
        if include_patterns:
            included = set()
            for pattern in include_patterns:
                regex = self._pattern_to_regex(pattern)
                included.update(t for t in result if re.match(regex, t, re.IGNORECASE))
            result = list(included)

        # Apply exclude filter
        if exclude_patterns:
            for pattern in exclude_patterns:
                regex = self._pattern_to_regex(pattern)
                result = [t for t in result if not re.match(regex, t, re.IGNORECASE)]

        return sorted(result)

    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert wildcard pattern to regex.

        Args:
            pattern: Wildcard pattern (e.g., 'sys_*', '*_log')

        Returns:
            Regex pattern string
        """
        regex = pattern.replace('*', '.*').replace('?', '.')
        return f'^{regex}$'

    def _build_table_mappings(
        self,
        source_tables: List[str],
        target_tables: List[str],
    ) -> Tuple[List[Tuple[str, str]], List[str], List[str]]:
        """Build table mappings for non-common tables mode.

        Args:
            source_tables: Source table names
            target_tables: Target table names

        Returns:
            Tuple of (mappings, unmatched_source, unmatched_target)
        """
        source_set = set(source_tables)
        target_set = set(target_tables)

        # Common tables - match by name
        common = source_set & target_set
        mappings = [(t, t) for t in sorted(common)]

        # Unmatched tables
        unmatched_source = sorted(source_set - target_set)
        unmatched_target = sorted(target_set - source_set)

        return mappings, unmatched_source, unmatched_target

    def _build_schema_summary(
        self,
        multi_summary: MultiTableDataSummary,
        source_tables: List[str],
        target_tables: List[str],
        filtered_source: List[str],
        filtered_target: List[str],
        unmatched_source: List[str],
        unmatched_target: List[str],
        elapsed_time: float,
    ) -> SchemaDataCompareSummary:
        """Build schema-level summary from multi-table results.

        Args:
            multi_summary: MultiTableDataSummary from comparison
            source_tables: All source tables
            target_tables: All target tables
            filtered_source: Filtered source tables
            filtered_target: Filtered target tables
            unmatched_source: Unmatched source tables
            unmatched_target: Unmatched target tables
            elapsed_time: Elapsed time in seconds

        Returns:
            SchemaDataCompareSummary
        """
        common_tables = len(filtered_source) - len(unmatched_source)

        # Calculate total rows
        total_rows_source = sum(
            r.source_row_count for r in []
        )  # Would need to fetch row counts for all tables
        total_rows_target = sum(
            r.target_row_count for r in []
        )

        # Calculate overall diff percentage
        overall_diff_percentage = None
        if multi_summary.total_rows_compared > 0:
            overall_diff_percentage = (
                multi_summary.total_diffs_found / multi_summary.total_rows_compared * 100
            )

        return SchemaDataCompareSummary(
            source_schema=self.source_schema,
            target_schema=self.target_schema,
            source_connection_name=self.source_connection_name,
            target_connection_name=self.target_connection_name,
            total_source_tables=len(source_tables),
            total_target_tables=len(target_tables),
            common_tables=common_tables,
            unmatched_source_tables=len(unmatched_source),
            unmatched_target_tables=len(unmatched_target),
            compared_tables=multi_summary.compared_tables,
            identical_tables=multi_summary.identical_tables,
            tables_with_diffs=multi_summary.tables_with_diffs,
            error_tables=multi_summary.error_tables,
            total_rows_source=total_rows_source,
            total_rows_target=total_rows_target,
            total_diffs_found=multi_summary.total_diffs_found,
            overall_diff_percentage=overall_diff_percentage,
            elapsed_time_seconds=elapsed_time,
        )
