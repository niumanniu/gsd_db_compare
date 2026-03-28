# Architecture Patterns

**Domain:** Schema selection and multi-mode comparison integration
**Researched:** 2026-03-29

## Executive Summary

The existing DB Compare architecture already supports three comparison modes (`single`, `multi`, `database`). The new features — schema selection dropdown for database-level comparison and explicit mode routing — integrate cleanly by extending the adapter layer with schema enumeration and adding a schema selection UI layer.

## Recommended Architecture

### System Structure with New Features

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React + TS)                         │
├─────────────────────────────────────────────────────────────────────────┤
│  App.tsx                                                                │
│  └── ComparisonView (mode state: single|multi|database)                │
│       └── TableBrowser.tsx                                              │
│            ├── Mode Switcher (Tag buttons: single|multi|database)       │
│            ├── Connection Selectors                                     │
│            ├── Schema Selector (NEW - database mode only)               │
│            └── Table Selection (varies by mode)                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  API Routers                                                            │
│  ├── /api/compare/schema         → Single table (existing)             │
│  ├── /api/compare/schema/batch   → Multi-table (existing)              │
│  ├── /api/compare/schema/database→ Database-level (existing)           │
│  ├── /api/connections/{id}/tables → Table list (MODIFIED)              │
│  └── /api/connections/{id}/schemas → Schema list (NEW)                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Services                                                               │
│  ├── SchemaComparator (existing - no changes needed)                   │
│  └── DatabaseAdapters (extend with get_schemas())                      │
│       ├── MySQLAdapter.get_schemas() [NEW]                             │
│       └── OracleAdapter.get_schemas() [NEW]                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | Changes Required |
|-----------|---------------|-------------------|------------------|
| `TableBrowser.tsx` | Mode selection, connection/table/schema UI | API `/api/connections/*`, parent `ComparisonView` | ADD schema dropdown UI (database mode only) |
| `App.tsx` | Mode state management, query orchestration | `TableBrowser`, `useComparison` | ADD schema query hooks |
| `useComparison.ts` | Comparison mutation hooks | API `/api/compare/*` | NONE (optional: pass schema context) |
| `connections.py` | Connection management, table/schema enumeration | Database adapters | ADD `/schemas` endpoint, MODIFY `get_tables` signature |
| `DatabaseAdapter` (base) | Abstract DB interface | Concrete adapters | ADD `get_schemas()` abstract method |
| `MySQLAdapter` | MySQL metadata extraction | MySQL server | ADD `get_schemas()`, MODIFY `get_tables(schema?)` |
| `OracleAdapter` | Oracle metadata extraction | Oracle server | ADD `get_schemas()`, MODIFY `get_tables(schema?)` |
| `compare.py` | Schema comparison endpoints | `SchemaComparator`, adapters | NONE (schema handled at fetch time) |
| `SchemaComparator` | Table metadata comparison logic | N/A | NONE (schema-agnostic) |

### Data Flow

#### Current Flow (Baseline)
```
User selects connections
    → Fetch tables (/api/connections/{id}/tables)
    → Select tables (single/multi) OR use all (database)
    → Compare (POST /api/compare/schema|batch|database)
```

#### New Flow (With Schema Selection)
```
User selects connections + database mode
    → Fetch schemas (/api/connections/{id}/schemas) [NEW]
    → User selects schema
    → Fetch tables filtered by schema (/api/connections/{id}/tables?schema=X) [MODIFIED]
    → User selects tables (or all for database-level)
    → Compare with schema context [EXISTING endpoints]
```

## Patterns to Follow

### Pattern 1: Schema Enumeration API

**What:** Add `get_schemas()` method to `DatabaseAdapter` base class and implement in MySQL/Oracle adapters.

**When:** Required for populating schema dropdown in database-level comparison mode.

**Implementation:**

```python
# backend/app/adapters/base.py
@abstractmethod
def get_schemas(self) -> list[dict]:
    """List all schemas in database.

    Returns:
        List of dicts with schema_name, owner, create_time, etc.
    """
    pass

# backend/app/adapters/mysql.py
def get_schemas(self) -> list[dict]:
    """List all databases (MySQL schemas = databases)."""
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor(dictionary=True)
    query = """
        SELECT
            SCHEMA_NAME as schema_name,
            DEFAULT_CHARACTER_SET_NAME as charset,
            DEFAULT_COLLATION_NAME as collation
        FROM information_schema.SCHEMATA
        ORDER BY SCHEMA_NAME
    """
    cursor.execute(query)
    schemas = cursor.fetchall()
    cursor.close()
    return schemas

# backend/app/adapters/oracle.py
def get_schemas(self) -> list[dict]:
    """List all schemas (Oracle users with tables)."""
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor()
    query = """
        SELECT
            USERNAME as schema_name,
            CREATED as create_time,
            DEFAULT_TABLESPACE
        FROM ALL_USERS
        WHERE USERNAME IN (SELECT DISTINCT OWNER FROM ALL_TABLES)
        ORDER BY USERNAME
    """
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    schemas = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    return schemas
```

### Pattern 2: Schema-Parameterized Table Fetching

**What:** Modify `get_tables()` to accept optional schema filter parameter.

**When:** Schema is selected in database-level comparison mode.

**Implementation:**

```python
# backend/app/adapters/base.py
@abstractmethod
def get_tables(self, schema: Optional[str] = None) -> list[dict]:
    """List all tables in database.

    Args:
        schema: Optional schema name to filter by

    Returns:
        List of dicts with table_name, table_type, row_count, create_time
    """
    pass

# backend/app/adapters/mysql.py
def get_tables(self, schema: Optional[str] = None) -> list[dict]:
    """List all tables, optionally filtered by schema (database)."""
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor(dictionary=True)
    base_query = """
        SELECT
            TABLE_NAME as table_name,
            TABLE_TYPE as table_type,
            TABLE_ROWS as row_count,
            CREATE_TIME as create_time
        FROM information_schema.TABLES
        WHERE 1=1
    """

    params = []
    # MySQL: schema = database name
    if schema:
        base_query += " AND TABLE_SCHEMA = %s"
        params.append(schema)
    else:
        # Default to configured database
        base_query += " AND TABLE_SCHEMA = %s"
        params.append(self.config['database'])

    base_query += " ORDER BY TABLE_NAME"
    cursor.execute(base_query, params)
    tables = cursor.fetchall()
    cursor.close()
    return tables

# backend/app/adapters/oracle.py
def get_tables(self, schema: Optional[str] = None) -> list[dict]:
    """List all tables, optionally filtered by schema (owner)."""
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor()
    query = """
        SELECT
            TABLE_NAME as table_name,
            'TABLE' as table_type,
            NUM_ROWS as row_count,
            CREATED as create_time
        FROM ALL_TABLES
        WHERE 1=1
    """

    if schema:
        query += " AND OWNER = :1"
        cursor.execute(query, [schema])
    else:
        # Default to current user's tables
        query += " AND OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')"
        cursor.execute(query)

    columns = [col[0] for col in cursor.description]
    tables = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    return tables
```

### Pattern 3: Frontend Schema Selection UI

**What:** Add schema dropdown to `TableBrowser.tsx`, shown only in database-level mode.

**When:** User selects "Database Level" comparison mode.

**Implementation:**

```typescript
// frontend/src/App.tsx (excerpt)
function ComparisonView() {
  // ... existing state ...
  const [sourceSchema, setSourceSchema] = useState<string | null>(null);
  const [targetSchema, setTargetSchema] = useState<string | null>(null);

  // Fetch schemas when in database mode
  const { data: sourceSchemas = [] } = useQuery({
    queryKey: ['connection-schemas', sourceConnectionId],
    queryFn: () =>
      sourceConnectionId
        ? fetch(`/api/connections/${sourceConnectionId}/schemas`).then(r => r.json())
        : Promise.resolve([]),
    enabled: !!sourceConnectionId && compareMode === 'database',
  });

  const { data: targetSchemas = [] } = useQuery({
    queryKey: ['connection-schemas', targetConnectionId],
    queryFn: () =>
      targetConnectionId
        ? fetch(`/api/connections/${targetConnectionId}/schemas`).then(r => r.json())
        : Promise.resolve([]),
    enabled: !!targetConnectionId && compareMode === 'database',
  });

  // Fetch tables with schema filter
  const { data: sourceTables = [] } = useQuery({
    queryKey: ['connection-tables', sourceConnectionId, sourceSchema],
    queryFn: () => {
      const schemaParam = sourceSchema ? `?schema=${sourceSchema}` : '';
      return sourceConnectionId
        ? fetch(`/api/connections/${sourceConnectionId}/tables${schemaParam}`).then(r => r.json())
        : Promise.resolve([]);
    },
    enabled: !!sourceConnectionId,
  });

  // ... similar for targetTables ...
}
```

### Pattern 4: Backend Schema Endpoint

**What:** Add new `/api/connections/{id}/schemas` endpoint.

**When:** Frontend requests schema list for dropdown population.

**Implementation:**

```python
# backend/app/api/connections.py
@router.get("/{conn_id}/schemas", response_model=List[dict])
async def get_connection_schemas(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> List[dict]:
    """Fetch schema list from a database connection.

    Connects to the database using stored credentials and retrieves schema metadata.
    For MySQL, returns database names. For Oracle, returns user/schema names.
    """
    # Fetch connection from database
    result = await db.execute(select(DbConnection).where(DbConnection.id == conn_id))
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {conn_id} not found",
        )

    # Create adapter with decrypted password
    config = {
        'host': connection.host,
        'port': connection.port,
        'database': connection.database,
        'username': connection.username,
        'password': decrypt_password(connection.password_encrypted),
    }

    adapter = get_adapter(connection.db_type, config)

    try:
        schemas = adapter.get_schemas()
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch schemas: {str(e)}",
        )
    finally:
        adapter.disconnect()
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Hardcoding Schema in Connection Model

**What:** Don't modify the `DbConnection` model to include a default schema field.

**Why bad:** Connections should be schema-agnostic; schema selection is a comparison-time concern, not a connection property.

**Instead:** Pass schema as a runtime parameter to `get_tables()` and comparison endpoints.

### Anti-Pattern 2: Duplicating Comparison Logic

**What:** Don't create new comparison endpoints for schema-aware comparison.

**Why bad:** The existing `SchemaComparator` is schema-agnostic; it compares table metadata regardless of schema source.

**Instead:** Fetch tables with schema filter, then pass to existing comparison logic unchanged.

### Anti-Pattern 3: Breaking Existing Mode Switching

**What:** Don't require schema selection for single/multi modes.

**Why bad:** Single-table and multi-table comparisons work at the connection level; requiring schema would add unnecessary friction.

**Instead:** Show schema selector ONLY in database-level mode. Reset schema state when switching modes.

### Anti-Pattern 4: Loading Schemas Unnecessarily

**What:** Don't fetch schemas when in single/multi mode.

**Why bad:** Wastes API calls and adds latency; schemas are irrelevant for non-database modes.

**Instead:** Use React Query's `enabled` option to conditionally fetch schemas only in database mode.

## Scalability Considerations

| Concern | At 100 tables | At 10K tables | At 1M tables |
|---------|---------------|---------------|--------------|
| Schema enumeration | Trivial (<100 schemas) | Trivial | Trivial |
| Table enumeration per schema | Fast (<100 tables/schema) | May need pagination | Require server-side pagination |
| Database comparison | Sequential comparison OK | Consider batch processing | Require chunked/streaming comparison |

## Suggested Build Order

```
Phase 1: Backend Schema Support
├── 1.1 Add get_schemas() to DatabaseAdapter base class
├── 1.2 Implement MySQLAdapter.get_schemas()
├── 1.3 Implement OracleAdapter.get_schemas()
├── 1.4 Modify get_tables() signature to accept optional schema parameter
├── 1.5 Implement MySQLAdapter.get_tables(schema?)
├── 1.6 Implement OracleAdapter.get_tables(schema?)
└── 1.7 Add /api/connections/{id}/schemas endpoint

Phase 2: Frontend Schema Selection UI
├── 2.1 Add schema state to ComparisonView (sourceSchema, targetSchema)
├── 2.2 Add schema query hooks in App.tsx (conditional on database mode)
├── 2.3 Add schema dropdown to TableBrowser.tsx (database mode only)
├── 2.4 Wire schema selection to table fetching (pass schema param)
└── 2.5 Reset schema state when switching modes

Phase 3: Integration & Polish
├── 3.1 Ensure schema selection clears when switching modes
├── 3.2 Handle schema loading/error states
├── 3.3 Add schema info to comparison results display (optional)
└── 3.4 Test cross-schema comparison flows
```

## New vs Modified Components

### New Components/Endpoints

| File | Purpose |
|------|---------|
| `GET /api/connections/{id}/schemas` | New endpoint for schema enumeration |
| `DatabaseAdapter.get_schemas()` | Abstract method for schema listing |
| `MySQLAdapter.get_schemas()` | MySQL schema listing via information_schema.SCHEMATA |
| `OracleAdapter.get_schemas()` | Oracle schema listing via ALL_USERS/ALL_TABLES |

### Modified Components

| File | Modification |
|------|--------------|
| `backend/app/adapters/base.py` | Add `get_schemas()` abstract method; modify `get_tables()` signature |
| `backend/app/adapters/mysql.py` | Implement `get_schemas()`; modify `get_tables(schema?)` |
| `backend/app/adapters/oracle.py` | Implement `get_schemas()`; modify `get_tables(schema?)` |
| `backend/app/api/connections.py` | Add `/schemas` endpoint; modify `get_tables` to accept schema param |
| `frontend/src/App.tsx` | Add schema state (`sourceSchema`, `targetSchema`), schema query hooks |
| `frontend/src/components/TableBrowser.tsx` | Add schema dropdown UI (database mode only), schema-related props |

### Unchanged Components

| Component | Reason |
|-----------|--------|
| `SchemaComparator` | Schema-agnostic; compares table metadata regardless of source |
| `/api/compare/schema` endpoints | Receive table metadata; schema context handled at fetch time |
| `MultiTableDiffViewer`, `DatabaseDiffViewer` | Display results; schema info can be added but not required for core functionality |
| `useComparison.ts` | Comparison hooks remain unchanged; schema is transparent to comparison logic |

## Integration Points Summary

```
Schema Selection Flow:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  TableBrowser   │────▶│  App.tsx         │────▶│  /api/connections/ │
│  (UI dropdown)  │     │  (useQuery hook) │     │  {id}/schemas      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  TableBrowser   │◀────│  App.tsx         │◀────│  get_schemas()   │
│  (re-render     │     │  (schemas state) │     │  (adapter)       │
│   table list)   │     │                  │     │                  │
└─────────────────┘     └──────────────────┘     └─────────────────┘

Table Fetch with Schema:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  TableBrowser   │────▶│  App.tsx         │────▶│  /api/connections/ │
│  (table select) │     │  (useQuery hook) │     │  {id}/tables?schema=│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Sources

- Existing codebase analysis (`backend/adapters/`, `frontend/src/`)
- MySQL `information_schema.SCHEMATA` documentation
- Oracle `ALL_USERS`/`ALL_TABLES` system view documentation
