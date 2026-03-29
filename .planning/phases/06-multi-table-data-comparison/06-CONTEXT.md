# Phase 6 Context: Multi-Table Data Comparison

**Phase:** 6
**Name:** Multi-Table Data Comparison
**Milestone:** v1.1

---

## Goal

实现多表批量数据比对和 Schema 级数据比对功能，让用户能够：
1. 选择多个表进行批量数据比对
2. 对整个 Schema 下所有表进行数据一致性检查

---

## Requirements (from REQUIREMENTS.md)

### Multi-Table Data Comparison (MTDC)

**MTDC-01:** User can select multiple tables from a schema for batch data comparison

**MTDC-02:** User can trigger schema-level comparison to compare all tables in a schema

**MTDC-03:** Results display summary statistics (total tables, tables with diffs, total rows compared)

**MTDC-04:** Results display per-table details (row counts, diff counts, status) with ability to drill down

**MTDC-05:** Support exclude patterns (wildcards like sys_*, *_log) to filter tables from comparison

**MTDC-06:** Progress indicator shows real-time status for each table being compared

---

## Design Reference

See design document: `docs/superpowers/specs/2026-03-29-multi-table-schema-data-comparison-design.md`

### Key Architecture Decisions

1. **MultiTableDataComparator** - Reuses existing DataComparator for single-table comparison, coordinates multi-table execution
2. **SchemaDataComparator** - Discovers tables, applies filters, delegates to MultiTableDataComparator
3. **Serial execution** - Avoid connection pool exhaustion, configurable per-table timeout
4. **Hash-first strategy** - Schema-level comparison uses hash mode for quick screening

### API Endpoints

- `POST /api/compare/multi-table-data` - Multi-table batch comparison
- `POST /api/compare/schema-data` - Schema-level comparison

### Frontend Components

- MultiTableDataCompareForm.tsx - Multi-table selection form
- SchemaDataCompareForm.tsx - Schema-level comparison form
- TableDataResultTable.tsx - Results table display
- ComparisonProgress.tsx - Progress indicator

---

## Dependencies

**Blocks:** Phase 7 (Multi-Mode Comparison), Phase 8 (Database Hardening)

**Blocked by:** Phase 3 (Data Comparison Engine - existing), Phase 5 (Schema Selection - complete)

---

## Success Criteria

1. User can select multiple tables for batch data comparison
2. User can trigger schema-level data comparison for all tables in a schema
3. Results show summary (total tables, diffs found) and per-table details
4. Support exclude patterns to filter tables from comparison
5. Progress indicator shows comparison status for each table
6. Handle large schemas with batching and timeout protection

---

## Implementation Notes

### Backend Files to Create

- `backend/app/comparison/multi_table.py` - MultiTableDataComparator, SchemaDataComparator
- `backend/app/api/data_compare.py` - Add new endpoints (multi-table-data, schema-data)
- `backend/app/schemas/api.py` - Add request/response schemas

### Frontend Files to Create

- `frontend/src/components/MultiTableDataCompareForm.tsx`
- `frontend/src/components/SchemaDataCompareForm.tsx`
- `frontend/src/components/TableDataResultTable.tsx`
- `frontend/src/components/ComparisonProgress.tsx`
- `frontend/src/hooks/useMultiTableComparison.ts`

### Existing Code to Reuse

- `backend/app/comparison/data.py` - DataComparator (reuse for single-table comparison)
- `backend/app/adapters/base.py` - DatabaseAdapter interface
- `frontend/src/components/DrillDownTable.tsx` - Reference for drill-down UI pattern
