---
phase: 03-data-comparison-engine
plan: 04
type: execute
wave: 4
depends_on: ["03-PLAN"]
files_modified:
  - frontend/src/App.tsx
  - backend/app/comparison/data.py
  - backend/app/api/data_compare.py
autonomous: true
requirements:
  - UI-DATA-04
  - PERF-01
  - ERROR-01

must_haves:
  truths:
    - "DataDiffViewer integrated into App.tsx"
    - "Full comparison flow works end-to-end"
    - "Error cases handled gracefully"
    - "Large table comparison performs acceptably"
  artifacts:
    - path: frontend/src/App.tsx
      provides: Application main component with data comparison
      contains: "DataDiffViewer", "import from './components/DataDiffViewer'"
  key_links:
    - from: frontend/src/App.tsx
      to: frontend/src/components/DataDiffViewer.tsx
      via: "Import and render DataDiffViewer"
      pattern: "import { DataDiffViewer } from './components/DataDiffViewer'"
---

<objective>
Integrate data comparison components into application and handle edge cases for production readiness.

Purpose: Complete Phase 3 by ensuring end-to-end functionality, proper error handling, and acceptable performance.
Output: Integrated UI, robust error handling, performance optimizations.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03-data-comparison-engine/CONTEXT.md
@.planning/phases/03-data-comparison-engine/03-PLAN.md
@frontend/src/App.tsx (current application structure)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Integrate DataDiffViewer into App.tsx</name>
  <files>frontend/src/App.tsx</files>
  <read_first>
    - frontend/src/App.tsx (current structure)
    - frontend/src/components/DataDiffViewer.tsx (from Wave 3)
  </read_first>
  <action>
    Update frontend/src/App.tsx:

    1. Import DataDiffViewer component:
       ```tsx
       import { DataDiffViewer } from './components/DataDiffViewer';
       ```

    2. Add route or conditional rendering for data comparison:
       - Option A: Add new route "/data-compare" in React Router
       - Option B: Add tab switching between Schema Compare and Data Compare
       - Recommended: Option B for consistency with existing UI

    3. Add state for active tab/mode:
       - 'schema' | 'data' comparison modes

    4. Render DataDiffViewer when data mode selected:
       - Pass required props (connection IDs, table names)
       - Handle navigation from table browser to data comparison

    5. Verify build succeeds:
       - Run `npm run build`
       - Fix any TypeScript errors
  </action>
  <acceptance_criteria>
    - DataDiffViewer imported in App.tsx
    - Data comparison UI accessible from main app
    - Tab switching or routing works correctly
    - npm run build succeeds without errors
    - No console errors in browser
  </acceptance_criteria>
  <verify>
    <automated>grep "DataDiffViewer" frontend/src/App.tsx</automated>
  </verify>
  <done>DataDiffViewer integrated into main application</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Add error handling for edge cases</name>
  <files>backend/app/api/data_compare.py, frontend/src/components/DataDiffViewer.tsx</files>
  <read_first>
    - backend/app/api/data_compare.py
    - frontend/src/components/DataDiffViewer.tsx
  </read_first>
  <action>
    Enhance error handling:

    Backend (backend/app/api/data_compare.py):
    1. Handle connection errors:
       - Database unreachable → return 503 Service Unavailable
       - Authentication failure → return 401 Unauthorized
       - Table not found → return 404 Not Found

    2. Handle comparison errors:
       - Timeout → return 504 Gateway Timeout
       - Memory limit exceeded → return 413 Payload Too Large
       - Type mismatch (cross-db comparison) → return 400 Bad Request

    3. Add detailed error messages:
       - Include actionable error information
       - Log full error details server-side

    Frontend (frontend/src/components/DataDiffViewer.tsx):
    1. Display user-friendly error messages:
       - Map HTTP status codes to user messages
       - Provide guidance for resolution

    2. Add retry mechanism:
       - "Retry" button for transient errors
       - Preserve user configuration on retry
  </action>
  <acceptance_criteria>
    - Backend handles all error cases with appropriate status codes
    - Frontend displays user-friendly error messages
    - Error messages provide actionable guidance
    - Retry button available for recoverable errors
    - User configuration preserved on error
  </acceptance_criteria>
  <verify>
    <automated>grep -E "HTTPException|503|404|504" backend/app/api/data_compare.py</automated>
  </verify>
  <done>Comprehensive error handling implemented for edge cases</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Performance optimization for large tables</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - backend/app/comparison/data.py (DataComparator implementation)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (Performance notes)
  </read_first>
  <action>
    Optimize DataComparator for performance:

    1. Implement streaming queries:
       - Use server-side cursors (SQLAlchemy execution_options)
       - Fetch rows in batches (yield from generator)
       - Clear batch memory after processing

    2. Optimize hash computation:
       - Hash incrementally (don't build full string)
       - Use hashlib.update() for streaming hash

    3. Optimize sampling query:
       - Use TABLESAMPLE if available (MySQL 8.0+)
       - Fallback to modulo on primary key
       - Ensure index on primary key

    4. Add progress tracking:
       - Track processed rows
       - Estimate completion percentage
       - Optional: yield progress updates

    5. Add timeout protection:
       - Set query timeout (SQLAlchemy statement timeout)
       - Raise TimeoutError if exceeded
       - Return partial results if available
  </action>
  <acceptance_criteria>
    - Uses server-side cursors for memory efficiency
    - Hash computation uses streaming approach
    - Sampling query optimized with TABLESAMPLE or index
    - Progress tracking implemented
    - Timeout protection prevents hanging queries
    - Memory usage stays bounded regardless of table size
  </acceptance_criteria>
  <verify>
    <automated>grep -E "execution_options|yield|streaming" backend/app/comparison/data.py</automated>
  </verify>
  <done>Performance optimizations implemented for large table comparison</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Cross-database type handling (optional/deferred)</name>
  <files>backend/app/comparison/data.py</files>
  <read_first>
    - backend/app/comparison/data.py
    - backend/app/comparison/type_mapping.py
  </read_first>
  <action>
    Handle cross-database type differences (MySQL vs Oracle):

    Note: This task may be deferred to Phase 4 if cross-database
    data comparison is out of scope for Phase 3.

    If implementing:
    1. Add type normalization in field comparison:
       - Use type_mapping module to normalize types
       - Handle type conversions (VARCHAR vs VARCHAR2)
       - Handle numeric type differences (INT vs NUMBER)

    2. Handle NULL consistently:
       - Oracle empty string = NULL
       - MySQL empty string != NULL
       - Document behavior difference

    3. Handle case sensitivity:
       - Oracle stores VARCHAR in exact case
       - MySQL case depends on collation
       - Normalize for comparison
  </action>
  <acceptance_criteria>
    - Cross-database type comparison documented
    - Type normalization applied where needed
    - NULL handling documented for cross-db mode
    - Or: Deferred to Phase 4 with documentation
  </acceptance_criteria>
  <verify>
    <automated>grep -E "cross.*database|type.*normal" backend/app/comparison/data.py</automated>
  </verify>
  <done>Cross-database type handling implemented or deferred with documentation</done>
</task>

</tasks>

<verification>
- Full end-to-end comparison flow works
- UI accessible from main application
- Error cases display user-friendly messages
- Large table comparison completes within time limits
- Memory usage stays bounded
- Timeout protection prevents hanging
- Progress feedback provided to user
</verification>

<success_criteria>
- frontend/src/App.tsx integrates DataDiffViewer
- Error handling covers all edge cases
- Performance acceptable for tables up to 10M rows
- Memory usage stays under 500MB for large comparisons
- User can successfully complete data comparison workflow
</success_criteria>

<output>
After completion, create `.planning/phases/03-data-comparison-engine/03-data-comparison-engine-04-SUMMARY.md` with:
- Integration approach and decisions
- Error handling matrix (status codes, messages)
- Performance optimization results
- Known limitations and deferred items
</output>
