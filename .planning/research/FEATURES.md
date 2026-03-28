# Feature Landscape: DB Compare

**Researched:** 2026-03-28

## Table Stakes (Must Have)

These features are expected by any database comparison tool:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Multi-DB Support** | MySQL (5.7/8.0+) and Oracle (12c/18c/19c+) connections | P0 |
| **Connection Management** | Save, edit, delete, test database connections | P0 |
| **Table List Discovery** | Browse available tables in connected databases | P0 |
| **Schema Comparison** | Compare columns, data types, nullability, defaults | P0 |
| **Index Comparison** | Compare indexes (type, columns, uniqueness) | P0 |
| **Constraint Comparison** | Compare PK, FK, unique, check constraints | P0 |
| **Data Comparison** | Row-by-row data diff with highlighting | P0 |
| **Side-by-Side Diff View** | Visual comparison UI | P0 |
| **Comparison Report** | Export results as HTML | P1 |

## Differentiators (Nice to Have)

These features provide competitive advantage:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Cross-Database Comparison** | Compare MySQL table structure to Oracle table | P1 |
| **Sampling Strategy** | Smart sampling for large tables (first/last N, random, boundary) | P1 |
| **Hash-Based Validation** | MD5/SHA checksum for quick data verification | P1 |
| **Scheduled Comparisons** | Recurring comparison tasks (hourly, daily, weekly) | P2 |
| **Alert Notifications** | Email, DingTalk, WeCom notifications on significant diffs | P2 |
| **Historical Tracking** | Track schema changes over time | P2 |
| **Type Mapping Visualization** | Show MySQL<->Oracle type equivalencies | P2 |
| **Performance Statistics** | Table size, row count, comparison duration | P2 |
| **Batch Comparison** | Compare multiple tables in one job | P2 |
| **Command-Line Interface** | Scriptable CLI for CI/CD integration | P3 |

## Anti-Features (Explicitly Not Building)

| Anti-Feature | Rationale for Exclusion |
|--------------|------------------------|
| **Auto Schema Sync** | Read-only tool — no DDL execution. Defer to future "sync" product |
| **Auto Data Sync** | No DML/INSERT/UPDATE/DELETE. Out of scope |
| **Real-Time Replication** | Batch comparison focus, not CDC (Change Data Capture) |
| **Database Administration** | Not a general DB admin tool — focused on comparison |
| **Query Editor** | Not a SQL client — comparison is the core use case |
| **Backup/Restore** | Completely different product category |
| **Performance Tuning** | Not a query optimizer or index advisor |
| **User Management/RBAC** | Single-user or simple auth initially, no complex permissions |
| **Mobile App** | Desktop/web-first, mobile use case is rare |
| **PostgreSQL/SQL Server Support** | Phase 1-4 scope is MySQL+Oracle only |

## Feature Prioritization Matrix

```
High Value, Low Complexity (Do First):
- MySQL connection management
- Table list discovery
- Schema comparison (columns)
- Side-by-side diff UI

High Value, High Complexity (Plan Carefully):
- Oracle connection management
- Cross-database type mapping
- Data comparison for large tables
- Hash-based validation

Low Value, Low Complexity (Filler):
- Connection test button
- Basic statistics (row count, table size)

Low Value, High Complexity (Avoid):
- Real-time sync monitoring
- Auto-remediation suggestions
- Mobile app
```

## User Stories

### Schema Comparison (Phase 1)
> As a DBA, I want to compare table structures between dev and prod databases so that I can verify deployment completeness.

**Acceptance Criteria:**
- Can select two MySQL connections
- Can select a table from each connection
- Shows column differences (added, removed, modified)
- Shows index differences
- Shows constraint differences
- Highlights data type mismatches
- Highlights default value differences

### Data Comparison (Phase 3)
> As an operations engineer, I want to compare data between two tables so that I can identify inconsistencies.

**Acceptance Criteria:**
- Can compare small tables (<10K rows) fully
- Can configure sampling for large tables
- Shows row count differences
- Shows rows only in table A
- Shows rows only in table B
- Shows rows with mismatched data
- Highlights specific column differences

### Scheduled Comparison (Phase 4)
> As a team lead, I want to schedule regular comparisons so that I'm notified when environments drift.

**Acceptance Criteria:**
- Can create recurring comparison jobs
- Can set schedule (cron-like)
- Can configure notification thresholds
- Receives email/DingTalk alert on significant differences
- Can view comparison history

## MVP Definition (Phase 1)

**In Scope:**
1. MySQL connection management (create, list, test, delete)
2. Table list browser
3. Schema comparison for MySQL tables
4. Column diff (name, type, nullable, default)
5. Index diff (name, columns, unique)
6. Basic web UI with side-by-side view

**Out of Scope:**
- Oracle support
- Data comparison
- Report export
- Scheduled tasks
- Notifications

## Feature Flags

Consider implementing feature flags for:
- `ENABLE_ORACLE` — Gate Oracle support until Phase 2
- `ENABLE_DATA_COMPARE` — Gate data comparison until Phase 3
- `ENABLE_SCHEDULING` — Gate scheduled tasks until Phase 4
- `MAX_TABLE_ROWS` — Configurable limit for full vs. sampling comparison

---
*Last updated: 2026-03-28*
