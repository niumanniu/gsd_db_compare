# Technology Stack

**Project:** DB Compare - v1.1 Schema Selection & Multi-Mode Enhancement
**Researched:** 2026-03-29

## Executive Summary

**Key Finding: NO NEW LIBRARIES REQUIRED.**

The existing architecture already supports single/multi/database-level comparison modes. The only gap is **schema selection for database-level comparison** - currently the system compares all tables in a database, but MySQL's `information_schema.TABLES` is already schema-filtered by the `database` connection parameter.

For MySQL: "schema" = "database" (same concept). If users need to compare different schemas on the same MySQL server, they should create separate connections with different `database` values.

For Oracle: Schema = user/owner. The current adapter queries `ALL_TABLES` which shows all tables visible to the connected user. Adding schema selection would require passing `OWNER` filter.

## Recommended Stack Changes

### NO NEW DEPENDENCIES NEEDED

The existing stack fully supports the required features:

| Feature | Status | Notes |
|---------|--------|-------|
| Single-table comparison | Already implemented | `/api/compare/schema` |
| Multi-table comparison | Already implemented | `/api/compare/schema/batch` |
| Database-level comparison | Already implemented | `/api/compare/schema/database` |
| Compare mode switcher UI | Already implemented | `TableBrowser.tsx` has mode tabs |
| Schema selection (MySQL) | **N/A - connection-level** | MySQL schema = database, set in connection |
| Schema selection (Oracle) | **Needs minor extension** | Add `schema` field to connection config |

### Stack Modification: Oracle Schema Support

For Oracle multi-schema databases, add optional schema selection:

| Change | Type | Purpose | Why |
|--------|------|---------|-----|
| `DbConnection.schema_name` (nullable) | Database schema | Store Oracle schema/owner name | Oracle databases contain multiple schemas; users may want to compare specific schema |
| `OracleAdapter.get_tables(schema?: string)` | Adapter method | Filter tables by owner | `ALL_TABLES WHERE OWNER = :schema` |
| `DatabaseCompareRequest.source_schema`, `target_schema` | API schema | Pass schema filter to comparison | Allow schema-level scoping for Oracle |

## Existing Stack (Confirmed Working)

### Backend Dependencies

```toml
# From backend/pyproject.toml
fastapi>=0.115,<0.130       # API framework
pydantic>=2.0               # Request/response validation
sqlalchemy>=2.0             # Metadata reflection
mysql-connector-python>=8.0 # MySQL driver
oracledb>=2.0               # Oracle driver (python-oracledb)
psycopg2-binary>=2.9        # PostgreSQL (app database)
APScheduler>=3.10.0         # Task scheduling
cryptography>=42.0          # Password encryption
Jinja2>=3.1                 # HTML report templates
openpyxl>=3.1               # Excel export
```

### Frontend Dependencies

```json
// From frontend/package.json
react: ^18.3.1
antd: ^5.22.0                    // UI components (Select, Table, etc.)
zustand: ^5.0.0                  // State management
axios: ^1.7.0                    // HTTP client
@tanstack/react-query: ^5.60.0   // API state management
@tanstack/react-table: ^8.20.0   // Table components
```

**All dependencies are current and sufficient.**

## Required Code Changes (No New Libraries)

### 1. Backend: Add Schema Field to Connection Model

```python
# backend/app/db/models.py
class DbConnection(Base):
    # Existing fields...
    schema_name = Column(String(255), nullable=True)  # Oracle schema/owner
```

### 2. Backend: Oracle Adapter Schema Filtering

```python
# backend/app/adapters/oracle.py
def get_tables(self, schema_name: Optional[str] = None) -> list[dict]:
    query = """
        SELECT table_name, table_type, num_rows as row_count, created as create_time
        FROM all_tables
        WHERE owner = :schema_name  -- Add filter if schema provided
        ORDER BY table_name
    """
```

### 3. Backend: Database Compare API Schema Extension

```python
# backend/app/schemas/api.py
class DatabaseCompareRequest(BaseModel):
    source_connection_id: int
    target_connection_id: int
    exclude_patterns: list[str] = Field(default_factory=list)
    source_schema: Optional[str] = None  # NEW: Oracle schema filter
    target_schema: Optional[str] = None  # NEW: Oracle schema filter
```

### 4. Frontend: Add Schema Selector to TableBrowser

```tsx
// frontend/src/components/TableBrowser.tsx
// Add Oracle schema dropdown when Oracle connection selected
// For MySQL: schema = database (already in connection config)
// For Oracle: show schema dropdown populated from ALL_TABLES owners
```

### 5. Frontend: Connection Form Schema Field

```tsx
// frontend/src/components/ConnectionForm.tsx
// Add optional "Schema" field for Oracle connections
// Hide for MySQL (schema = database)
```

## Integration Points with Existing Code

| Existing Component | How It Works | Changes Needed |
|-------------------|--------------|----------------|
| `TableBrowser.tsx` | Already has `compareMode` prop with single/multi/database | Add schema dropdown state & API calls |
| `useComparison.ts` hook | Already has `compareDatabase` mutation | Add `source_schema`/`target_schema` params |
| `compare.py` router | Already has `/database` endpoint | Add schema filtering logic |
| `OracleAdapter` | Queries `ALL_TABLES` | Add `WHERE OWNER = :schema` filter |
| `MySQLAdapter` | Queries `information_schema.TABLES WHERE TABLE_SCHEMA = ?` | No change needed (already schema-scoped by database) |

## What NOT to Add

| Library | Why Not |
|---------|---------|
| Additional DB drivers | MySQL + Oracle already supported |
| UI component libraries | Ant Design already provides all needed components |
| State management | Zustand is sufficient; no need for Redux |
| Form libraries | Controlled components work fine |
| Schema introspection libs | SQLAlchemy inspect() already handles this |

## Schema Selection Implementation Notes

### MySQL (No Changes Needed)

MySQL schema selection is **already handled at the connection level**:

```python
# When connection.database = 'my_schema', get_tables() queries:
SELECT ... FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'my_schema'  -- Already filtered!
```

Users who want to compare different MySQL schemas should **create separate connections** with different database names.

### Oracle (Minor Extension)

Oracle requires explicit schema filtering since one connection can see multiple schemas:

```python
# OracleAdapter.get_tables() needs:
query = """
    SELECT table_name, ...
    FROM all_tables
    WHERE owner = :owner  -- Add this filter
"""
```

**Optional enhancement:** Add a `get_schemas()` method to list available schemas for a dropdown:

```python
def get_schemas(self) -> list[str]:
    """List all schemas (owners) visible to this connection."""
    cursor = self._connection.cursor()
    cursor.execute("SELECT username FROM all_users ORDER BY username")
    return [row[0] for row in cursor.fetchall()]
```

## API Changes Summary

### Database Compare Request - Before vs After

```python
# BEFORE (current)
class DatabaseCompareRequest(BaseModel):
    source_connection_id: int
    target_connection_id: int
    exclude_patterns: list[str] = []

# AFTER (with schema support)
class DatabaseCompareRequest(BaseModel):
    source_connection_id: int
    target_connection_id: int
    exclude_patterns: list[str] = []
    source_schema: Optional[str] = None  # NEW: Oracle schema filter
    target_schema: Optional[str] = None  # NEW: Oracle schema filter
```

### Connection Create - Before vs After

```python
# BEFORE (current)
class ConnectionCreate(BaseModel):
    name: str
    db_type: str  # 'mysql' or 'oracle'
    host: str
    port: int
    database: str  # MySQL: schema name, Oracle: service name
    username: str
    password: str

# AFTER (with schema support)
class ConnectionCreate(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    schema_name: Optional[str] = None  # NEW: Oracle schema/owner (nullable)
```

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| No new libraries needed | HIGH | Existing stack already has all comparison modes |
| MySQL schema handling | HIGH | MySQL schema = database, already connection-scoped |
| Oracle schema handling | MEDIUM | Requires `OWNER` filter in ALL_TABLES query |
| UI component changes | HIGH | Ant Design Select component sufficient |
| API extension | HIGH | Simple optional field additions |

## Sources

- Existing codebase analysis (`backend/app/api/compare.py`, `frontend/src/components/TableBrowser.tsx`)
- MySQL documentation: `information_schema.TABLES` schema filtering
- Oracle documentation: `ALL_TABLES` view with `OWNER` filter
