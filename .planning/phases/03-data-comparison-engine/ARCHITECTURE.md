# Phase 3: Data Comparison Engine - Architecture Overview

## System Architecture After Phase 3

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  ConnectionList  │  │   TableBrowser   │  │    SchemaDiffViewer      │  │
│  │  (Phase 1)       │  │   (Phase 1)      │  │    (Phase 1)             │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│                                                            │                 │
│  ┌─────────────────────────────────────────────────────────▼──────────┐    │
│  │                  DataDiffViewer (NEW - Phase 3)                     │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                          │    │
│  │  │  SummaryPanel   │  │  DrillDownTable │                          │    │
│  │  │  - Row counts   │  │  - Diff rows    │                          │    │
│  │  │  - Diff stats   │  │  - Field diffs  │                          │    │
│  │  │  - Mode badge   │  │  - Pagination   │                          │    │
│  │  └─────────────────┘  └─────────────────┘                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    useDataComparison Hook (NEW)                      │   │
│  │  - compareData()                                                      │   │
│  │  - isComparing                                                        │   │
│  │  - comparisonResult                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Routes                                   │   │
│  │  ┌─────────────────────┐  ┌─────────────────────┐                  │   │
│  │  │ /api/connections    │  │  /api/compare       │                  │   │
│  │  │ (Phase 1)           │  │  /schema (Phase 1)  │                  │   │
│  │  └─────────────────────┘  └──────────┬──────────┘                  │   │
│  │                                      │                               │   │
│  │  ┌─────────────────────┐  ┌──────────▼──────────┐                  │   │
│  │  │ /api/reports        │  │  /data [NEW]        │                  │   │
│  │  │ (Phase 2)           │  │  POST /api/compare  │                  │   │
│  │  └─────────────────────┘  │  /data              │                  │   │
│  │                           └─────────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    DataComparator (NEW - Phase 3)                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  compare(mode) - Auto-select comparison strategy                │  │  │
│  │  │    │                                                             │  │  │
│  │  │    ├─► Row Count < Threshold ──► _full_compare()               │  │  │
│  │  │    │                              (逐行比对)                      │  │  │
│  │  │    │                                                             │  │  │
│  │  │    └─► Row Count >= Threshold ──► _hash_verify()               │  │  │
│  │  │                                   (MD5 checksum)                │  │  │
│  │  │                                       │                         │  │  │
│  │  │                                       ▼                         │  │  │
│  │  │                              Hash match?                        │  │  │
│  │  │                               │        │                        │  │  │
│  │  │                              Yes      No                         │  │  │
│  │  │                               │        │                         │  │  │
│  │  │                               │        └──► _sample_compare()   │  │  │
│  │  │                            Identical      (抽样定位差异)           │  │  │
│  │  │                               │                                 │  │  │
│  │  │                               ▼                                 │  │  │
│  │  │                          Return success                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    Database Adapter Factory                            │  │
│  │  ┌─────────────────┐                   ┌─────────────────┐           │  │
│  │  │  MySQLAdapter   │                   │  OracleAdapter  │           │  │
│  │  │  (Phase 1)      │                   │  (Phase 2)      │           │  │
│  │  └─────────────────┘                   └─────────────────┘           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
        ┌───────────────────────┐           ┌───────────────────────┐
        │     MySQL Database    │           │    Oracle Database    │
        └───────────────────────┘           └───────────────────────┘
```

---

## Data Flow: Comparison Mode Selection

```
┌─────────────┐
│ User Clicks │
│  "Compare   │
│   Data"     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/compare/data                                         │
│  {                                                              │
│    "source_connection_id": 1,                                   │
│    "target_connection_id": 2,                                   │
│    "source_table": "users",                                     │
│    "target_table": "users",                                     │
│    "mode": "auto",          # auto|full|hash|sample             │
│    "threshold": 100000      # Optional, default 100K            │
│  }                                                              │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  DataComparator.compare(mode='auto')                            │
│                                                                  │
│  1. Get row counts from both tables                             │
│     - source_count = COUNT(*) FROM source_table                 │
│     - target_count = COUNT(*) FROM target_table                 │
│                                                                  │
│  2. Select mode based on row count vs threshold                 │
│     - If row_count < threshold → use _full_compare()            │
│     - If row_count >= threshold → use _hash_verify()            │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ├─────────────────┬─────────────────────────────────┐
       │                 │                                 │
       ▼                 ▼                                 ▼
┌─────────────┐   ┌─────────────┐                 ┌─────────────┐
│ Full Mode   │   │ Hash Mode   │                 │ Sample Mode │
│ (<100K rows)│   │ (>=100K)    │                 │ (Follow-up) │
└──────┬──────┘   └──────┬──────┘                 └──────┬──────┘
       │                 │                                │
       ▼                 ▼                                ▼
┌─────────────┐   ┌─────────────┐                 ┌─────────────┐
│ Batch query │   │ Compute MD5 │                 │ SELECT with │
│ all rows    │   │ checksums   │                 │ INTERVAL    │
│ (LIMIT/     │   │ for both    │                 │ sampling    │
│ OFFSET)     │   │ tables      │                 │ on PK       │
└──────┬──────┘   └──────┬──────┘                 └──────┬──────┘
       │                 │                                │
       ▼                 ▼                                ▼
┌─────────────┐   ┌─────────────┐                 ┌─────────────┐
│ Compare     │   │ Hashes      │                 │ Compare     │
│ row-by-row  │   │ match?      │                 │ sampled     │
│ in memory   │   │  - Yes: done│                 │ rows only   │
│             │   │  - No: sample│                │             │
└──────┬──────┘   └──────┬──────┘                 └──────┬──────┘
       │                 │                                │
       ▼                 ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DataDiffResult                               │
│  {                                                              │
│    "summary": {                                                 │
│      "source_row_count": 150000,                                │
│      "target_row_count": 150000,                                │
│      "diff_count": 12,                                          │
│      "diff_percentage": 0.008,                                  │
│      "mode_used": "hash+sample"                                 │
│    },                                                           │
│    "diffs": [...],  # Array of RowDiff                          │
│    "has_more": true                                            │
│  }                                                              │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: DataDiffViewer                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  SummaryPanel       │  │  DrillDownTable     │              │
│  │  - 150,000 rows     │  │  - 12 differences   │              │
│  │  - 12 diffs (0.008%)│  │  - Field highlights │              │
│  │  - Mode: hash+sample│  │  - Pagination       │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparison Strategy Matrix

| Scenario | Row Count | Mode Selected | Algorithm | Performance |
|----------|-----------|---------------|-----------|-------------|
| Small table | < 100,000 | Full | Batch query + row-by-row compare | O(n), accurate |
| Large table, identical | >= 100,000 | Hash | MD5 checksum | O(n), fast exit |
| Large table, different | >= 100,000 | Hash + Sample | MD5 + PK sampling | O(sample_size) |
| Explicit full | Any | Full | Batch query + row-by-row | O(n), accurate |
| Explicit hash | Any | Hash | MD5 checksum | O(n), binary result |
| Explicit sample | Any | Sample | PK interval sampling | O(sample_size) |

---

## DataComparator Class Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                      DataComparator                              │
├─────────────────────────────────────────────────────────────────┤
│  + __init__(source_adapter, target_adapter, threshold,          │
│             batch_size, sample_size)                             │
│                                                                  │
│  + compare(source_table, target_table, mode) → DataDiffResult   │
│                                                                  │
│  - _full_compare(source_table, target_table) → DataDiffResult   │
│  - _hash_verify(source_table, target_table) → DataDiffResult    │
│  - _sample_compare(source_table, target_table) → DataDiffResult │
│                                                                  │
│  - _compare_field(source_val, target_val, field_type) → bool    │
│  - _fetch_batch(table, offset, limit) → Generator[Row]          │
│  - _compute_hash(table) → str                                    │
│  - _get_primary_key(table) → str                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Special Field Handling

### NULL Value Comparison

```
Standard SQL Behavior:
  NULL = NULL → UNKNOWN (not equal in WHERE clause)
  NULL IS NULL → TRUE

This Project Behavior:
  NULL = NULL → TRUE (more intuitive for comparison)

Implementation:
  def _compare_field(source_val, target_val):
      if source_val is None and target_val is None:
          return True  # Both NULL → equal
      if source_val is None or target_val is None:
          return False  # One NULL → different
      return source_val == target_val
```

### BLOB/CLOB/TEXT Field Comparison

```
Strategy: Compare LENGTH only (not content)

Rationale:
  - BLOB/CLOB can be very large (MB to GB)
  - Full content comparison is expensive
  - Length difference indicates data corruption
  - Length match provides reasonable confidence

Implementation:
  def _compare_field(source_val, target_val, field_type):
      if field_type in ('BLOB', 'CLOB', 'TEXT', 'BINARY'):
          return len(source_val) == len(target_val)
      return source_val == target_val
```

---

## Sampling Algorithm

```
Primary Key Interval Sampling:

Input:
  - table: target table name
  - total_rows: estimated row count
  - sample_size: desired sample count (default 1,000)

Algorithm:
  1. Get primary key column name (pk_col)
  2. Calculate interval: interval = total_rows // sample_size
  3. Build sampling query:

     SELECT * FROM table
     WHERE pk_col % interval = 0
     ORDER BY pk_col
     LIMIT sample_size

  4. For databases without modulo support:
     Use ROW_NUMBER() OVER (ORDER BY pk_col) % interval = 0

Example:
  total_rows = 1,000,000
  sample_size = 1,000
  interval = 1,000

  Query returns rows where pk_col % 1000 = 0
  → Rows 0, 1000, 2000, 3000, ... 999000
  → Approximately 1,000 rows sampled
```

---

## Memory Management

```
Batch Processing Strategy:

┌──────────────────────────────────────────────────────────────┐
│  Memory-Bounded Comparison                                    │
│                                                               │
│  Batch 1: Fetch 1,000 rows → Compare → Release memory        │
│  Batch 2: Fetch 1,000 rows → Compare → Release memory        │
│  Batch 3: Fetch 1,000 rows → Compare → Release memory        │
│  ...                                                          │
│                                                               │
│  Peak memory usage: O(batch_size) not O(total_rows)          │
└──────────────────────────────────────────────────────────────┘

Implementation:
  def _fetch_batch(table, offset, limit):
      query = select(Table).limit(limit).offset(offset)
      result = await session.execute(query)
      for row in result:
          yield row
      # Row released from memory after yield

  async for batch in _fetch_batch(table, offset, batch_size):
      # Process batch
      compare_batch(batch)
      # Batch released from memory
```

---

## API Request/Response Flow

```
Request: POST /api/compare/data
┌─────────────────────────────────────────────────────────────┐
│ {                                                            │
│   "source_connection_id": 1,                                 │
│   "target_connection_id": 2,                                 │
│   "source_table": "orders",                                  │
│   "target_table": "orders",                                  │
│   "mode": "auto",                                            │
│   "threshold": 100000,                                       │
│   "sample_size": 1000                                        │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘

Response: 200 OK
┌─────────────────────────────────────────────────────────────┐
│ {                                                            │
│   "summary": {                                               │
│     "source_row_count": 150000,                              │
│     "target_row_count": 150000,                              │
│     "diff_count": 12,                                        │
│     "diff_percentage": 0.008,                                │
│     "mode_used": "hash+sample",                              │
│     "hash_source": "a1b2c3d4...",                            │
│     "hash_target": "x9y8z7w6..."                             │
│   },                                                         │
│   "diffs": [                                                 │
│     {                                                        │
│       "primary_key_value": 12345,                            │
│       "diff_type": "modified",                               │
│       "field_diffs": [                                       │
│         {                                                    │
│           "field_name": "email",                             │
│           "source_value": "a@example.com",                   │
│           "target_value": "b@example.com",                   │
│           "difference_type": "value_changed"                 │
│         }                                                    │
│       ]                                                      │
│     }                                                        │
│   ],                                                         │
│   "has_more": true,                                          │
│   "truncated": false                                         │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Wave Dependencies

```
        Wave 1                        Wave 2                        Wave 3
    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
    │  01-PLAN    │               │  02-PLAN    │               │  03-PLAN    │
    │             │               │             │               │             │
    │ DataCompar- │               │  API        │               │  UI         │
    │ ator Core   │──────────────▶│  Endpoints  │──────────────▶│  Components │
    │             │               │             │               │             │
    │ - Full      │               │  Schemas    │               │  DataDiff   │
    │ - Hash      │               │  Endpoint   │               │  Summary    │
    │ - Sample    │               │  Task track │               │  DrillDown  │
    └─────────────┘               └──────┬──────┘               └──────┬──────┘
                                         │                             │
                                         │                             │
                                         └──────────────┬──────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────┐
                                                │  04-PLAN    │
                                                │             │
                                                │ Integration │
                                                │ + Edge cases│
                                                └─────────────┘

    Legend:
    ──────▶  Dependency (must complete first)
```

---

## Technology Stack (Phase 3)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Comparison Engine | Python (hashlib) | MD5 checksum computation |
| Batch Processing | SQLAlchemy | Server-side cursors, generators |
| Frontend Components | React + TypeScript | UI components |
| State Management | React Query (TanStack) | Async state management |
| UI Framework | Ant Design | Pre-built components |

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Small table (<100K) | <30 seconds | End-to-end comparison |
| Large table (1M rows) | <5 minutes | Hash verification |
| Memory usage | <500MB | Peak RSS during comparison |
| Sample size | 1,000 rows | Configurable |
| Batch size | 1,000-5,000 rows | Configurable |

---

*This architecture document complements the PLAN.md files by providing visual diagrams and technical details for the Data Comparison Engine.*
