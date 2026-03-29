# Plan 6.4 Summary: Frontend Schema-Level Comparison UI

**Status:** completed
**Area:** frontend
**Phase:** 6

---

## Goal

Create schema-level comparison form and results display

---

## Tasks Completed

1. Created `frontend/src/components/SchemaDataCompareForm.tsx`:
   - Connection and schema selection
   - Exclude patterns input with tag input
   - Include patterns input (optional)
   - "Only common tables" checkbox
   - Comparison mode selector (default: hash)
   - Preview: shows table count before running
   - Displays unmatched and excluded tables

2. Created `frontend/src/hooks/useSchemaDataComparison.ts`:
   - `compareSchema()` mutation
   - State management for schema comparison
   - Progress tracking

3. Updated existing components:
   - `TableDataResultTable` - reused for displaying results
   - `ComparisonProgress` - reused for progress indication

---

## Success Criteria

- [x] User can configure exclude patterns
- [x] Preview shows table count before running
- [x] Results show matched/unmatched/excluded tables
- [x] Summary statistics display correctly

---

## Files Created

**Create:**
- `frontend/src/components/SchemaDataCompareForm.tsx`
- `frontend/src/hooks/useSchemaDataComparison.ts`

**Dependencies:**
- `frontend/src/components/TableDataResultTable.tsx` (existing)
- `frontend/src/components/ComparisonProgress.tsx` (existing)
- `frontend/src/types/data_compare.ts` (existing, extended)

---

## Implementation Notes

- Default mode is 'hash' for fast schema-level screening
- Exclude patterns support wildcards (e.g., `sys_*`, `*_log`)
- Table preview shows source/target/common table counts before running
- Unmatched tables displayed separately for source and target
- Excluded tables shown with count if more than 20
