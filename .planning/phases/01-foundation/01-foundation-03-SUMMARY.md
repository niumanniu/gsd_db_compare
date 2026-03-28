---
plan: 01-foundation-03
status: complete
completed: 2026-03-28
duration: ~25 min
tasks: 3/3
---

# Plan 03: Schema Comparison Engine - Summary

## What Was Built

Complete schema comparison engine that compares two table metadata structures and identifies all differences.

## Key Files Created

| File | Purpose |
|------|---------|
| `backend/app/comparison/__init__.py` | Package init |
| `backend/app/comparison/schema.py` | SchemaComparator with full comparison logic |

## Data Classes

### ColumnDiff
- `column_name`, `diff_type` (added/removed/modified)
- `source_def`, `target_def` - Original column definitions
- `differences` - List of specific differences (type, nullable, default, comment)

### IndexDiff
- `index_name`, `diff_type`
- Compares: columns (order matters), unique flag, index type

### ConstraintDiff
- `constraint_name`, `diff_type`, `constraint_type` (PRIMARY KEY, FOREIGN KEY, UNIQUE)
- Compares: columns, referred table/columns

### SchemaDiff
- `source_table`, `target_table`
- Collections: `column_diffs`, `index_diffs`, `constraint_diffs`
- Properties: `has_differences`, `diff_count`
- Method: `to_dict()` for JSON serialization

## SchemaComparator Class

### Main Method
```python
compare(source_metadata: dict, target_metadata: dict) -> SchemaDiff
```

### Comparison Methods
- `compare_columns()` - Identifies added, removed, modified columns
- `compare_indexes()` - Identifies added, removed, modified indexes
- `compare_constraints()` - Compares PK, FK, unique constraints

### Type Normalization
`_normalize_type()` handles:
- `VARCHAR(255)` vs `VARCHAR(100)` → both normalize to `varchar` (same base type)
- `DECIMAL(10,2)` → keeps full specification `decimal(10,2)` (precision matters)

## Comparison Logic

### Columns
1. Build column maps by name
2. Find removed (in source, not in target)
3. Find added (in target, not in source)
4. For common columns, compare:
   - Type (normalized)
   - Nullable
   - Default value
   - Comment

### Indexes
1. Build index maps by name
2. Find added/removed indexes
3. For common indexes, compare:
   - Column list (order matters)
   - Unique flag
   - Index type (BTREE, HASH, etc.)

### Constraints
- **Primary Keys**: Compare column lists
- **Foreign Keys**: Compare name, referred table, columns, referred columns
- **Unique Constraints**: Compare column lists

## Requirements Delivered

- [x] SCHEMA-01: Schema comparison engine
- [x] SCHEMA-02: Column, index, constraint diff identification

## Design Decisions

1. **Dataclass-based**: Clean, type-safe, serializable to dict
2. **Comprehensive diff**: Captures both high-level (added/removed) and detailed (what changed) differences
3. **Type normalization**: VARCHAR(n) variations treated as same type with different length
4. **Order-sensitive**: Index columns compared with order (idx(a,b) ≠ idx(b,a))

## Integration Points

- Uses metadata format from `MySQLAdapter.get_table_metadata()` (Plan 02)
- Returns `SchemaDiff` that converts to `SchemaDiffResponse` schema (Plan 02)
- Ready for API integration (Plan 04)

## Next Steps

Wave 2 (Plans 04, 05) will build:
- REST API endpoints to trigger comparisons
- React frontend for connection management
