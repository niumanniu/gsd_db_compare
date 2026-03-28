"""Schema comparison engine for comparing table structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnDiff:
    """Column-level difference."""

    column_name: str
    diff_type: str  # 'added', 'removed', 'modified'
    source_def: Optional[dict]
    target_def: Optional[dict]
    differences: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'column_name': self.column_name,
            'diff_type': self.diff_type,
            'source_definition': self.source_def,
            'target_definition': self.target_def,
            'differences': self.differences,
        }


@dataclass
class IndexDiff:
    """Index-level difference."""

    index_name: str
    diff_type: str  # 'added', 'removed', 'modified'
    source_def: Optional[dict]
    target_def: Optional[dict]
    differences: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'index_name': self.index_name,
            'diff_type': self.diff_type,
            'source_definition': self.source_def,
            'target_definition': self.target_def,
            'differences': self.differences,
        }


@dataclass
class ConstraintDiff:
    """Constraint-level difference."""

    constraint_name: str
    diff_type: str  # 'added', 'removed', 'modified'
    constraint_type: str  # 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE'
    source_def: Optional[dict]
    target_def: Optional[dict]
    differences: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'constraint_name': self.constraint_name,
            'diff_type': self.diff_type,
            'constraint_type': self.constraint_type,
            'source_definition': self.source_def,
            'target_definition': self.target_def,
            'differences': self.differences,
        }


@dataclass
class SchemaDiff:
    """Complete schema difference result."""

    source_table: str
    target_table: str
    column_diffs: List[ColumnDiff] = field(default_factory=list)
    index_diffs: List[IndexDiff] = field(default_factory=list)
    constraint_diffs: List[ConstraintDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.column_diffs or self.index_diffs or self.constraint_diffs)

    @property
    def diff_count(self) -> int:
        return len(self.column_diffs) + len(self.index_diffs) + len(self.constraint_diffs)

    def to_dict(self) -> dict:
        return {
            'source_table': self.source_table,
            'target_table': self.target_table,
            'column_diffs': [d.to_dict() for d in self.column_diffs],
            'index_diffs': [d.to_dict() for d in self.index_diffs],
            'constraint_diffs': [d.to_dict() for d in self.constraint_diffs],
            'has_differences': self.has_differences,
            'diff_count': self.diff_count,
        }


class SchemaComparator:
    """Compares two table metadata structures and identifies differences.

    Supports same-database comparison (e.g., MySQL vs MySQL) with strict matching
    and cross-database comparison (e.g., MySQL vs Oracle) with canonical type matching.
    """

    def __init__(
        self,
        source_db_type: str = 'mysql',
        target_db_type: str = 'mysql',
    ):
        """Initialize SchemaComparator.

        Args:
            source_db_type: Source database type ('mysql' or 'oracle')
            target_db_type: Target database type ('mysql' or 'oracle')
        """
        self.source_db_type = source_db_type
        self.target_db_type = target_db_type
        self.same_db_type = source_db_type == target_db_type

    def compare(
        self,
        source_metadata: dict,
        target_metadata: dict,
        source_db_type: Optional[str] = None,
        target_db_type: Optional[str] = None,
    ) -> SchemaDiff:
        """Compare two table metadata structures.

        Args:
            source_metadata: Source table metadata from adapter.get_table_metadata()
            target_metadata: Target table metadata
            source_db_type: Optional override for source database type
            target_db_type: Optional override for target database type

        Returns:
            SchemaDiff with all identified differences
        """
        # Use instance defaults or provided values
        source_db_type = source_db_type or self.source_db_type
        target_db_type = target_db_type or self.target_db_type

        return SchemaDiff(
            source_table=source_metadata.get('table_name', 'unknown'),
            target_table=target_metadata.get('table_name', 'unknown'),
            column_diffs=self.compare_columns(source_metadata, target_metadata, source_db_type, target_db_type),
            index_diffs=self.compare_indexes(source_metadata, target_metadata),
            constraint_diffs=self.compare_constraints(source_metadata, target_metadata),
        )

    def compare_columns(
        self,
        source: dict,
        target: dict,
        source_db_type: Optional[str] = None,
        target_db_type: Optional[str] = None,
    ) -> List[ColumnDiff]:
        """Compare columns between two tables.

        Identifies added, removed, and modified columns.

        Args:
            source: Source table metadata
            target: Target table metadata
            source_db_type: Source database type
            target_db_type: Target database type
        """
        diffs = []

        source_columns = {col['name']: col for col in source.get('columns', [])}
        target_columns = {col['name']: col for col in target.get('columns', [])}

        source_names = set(source_columns.keys())
        target_names = set(target_columns.keys())

        # Removed columns (in source, not in target)
        for name in source_names - target_names:
            diffs.append(ColumnDiff(
                column_name=name,
                diff_type='removed',
                source_def=source_columns[name],
                target_def=None,
                differences=['Column exists in source but not in target'],
            ))

        # Added columns (in target, not in source)
        for name in target_names - source_names:
            diffs.append(ColumnDiff(
                column_name=name,
                diff_type='added',
                source_def=None,
                target_def=target_columns[name],
                differences=['Column exists in target but not in source'],
            ))

        # Modified columns (in both, check for differences)
        for name in source_names & target_names:
            col_diffs = self._compare_column_definitions(
                source_columns[name],
                target_columns[name],
                source_db_type or self.source_db_type,
                target_db_type or self.target_db_type,
            )
            if col_diffs:
                diffs.append(ColumnDiff(
                    column_name=name,
                    diff_type='modified',
                    source_def=source_columns[name],
                    target_def=target_columns[name],
                    differences=col_diffs,
                ))

        return diffs

    def _compare_column_definitions(
        self,
        source_col: dict,
        target_col: dict,
        source_db_type: Optional[str] = None,
        target_db_type: Optional[str] = None,
    ) -> List[str]:
        """Compare two column definitions and return list of differences.

        Args:
            source_col: Source column definition
            target_col: Target column definition
            source_db_type: Source database type
            target_db_type: Target database type
        """
        differences = []

        # Compare type (normalized)
        # For same-db comparison: use strict matching
        # For cross-db comparison: use canonical type matching
        source_type_str = source_col.get('type', '')
        target_type_str = target_col.get('type', '')

        if self.same_db_type:
            # Same database: strict comparison (normalize only precision/scale)
            source_type = self._normalize_type_strict(source_type_str)
            target_type = self._normalize_type_strict(target_type_str)
        else:
            # Cross-database: canonical type comparison
            source_db = source_db_type or self.source_db_type
            target_db = target_db_type or self.target_db_type
            source_type = normalize_database_type(source_type_str, source_db)
            target_type = normalize_database_type(target_type_str, target_db)

        if source_type != target_type:
            differences.append(f"Type differs: {source_col.get('type')} vs {target_col.get('type')}")

        # Compare nullable
        if source_col.get('nullable') != target_col.get('nullable'):
            differences.append(f"Nullable differs: {source_col.get('nullable')} vs {target_col.get('nullable')}")

        # Compare default
        source_default = source_col.get('default')
        target_default = target_col.get('default')
        if str(source_default) != str(target_default):
            differences.append(f"Default differs: {source_default} vs {target_default}")

        # Compare comment
        if source_col.get('comment') != target_col.get('comment'):
            differences.append(f"Comment differs")

        return differences

    def _normalize_type_strict(self, type_str: str) -> str:
        """Normalize SQL type string for same-database comparison.

        Handles VARCHAR(n) vs VARCHAR(m) as same base type.
        Keeps precision for DECIMAL/NUMERIC types.
        """
        if not type_str:
            return ''

        type_str = type_str.lower().strip()

        # Extract base type (e.g., 'varchar(255)' -> 'varchar')
        if '(' in type_str:
            base_type = type_str.split('(')[0]
            # For DECIMAL/NUMERIC, include precision
            if base_type in ('decimal', 'numeric'):
                return type_str  # Keep full specification
            return base_type

        return type_str

    def _normalize_type(self, type_str: str, db_type: Optional[str] = None) -> str:
        """Normalize database type to canonical form.

        Uses type_mapping module for cross-database type normalization.

        Args:
            type_str: Database-specific type string
            db_type: Database type ('mysql' or 'oracle')
        """
        db = db_type or self.source_db_type
        return normalize_database_type(type_str, db)

    def compare_indexes(self, source: dict, target: dict) -> List[IndexDiff]:
        """Compare indexes between two tables."""
        diffs = []

        source_indexes = {idx['name']: idx for idx in source.get('indexes', [])}
        target_indexes = {idx['name']: idx for idx in target.get('indexes', [])}

        source_names = set(source_indexes.keys())
        target_names = set(target_indexes.keys())

        # Removed indexes
        for name in source_names - target_names:
            diffs.append(IndexDiff(
                index_name=name,
                diff_type='removed',
                source_def=source_indexes[name],
                target_def=None,
                differences=['Index exists in source but not in target'],
            ))

        # Added indexes
        for name in target_names - source_names:
            diffs.append(IndexDiff(
                index_name=name,
                diff_type='added',
                source_def=None,
                target_def=target_indexes[name],
                differences=['Index exists in target but not in source'],
            ))

        # Modified indexes
        for name in source_names & target_names:
            idx_diffs = self._compare_index_definitions(
                source_indexes[name],
                target_indexes[name],
            )
            if idx_diffs:
                diffs.append(IndexDiff(
                    index_name=name,
                    diff_type='modified',
                    source_def=source_indexes[name],
                    target_def=target_indexes[name],
                    differences=idx_diffs,
                ))

        return diffs

    def _compare_index_definitions(self, source_idx: dict, target_idx: dict) -> List[str]:
        """Compare two index definitions."""
        differences = []

        # Compare columns (order matters)
        source_cols = source_idx.get('columns', [])
        target_cols = target_idx.get('columns', [])
        if source_cols != target_cols:
            differences.append(f"Columns differ: {source_cols} vs {target_cols}")

        # Compare unique flag
        if source_idx.get('unique') != target_idx.get('unique'):
            differences.append(f"Unique differs: {source_idx.get('unique')} vs {target_idx.get('unique')}")

        # Compare index type
        if source_idx.get('index_type') != target_idx.get('index_type'):
            differences.append(f"Type differs: {source_idx.get('index_type')} vs {target_idx.get('index_type')}")

        return differences

    def compare_constraints(self, source: dict, target: dict) -> List[ConstraintDiff]:
        """Compare constraints between two tables."""
        diffs = []

        # Compare primary keys
        source_pk = source.get('primary_key')
        target_pk = target.get('primary_key')
        pk_diffs = self._compare_primary_keys(source_pk, target_pk)
        diffs.extend(pk_diffs)

        # Compare foreign keys
        source_fks = {fk['name']: fk for fk in source.get('foreign_keys', [])}
        target_fks = {fk['name']: fk for fk in target.get('foreign_keys', [])}
        fk_diffs = self._compare_foreign_keys(source_fks, target_fks)
        diffs.extend(fk_diffs)

        # Compare unique constraints
        source_uc = {uc['name']: uc for uc in source.get('unique_constraints', [])}
        target_uc = {uc['name']: uc for uc in target.get('unique_constraints', [])}
        uc_diffs = self._compare_unique_constraints(source_uc, target_uc)
        diffs.extend(uc_diffs)

        return diffs

    def _compare_primary_keys(self, source_pk: Optional[dict], target_pk: Optional[dict]) -> List[ConstraintDiff]:
        """Compare primary keys."""
        if source_pk is None and target_pk is None:
            return []

        if source_pk is None:
            return [ConstraintDiff(
                constraint_name='PRIMARY KEY',
                diff_type='added',
                constraint_type='PRIMARY KEY',
                source_def=None,
                target_def=target_pk,
                differences=['Primary key exists in target but not in source'],
            )]

        if target_pk is None:
            return [ConstraintDiff(
                constraint_name='PRIMARY KEY',
                diff_type='removed',
                constraint_type='PRIMARY KEY',
                source_def=source_pk,
                target_def=None,
                differences=['Primary key exists in source but not in target'],
            )]

        # Both exist - compare columns
        source_cols = set(source_pk.get('columns', []))
        target_cols = set(target_pk.get('columns', []))
        if source_cols != target_cols:
            return [ConstraintDiff(
                constraint_name='PRIMARY KEY',
                diff_type='modified',
                constraint_type='PRIMARY KEY',
                source_def=source_pk,
                target_def=target_pk,
                differences=[f'Columns differ: {source_pk.get("columns")} vs {target_pk.get("columns")}'],
            )]

        return []

    def _compare_foreign_keys(
        self,
        source_fks: dict,
        target_fks: dict,
    ) -> List[ConstraintDiff]:
        """Compare foreign keys."""
        diffs = []

        source_names = set(source_fks.keys())
        target_names = set(target_fks.keys())

        # Removed FKs
        for name in source_names - target_names:
            diffs.append(ConstraintDiff(
                constraint_name=name,
                diff_type='removed',
                constraint_type='FOREIGN KEY',
                source_def=source_fks[name],
                target_def=None,
                differences=['Foreign key exists in source but not in target'],
            ))

        # Added FKs
        for name in target_names - source_names:
            diffs.append(ConstraintDiff(
                constraint_name=name,
                diff_type='added',
                constraint_type='FOREIGN KEY',
                source_def=None,
                target_def=target_fks[name],
                differences=['Foreign key exists in target but not in source'],
            ))

        # Modified FKs
        for name in source_names & target_names:
            fk_diffs = self._compare_fk_definitions(source_fks[name], target_fks[name])
            if fk_diffs:
                diffs.append(ConstraintDiff(
                    constraint_name=name,
                    diff_type='modified',
                    constraint_type='FOREIGN KEY',
                    source_def=source_fks[name],
                    target_def=target_fks[name],
                    differences=fk_diffs,
                ))

        return diffs

    def _compare_fk_definitions(self, source_fk: dict, target_fk: dict) -> List[str]:
        """Compare two foreign key definitions."""
        differences = []

        if source_fk.get('referred_table') != target_fk.get('referred_table'):
            differences.append(f"Referred table differs")

        if source_fk.get('columns') != target_fk.get('columns'):
            differences.append(f"Columns differ")

        if source_fk.get('referred_columns') != target_fk.get('referred_columns'):
            differences.append(f"Referred columns differ")

        return differences

    def _compare_unique_constraints(
        self,
        source_uc: dict,
        target_uc: dict,
    ) -> List[ConstraintDiff]:
        """Compare unique constraints."""
        diffs = []

        source_names = set(source_uc.keys())
        target_names = set(target_uc.keys())

        # Removed UCs
        for name in source_names - target_names:
            diffs.append(ConstraintDiff(
                constraint_name=name,
                diff_type='removed',
                constraint_type='UNIQUE',
                source_def=source_uc[name],
                target_def=None,
                differences=['Unique constraint exists in source but not in target'],
            ))

        # Added UCs
        for name in target_names - source_names:
            diffs.append(ConstraintDiff(
                constraint_name=name,
                diff_type='added',
                constraint_type='UNIQUE',
                source_def=None,
                target_def=target_uc[name],
                differences=['Unique constraint exists in target but not in source'],
            ))

        # Modified UCs
        for name in source_names & target_names:
            source_cols = set(source_uc[name].get('columns', []))
            target_cols = set(target_uc[name].get('columns', []))
            if source_cols != target_cols:
                diffs.append(ConstraintDiff(
                    constraint_name=name,
                    diff_type='modified',
                    constraint_type='UNIQUE',
                    source_def=source_uc[name],
                    target_def=target_uc[name],
                    differences=[f'Columns differ: {source_cols} vs {target_cols}'],
                ))

        return diffs
