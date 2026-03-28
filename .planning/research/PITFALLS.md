# Domain Pitfalls: Schema Selection & Multi-Mode Comparison

**Domain:** Database Comparison Tools — Adding Schema Selection UI and Multi-Mode Comparison
**Researched:** 2026-03-29
**Context:** Adding schema selection dropdown for database-level comparison and single/multi/database-level comparison modes to existing DB Compare application

---

## Overview

This document focuses on pitfalls **specific to adding schema selection UI and multi-mode comparison features** to the existing DB Compare application. General database comparison pitfalls (type mapping, NULL handling, etc.) are covered in the original PITFALLS.md.

---

## Critical Pitfalls

### Pitfall 1: Schema Enumeration Performance on Large Databases

**What goes wrong:** When implementing schema selection dropdowns, the naive approach fetches ALL schemas/tables upfront on connection change. Databases with hundreds of schemas (common in multi-tenant SaaS, legacy systems) cause:
- UI freeze during dropdown render (Ant Design Select with 500+ options)
- Network timeout on metadata fetch (default 30s may not be enough)
- Memory bloat storing full schema list in React state

**Why it happens:**
- Current `get_tables()` API returns complete table list without pagination
- `TableBrowser.tsx` loads all tables into `sourceTables`/`targetTables` state
- No search-as-you-type or virtualization for large lists

**Consequences:**
- Users with 1000+ tables experience 5-10 second delays
- Browser tab may crash with 5000+ tables
- Comparison workflow blocked until metadata loads

**Prevention:**
```typescript
// Use virtual scrolling for large table lists
<Select
  showSearch
  filterOption={(input, option) =>
    (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
  }
  listHeight={400}  // Fixed dropdown height
  // Consider react-window for 1000+ items
/>
```

**Backend prevention:**
```python
# Add pagination/limit to get_tables endpoint
@router.get("/{conn_id}/tables")
async def get_connection_tables(
    conn_id: int,
    limit: int = 500,  # Default cap
    search: str = "",  # Optional filter
    ...
):
    tables = adapter.get_tables()
    if search:
        tables = [t for t in tables if search.lower() in t['table_name'].lower()]
    return tables[:limit]
```

**Detection:**
- Add performance monitoring: `performance.measure()` around table fetch
- Show warning when table count exceeds 100
- Display loading indicator with table count during fetch

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 2: Cross-Database Schema Name Case Sensitivity

**What goes wrong:** MySQL schema names are case-sensitive on Linux, case-insensitive on Windows. Oracle schema names are typically uppercase. When users select schemas from dropdown:
- Selected schema name doesn't match actual schema in queries
- Table comparisons fail silently with "table not found"
- Cross-database comparisons (MySQL ↔ Oracle) break on schema reference

**Why it happens:**
- Current `get_tables()` returns schema names as-is from database
- No normalization of schema identifiers before comparison
- `information_schema.TABLES` queries use exact string matching

**Consequences:**
- Intermittent failures depending on OS/database combination
- Users see empty results for valid selections
- Debugging is difficult because error messages are generic

**Prevention:**
```python
# Normalize schema names consistently
def normalize_schema_name(schema: str, db_type: str) -> str:
    if db_type == 'oracle':
        return schema.upper()  # Oracle always uppercase
    elif db_type == 'mysql':
        # Respect lower_case_table_names setting
        return schema.lower() if is_linux_case_insensitive() else schema
    return schema

# Use explicit schema qualification in queries
query = """
    SELECT ... FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = %s COLLATE utf8mb4_general_ci  # Case-insensitive
"""
```

**Detection:**
- Log schema name mismatches during comparison
- Show warning when comparing across different database types
- Display canonical schema name format in UI hints

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 3: State Desynchronization Between Compare Modes

**What goes wrong:** When switching between single/multi/database comparison modes, selection state becomes inconsistent:
- Single-table selection persists when switching to multi-table mode
- Exclude patterns from database mode leak into multi-table mode
- Batch comparison uses stale single-table selections

**Why it happens:**
- Current implementation in `App.tsx` uses `useEffect` to reset state, but:
  - Reset order matters (resetting tables before mode causes race conditions)
  - Async operations may complete after mode switch
  - Multiple `useState` calls create temporal coupling

**Consequences:**
- Users unknowingly compare wrong tables
- Database comparison includes tables that should be excluded
- Hard-to-reproduce bugs in CI/CD pipelines

**Prevention:**
```typescript
// Use a single state object for mode-specific selections
const [compareState, setCompareState] = useState({
  mode: 'single' as CompareMode,
  singleTable: { source: null, target: null },
  multiTable: { source: [], target: [] },
  database: { excludePatterns: [] },
});

// Reset ALL mode-specific state when mode changes
useEffect(() => {
  setCompareState(prev => ({
    mode: newMode,
    singleTable: { source: null, target: null },
    multiTable: { source: [], target: [] },
    database: { excludePatterns: [] },
  }));
  resetComparison();  // Clear previous results
}, [newMode]);
```

**Detection:**
- Add debug mode that logs current selection state on compare
- Show confirmation dialog with selected tables before comparing
- Visual indicators showing which tables will be compared

**Phase:** Phase 2 - Multi-Mode Support

---

### Pitfall 4: Database-Level Comparison Memory Exhaustion

**What goes wrong:** Database-level comparison loads ALL tables into memory before returning results. Large databases (500+ tables, millions of rows) cause:
- Backend OOM crashes during metadata comparison
- Response payload exceeds API gateway limits (typically 10MB)
- Frontend freezes rendering 500+ table rows

**Why it happens:**
- Current `compare_databases` endpoint builds complete result array before returning
- No streaming or pagination of results
- `table_summaries` array grows unbounded

**Consequences:**
- Comparison fails silently with 500 error
- Users receive "Failed to compare databases" with no diagnostic info
- Server may need restart to recover memory

**Prevention:**
```python
# Stream results and cap table count
@router.post("/schema/database")
async def compare_databases(request: DatabaseCompareRequest):
    # Cap at 200 tables per comparison
    MAX_TABLES = 200
    matching_tables = sorted(source_set & target_set)[:MAX_TABLES]

    # Yield results incrementally (FastAPI StreamingResponse)
    async def generate_results():
        summaries = []
        for i, table_name in enumerate(matching_tables):
            diff = comparator.compare(...)
            summaries.append(build_summary(table_name, diff))

            # Return partial results every 50 tables
            if i % 50 == 0:
                yield json.dumps({"partial": True, "summaries": summaries})
                summaries = []

        yield json.dumps({"partial": False, "summaries": summaries})

    return StreamingResponse(generate_results())
```

**Frontend prevention:**
```typescript
// Virtualize table results
import { FixedSizeList } from 'react-window';

const DatabaseResultsTable = ({ results }) => (
  <FixedSizeList height={600} itemCount={results.length} itemSize={50}>
    {({ index, style }) => (
      <div style={style}>
        <SummaryRow data={results[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

**Detection:**
- Monitor heap usage during comparison (`process.memoryUsage()`)
- Add table count warning before starting comparison
- Implement circuit breaker: "Comparing 500+ tables may take several minutes"

**Phase:** Phase 2 - Database-Level Comparison

---

### Pitfall 5: Schema Selection Permission Blindness

**What goes wrong:** Users can see schemas in dropdown they cannot actually access. When comparison runs:
- Comparison fails with cryptic "permission denied" errors
- Partial results returned (some schemas compared, others silently skipped)
- User assumes schemas are identical when comparison never ran

**Why it happens:**
- Current `get_tables()` doesn't filter by user permissions
- No error differentiation between "schema doesn't exist" and "no permission"
- Oracle's `ALL_TABLES` shows tables user can SELECT from, MySQL shows all

**Consequences:**
- Security audit failures (users discover restricted schemas exist)
- Incomplete comparisons appear successful
- Debugging requires DBA intervention

**Prevention:**
```python
# Filter tables by actual permissions
def get_tables(self) -> list[dict]:
    # MySQL: Check INFORMATION_SCHEMA with privilege filtering
    query = """
        SELECT TABLE_NAME, TABLE_TYPE, TABLE_ROWS, CREATE_TIME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME IN (
            SELECT TABLE_NAME FROM information_schema.TABLE_PRIVILEGES
            WHERE GRANTEE = CURRENT_USER()
              AND TABLE_SCHEMA = %s
              AND PRIVILEGE_TYPE IN ('SELECT', 'SHOW VIEW')
          )
    """
    # Oracle: Use USER_TABLES instead of ALL_TABLES for permission-aware listing
```

**Detection:**
- Show permission status icon next to each schema in dropdown
- Log permission-denied errors separately from other failures
- Add "Schema Access Report" showing which schemas were actually compared

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 6: Exclude Pattern Ambiguity in Database Mode

**What goes wrong:** Wildcard patterns like `sys_*` behave differently than expected:
- `*` matches underscore in some patterns (`sys_` matches `sys_audit_log`)
- Case sensitivity varies (`USER_*` doesn't match `user_sessions` on MySQL)
- Special characters in table names break pattern matching

**Why it happens:**
- Current implementation uses simple regex conversion: `pattern.replace('*', '.*')`
- No escaping of regex special characters in table names
- Patterns applied before fetching vs. after fetching affects performance

**Consequences:**
- Users exclude wrong tables unintentionally
- Critical tables skipped from comparison
- Pattern debugging is trial-and-error

**Prevention:**
```python
# Use proper glob-to-regex conversion with escaping
import fnmatch
import re

def should_exclude_table(self, table_name: str) -> bool:
    for pattern in self.exclude_patterns:
        # fnmatch handles glob escaping correctly
        if fnmatch.fnmatch(table_name, pattern):
            return True
        # Also try case-insensitive for MySQL
        if fnmatch.fnmatch(table_name.lower(), pattern.lower()):
            return True
    return False

# Pre-compile patterns and validate before saving
def validate_exclude_pattern(pattern: str) -> tuple[bool, str]:
    """Validate pattern and return (is_valid, error_message)"""
    try:
        regex = fnmatch.translate(pattern)
        re.compile(regex)
        return True, ""
    except re.error as e:
        return False, f"Invalid pattern: {e}"
```

**Frontend prevention:**
```typescript
// Show pattern preview/matching tables in real-time
const ExcludePatternInput = ({ value, allTables, onExcludeMatch }) => {
  const matchingTables = useMemo(() => {
    const regex = new RegExp(`^${value.replace(/\*/g, '.*')}$`, 'i');
    return allTables.filter(t => regex.test(t.table_name));
  }, [value, allTables]);

  return (
    <>
      <Input value={value} onChange={...} />
      {matchingTables.length > 0 && (
        <Text type="secondary">
          This pattern will exclude: {matchingTables.map(t => t.table_name).join(', ')}
        </Text>
      )}
    </>
  );
};
```

**Detection:**
- Show "matched tables" preview as user types patterns
- Validate patterns before starting comparison
- Log excluded table count in comparison summary

**Phase:** Phase 2 - Database-Level Comparison

---

## Moderate Pitfalls

### Pitfall 7: Concurrent Comparison Race Conditions

**What goes wrong:** Users can trigger multiple comparisons simultaneously by:
- Clicking compare button multiple times before first completes
- Switching modes mid-comparison and triggering new comparison
- Opening multiple browser tabs with same connection

**Why it happens:**
- React Query mutations don't prevent concurrent calls by default
- Backend comparison endpoints are stateless
- No request deduplication or cancellation

**Prevention:**
```typescript
// Disable button during comparison
<Button
  type="primary"
  onClick={handleCompare}
  loading={isComparing}
  disabled={isComparing}  // Critical: prevent clicks
/>

// Cancel previous comparison when mode changes
const compareQuery = useMutation({
  mutationFn: compareSchemas,
  onMutate: () => {
    // Cancel any in-flight comparisons
    queryClient.removeQueries(['comparison', 'pending']);
  },
});
```

**Phase:** Phase 2 - Multi-Mode Support

---

### Pitfall 8: Table Name Encoding Issues

**What goes wrong:** Table names with special characters break comparison:
- Spaces: `My Table` → SQL injection vulnerability if not escaped
- Quotes: `Table"WithQuote` → SQL syntax errors
- Unicode: `用户表` → encoding mismatches between MySQL and Oracle

**Why it happens:**
- Current code uses parameterized queries but table names are interpolated
- `adapter.get_table_metadata(table_name)` doesn't validate/escape table names
- Cross-database comparisons may mangle non-ASCII characters

**Prevention:**
```python
# Validate and quote table names
from sqlalchemy.sql import quoted_name

def get_table_metadata(self, table_name: str) -> dict:
    # Validate table name format
    if not re.match(r'^[\w\u4e00-\u9fff]+$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    # Use quoted_name for proper escaping
    safe_table_name = quoted_name(table_name, self.requires_quoting)

    # Use parameterized query where possible
    query = text("""
        SELECT ... FROM information_schema.COLUMNS
        WHERE TABLE_NAME = :table_name
    """).bindparams(table_name=safe_table_name)
```

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 9: Schema Comparison Result Size Explosion

**What goes wrong:** Comparing schemas with hundreds of columns generates massive response payloads:
- 500-column table × 4 difference types = 2000+ diff objects
- JSON response exceeds 5MB
- Frontend table component crashes rendering 1000+ rows

**Why it happens:**
- Current `SchemaDiffResponse` has no pagination or truncation
- All diffs returned even if user only sees first 50
- No compression for highly similar schemas

**Prevention:**
```python
# Truncate and paginate diffs
@router.post("/schema", response_model=SchemaDiffResponse)
async def compare_schemas(
    request: SchemaCompareRequest,
    limit: int = 100,  # Max diffs per category
) -> SchemaDiffResponse:
    diff = comparator.compare(...)

    return SchemaDiffResponse(
        ...
        column_diffs=diff.column_diffs[:limit],
        index_diffs=diff.index_diffs[:limit],
        constraint_diffs=diff.constraint_diffs[:limit],
        truncated=len(diff.column_diffs) > limit,  # Flag for UI
    )
```

**Frontend prevention:**
```typescript
// Use virtualized table for diffs
import { FixedSizeList } from 'react-window';

<SchemaDiffViewer
  diffResult={comparisonResult}
  maxInitialDiffs={50}  // Show first 50, lazy load rest
/>
```

**Phase:** Phase 2 - Multi-Mode Support

---

## Minor Pitfalls

### Pitfall 10: Connection Change Clears User Selections

**What goes wrong:** Changing connection resets table selection, but:
- User has already selected tables for previous connection
- Comparison button state doesn't update correctly
- Error message says "select tables" but dropdown shows new tables

**Prevention:** Reset selections in the same event handler as connection change, not in useEffect.

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 11: Empty Schema Edge Case

**What goes wrong:** Empty databases or filtered schemas show:
- "No tables available" but compare button is still enabled
- Comparison runs and fails with no clear error

**Prevention:** Disable compare button when either schema has zero tables after filtering.

**Phase:** Phase 1 - Schema Selection UI

---

### Pitfall 12: Loading State Doesn't Reflect Nested Operations

**What goes wrong:** Multiple async operations (fetch source tables, fetch target tables, compare) show:
- Single loading spinner for all operations
- User can't tell which step is running
- Spinner disappears between steps making it seem like nothing is happening

**Prevention:** Use granular loading states: `isLoadingSource`, `isLoadingTarget`, `isComparing`.

**Phase:** Phase 1 - Schema Selection UI

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Schema dropdown implementation | Performance on large schemas | Implement virtual scrolling + search-as-you-type from day one |
| Multi-table selection state | State desynchronization between modes | Use single state object, reset atomically on mode change |
| Database comparison | Memory exhaustion on large databases | Add table count limits (200 max) before building full result |
| Exclude patterns UI | Pattern ambiguity | Add real-time "matching tables" preview |
| Cross-database comparison | Case sensitivity issues | Normalize schema/table names by database type |
| Error handling | Permission blindness | Differentiate "doesn't exist" from "no permission" |
| Result display | Result size explosion | Paginate diffs, truncate at 100 per category |
| Concurrent operations | Race conditions | Disable buttons during comparison, cancel in-flight requests |

---

## Integration with Existing Pitfalls

This document complements the original PITFALLS.md. When implementing schema selection and multi-mode comparison:

1. **Also apply original pitfalls:**
   - Pitfall #1 (Metadata Query Performance) - applies to schema dropdown
   - Pitfall #3 (MySQL-Oracle Type Mapping) - applies to cross-database comparison
   - Pitfall #10 (Schema Case Sensitivity) - applies to schema selection
   - Pitfall #12 (SQL Injection) - applies to dynamic table names

2. **New pitfalls are specific to:**
   - UI state management across modes
   - Large schema enumeration performance
   - Exclude pattern handling
   - Database-level comparison scalability

---

## Sources

- Internal codebase analysis: `backend/app/api/connections.py`, `backend/app/api/compare.py`, `frontend/src/App.tsx`, `frontend/src/components/TableBrowser.tsx`, `frontend/src/hooks/useComparison.ts`
- Ant Design Select performance documentation
- SQLAlchemy metadata reflection best practices
- MySQL information_schema privilege filtering
- Oracle ALL_TABLES vs USER_TABLES access patterns
- FastAPI StreamingResponse documentation
- React Query mutation concurrency patterns

---

*Last updated: 2026-03-29*
