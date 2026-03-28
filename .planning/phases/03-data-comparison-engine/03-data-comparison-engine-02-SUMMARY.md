---
phase: 03-data-comparison-engine
plan: 02
type: execute
wave: 2
completed: 2026-03-28
---

# Phase 3 Plan 02 Summary: Data Comparison API + Task Tracking

## Overview

This plan implemented the REST API layer for data comparison functionality, exposing the DataComparator engine through HTTP endpoints with proper request/response validation and task tracking.

## Implementation Details

### Task 1: Data Comparison Pydantic Schemas

**File:** `backend/app/schemas/api.py`

Added five new schemas:

1. **DataCompareRequest** - Request schema with:
   - `source_connection_id`, `target_connection_id`: Database connection IDs
   - `source_table`, `target_table`: Table names to compare
   - `mode`: Comparison mode (auto|full|hash|sample), default "auto"
   - `threshold`: Row count threshold for auto mode, default 100,000
   - `sample_size`: Sample size for sample mode, default 1,000
   - `batch_size`: Batch size for full compare, default 1,000

2. **FieldDiffAPI** - Single field difference:
   - `field_name`: Name of the field
   - `source_value`, `target_value`: Field values (Any type)
   - `difference_type`: Type of difference (value|null|type|length)

3. **RowDiffAPI** - Single row difference:
   - `primary_key_value`: Primary key value
   - `diff_type`: Row diff type (missing_in_target|missing_in_source|content_diff)
   - `field_diffs`: List of FieldDiffAPI objects
   - `source_row`, `target_row`: Full row data (optional)

4. **DataSummary** - Comparison summary statistics:
   - `source_row_count`, `target_row_count`: Row counts
   - `diff_count`: Number of differences found
   - `diff_percentage`: Percentage of rows with differences
   - `mode_used`: Comparison mode that was used
   - `hash_source`, `hash_target`: MD5 hashes (if hash mode)
   - `sampled_row_count`: Rows sampled (if sample mode)

5. **DataCompareResponse** - Complete response:
   - `summary`: DataSummary object
   - `diffs`: List of RowDiffAPI objects
   - `has_more`: Whether more diffs exist (for sample mode)
   - `truncated`: Whether diffs were truncated due to size

### Task 2: Data Comparison API Endpoint

**File:** `backend/app/api/data_compare.py`

Created new module with:

**POST /api/compare/data:**
- Accepts DataCompareRequest
- Fetches database connections from database
- Decrypts passwords using Fernet encryption
- Creates adapters using get_adapter() factory
- Instantiates DataComparator with custom settings
- Executes comparison
- Returns DataCompareResponse
- Creates and updates ComparisonTask records

**GET /api/compare/data/{task_id}:**
- Retrieves comparison task by ID
- Returns stored result from database
- Handles various task states (pending, running, failed, completed)

**Helper functions:**
- `convert_row_diff()`: Converts internal RowDiff to API RowDiffAPI
- `convert_result_to_response()`: Converts DataDiffResult to DataCompareResponse
- `create_task_record()`: Creates task record before comparison
- `update_task_completed()`: Updates task after successful comparison
- `update_task_failed()`: Updates task on error

**Error handling:**
- 400 Bad Request: Connection not found
- 404 Not Found: Task not found
- 500 Internal Server Error: Comparison or unexpected errors

### Task 3: ComparisonTask Model Verification

**File:** `backend/app/db/models.py`

Verified existing ComparisonTask model supports data comparisons:
- `task_type` field accepts "schema" or "data"
- All required fields already present (connection IDs, table names, status, result JSON)
- No changes required

### Task 4: Router Registration and Task Tracking

**File:** `backend/app/main.py`

- Imported data_compare router
- Registered router with app.include_router()
- Fixed pre-existing CORS middleware typo (duplicate allow_headers)

## Design Decisions

### 1. Schema Naming Convention
Used `FieldDiffAPI` and `RowDiffAPI` instead of `FieldDiff` and `RowDiff` to avoid naming conflicts with the internal dataclasses in `comparison/data.py`. This maintains clear separation between internal data structures and API-facing schemas.

### 2. Task Tracking Integration
Every comparison request creates a ComparisonTask record before execution:
- Status set to "running" initially
- Updated to "completed" with result JSON on success
- Updated to "failed" with error message on error

This enables:
- Async comparison support (future Celery integration)
- Result persistence and retrieval
- Audit trail of all comparisons

### 3. Result Truncation
API response limits diffs to 100 rows by default to prevent large payloads. The `truncated` flag indicates when more diffs exist. Clients can use this for pagination or drill-down scenarios.

### 4. Mode Selection
Client can override automatic mode selection:
- `auto`: System chooses based on table size
- `full`: Compare all rows (small tables)
- `hash`: MD5 checksum only (quick verification)
- `sample`: Sampled rows (large tables)

### 5. Threshold Override
Client can override the default 100,000 row threshold for auto mode selection, allowing fine-tuning for specific use cases.

## API Usage Examples

### Start Data Comparison
```bash
POST /api/compare/data
{
  "source_connection_id": 1,
  "target_connection_id": 2,
  "source_table": "users",
  "target_table": "users",
  "mode": "auto",
  "threshold": 50000
}
```

### Retrieve Task Result
```bash
GET /api/compare/data/123
```

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/schemas/api.py` | +57 lines: Added 5 new schemas |
| `backend/app/api/data_compare.py` | +308 lines: New module |
| `backend/app/main.py` | +2/-2 lines: Router registration, CORS fix |

## Verification

Schemas created:
```bash
grep -E "class (DataCompareRequest|DataCompareResponse|DataSummary|RowDiffAPI|FieldDiffAPI)" backend/app/schemas/api.py
```

Endpoint implemented:
```bash
grep -E "router|POST|/api/compare/data" backend/app/api/data_compare.py
```

Router registered:
```bash
grep "data_compare" backend/app/main.py
```

Python compilation:
```bash
python -m py_compile backend/app/schemas/api.py backend/app/api/data_compare.py backend/app/main.py
# Compilation successful
```

## Integration Points

- **DataComparator** (`comparison/data.py`): Core comparison engine from Wave 1
- **ComparisonTask** (`db/models.py`): Task persistence model
- **get_adapter** (`adapters/__init__.py`): Database adapter factory
- **DbConnection** (`db/models.py`): Connection model for fetching credentials

## Next Steps

Future enhancements could include:
1. Celery worker integration for async comparisons
2. Pagination support for large diff results
3. Diff filtering by field or diff type
4. Export diffs to CSV/Excel
5. Real-time progress updates via WebSocket

## Related Plans

- Depends on: Phase 3 Plan 01 (DataComparator Core Engine)
- Enables: Phase 3 Plan 03 (Data Comparison UI)
