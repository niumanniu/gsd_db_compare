# Phase 1: Foundation - Research

**Phase:** 01-foundation
**Researched:** 2026-03-28

## Standard Stack

### Backend (Python 3.11+)
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115,<0.130 | Web framework |
| uvicorn[standard] | >=0.30 | ASGI server |
| pydantic | >=2.0 | Data validation |
| pydantic-settings | >=2.0 | Settings management |
| sqlalchemy | >=2.0 | ORM and metadata reflection |
| psycopg2-binary | >=2.9 | PostgreSQL driver |
| mysql-connector-python | >=8.0 | MySQL driver |
| alembic | >=1.12 | Database migrations |
| celery[redis] | >=5.4 | Task queue |
| redis | >=5.0 | Cache and broker |
| cryptography | >=42.0 | Credential encryption |
| structlog | >=24.0 | Structured logging |

### Frontend (React 18+)
| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.2+ | UI framework |
| typescript | 5.0+ | Type safety |
| vite | 5.0+ | Build tool |
| antd | 5.0+ | UI components |
| zustand | 4.0+ | State management |
| axios | 1.6+ | HTTP client |
| @tanstack/react-query | 5.0+ | Server state management |
| @tanstack/react-table | 8.0+ | Table component |
| react-diff-viewer | 3.1+ | Diff visualization |

## MySQL Metadata Queries

### List Tables
```sql
SELECT
    TABLE_NAME,
    TABLE_SCHEMA,
    TABLE_TYPE,
    TABLE_ROWS,
    CREATE_TIME,
    UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'your_database'
ORDER BY TABLE_NAME;
```

### Get Columns
```sql
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT,
    ORDINAL_POSITION
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'your_database'
  AND TABLE_NAME = 'your_table'
ORDER BY ORDINAL_POSITION;
```

### Get Indexes
```sql
SELECT
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    NON_UNIQUE,
    INDEX_TYPE,
    COLLATION
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'your_database'
  AND TABLE_NAME = 'your_table'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;
```

### Get Primary Key
```sql
SELECT
    COLUMN_NAME,
    ORDINAL_POSITION
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'your_database'
  AND TABLE_NAME = 'your_table'
  AND CONSTRAINT_NAME = 'PRIMARY'
ORDER BY ORDINAL_POSITION;
```

### Get Foreign Keys
```sql
SELECT
    kcu.CONSTRAINT_NAME,
    kcu.COLUMN_NAME,
    kcu.REFERENCED_TABLE_SCHEMA,
    kcu.REFERENCED_TABLE_NAME,
    kcu.REFERENCED_COLUMN_NAME,
    rc.UPDATE_RULE,
    rc.DELETE_RULE
FROM information_schema.KEY_COLUMN_USAGE kcu
JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
  ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
WHERE kcu.TABLE_SCHEMA = 'your_database'
  AND kcu.TABLE_NAME = 'your_table'
  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION;
```

### Get Unique Constraints
```sql
SELECT
    tc.CONSTRAINT_NAME,
    kcu.COLUMN_NAME,
    kcu.ORDINAL_POSITION
FROM information_schema.TABLE_CONSTRAINTS tc
JOIN information_schema.KEY_COLUMN_USAGE kcu
  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.TABLE_SCHEMA = 'your_database'
  AND tc.TABLE_NAME = 'your_table'
  AND tc.CONSTRAINT_TYPE = 'UNIQUE'
ORDER BY tc.CONSTRAINT_NAME, kcu.ORDINAL_POSITION;
```

## SQLAlchemy Metadata Reflection

### Using inspect()
```python
from sqlalchemy import create_engine, inspect

engine = create_engine("mysql+mysqlconnector://user:pass@host/db")
inspector = inspect(engine)

# Get column info
columns = inspector.get_columns("table_name")
# Returns: [{'name': 'id', 'type': INTEGER, 'nullable': False, 'default': None, ...}]

# Get indexes
indexes = inspector.get_indexes("table_name")
# Returns: [{'name': 'idx_name', 'column_names': ['col1'], 'unique': False, ...}]

# Get foreign keys
fkeys = inspector.get_foreign_keys("table_name")
# Returns: [{'name': 'fk_name', 'constrained_columns': ['col1'],
#            'referred_schema': 'db', 'referred_table': 'table2',
#            'referred_columns': ['col2']}]

# Get primary key
pk = inspector.get_pk_constraint("table_name")
# Returns: {'name': 'PRIMARY', 'constrained_columns': ['id']}

# Get unique constraints
unique = inspector.get_unique_constraints("table_name")
# Returns: [{'name': 'uk_name', 'column_names': ['col1']}]
```

### Using MetaData.reflect()
```python
from sqlalchemy import MetaData

metadata = MetaData()
metadata.reflect(bind=engine, only=['table1', 'table2'])

for table_name, table in metadata.tables.items():
    for column in table.columns:
        print(f"{column.name}: {column.type} (nullable={column.nullable})")
    for index in table.indexes:
        print(f"Index: {index.name} on {index.columns}")
```

## FastAPI Patterns

### Connection CRUD Endpoints
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/connections", tags=["connections"])

@router.post("")
async def create_connection(conn: ConnectionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new database connection."""
    # Validate connection
    if not await test_connection(conn):
        raise HTTPException(400, "Cannot connect to database")

    # Save to DB
    db_conn = DbConnection(**conn.dict())
    db.add(db_conn)
    await db.commit()
    return db_conn

@router.get("")
async def list_connections(db: AsyncSession = Depends(get_db)):
    """List all saved connections."""
    result = await db.execute(select(DbConnection))
    return result.scalars().all()

@router.get("/{conn_id}")
async def get_connection(conn_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific connection."""
    conn = await db.get(DbConnection, conn_id)
    if not conn:
        raise HTTPException(404, "Connection not found")
    return conn

@router.delete("/{conn_id}")
async def delete_connection(conn_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a connection."""
    conn = await db.get(DbConnection, conn_id)
    if not conn:
        raise HTTPException(404, "Connection not found")
    await db.delete(conn)
    await db.commit()
    return {"status": "deleted"}
```

### Comparison Endpoint (Async)
```python
@router.post("/api/compare/schema")
async def compare_schemas(request: SchemaCompareRequest, db: AsyncSession = Depends(get_db)):
    """Compare schemas between two databases."""
    # Create Celery task
    task = compare_schema_task.delay(
        request.source_connection_id,
        request.source_table,
        request.target_connection_id,
        request.target_table,
    )

    # Return task ID for polling
    return {"task_id": task.id, "status": "pending"}

@router.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get task status and result."""
    task = compare_schema_task.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif task.state == "STARTED":
        return {"task_id": task_id, "status": "running"}
    elif task.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": task.result}
    elif task.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task.info)}
```

## React Patterns

### Connection Form Component
```tsx
import { Form, Input, Select, Button } from 'antd';
import { useConnections } from '../hooks/useConnections';

export function ConnectionForm({ onClose }: { onClose: () => void }) {
  const [form] = Form.useForm();
  const { createConnection } = useConnections();

  const handleSubmit = async (values: any) => {
    try {
      await createConnection(values);
      onClose();
    } catch (error) {
      // Handle error
    }
  };

  return (
    <Form form={form} onFinish={handleSubmit}>
      <Form.Item name="name" label="Connection Name" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="dbType" label="Database Type">
        <Select>
          <Select.Option value="mysql">MySQL</Select.Option>
          <Select.Option value="oracle" disabled>Oracle (Coming Soon)</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item name="host" label="Host" rules={[{ required: true }]}>
        <Input placeholder="localhost" />
      </Form.Item>
      <Form.Item name="port" label="Port">
        <Input type="number" placeholder="3306" />
      </Form.Item>
      <Form.Item name="database" label="Database" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="username" label="Username">
        <Input />
      </Form.Item>
      <Form.Item name="password" label="Password">
        <Input.Password />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">Save</Button>
      </Form.Item>
    </Form>
  );
}
```

### Schema Diff Viewer Component
```tsx
import { Table, Tag, Collapse } from 'antd';
import type { SchemaDiff } from '../types';

export function SchemaDiffViewer({ diff }: { diff: SchemaDiff }) {
  const columnColumns = [
    { title: 'Column', dataIndex: 'column_name' },
    { title: 'Source', dataIndex: 'source_def', render: renderDef },
    { title: 'Target', dataIndex: 'target_def', render: renderDef },
    {
      title: 'Differences',
      dataIndex: 'differences',
      render: (diffs: string[]) => (
        <>
          {diffs.map(d => (
            <Tag color={getDiffColor(d)} key={d}>{d}</Tag>
          ))}
        </>
      )
    },
  ];

  return (
    <div>
      <Collapse
        items={[
          {
            key: 'columns',
            label: `Columns (${diff.column_diffs.length} differences)`,
            children: <Table columns={columnColumns} dataSource={diff.column_diffs} rowKey="column_name" />,
          },
          {
            key: 'indexes',
            label: `Indexes (${diff.index_diffs.length} differences)`,
            children: <IndexTable indexes={diff.index_diffs} />,
          },
          {
            key: 'constraints',
            label: `Constraints (${diff.constraint_diffs.length} differences)`,
            children: <ConstraintTable constraints={diff.constraint_diffs} />,
          },
        ]}
      />
    </div>
  );
}
```

## Celery Configuration

### celery_config.py
```python
from celery import Celery

celery_app = Celery(
    'db_compare',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute timeout
)
```

### Task Definition
```python
from celery import Task
from db_compare.celery_config import celery_app

class DatabaseTask(Task):
    def __init__(self):
        self._db_engine = None

    @property
    def db_engine(self):
        if self._db_engine is None:
            from sqlalchemy import create_engine
            self._db_engine = create_engine(self.db_url)
        return self._db_engine

@celery_app.task(base=DatabaseTask, bind=True)
def compare_schema_task(self, source_conn_id, source_table, target_conn_id, target_table):
    """Compare schemas between two databases."""
    # Fetch metadata
    source_metadata = fetch_mysql_metadata(self.source_engine, source_table)
    target_metadata = fetch_mysql_metadata(self.target_engine, target_table)

    # Compare
    diff = compare_schemas(source_metadata, target_metadata)

    return diff.to_dict()
```

## Testing Patterns

### pytest Fixtures
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture
def test_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_mysql_connection():
    return {
        "name": "Test MySQL",
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass",
    }
```

### Unit Test Example
```python
# test_schema_comparator.py
def test_compare_columns_added():
    source = TableMetadata(columns=[
        ColumnInfo(name="id", type="int", nullable=False),
        ColumnInfo(name="name", type="varchar(50)", nullable=True),
    ])
    target = TableMetadata(columns=[
        ColumnInfo(name="id", type="int", nullable=False),
        ColumnInfo(name="name", type="varchar(50)", nullable=True),
        ColumnInfo(name="created_at", type="datetime", nullable=True),
    ])

    diff = compare_columns(source, target)

    assert len(diff) == 1
    assert diff[0].column_name == "created_at"
    assert diff[0].diff_type == "added"
```

---
*Last updated: 2026-03-28*
