# Architecture Patterns: DB Compare

**Researched:** 2026-03-28

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Connection  │  │   Discovery  │  │   Diff Visualization │  │
│  │  Management  │  │   & Selection│  │   (Side-by-Side)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  /api/conn   │  │  /api/compare│  │   /api/tasks         │  │
│  │  (CRUD)      │  │  (Schema/Data)│  │   (History/Status)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Comparison Engine Layer                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Schema Comparator                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │ │
│  │  │ Column Diff │  │ Index Diff  │  │ Constraint Diff │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Data Comparator                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │ │
│  │  │ Full Scan   │  │ Sampling    │  │ Hash Validation │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Adapter Layer                        │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │   MySQL Adapter     │        │   Oracle Adapter    │        │
│  │  - metadata query   │        │  - metadata query   │        │
│  │  - data fetch       │        │  - data fetch       │        │
│  │  - type mapping     │        │  - type mapping     │        │
│  └─────────────────────┘        └─────────────────────┘        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Unified Metadata Model                        │ │
│  │  TableInfo, ColumnInfo, IndexInfo, ConstraintInfo          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │  MySQL   │   │  Oracle  │   │PostgreSQL│
        │  Server  │   │  Server  │   │(App Data)│
        └──────────┘   └──────────┘   └──────────┘
```

## Component Responsibilities

### Frontend (React + TypeScript)

**ConnectionManager**
- List/save/edit/delete database connections
- Test connection connectivity
- Connection form validation

**DiscoveryBrowser**
- Fetch and display table list
- Table search and filtering
- Preview table metadata

**DiffViewer**
- Side-by-side schema comparison
- Color-coded differences (added/removed/modified)
- Expandable details for indexes/constraints
- Data diff grid with row highlighting

### Backend (FastAPI + Python)

**API Layer**
- `POST /api/connections` — Create connection
- `GET /api/connections` — List connections
- `GET /api/connections/{id}/tables` — List tables
- `POST /api/compare/schema` — Compare schemas
- `POST /api/compare/data` — Compare data
- `GET /api/tasks/{id}` — Get task status
- `GET /api/tasks/{id}/report` — Get comparison report

**Comparison Engine**

```python
class SchemaComparator:
    def compare(self, source: TableInfo, target: TableInfo) -> SchemaDiff:
        # Compare columns
        # Compare indexes
        # Compare constraints
        # Return structured diff

class DataComparator:
    def compare_full(self, source: DataIterator, target: DataIterator) -> DataDiff:
        # Full row-by-row comparison

    def compare_sampling(self, source: DataIterator, target: DataIterator,
                         strategy: SamplingStrategy) -> DataDiff:
        # Sampling-based comparison

    def compare_hash(self, source: DataIterator, target: DataIterator) -> HashDiff:
        # MD5/SHA checksum comparison
```

**Database Adapters**

```python
class DatabaseAdapter(ABC):
    @abstractmethod
    def connect(self, config: ConnectionConfig) -> Connection:
        pass

    @abstractmethod
    def get_tables(self) -> list[TableInfo]:
        pass

    @abstractmethod
    def get_table_metadata(self, table_name: str) -> TableInfo:
        pass

    @abstractmethod
    def fetch_data(self, table_name: str, chunk_size: int) -> DataIterator:
        pass

class MySQLAdapter(DatabaseAdapter):
    # Query information_schema
    # Use mysql-connector-python

class OracleAdapter(DatabaseAdapter):
    # Query ALL_TAB_COLUMNS, ALL_CONSTRAINTS, etc.
    # Use oracledb
```

### Application Data (PostgreSQL)

```sql
-- Database connections (credentials encrypted)
CREATE TABLE db_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL,  -- 'mysql', 'oracle'
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comparison task history
CREATE TABLE comparison_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,  -- 'schema', 'data'
    source_connection_id INTEGER REFERENCES db_connections(id),
    target_connection_id INTEGER REFERENCES db_connections(id),
    source_table VARCHAR(255) NOT NULL,
    target_table VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    result JSONB,  -- Structured diff result
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled jobs
CREATE TABLE scheduled_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    comparison_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Data Flow: Schema Comparison

```
1. User selects two connections + table
          │
2. Frontend: POST /api/compare/schema
   {source_connection_id, source_table, target_connection_id, target_table}
          │
3. Backend: Fetch metadata from both databases (parallel)
   ├─ MySQL Adapter: query information_schema
   └─ Oracle Adapter: query ALL_TAB_* views
          │
4. SchemaComparator.compare(source_metadata, target_metadata)
   ├─ Compare columns (name, type, nullable, default)
   ├─ Compare indexes
   └─ Compare constraints
          │
5. Return SchemaDiff JSON
          │
6. Frontend: Render side-by-side diff view
```

## Data Flow: Data Comparison

```
1. User initiates data comparison
          │
2. Frontend: POST /api/compare/data
   {source_connection_id, source_table, target_connection_id, target_table,
    comparison_type: 'full' | 'sampling' | 'hash'}
          │
3. Backend: Spawn Celery task (async)
          │
4. Celery Worker: DataComparator.compare_*()
   ├─ Fetch data in chunks from both databases
   ├─ Compare rows (primary key based)
   ├─ Identify: only_in_source, only_in_target, mismatched
   └─ Store result in PostgreSQL
          │
5. Frontend: Poll /api/tasks/{id} for status
          │
6. When completed: Fetch and display diff
```

## Design Patterns

### Adapter Pattern
```python
# Unified interface for different database types
DatabaseAdapter
├── MySQLAdapter
├── OracleAdapter
└── (Future: PostgreSQLAdapter, SQLServerAdapter)
```

### Strategy Pattern
```python
# Interchangeable comparison strategies
ComparisonStrategy
├── FullComparisonStrategy
├── SamplingComparisonStrategy
└── HashComparisonStrategy
```

### Factory Pattern
```python
# Create appropriate adapter based on connection type
def get_adapter(connection: ConnectionConfig) -> DatabaseAdapter:
    if connection.db_type == 'mysql':
        return MySQLAdapter(connection)
    elif connection.db_type == 'oracle':
        return OracleAdapter(connection)
```

### Repository Pattern
```python
# Abstract data access
ConnectionRepository
├── save(connection)
├── find_by_id(id)
├── list_all()
└── delete(id)

TaskRepository
├── create(task)
├── find_by_id(id)
├── update_status(id, status)
└── list_history()
```

## Error Handling

### Connection Errors
```python
try:
    adapter.connect(config)
except ConnectionError as e:
    # Host unreachable, wrong port
    raise APIError(400, f"Cannot connect: {e}")
except AuthenticationError as e:
    # Wrong credentials
    raise APIError(401, f"Authentication failed: {e}")
except DatabaseNotFoundError as e:
    # Database doesn't exist
    raise APIError(404, f"Database not found: {e}")
```

### Comparison Errors
```python
try:
    comparator.compare(source, target)
except TableNotFoundError as e:
    raise APIError(404, f"Table not found: {e}")
except TypeMismatchError as e:
    # Log warning, continue with best-effort comparison
    result.add_warning(f"Type mismatch: {e}")
except MemoryLimitError as e:
    raise APIError(400, f"Table too large for full comparison: {e}")
```

## Security Considerations

### Credential Storage
```python
from cryptography.fernet import Fernet

class CredentialManager:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt(self, password: str) -> bytes:
        return self.cipher.encrypt(password.encode())

    def decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()
```

### Read-Only Enforcement
```python
# All database connections use read-only accounts
# Application never executes:
# - DDL: CREATE, ALTER, DROP, TRUNCATE
# - DML: INSERT, UPDATE, DELETE, MERGE
# - Only SELECT queries allowed
```

## Performance Considerations

### Metadata Query Optimization
```sql
-- MySQL: Selective metadata query
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'your_db'
  AND TABLE_NAME IN ('table1', 'table2')  -- Only requested tables
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Oracle: Selective metadata query
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
FROM ALL_TAB_COLUMNS
WHERE OWNER = 'YOUR_SCHEMA'
  AND TABLE_NAME IN ('TABLE1', 'TABLE2')
ORDER BY TABLE_NAME, COLUMN_ID;
```

### Chunked Data Processing
```python
def fetch_data_chunked(cursor, table: str, chunk_size: int = 10000):
    offset = 0
    while True:
        cursor.execute(f"""
            SELECT * FROM {table}
            ORDER BY PRIMARY_KEY
            LIMIT {chunk_size} OFFSET {offset}
        """)
        rows = cursor.fetchall()
        if not rows:
            break
        yield rows
        offset += chunk_size
```

---
*Last updated: 2026-03-28*
