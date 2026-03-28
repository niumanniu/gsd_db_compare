---
phase: 03-data-comparison-engine
plan: 02
type: execute
wave: 2
depends_on: ["01-PLAN"]
files_modified:
  - backend/app/schemas/api.py
  - backend/app/api/data_compare.py
  - backend/app/db/models.py
autonomous: true
requirements:
  - DATA-COMP-06
  - API-DATA-01
  - API-DATA-02

must_haves:
  truths:
    - "DataCompareRequest schema defined with all fields"
    - "DataCompareResponse schema includes summary and diffs"
    - "POST /api/compare/data endpoint implemented"
    - "Task records created for comparison requests"
  artifacts:
    - path: backend/app/schemas/api.py
      provides: Pydantic schemas for data comparison
      contains: "class DataCompareRequest", "class DataCompareResponse", "class DataSummary"
    - path: backend/app/api/data_compare.py
      provides: Data comparison API endpoints
      contains: "router", "POST /api/compare/data"
  key_links:
    - from: backend/app/api/data_compare.py
      to: backend/app/comparison/data.py
      via: "Uses DataComparator"
      pattern: "from app.comparison.data import DataComparator"
---

<objective>
Create API endpoints and schemas for data comparison functionality.

Purpose: Expose data comparison engine through REST API with proper request/response validation and task tracking.
Output: Data comparison schemas, API endpoints, and task persistence.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03-data-comparison-engine/CONTEXT.md
@.planning/phases/03-data-comparison-engine/01-PLAN.md
@backend/app/api/compare.py (reference for schema comparison endpoint)
@backend/app/schemas/api.py
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create data comparison Pydantic schemas</name>
  <files>backend/app/schemas/api.py</files>
  <read_first>
    - backend/app/schemas/api.py (existing schemas)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md (API Design section)
  </read_first>
  <action>
    Add data comparison schemas to backend/app/schemas/api.py:

    1. DataCompareRequest:
       - source_connection_id: int
       - target_connection_id: int
       - source_table: str
       - target_table: str
       - mode: str = "auto" (auto|full|hash|sample)
       - threshold: int = 100000 (optional, override default)
       - sample_size: int = 1000 (optional)
       - batch_size: int = 1000 (optional)

    2. FieldDiff (for API response):
       - field_name: str
       - source_value: Any | null
       - target_value: Any | null
       - difference_type: str (value_changed, null_added, null_removed, length_diff)

    3. RowDiff (for API response):
       - primary_key_value: Any
       - diff_type: str (added|removed|modified)
       - field_diffs: list[FieldDiff]

    4. DataSummary:
       - source_row_count: int
       - target_row_count: int
       - diff_count: int
       - diff_percentage: float
       - mode_used: str
       - hash_source: str | null (if hash mode)
       - hash_target: str | null (if hash mode)
       - sampled_row_count: int | null (if sample mode)

    5. DataCompareResponse:
       - summary: DataSummary
       - diffs: list[RowDiff]
       - has_more: bool
       - truncated: bool (if diffs exceeded max return limit)
  </action>
  <acceptance_criteria>
    - DataCompareRequest schema has all required fields
    - mode field defaults to "auto"
    - threshold field defaults to 100000
    - DataSummary includes row counts and diff statistics
    - DataCompareResponse includes summary and diffs
    - All schemas have proper type hints
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class (DataCompareRequest|DataCompareResponse|DataSummary|RowDiff|FieldDiff)" backend/app/schemas/api.py</automated>
  </verify>
  <done>Data comparison Pydantic schemas created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Implement data comparison API endpoint</name>
  <files>backend/app/api/data_compare.py</files>
  <read_first>
    - backend/app/api/compare.py (reference implementation)
    - backend/app/comparison/data.py (DataComparator from Wave 1)
    - backend/app/schemas/api.py (schemas from Task 1)
  </read_first>
  <action>
    Create backend/app/api/data_compare.py:

    1. Setup:
       - Create APIRouter with prefix="/api/compare", tags=["data-compare"]
       - Import dependencies: get_db_session, get_adapter, DataComparator
       - Setup encryption/decryption for passwords (same as compare.py)

    2. POST /api/compare/data endpoint:
       - Accept DataCompareRequest
       - Fetch both connections from database
       - Validate connections exist
       - Create adapters using get_adapter() factory
       - Instantiate DataComparator with adapters
       - Call comparator.compare() with mode and options
       - Convert result to DataCompareResponse
       - Return response

    3. Error handling:
       - Connection not found → 400 Bad Request
       - Table not found → 404 Not Found
       - Comparison error → 500 Internal Server Error
       - Timeout → 504 Gateway Timeout

    4. Finally block:
       - Disconnect both adapters
  </action>
  <acceptance_criteria>
    - backend/app/api/data_compare.py exists
    - Contains APIRouter with correct prefix
    - POST /api/compare/data endpoint implemented
    - Fetches connections from database
    - Uses DataComparator for comparison
    - Returns DataCompareResponse
    - Proper error handling
  </acceptance_criteria>
  <verify>
    <automated>grep -E "router|POST|/api/compare/data" backend/app/api/data_compare.py</automated>
  </verify>
  <done>Data comparison API endpoint implemented</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Update ComparisonTask model for data comparisons</name>
  <files>backend/app/db/models.py</files>
  <read_first>
    - backend/app/db/models.py (existing models)
    - .planning/phases/03-data-comparison-engine/CONTEXT.md
  </read_first>
  <action>
    Review and verify ComparisonTask model supports data comparisons:

    1. Verify existing fields are sufficient:
       - task_type: "schema" or "data" ✓
       - source_connection_id ✓
       - target_connection_id ✓
       - source_table ✓
       - target_table ✓
       - status: pending/running/completed/failed ✓
       - result: JSON ✓
       - error_message ✓

    2. No changes needed - existing model supports data comparisons

    3. Add result storage helper (optional):
       - Method to serialize DataDiffResult to JSON for storage
  </action>
  <acceptance_criteria>
    - ComparisonTask model supports task_type="data"
    - result JSON field can store comparison results
    - No schema changes required
  </acceptance_criteria>
  <verify>
    <automated>grep -A 20 "class ComparisonTask" backend/app/db/models.py</automated>
  </verify>
  <done>ComparisonTask model verified for data comparison support</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Register data comparison router and create task records</name>
  <files>backend/app/api/__init__.py, backend/app/api/data_compare.py</files>
  <read_first>
    - backend/app/api/__init__.py (current router registration)
    - backend/app/api/data_compare.py (Task 2 output)
  </read_first>
  <action>
    1. Update backend/app/api/__init__.py:
       - Import data_compare router
       - Add to app.include_router()

    2. Enhance POST /api/compare/data to create task record:
       - Before comparison: create ComparisonTask with status="running"
       - After comparison: update status="completed", store result in JSON
       - On error: update status="failed", store error_message

    3. Add optional GET /api/compare/data/{task_id} endpoint:
       - Fetch ComparisonTask by ID
       - Return task status and result if completed
  </action>
  <acceptance_criteria>
    - Data comparison router registered in app
    - ComparisonTask records created for each comparison
    - Task status updated correctly
    - Result stored in database
    - GET endpoint retrieves task status
  </acceptance_criteria>
  <verify>
    <automated>grep "data_compare" backend/app/api/__init__.py</automated>
  </verify>
  <done>Data comparison endpoint integrated and task tracking enabled</done>
</task>

</tasks>

<verification>
- DataCompareRequest/Response schemas validate correctly
- POST /api/compare/data accepts valid requests
- API returns correct summary statistics
- Mode selection works (auto/full/hash/sample)
- Threshold override functions properly
- Task records created in database
- Task status updated after comparison
</verification>

<success_criteria>
- backend/app/schemas/api.py contains all data comparison schemas
- backend/app/api/data_compare.py implements comparison endpoint
- API endpoint returns properly formatted responses
- Comparison tasks tracked in database
- Error handling covers edge cases
</success_criteria>

<output>
After completion, create `.planning/phases/03-data-comparison-engine/03-data-comparison-engine-02-SUMMARY.md` with:
- API endpoint design decisions
- Schema field explanations
- Task tracking implementation
- Error handling approach
</output>
