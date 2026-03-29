"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator
import re


# ============= Connection Schemas =============


class ConnectionCreate(BaseModel):
    """Schema for creating a new database connection."""

    name: str = Field(..., description="Connection name")
    db_type: str = Field(..., description="Database type (mysql, oracle)")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")


class ConnectionResponse(BaseModel):
    """Schema for connection response (password hidden)."""

    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionTestRequest(BaseModel):
    """Schema for testing a database connection."""

    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""

    success: bool
    message: str


# ============= Table Metadata Schemas =============


class TableInfo(BaseModel):
    """Basic table information."""

    table_name: str
    table_type: str
    row_count: Optional[int] = None
    create_time: Optional[datetime] = None


class SchemaInfo(BaseModel):
    """Schema information for dropdown response."""

    schema_name: str = Field(..., description="Schema name (database in MySQL, user in Oracle)")
    charset: Optional[str] = None  # MySQL: character set; Oracle: null
    collation: Optional[str] = None  # MySQL: collation; Oracle: null
    account_status: Optional[str] = None  # Oracle: account status; MySQL: null
    created_time: Optional[str] = None  # Creation time if available


class ColumnInfo(BaseModel):
    """Column metadata."""

    name: str
    type: str
    nullable: bool
    default: Optional[Any] = None
    comment: Optional[str] = None


class IndexInfo(BaseModel):
    """Index metadata."""

    name: str
    columns: list[str]
    unique: bool = False
    index_type: Optional[str] = None


class ConstraintInfo(BaseModel):
    """Constraint metadata."""

    name: str
    constraint_type: str  # PRIMARY KEY, FOREIGN KEY, UNIQUE
    columns: list[str]
    referred_table: Optional[str] = None


# ============= Comparison Schemas =============


class SchemaCompareRequest(BaseModel):
    """Request schema for schema comparison."""

    source_connection_id: int
    source_table: str
    target_connection_id: int
    target_table: str


class ColumnDiff(BaseModel):
    """Column-level difference."""

    column_name: str
    diff_type: str  # added, removed, modified
    source_definition: Optional[dict] = None
    target_definition: Optional[dict] = None
    differences: list[str] = Field(default_factory=list)


class IndexDiff(BaseModel):
    """Index-level difference."""

    index_name: str
    diff_type: str  # added, removed, modified
    source_definition: Optional[dict] = None
    target_definition: Optional[dict] = None
    differences: list[str] = Field(default_factory=list)


class ConstraintDiff(BaseModel):
    """Constraint-level difference."""

    constraint_name: str
    diff_type: str  # added, removed, modified
    constraint_type: str
    source_definition: Optional[dict] = None
    target_definition: Optional[dict] = None
    differences: list[str] = Field(default_factory=list)


class SchemaDiffResponse(BaseModel):
    """Complete schema comparison response."""

    source_table: str
    target_table: str
    column_diffs: list[ColumnDiff] = Field(default_factory=list)
    index_diffs: list[IndexDiff] = Field(default_factory=list)
    constraint_diffs: list[ConstraintDiff] = Field(default_factory=list)
    has_differences: bool = False
    source_db_type: Optional[str] = None
    target_db_type: Optional[str] = None
    comparison_mode: Optional[str] = None  # 'same-database' or 'cross-database'

    @property
    def diff_count(self) -> int:
        return len(self.column_diffs) + len(self.index_diffs) + len(self.constraint_diffs)

    @model_validator(mode='after')
    def set_has_differences(self):
        if self.diff_count > 0:
            self.has_differences = True
        # Set comparison mode if not already set
        if self.comparison_mode is None and self.source_db_type and self.target_db_type:
            self.comparison_mode = 'same-database' if self.source_db_type == self.target_db_type else 'cross-database'
        return self


class TableCompareSummary(BaseModel):
    """Summary of a single table comparison in batch/database compare."""

    source_table: str
    target_table: str
    has_differences: bool = False
    diff_count: int = 0
    status: str = 'success'  # 'success' or 'error'
    error_message: Optional[str] = None


class MultiTableCompareRequest(BaseModel):
    """Request for batch multi-table schema comparison."""

    source_connection_id: int
    target_connection_id: int
    source_tables: list[str]  # Source table names
    target_tables: list[str]  # Target table names
    table_mapping: Optional[dict[str, str]] = None  # Optional {source_table: target_table} mapping


class MultiTableCompareResponse(BaseModel):
    """Response for batch multi-table schema comparison."""

    summary: list[TableCompareSummary] = Field(default_factory=list)
    table_results: dict[str, SchemaDiffResponse] = Field(default_factory=dict)


class DatabaseCompareRequest(BaseModel):
    """Request for database-level comparison."""

    source_connection_id: int
    target_connection_id: int
    exclude_patterns: list[str] = Field(default_factory=list)  # Patterns to exclude (supports wildcards)

    def should_exclude_table(self, table_name: str) -> bool:
        """Check if a table should be excluded based on patterns."""
        for pattern in self.exclude_patterns:
            # Convert wildcard pattern to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            if re.match(f'^{regex_pattern}$', table_name, re.IGNORECASE):
                return True
        return False


class DatabaseCompareResponse(BaseModel):
    """Response for database-level comparison."""

    source_database: str
    target_database: str
    source_connection_name: str
    target_connection_name: str
    total_tables: int  # Total tables that could be compared
    compared_tables: int  # Tables actually compared
    tables_with_diffs: int  # Tables that have differences
    table_summaries: list[TableCompareSummary] = Field(default_factory=list)
    excluded_tables: list[str] = Field(default_factory=list)  # Tables excluded by pattern
    unmatched_source_tables: list[str] = Field(default_factory=list)  # Source tables without matching target
    unmatched_target_tables: list[str] = Field(default_factory=list)  # Target tables without matching source


# ============= Data Comparison Schemas =============


class DataCompareRequest(BaseModel):
    """Request schema for data comparison."""

    source_connection_id: int = Field(..., description="Source database connection ID")
    target_connection_id: int = Field(..., description="Target database connection ID")
    source_table: str = Field(..., description="Source table name")
    target_table: str = Field(..., description="Target table name")
    mode: str = Field(default="auto", description="Comparison mode: auto|full|hash|sample")
    threshold: Optional[int] = Field(default=100000, description="Row count threshold for auto mode")
    sample_size: Optional[int] = Field(default=1000, description="Sample size for sample mode")
    batch_size: Optional[int] = Field(default=1000, description="Batch size for full compare")
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds (default 300s)")


class FieldDiffAPI(BaseModel):
    """Single field difference for API response."""

    field_name: str
    source_value: Optional[Any] = None
    target_value: Optional[Any] = None
    diff_type: str  # 'value', 'null', 'type', 'length'


class RowDiffAPI(BaseModel):
    """Single row difference for API response."""

    primary_key_value: Any
    diff_type: str  # 'missing_in_target', 'missing_in_source', 'content_diff'
    field_diffs: list[FieldDiffAPI] = Field(default_factory=list)
    source_row: Optional[dict] = None
    target_row: Optional[dict] = None


class DataSummary(BaseModel):
    """Data comparison summary statistics."""

    source_row_count: int
    target_row_count: int
    diff_count: int
    diff_percentage: Optional[float] = None
    mode_used: str  # 'full', 'hash', 'sample', 'hash+sample'
    hash_source: Optional[str] = None  # MD5 hash if hash mode used
    hash_target: Optional[str] = None  # MD5 hash if hash mode used
    sampled_row_count: Optional[int] = None  # Rows sampled if sample mode used


class DataCompareResponse(BaseModel):
    """Complete data comparison response."""

    summary: DataSummary
    diffs: list[RowDiffAPI] = Field(default_factory=list)
    has_more: bool = False
    truncated: bool = False  # True if diffs exceeded max return limit
