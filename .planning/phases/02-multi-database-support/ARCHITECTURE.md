# Phase 2: Multi-Database Support - Architecture Overview

## System Architecture After Phase 2

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  ConnectionList  │  │   TableBrowser   │  │    SchemaDiffViewer      │  │
│  │  (Phase 1)       │  │   (Phase 1)      │  │    + DB Type Info        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│                                                            │                 │
│  ┌─────────────────────────────────────────────────────────▼──────────┐    │
│  │                      ReportViewer (NEW - Phase 2)                   │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                          │    │
│  │  │ Export HTML     │  │  Export Excel   │                          │    │
│  │  └─────────────────┘  └─────────────────┘                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    useComparison Hook (Enhanced)                      │   │
│  │  - compareSchemas()                                                   │   │
│  │  - exportHTML() [NEW]                                                 │   │
│  │  - exportExcel() [NEW]                                                │   │
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
│  │  │ (Phase 1)           │  │  /schema            │                  │   │
│  │  └─────────────────────┘  └─────────────────────┘                  │   │
│  │  ┌─────────────────────┐  ┌─────────────────────┐                  │   │
│  │  │ /api/reports        │  │  /api/tasks         │                  │   │
│  │  │ /html [NEW]         │  │  /{task_id}         │                  │   │
│  │  │ /excel [NEW]        │  │                     │                  │   │
│  │  └─────────────────────┘  └─────────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    Report Generators (NEW)                             │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐            │  │
│  │  │ HTMLReportGenerator     │  │  ExcelReportGenerator   │            │  │
│  │  │ - Jinja2 templates      │  │  - openpyxl             │            │  │
│  │  │ - Styled HTML output    │  │  - Multi-sheet xlsx     │            │  │
│  │  └─────────────────────────┘  └─────────────────────────┘            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    SchemaComparator (Enhanced)                         │  │
│  │  - Database-aware comparison (same-db vs cross-db modes)              │  │
│  │  - Type normalization via type_mapping module                         │  │
│  │  - Supports: MySQL vs MySQL, Oracle vs Oracle, MySQL vs Oracle        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                    Database Adapter Factory                            │  │
│  │  ┌─────────────────────────────────────────────────────────────┐     │  │
│  │  │  get_adapter(db_type, config) → DatabaseAdapter             │     │  │
│  │  └─────────────────────────────────────────────────────────────┘     │  │
│  │         │                                       │                     │  │
│  │         ▼                                       ▼                     │  │
│  │  ┌─────────────────┐                   ┌─────────────────┐           │  │
│  │  │  MySQLAdapter   │                   │  OracleAdapter  │           │  │
│  │  │  (Phase 1)      │                   │  (NEW - Phase 2)│           │  │
│  │  │  - information  │                   │  - ALL_* views  │           │  │
│  │  │    _schema      │                   │  - oracledb     │           │  │
│  │  └─────────────────┘                   └─────────────────┘           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
        ┌───────────────────────┐           ┌───────────────────────┐
        │     MySQL Database    │           │    Oracle Database    │
        │   (5.7 / 8.0+)        │           │   (11g / 12c / 19c+)  │
        └───────────────────────┘           └───────────────────────┘
```

---

## Data Flow: Report Export

```
┌──────────┐     ┌───────────┐     ┌──────────────┐     ┌─────────────┐
│  User    │────▶│  Compare  │────▶│  SchemaDiff  │────▶│ ReportViewer│
│  clicks  │     │  schemas  │     │   response   │     │  component  │
│  Export  │     └───────────┘     └──────────────┘     └─────────────┘
└──────────┘                                                   │
          │                                                    │
          │◀───────────────────────────────────────────────────┘
          │
          ▼     ┌─────────────────────────────────────────┐
          │     │  POST /api/reports/html or /excel       │
          │     │  - diff_result: SchemaDiffResponse      │
┌─────────▼─────┤  - source_db: string                    │
│  FastAPI      │  - target_db: string                    │
│  Endpoint     │                                         │
└─────────┬─────┤  Returns: FileResponse (downloadable)   │
          │     └─────────────────────────────────────────┘
          │
          ▼     ┌─────────────────────────────────────────┐
          │     │  ReportGenerator                        │
          │     │  1. Receive SchemaDiffResponse          │
┌─────────▼─────┤  2. Apply Jinja2 template (HTML)        │
│  Generator    │     or openpyxl (Excel)                 │
└─────────┬─────┤  3. Write to temp file                  │
          │     │  4. Return file path                    │
          │     └─────────────────────────────────────────┘
          │
          ▼
┌──────────────────┐
│  Downloaded File │
│  - .html or .xlsx│
│  - Styled output │
│  - All diff data │
└──────────────────┘
```

---

## Database Adapter Interface

```
┌─────────────────────────────────────────────────────────────┐
│                   DatabaseAdapter (ABC)                      │
├─────────────────────────────────────────────────────────────┤
│  + __init__(connection_config: dict)                         │
│  + connect() → Any                                           │
│  + disconnect() → None                                       │
│  + get_tables() → list[dict]                                 │
│  + get_table_metadata(table_name: str) → dict               │
│  + test_connection() → bool                                  │
│  + get_database_type() → str                                 │
│  + get_database_version() → str                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
            ┌───────────────┴───────────────┐
            │                               │
┌───────────┴───────────┐       ┌───────────┴───────────┐
│    MySQLAdapter       │       │    OracleAdapter      │
├───────────────────────┤       ├───────────────────────┤
│ - Uses:               │       │ - Uses:               │
│   mysql-connector     │       │   oracledb            │
│   SQLAlchemy inspect  │       │   SQLAlchemy inspect  │
│                       │       │                       │
│ - Queries:            │       │ - Queries:            │
│   information_schema  │       │   ALL_TABLES          │
│   TABLES, COLUMNS     │       │   ALL_TAB_COLUMNS     │
│   STATISTICS          │       │   ALL_CONSTRAINTS     │
│   TABLE_CONSTRAINTS   │       │   ALL_INDEXES         │
│                       │       │   ALL_COL_COMMENTS    │
└───────────────────────┘       └───────────────────────┘
```

---

## Type Mapping Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Input: Database-Specific Types                  │
│  MySQL: VARCHAR(255), INT(11), DECIMAL(10,2), DATETIME       │
│  Oracle: VARCHAR2(255), NUMBER(11), NUMBER(10,2), TIMESTAMP  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           normalize_database_type() Function                 │
│  1. Extract base type (remove precision/scale)              │
│  2. Lookup in CANONICAL_TYPES mapping                        │
│  3. Return canonical type                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Output: Canonical Types                         │
│  'string', 'integer', 'decimal', 'datetime', 'binary', etc.  │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    Same DB Mode                    Cross-DB Mode
    (MySQL vs MySQL)                (MySQL vs Oracle)
            │                               │
            ▼                               ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  Strict Match    │          │  Canonical Match │
    │  VARCHAR(255) == │          │  VARCHAR(255) ≈  │
    │  VARCHAR(255)    │          │  VARCHAR2(255)   │
    │  (exact string)  │          │  (both 'string') │
    └──────────────────┘          └──────────────────┘
```

---

## Report Structure

### HTML Report

```
┌────────────────────────────────────────────────────────────┐
│  DB Schema Comparison Report                               │
│  Generated: 2026-03-28 14:30:00                            │
├────────────────────────────────────────────────────────────┤
│  Source: MySQL 8.0.32 (prod_db)                            │
│  Target: MySQL 5.7.40 (staging_db)                         │
├────────────────────────────────────────────────────────────┤
│  SUMMARY                                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┐  │
│  │  Column Diffs  │  Index Diffs    │  Constraint Diffs│  │
│  │       5        │        2        │        1        │  │
│  └─────────────────┴─────────────────┴─────────────────┘  │
├────────────────────────────────────────────────────────────┤
│  ▼ COLUMN DIFFERENCES (5)                                  │
│  ┌──────────┬────────────┬─────────────┬─────────────────┐ │
│  │ Column   │ Diff Type  │   Source    │    Target       │ │
│  ├──────────┼────────────┼─────────────┼─────────────────┤ │
│  │ email    │ [MODIFIED] │ NULL | text │ NOT NULL | text │ │
│  │ age      │ [ADDED]    │    N/A      │    INT          │ │
│  └──────────┴────────────┴─────────────┴─────────────────┘ │
├────────────────────────────────────────────────────────────┤
│  ▼ INDEX DIFFERENCES (2)                                   │
│  ┌──────────┬────────────┬─────────────┬─────────────────┐ │
│  │ Index    │ Diff Type  │   Source    │    Target       │ │
│  ├──────────┼────────────┼─────────────┼─────────────────┤ │
│  │ idx_name │ [ADDED]    │    N/A      │  BTREE (name)   │ │
│  └──────────┴────────────┴─────────────┴─────────────────┘ │
├────────────────────────────────────────────────────────────┤
│  ▼ CONSTRAINT DIFFERENCES (1)                              │
│  ┌──────────┬────────────┬─────────────┬─────────────────┐ │
│  │ Constraint│Diff Type  │   Source    │    Target       │ │
│  ├──────────┼────────────┼─────────────┼─────────────────┤ │
│  │ PRIMARY  │ [MODIFIED] │  (id)       │  (id, email)    │ │
│  └──────────┴────────────┴─────────────┴─────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Excel Report Structure

```
Sheet 1: Summary
┌────────────────────────────────────────────────────────────┐
│  Comparison Summary                                         │
│  Generated: 2026-03-28 14:30:00                            │
│  Source: MySQL 8.0.32 (prod_db)                            │
│  Target: MySQL 5.7.40 (staging_db)                         │
│                                                             │
│  Statistics:                                                │
│  Column Differences: 5                                      │
│  Index Differences: 2                                       │
│  Constraint Differences: 1                                  │
│  Total: 8                                                   │
└────────────────────────────────────────────────────────────┘

Sheet 2: Column Differences
┌──────────┬────────────┬─────────────┬──────────────────────┐
│ Column   │ Diff Type  │   Source    │    Target            │
├──────────┼────────────┼─────────────┼──────────────────────┤
│ email    │ MODIFIED   │ NULL | text │ NOT NULL | text      │
│ age      │ ADDED      │    N/A      │    INT               │
└──────────┴────────────┴─────────────┴──────────────────────┘
(Rows color-coded: Green=Added, Yellow=Modified, Red=Removed)

Sheet 3: Index Differences
(Same structure as columns)

Sheet 4: Constraint Differences
(Same structure as columns)
```

---

## Wave Dependencies

```
        Wave 1                        Wave 2                        Wave 3
    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
    │  01-PLAN    │               │  02-PLAN    │               │  04-PLAN    │
    │             │               │             │               │             │
    │ OracleAdapt │               │  HTML       │               │  Report     │
    │ erFactory   │──────────────▶│  Excel      │──────────────▶│  Viewer UI  │
    │             │               │  Generators │               │             │
    │             │               │             │               │             │
    └─────────────┘               └──────┬──────┘               └─────────────┘
                                         │
                                         │
                                ┌────────▼──────┐
                                │  03-PLAN      │
                                │               │
                                │ Type Mapping  │
                                │ Enhanced Comp │
                                └───────────────┘

    Legend:
    ──────▶  Dependency (must complete first)
```

---

## Technology Stack Additions (Phase 2)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Oracle Driver | oracledb ^2.0 | Oracle database connectivity |
| HTML Templates | Jinja2 ^3.1 | Report templating |
| Excel Generation | openpyxl ^3.1 | .xlsx file creation |
| Type Mapping | Custom module | Cross-database type normalization |

---

*This architecture document complements the PLAN.md by providing visual diagrams of the system structure and data flow.*
