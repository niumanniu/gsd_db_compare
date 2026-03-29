# Phase 5: Schema Selection - Research

**Researched:** 2026-03-29
**Domain:** Database schema enumeration (MySQL databases, Oracle users/schemas)
**Confidence:** HIGH

## Summary

Phase 5 implements schema selection for database-level comparisons. Users need to select which schemas (MySQL: databases, Oracle: users) to compare, not just which connections.

**Primary recommendation:** Add `get_schemas()` method to adapters, create `/api/connections/{id}/schemas` endpoint, add schema dropdowns in TableBrowser.tsx for database-level mode.

**Key technical insight:** MySQL and Oracle have fundamentally different schema concepts:
- **MySQL:** Schema = Database. Query `information_schema.SCHEMATA` to list all databases the user has access to.
- **Oracle:** Schema = User. Query `ALL_USERS` or `DBA_USERS` to list all schemas. Tables are owned by users.

## User Constraints (from CONTEXT.md)

_N/A - No CONTEXT.md exists for this phase_

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCH-01 | User can select source schema from dropdown when in database-level comparison mode | Backend: `get_schemas()` in adapters; API: `/schemas` endpoint; Frontend: schema dropdown |
| SCH-02 | User can select target schema from dropdown when in database-level comparison mode | Same as SCH-01 |
| SCH-03 | Schema dropdown shows only schemas from selected connections | Backend filters by connection; Frontend fetches per-connection |
| SCH-04 | Schema dropdown supports search/filter for databases with many schemas | Ant Design Select `showSearch` + `optionFilterProp` |
| SCH-05 | Backend API endpoint /api/connections/{id}/schemas returns available schemas | New endpoint in connections.py |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mysql-connector-python | >=8.0 | MySQL driver | Already in use; queries information_schema |
| oracledb | >=1.0 | Oracle driver | Already in use; Thin mode, no Oracle client needed |
| SQLAlchemy | 2.0 | ORM/metadata | Used for table reflection, consistent across adapters |
| FastAPI | 0.100+ | API framework | Existing API layer |
| Ant Design | 5.x | UI components | Existing UI library; Select component supports search |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-query | 5.x | Data fetching | Existing pattern for API calls |

## Architecture Patterns

### Adapter Interface Extension

Add `get_schemas()` method to `DatabaseAdapter` base class:

```python
# backend/app/adapters/base.py
@abstractmethod
def get_schemas(self) -> list[dict]:
    """List all schemas accessible to the current user.

    Returns:
        List of dicts with schema_name, owner, created_at, etc.
    """
    pass
```

### MySQL Implementation: information_schema.SCHEMATA

MySQL schemas are synonymous with databases. The `information_schema.SCHEMATA` table contains one row per database:

```python
# backend/app/adapters/mysql.py
def get_schemas(self) -> list[dict]:
    """List all databases (schemas) accessible to the user.

    Queries information_schema.SCHEMATA.

    Returns:
        List of dicts with schema_name, default_character_set, etc.
    """
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor(dictionary=True)
    query = """
        SELECT
            SCHEMA_NAME as schema_name,
            DEFAULT_CHARACTER_SET_NAME as charset,
            DEFAULT_COLLATION_NAME as collation,
            'N/A' as created_time  -- MySQL doesn't track creation time
        FROM information_schema.SCHEMATA
        ORDER BY SCHEMA_NAME
    """
    cursor.execute(query)
    schemas = cursor.fetchall()
    cursor.close()
    return schemas
```

**Columns in information_schema.SCHEMATA:**
- `SCHEMA_NAME`: Database/schema name
- `DEFAULT_CHARACTER_SET_NAME`: Default charset (utf8mb4, latin1, etc.)
- `DEFAULT_COLLATION_NAME`: Default collation
- `SQL_PATH`: Data directory path (requires privileges)

### Oracle Implementation: ALL_USERS

Oracle schemas are synonymous with database users. Use `ALL_USERS` to list all schemas the current user can access:

```python
# backend/app/adapters/oracle.py
def get_schemas(self) -> list[dict]:
    """List all schemas (users) accessible to the current user.

    Queries ALL_USERS view. For privileged users, DBA_USERS shows all schemas.

    Returns:
        List of dicts with schema_name, created_at, account_status
    """
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor()
    # ALL_USERS shows all users accessible to current user
    # DBA_USERS requires DBA privilege but shows all users in database
    query = """
        SELECT
            USERNAME as schema_name,
            CREATED as created_time,
            ACCOUNT_STATUS as account_status
        FROM ALL_USERS
        ORDER BY USERNAME
    """
    cursor.execute(query)
    columns = ['schema_name', 'created_time', 'account_status']
    schemas = []
    for row in cursor.fetchall():
        schema_dict = {}
        for i, col in enumerate(columns):
            schema_dict[col] = row[i]
        schemas.append(schema_dict)
    cursor.close()
    return schemas
```

**Key Oracle schema views:**
| View | Requires | Description |
|------|----------|-------------|
| `USER_USERS` | None | Current user only (not useful for listing) |
| `ALL_USERS` | None | All users accessible to current user |
| `DBA_USERS` | DBA privilege | All users in database |

### API Endpoint Design

Add new endpoint to `backend/app/api/connections.py`:

```python
@router.get("/{conn_id}/schemas", response_model=List[SchemaInfo])
async def get_connection_schemas(
    conn_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> List[dict]:
    """Fetch available schemas from a database connection.

    Returns schemas (databases in MySQL, users in Oracle) that the
    connection's credentials have access to.
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

    # Use adapter factory
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

### Frontend: Schema Dropdown in TableBrowser

Add schema selection state and API call:

```typescript
// frontend/src/hooks/useConnections.ts
const getSchemasMutation = useMutation({
  mutationFn: (id: number) => apiClient.get(`/api/connections/${id}/schemas`).then(r => r.data),
});

return {
  // ... existing
  getSchemas: getSchemasMutation.mutateAsync,
  isFetchingSchemas: getSchemasMutation.isPending,
};
```

```typescript
// frontend/src/components/TableBrowser.tsx
// Add to props
interface TableBrowserProps {
  // ... existing
  sourceSchema?: string | null;
  targetSchema?: string | null;
  onSourceSchemaChange?: (schema: string | null) => void;
  onTargetSchemaChange?: (schema: string | null) => void;
  sourceSchemas?: SchemaInfo[];  // { schema_name: string }
  targetSchemas?: SchemaInfo[];
  isFetchingSchemas?: boolean;
}
```

```tsx
// In database-level mode, show schema dropdowns
{compareMode === 'database' && (
  <Row gutter={16} style={{ marginBottom: 20 }}>
    <Col span={12}>
      <Typography.Text strong>Source Schema</Typography.Text>
      <Select
        style={{ width: '100%' }}
        placeholder="Select schema (database)"
        value={sourceSchema}
        onChange={onSourceSchemaChange}
        disabled={!sourceConnectionId}
        showSearch
        optionFilterProp="children"
      >
        {sourceSchemas?.map((schema) => (
          <Option key={schema.schema_name} value={schema.schema_name}>
            {schema.schema_name}
          </Option>
        ))}
      </Select>
    </Col>
    <Col span={12}>
      <Typography.Text strong>Target Schema</Typography.Text>
      <Select
        style={{ width: '100%' }}
        placeholder="Select schema (user)"
        value={targetSchema}
        onChange={onTargetSchemaChange}
        disabled={!targetConnectionId}
        showSearch
        optionFilterProp="children"
      >
        {targetSchemas?.map((schema) => (
          <Option key={schema.schema_name} value={schema.schema_name}>
            {schema.schema_name}
          </Option>
        ))}
      </Select>
    </Col>
  </Row>
)}
```

### Schema-Filtered Table Listing

Current `get_tables()` in adapters uses the connection-level `database` parameter. For schema-level selection, we need to pass the schema to filter:

```python
# backend/app/adapters/base.py
@abstractmethod
def get_tables(self, schema: str | None = None) -> list[dict]:
    """List all tables in database.

    Args:
        schema: Optional schema name to filter by. If None, uses connection default.

    Returns:
        List of table metadata dicts
    """
    pass
```

```python
# backend/app/adapters/mysql.py
def get_tables(self, schema: str | None = None) -> list[dict]:
    """List all tables in the database.

    Args:
        schema: Optional schema name. If None, uses connection's database.

    Returns:
        List of dicts with table_name, table_type, row_count, create_time
    """
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor(dictionary=True)
    query = """
        SELECT
            TABLE_NAME as table_name,
            TABLE_TYPE as table_type,
            TABLE_ROWS as row_count,
            CREATE_TIME as create_time
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
    """
    # Use provided schema or fall back to connection config
    schema_name = schema or self.config['database']
    cursor.execute(query, (schema_name,))
    tables = cursor.fetchall()
    cursor.close()
    return tables
```

```python
# backend/app/adapters/oracle.py
def get_tables(self, schema: str | None = None) -> list[dict]:
    """List all tables in the schema.

    Args:
        schema: Optional schema name (Oracle username). If None, uses current schema.

    Returns:
        List of dicts with table_name, table_type, row_count, create_time
    """
    if not self._connection:
        self.connect()

    cursor = self._connection.cursor()
    # Use provided schema or current session schema
    owner_clause = """OWNER = :owner""" if schema else """OWNER = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')"""
    query = f"""
        SELECT
            TABLE_NAME as table_name,
            'TABLE' as table_type,
            NUM_ROWS as row_count,
            CREATED as create_time
        FROM ALL_TABLES
        WHERE {owner_clause}
        ORDER BY TABLE_NAME
    """
    params = {'owner': schema.upper()} if schema else {}
    cursor.execute(query, params)
    # ... rest of implementation
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema enumeration | Custom metadata tables | information_schema.SCHEMATA (MySQL), ALL_USERS (Oracle) | System views are always up-to-date with permissions |
| Schema filtering | Manual string matching | SQL WHERE clause with parameter binding | Prevents SQL injection, respects database permissions |
| Dropdown search | Custom filtering logic | Ant Design Select `showSearch` + `optionFilterProp` | Built-in accessibility, keyboard navigation, virtualization |

## Case Sensitivity Handling

### MySQL
- Database names are **case-sensitive** on Linux, **case-insensitive** on Windows
- Controlled by `lower_case_table_names` server variable
- **Recommendation:** Always use exact case as stored in information_schema

### Oracle
- Unquoted identifiers are **UPPERCASE** by default
- Quoted identifiers preserve case but require quotes everywhere
- **Recommendation:** Store and compare in UPPERCASE; convert user input with `.upper()`

```python
# Oracle adapter: normalize schema name
def get_tables(self, schema: str | None = None) -> list[dict]:
    if schema:
        schema = schema.upper()  # Normalize to uppercase
    # ...
```

## Performance Considerations for Large Schema Lists

### Problem
- MySQL instances with 500+ databases
- Oracle with 1000+ users
- Slow dropdown rendering and network transfer

### Solutions

1. **Server-side pagination:** Don't implement for Phase 5. Schema lists rarely exceed 100 in typical enterprise scenarios.

2. **Client-side virtualization:** Ant Design Select handles 500+ options efficiently with built-in virtualization.

3. **Query optimization:**
   ```sql
   -- MySQL: only fetch needed columns
   SELECT SCHEMA_NAME FROM information_schema.SCHEMATA ORDER BY SCHEMA_NAME;

   -- Oracle: avoid expensive joins
   SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME;
   ```

4. **Caching:** Add React Query cache for schema lists:
   ```typescript
   const { data: schemas } = useQuery({
     queryKey: ['schemas', connectionId],
     queryFn: () => apiClient.get(`/api/connections/${connectionId}/schemas`).then(r => r.data),
     staleTime: 5 * 60 * 1000,  // 5 minutes
   });
   ```

## Integration Points

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/adapters/base.py` | Modify | Add abstract `get_schemas()` method |
| `backend/app/adapters/mysql.py` | Modify | Implement `get_schemas()` with information_schema.SCHEMATA |
| `backend/app/adapters/oracle.py` | Modify | Implement `get_schemas()` with ALL_USERS |
| `backend/app/api/connections.py` | Modify | Add `GET /api/connections/{id}/schemas` endpoint |
| `frontend/src/hooks/useConnections.ts` | Modify | Add `getSchemas` mutation |
| `frontend/src/components/TableBrowser.tsx` | Modify | Add schema dropdowns for database mode |
| `frontend/src/App.tsx` | Modify | Wire up schema selection state |
| `backend/app/schemas/api.py` | Modify | Add `SchemaInfo` response schema |

## Dependencies and Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| User has permission to list schemas | LOW - connection test already validates credentials | Document in error messages; return empty list if no schemas visible |
| Oracle ALL_USERS shows limited schemas | MEDIUM - depends on grants | Document behavior; users with DBA privilege see more |
| Schema selection breaks existing single-table mode | LOW - database mode is separate | Keep changes isolated to `compareMode === 'database'` |
| Large schema lists cause UI lag | LOW - Ant Design handles 1000s of options | Use `showSearch` to help users filter |

## Build Order Recommendation

1. **Backend first:**
   - Task 1: Add `get_schemas()` abstract method to `DatabaseAdapter` base class
   - Task 2: Implement `get_schemas()` in `MySQLAdapter` (information_schema.SCHEMATA)
   - Task 3: Implement `get_schemas()` in `OracleAdapter` (ALL_USERS)
   - Task 4: Add `GET /api/connections/{id}/schemas` endpoint
   - Task 5: Add `SchemaInfo` Pydantic schema

2. **Frontend second:**
   - Task 6: Add `getSchemas` mutation to `useConnections.ts`
   - Task 7: Add `SchemaInfo` TypeScript type to `types/index.ts`
   - Task 8: Add schema dropdown props to `TableBrowser.tsx`
   - Task 9: Wire up schema selection in `App.tsx` (fetch schemas on connection change)
   - Task 10: Pass selected schemas to compare API call

3. **Integration testing:**
   - Task 11: Test MySQL with multiple databases
   - Task 12: Test Oracle with multiple users
   - Task 13: Verify dropdown search/filter works

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (backend), Vitest + React Testing Library (frontend) |
| Config file | `backend/pyproject.toml` (pytest), frontend uses Vite config |
| Quick run command | `pytest backend/tests/ -x -k schema` |
| Full suite command | `pytest backend/tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCH-01 | Schema dropdown shows in database mode | Frontend component | `vitest run src/components/TableBrowser.test.tsx` | ❌ Wave 0 |
| SCH-02 | Target schema selectable | Frontend component | `vitest run src/components/TableBrowser.test.tsx` | ❌ Wave 0 |
| SCH-03 | Schemas filtered by connection | Backend unit | `pytest backend/tests/api/test_connections.py::test_get_schemas` | ❌ Wave 0 |
| SCH-04 | Dropdown search works | Frontend integration | `vitest run src/components/TableBrowser.test.tsx` | ❌ Wave 0 |
| SCH-05 | `/api/connections/{id}/schemas` returns list | Backend unit | `pytest backend/tests/api/test_connections.py::test_get_schemas` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/ -x -k "schema"` (backend), `vitest run --changed` (frontend)
- **Per wave merge:** `pytest backend/tests/` + `vitest run`
- **Phase gate:** All SCH-* tests passing before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/adapters/test_mysql.py::test_get_schemas` — tests MySQL schema enumeration
- [ ] `backend/tests/adapters/test_oracle.py::test_get_schemas` — tests Oracle schema enumeration
- [ ] `backend/tests/api/test_connections.py::test_get_schemas_endpoint` — tests API endpoint
- [ ] `frontend/src/components/TableBrowser.test.tsx` — tests schema dropdown UI
- [ ] `frontend/src/hooks/useConnections.test.ts` — tests getSchemas hook

## Common Pitfalls

### Pitfall 1: Oracle Schema Name Case
**What goes wrong:** User types lowercase schema name, Oracle stores as UPPERCASE, table lookup fails.

**Why it happens:** Oracle normalizes unquoted identifiers to uppercase. `my_schema` becomes `MY_SCHEMA`.

**How to avoid:** Always normalize Oracle schema names with `.upper()` before querying.

**Warning signs:** "Table not found" errors when schema was selected from dropdown (dropdown shows UPPERCASE).

### Pitfall 2: MySQL Schema vs Database Confusion
**What goes wrong:** User thinks "schema" and "database" are different; selects wrong thing.

**Why it happens:** MySQL uses `CREATE DATABASE` and `CREATE SCHEMA` interchangeably.

**How to avoid:** Add helper text: "Schema (MySQL) = Database" in UI.

### Pitfall 3: Missing Schema Permissions
**What goes wrong:** Connection works but schema list is empty.

**Why it happens:** User account lacks privileges to see information_schema.SCHEMATA or ALL_USERS rows.

**How to avoid:** Check if at least one schema visible; show warning if connection works but no schemas returned.

**Warning signs:** `GET /schemas` returns `[]` but `GET /tables` works.

### Pitfall 4: Oracle Thin Mode Limitations
**What goes wrong:** ALL_USERS query fails in Thin mode.

**Why it happens:** Some Oracle views require Thick mode (Oracle client libraries).

**How to avoid:** Test with `oracledb` Thin mode first; fall back to alternative query if needed.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| cx_Oracle (Oracle) | oracledb Thin mode | 2023 | No Oracle client needed; pure Python |
| Manual SQL building | SQLAlchemy inspect() | 2020+ | Database-agnostic metadata access |
| Sync API endpoints | FastAPI async endpoints | 2020+ | Better concurrency for DB calls |

**Deprecated/outdated:**
- `cx_Oracle`: Oracle renamed to `oracledb`; cx_Oracle is 7.x and unmaintained

## Open Questions

1. **Schema ownership tracking in Oracle**
   - What we know: Oracle schemas = users; tables are owned by users
   - What's unclear: Should we filter schemas to only those with tables?
   - Recommendation: Show all schemas; let user decide

2. **MySQL cross-schema table comparison**
   - What we know: Current get_tables() is scoped to connection's database
   - What's unclear: Should users be able to compare tables across different MySQL databases on same server?
   - Recommendation: Phase 5 supports different connections (potentially same server, different database); document pattern

3. **Oracle service_name vs SID for schema selection**
   - What we know: Connection uses service_name
   - What's unclear: Can a single connection see schemas from other service_names?
   - Recommendation: Document limitation; each connection is scoped to its service_name

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MySQL server | Schema enumeration | ✓ (user's environment) | 8.0+ assumed | — |
| Oracle server | Schema enumeration | ✓ (user's environment) | 19c+ assumed | — |
| mysql-connector-python | Backend | ✓ (in pyproject.toml) | >=8.0 | — |
| oracledb | Backend | ✓ (in pyproject.toml) | >=1.0 | — |
| Ant Design Select | Frontend | ✓ (existing) | 5.x | — |

## Sources

### Primary (HIGH confidence)
- MySQL 8.0 Reference Manual — `information_schema.SCHEMATA` table structure
- Oracle Database SQL Language Reference — `ALL_USERS` view
- oracledb documentation — Thin mode capabilities
- mysql-connector-python documentation — information_schema queries

### Secondary (MEDIUM confidence)
- FastAPI documentation — async endpoint patterns
- Ant Design documentation — Select component search/filter
- SQLAlchemy documentation — inspector API for metadata

### Tertiary (LOW confidence)
- Stack Overflow threads on Oracle schema enumeration — marked for validation
- Blog posts on MySQL cross-database queries — verify with official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing project dependencies
- Architecture: HIGH — follows established adapter pattern
- Pitfalls: MEDIUM — based on common database patterns, some marked for validation

**Research date:** 2026-03-29
**Valid until:** 30 days for stable (database fundamentals don't change rapidly)
