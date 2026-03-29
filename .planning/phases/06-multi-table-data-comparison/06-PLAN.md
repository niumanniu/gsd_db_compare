# Phase 6 Plan: Multi-Table Data Comparison

**Phase:** 6
**Name:** Multi-Table Data Comparison
**Milestone:** v1.1

---

## Plans

### Plan 6.1: Backend Multi-Table Comparison Engine

**Goal:** Implement MultiTableDataComparator and SchemaDataComparator classes

**Tasks:**
1. Create `backend/app/comparison/multi_table.py` with MultiTableDataComparator class
   - `_compare_single_table()` - wraps DataComparator for single table
   - `compare()` - coordinates multi-table comparison
   - `_build_summary()` - aggregates results

2. Create SchemaDataComparator class in same file
   - `_get_schema_tables()` - discovers tables in schema
   - `_apply_filters()` - applies exclude/include patterns
   - `compare()` - orchestrates schema-level comparison

3. Add unit tests for both comparators

**Success Criteria:**
- [ ] MultiTableDataComparator can compare multiple table pairs
- [ ] SchemaDataComparator can discover and filter tables
- [ ] Tests pass for both classes

---

### Plan 6.2: Backend API Endpoints and Schemas

**Goal:** Add Pydantic schemas and API endpoints for multi-table and schema-level comparison

**Tasks:**
1. Update `backend/app/schemas/api.py`:
   - MultiTableDataCompareRequest/Response
   - SchemaDataCompareRequest/Response
   - TableDataResult, MultiTableDataSummary, SchemaDataCompareSummary

2. Update `backend/app/api/data_compare.py`:
   - `POST /api/compare/multi-table-data` endpoint
   - `POST /api/compare/schema-data` endpoint

3. Update `frontend/src/types/data_compare.ts`:
   - TypeScript types for new API schemas

**Success Criteria:**
- [ ] All Pydantic schemas defined with proper validation
- [ ] API endpoints accept requests and return proper responses
- [ ] TypeScript types match backend schemas

---

### Plan 6.3: Frontend Multi-Table Comparison UI

**Goal:** Create multi-table comparison form and results display

**Tasks:**
1. Create `frontend/src/components/MultiTableDataCompareForm.tsx`:
   - Connection and schema selection
   - Multi-select table checklist with checkboxes
   - Comparison mode selector (auto/hash/full/sample)
   - Submit button with loading state

2. Create `frontend/src/components/TableDataResultTable.tsx`:
   - Summary statistics cards
   - Per-table results table
   - Status badges (success/error/identical)
   - Drill-down button for each table

3. Create `frontend/src/components/ComparisonProgress.tsx`:
   - Progress bar for batch comparison
   - Per-table status indicators
   - Real-time updates during comparison

4. Create `frontend/src/hooks/useMultiTableComparison.ts`:
   - `compareTables()` mutation
   - Progress state management
   - Error handling

**Success Criteria:**
- [ ] User can select multiple tables with checkboxes
- [ ] Comparison submits and shows loading progress
- [ ] Results display summary and per-table details

---

### Plan 6.4: Frontend Schema-Level Comparison UI

**Goal:** Create schema-level comparison form and results display

**Tasks:**
1. Create `frontend/src/components/SchemaDataCompareForm.tsx`:
   - Connection and schema selection
   - Exclude patterns input (comma-separated or tag input)
   - "Only common tables" checkbox
   - Comparison mode selector (default: hash)
   - Preview: shows table count before running

2. Update comparison results component to handle schema-level results:
   - Show unmatched tables list
   - Show excluded tables list
   - Enhanced summary statistics

3. Add route/page for schema-level comparison:
   - `frontend/src/pages/SchemaDataCompare.tsx` (or integrate into existing Compare page)

4. Create `frontend/src/hooks/useSchemaDataComparison.ts`:
   - `compareSchema()` mutation
   - State management for schema comparison

**Success Criteria:**
- [ ] User can configure exclude patterns
- [ ] Preview shows table count before running
- [ ] Results show matched/unmatched/excluded tables
- [ ] Summary statistics display correctly

---

## Execution Order

```
Plan 6.1 (Backend Comparator)  →  Plan 6.2 (API Schemas/Endpoints)
                                          ↓
Plan 6.4 (Schema UI) ←────────── Plan 6.3 (Multi-Table UI)
```

**Recommended order:** 6.1 → 6.2 → 6.3 → 6.4

---

## Verification

**UAT Scenarios:**

1. **Multi-table comparison:**
   - Select 3 tables → Run comparison → See 3 results in summary
   - One table has errors → Error status shown with message
   - Click drill-down → See detailed row differences

2. **Schema-level comparison:**
   - Enter exclude pattern `sys_*` → Preview shows filtered count
   - Run comparison → Results show excluded tables list
   - Results show total tables, identical, with diffs breakdown

3. **Progress indicator:**
   - Start comparison with 10 tables → Progress updates as each table completes
   - Error on table 5 → Shows error status, continues with remaining tables

---

## Notes

- Reuse existing `DataComparator` for single-table comparison
- Serial execution to avoid connection pool exhaustion
- Default timeout: 300 seconds per table
- Hash mode recommended for schema-level comparison (fast screening)
