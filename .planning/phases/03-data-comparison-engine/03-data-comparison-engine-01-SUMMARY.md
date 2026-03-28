---
phase: 03-data-comparison-engine
plan: 01
wave: 1
completed: 2026-03-28
status: completed
---

# Phase 3 Plan 01 Summary: DataComparator Core Engine

## Overview

Implemented the core `DataComparator` class with multiple comparison modes for cross-database data comparison.

## Implementation Details

### File Created

- `backend/app/comparison/data.py` - Complete DataComparator implementation

### Files Modified

- `backend/app/comparison/__init__.py` - Added exports for new classes

### Dataclasses Implemented

#### FieldDiff
Represents a single field difference between source and target rows.
- **Fields:** `field_name`, `source_value`, `target_value`, `diff_type`
- **Diff types:** `value`, `null`, `type`, `length`
- **Special handling:** Serializes binary data as `<binary:N bytes>`

#### RowDiff
Represents a single row difference between tables.
- **Fields:** `primary_key`, `diff_type`, `field_diffs`, `source_row`, `target_row`
- **Diff types:** `missing_in_target`, `missing_in_source`, `content_diff`
- **Methods:** `to_dict()` for JSON serialization

#### DataDiffResult
Complete data comparison result.
- **Fields:** `source_table`, `target_table`, `source_row_count`, `target_row_count`, `diff_count`, `mode_used`, `diffs`, `has_more`, `source_hash`, `target_hash`, `sampled_row_count`, `diff_percentage`
- **Methods:** `to_dict()` returning structured summary + diffs

### DataComparator Class

#### Constructor Parameters
- `source_adapter`: Source database adapter
- `target_adapter`: Target database adapter
- `threshold`: Row count threshold for auto mode (default: 100,000)
- `batch_size`: Rows per batch for batched queries (default: 1,000)
- `sample_size`: Rows to sample for large tables (default: 1,000)

#### Public Methods

##### `compare(source_table, target_table, mode='auto')`
Main entry point for data comparison.

**Mode Selection Logic:**
- `'full'`: Always use full compare
- `'hash'`: Always use hash verify
- `'sample'`: Always use sample compare
- `'auto'`:
  - If both tables < threshold: use `'full'`
  - Otherwise: use `'hash+sample'` (hash first, then sample if different)

**Returns:** `DataDiffResult` with comparison summary and differences

#### Private Methods

##### `_full_compare()`
Full row-by-row comparison for small tables.
- Fetches all rows using batched LIMIT/OFFSET pagination
- Builds lookup dict from target rows by primary key
- Compares each source row field-by-field
- Detects: missing rows, extra rows, content differences
- Returns all differences (has_more=False)

##### `_hash_verify()`
MD5 checksum comparison for quick difference detection.
- Computes deterministic hash for each table
- Row string format: `pk|col1|col2|...;pk2|col1|...`
- Handles NULL as `<NULL>` marker
- Handles LOB types as `<LOB:length>`
- Returns hash values in result summary
- If hashes match: tables identical
- If hashes differ: follow up with sample compare

##### `_sample_compare()`
Primary key interval sampling for large tables.
- Calculates sampling interval: `total_rows / sample_size`
- Uses modulo query: `WHERE MOD(pk_column, interval) = 0`
- Compares sampled rows field-by-field
- Returns sampled differences with `has_more=True`
- Includes `diff_percentage` extrapolated from sample

##### `_compare_field()`
Field-level comparison with special handling:
- **NULL = NULL:** Two NULL values treated as equal (non-SQL standard)
- **LOB types:** BLOB/CLOB/TEXT compared by length only
- **Normal types:** Direct value comparison

##### Helper Methods
- `_get_row_count()`: COUNT(*) query
- `_get_primary_key_column()`: From table metadata
- `_get_columns()`: Column names list
- `_get_column_types()`: Type mapping for LOB detection
- `_is_lob_type()`: Check if type is BLOB/CLOB/TEXT
- `_fetch_rows_batch()`: Paginated fetch with LIMIT/OFFSET
- `_fetch_all_rows_streaming()`: Stream all rows in batches
- `_fetch_sampled_rows()`: Modulo-based sampling
- `_compute_row_hash()`: Deterministic row string for hashing
- `_compute_table_hash()`: MD5 of concatenated rows

## Key Design Decisions

### NULL Handling
**Decision:** NULL = NULL treated as equal

Rationale: More intuitive comparison behavior, even though non-SQL standard.

Implementation:
```python
if source_value is None and target_value is None:
    return None  # Equal, no diff
```

### LOB Field Handling
**Decision:** Compare length only, not content

Rationale: BLOB/CLOB/TEXT fields can be very large; length comparison is practical.

Implementation:
```python
if self._is_lob_type(field_type):
    # Compare lengths only
    if len(source_value) != len(target_value):
        return FieldDiff(..., diff_type='length')
```

### Batch Processing
**Decision:** Use LIMIT/OFFSET pagination with configurable batch size

Rationale: Memory efficiency for large tables; avoids loading entire table at once.

Default batch size: 1,000 rows

### Sampling Strategy
**Decision:** Primary key modulo sampling

Rationale: Simple, efficient, distributes samples evenly across table.

Query:
```sql
SELECT * FROM table WHERE MOD(pk_column, interval) = 0 LIMIT sample_size
```

### Hash Strategy
**Decision:** MD5 of deterministic concatenated row strings

Rationale: Fast checksum computation; deterministic ordering by primary key.

Row string format: `pk|col1_val|col2_val|...` (columns sorted alphabetically)

## Usage Example

```python
from app.adapters import get_adapter
from app.comparison import DataComparator

# Create adapters
source_adapter = get_adapter('mysql', {'host': 'localhost', ...})
target_adapter = get_adapter('mysql', {'host': 'remote', ...})

# Create comparator
comparator = DataComparator(
    source_adapter=source_adapter,
    target_adapter=target_adapter,
    threshold=100000,
)

# Auto mode (recommended)
result = comparator.compare('users', 'users', mode='auto')

# Check results
if result.diff_count == 0:
    print("Tables are identical")
else:
    print(f"Found {result.diff_count} differences")
    print(f"Mode used: {result.mode_used}")
    for diff in result.diffs:
        print(f"  PK={diff.primary_key}: {diff.diff_type}")
```

## Acceptance Criteria Verification

- [x] `backend/app/comparison/data.py` exists
- [x] Contains `class DataComparator`
- [x] Contains dataclasses: `DataDiffResult`, `RowDiff`, `FieldDiff`
- [x] `compare()` accepts mode parameter ('auto', 'full', 'hash', 'sample')
- [x] Mode selection logic uses threshold for 'auto' mode
- [x] `_full_compare()` uses batched queries
- [x] NULL = NULL treated as equal
- [x] BLOB/CLOB/TEXT compared by length only
- [x] `_hash_verify()` computes MD5 checksums
- [x] `_sample_compare()` uses primary key interval sampling
- [x] Python syntax valid

## Dependencies

- `hashlib` (Python standard library)
- `app.adapters.DatabaseAdapter` (base class)
- `app.adapters.get_adapter` (factory)

## Next Steps

Potential future enhancements (not in scope for Wave 1):
1. Add data comparison API endpoint (`POST /api/compare/data`)
2. Add progress callbacks for long-running comparisons
3. Add configurable column filters (compare subset of columns)
4. Add row filter support (compare subset of rows with WHERE clause)
5. Excel/HTML report generation for comparison results
6. Statistical analysis of differences (pattern detection)
