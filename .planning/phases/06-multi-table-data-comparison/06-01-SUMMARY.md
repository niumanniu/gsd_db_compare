# Plan 6.1 Summary: Backend Multi-Table Comparison Engine

**Status:** pending
**Area:** backend
**Phase:** 6

---

## Goal

Implement MultiTableDataComparator and SchemaDataComparator classes

---

## Tasks

1. Create `backend/app/comparison/multi_table.py` with MultiTableDataComparator class
   - `_compare_single_table()` - wraps DataComparator for single table
   - `compare()` - coordinates multi-table comparison
   - `_build_summary()` - aggregates results

2. Create SchemaDataComparator class in same file
   - `_get_schema_tables()` - discovers tables in schema
   - `_apply_filters()` - applies exclude/include patterns
   - `compare()` - orchestrates schema-level comparison

3. Add unit tests for both comparators

---

## Success Criteria

- [ ] MultiTableDataComparator can compare multiple table pairs
- [ ] SchemaDataComparator can discover and filter tables
- [ ] Tests pass for both classes

---

## Files to Create/Modify

**Create:**
- `backend/app/comparison/multi_table.py`
- `backend/tests/comparison/test_multi_table.py`

**Dependencies:**
- `backend/app/comparison/data.py` - DataComparator (reuse)
- `backend/app/adapters/base.py` - DatabaseAdapter

---

## Implementation Notes

- Reuse existing DataComparator for single-table comparison
- Serial execution to avoid connection pool exhaustion
- Default timeout: 300 seconds per table
