# Phase 1: Foundation - Context

**Phase:** 01-foundation
**Goal:** 建立基础框架，实现 MySQL 表结构比对

## Design Context

### D-1: Project Structure
Backend uses FastAPI with SQLAlchemy, frontend uses React with TypeScript. Application data (connections, task history) stored in PostgreSQL.

### D-2: Database Adapter Pattern
Abstract database operations behind a common interface. MySQL adapter implemented first, Oracle adapter added in Phase 2.

### D-3: Metadata Query Strategy
Query `information_schema` for MySQL metadata:
- `information_schema.TABLES` — Table list and basic stats
- `information_schema.COLUMNS` — Column definitions
- `information_schema.STATISTICS` — Index information
- `information_schema.TABLE_CONSTRAINTS` — Constraint definitions
- `information_schema.KEY_COLUMN_USAGE` — Foreign key details

### D-4: Schema Comparison Algorithm
1. Fetch metadata from both databases
2. Normalize column types (lowercase, remove length for comparison)
3. Compare by column name:
   - Added columns (in target, not in source)
   - Removed columns (in source, not in target)
   - Modified columns (same name, different definition)
4. Compare indexes similarly
5. Compare constraints similarly

### D-5: Diff Data Structure
```python
@dataclass
class SchemaDiff:
    source_table: str
    target_table: str
    column_diffs: list[ColumnDiff]
    index_diffs: list[IndexDiff]
    constraint_diffs: list[ConstraintDiff]

@dataclass
class ColumnDiff:
    column_name: str
    diff_type: str  # 'added', 'removed', 'modified'
    source_definition: ColumnInfo | None
    target_definition: ColumnInfo | None
    differences: list[str]  # e.g., ["type", "nullable", "default"]
```

### D-6: Read-Only Enforcement
All database connections use read-only SQL queries. No DDL or DML statements executed.

### D-7: Async Task Processing
Long-running comparisons executed as Celery tasks. API returns task ID immediately. Frontend polls for completion.

### D-8: Credential Security
Database passwords encrypted at rest using `cryptography.fernet`. Encryption key from environment variable.

### D-9: Error Handling Strategy
- Connection errors → 400/401/404 HTTP responses
- Table not found → 404 with clear message
- Comparison errors → 500 with error details
- All errors logged with structured logging

### D-10: UI Design Principles
- Side-by-side diff view (like git diff)
- Color coding: green=added, red=removed, yellow=modified
- Expandable sections for columns, indexes, constraints
- Summary at top showing total differences

## Technical Context

### T-1: MySQL Version Support
- MySQL 5.7+ (information_schema structure consistent)
- MySQL 8.0+ preferred (better performance)

### T-2: SQLAlchemy Metadata Reflection
Use SQLAlchemy's `inspect()` function for metadata:
```python
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns(table_name)
indexes = inspector.get_indexes(table_name)
fk_constraints = inspector.get_foreign_keys(table_name)
pk_constraint = inspector.get_pk_constraint(table_name)
```

### T-3: FastAPI Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── connections.py   # Connection CRUD
│   │   └── compare.py       # Comparison endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py          # SQLAlchemy Base
│   │   ├── models.py        # ORM models
│   │   └── session.py       # DB session factory
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py          # DatabaseAdapter ABC
│   │   └── mysql.py         # MySQL implementation
│   ├── comparison/
│   │   ├── __init__.py
│   │   └── schema.py        # SchemaComparator
│   └── schemas/
│       ├── __init__.py
│       └── api.py           # Pydantic schemas
├── alembic/
│   └── versions/
└── pyproject.toml
```

### T-4: React Project Structure
```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── ConnectionForm.tsx
│   │   ├── ConnectionList.tsx
│   │   ├── TableBrowser.tsx
│   │   ├── SchemaDiff.tsx
│   │   └── DiffViewer.tsx
│   ├── hooks/
│   │   ├── useConnections.ts
│   │   └── useComparison.ts
│   ├── api/
│   │   └── client.ts        # Axios instance
│   └── types/
│       └── index.ts
├── package.json
└── vite.config.ts
```

### T-5: PostgreSQL Schema (App Data)
See ARCHITECTURE.md for full schema. Key tables:
- `db_connections` — Connection configurations
- `comparison_tasks` — Task history and results

### T-6: Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/db_compare
ENCRYPTION_KEY=<32-byte-key-for-fernet>
CELERY_BROKER_URL=redis://localhost:6379/0

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

## Assumptions

### A-1: User Has Database Access
Users must provide their own MySQL credentials. Application does not manage database users.

### A-2: Read-Only Database Accounts
Users should create read-only database accounts for comparison:
```sql
-- MySQL
CREATE USER 'db_compare'@'%' IDENTIFIED BY 'password';
GRANT SELECT ON information_schema.* TO 'db_compare'@'%';
GRANT SELECT ON your_database.* TO 'db_compare'@'%';
```

### A-3: Network Connectivity
Application server must have network access to MySQL databases.

### A-4: Single User Initially
Phase 1 assumes single-user or simple shared access. No authentication/authorization in Phase 1.

### A-5: MySQL First
Oracle support deferred to Phase 2. All Phase 1 development targets MySQL only.

## Constraints

### C-1: Read-Only Mode
Application never executes:
- DDL: CREATE, ALTER, DROP, TRUNCATE
- DML: INSERT, UPDATE, DELETE, MERGE
- Only SELECT queries on system views and user tables

### C-2: Performance Budget
- Metadata fetch: <5 seconds for databases with 1000 tables
- Schema comparison: <10 seconds for tables with 100 columns
- UI render: <1 second for diff display

### C-3: Memory Budget
- Process metadata: <100MB for 1000 tables
- Process data comparison: <500MB (chunked processing)

---
*Last updated: 2026-03-28*
