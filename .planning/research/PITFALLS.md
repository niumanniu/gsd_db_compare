# Domain Pitfalls: DB Compare

**Researched:** 2026-03-28

## Critical Pitfalls (Must Avoid)

### Pitfall 1: Metadata Query Performance Degradation

**Problem:**
Querying `information_schema` on MySQL or `ALL_TAB_*` views on Oracle with 10,000+ tables can take 30+ seconds if not properly filtered.

**Impact:**
- UI appears frozen
- Connection timeout errors
- Poor first-time user experience

**Prevention:**
```sql
-- BAD: Fetch all tables
SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'your_db';

-- GOOD: Fetch only requested tables
SELECT * FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'your_db'
  AND TABLE_NAME IN ('table1', 'table2', 'table3');

-- BETTER: Paginate for table browser
SELECT * FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'your_db'
ORDER BY TABLE_NAME
LIMIT 100 OFFSET 0;
```

**Phase:** Phase 1

---

### Pitfall 2: Memory Exhaustion on Large Table Comparison

**Problem:**
Loading entire table data into memory for comparison causes OOM (Out Of Memory) errors on tables with millions of rows.

**Impact:**
- Application crashes
- Comparison fails silently
- Unreliable for production use cases

**Prevention:**
```python
# BAD: Load entire table
def compare_data_bad(source_conn, target_conn, table):
    source_data = list(source_conn.execute(f"SELECT * FROM {table}"))
    target_data = list(target_conn.execute(f"SELECT * FROM {table}"))
    # OOM on large tables!

# GOOD: Stream and compare in chunks
def compare_data_good(source_conn, target_conn, table, chunk_size=10000):
    source_iter = fetch_chunked(source_conn, table, chunk_size)
    target_iter = fetch_chunked(target_conn, table, chunk_size)

    for source_chunk, target_chunk in zip(source_iter, target_iter):
        compare_chunk(source_chunk, target_chunk)
        # GC can clean up after each chunk
```

**Phase:** Phase 3

---

### Pitfall 3: MySQL-Oracle Type Mapping Complexity

**Problem:**
MySQL and Oracle have different type systems with subtle incompatibilities:

| MySQL | Oracle | Notes |
|-------|--------|-------|
| VARCHAR(50) | VARCHAR2(50) | Oracle VARCHAR2 is different from VARCHAR |
| DATETIME | DATE | Oracle DATE includes time |
| DATETIME(6) | TIMESTAMP | Microsecond precision |
| TINYINT(1) | NUMBER(1) | Boolean representation |
| TEXT | CLOB | Large text handling |
| BLOB | BLOB | Binary handling differs |
| DECIMAL(10,2) | NUMBER(10,2) | Equivalent but different names |

**Impact:**
- False positive differences reported
- Confusing type mismatch errors
- Cross-database comparison fails

**Prevention:**
```python
# Type mapping registry with canonicalization
TYPE_MAPPING_MYSQL_TO_ORACLE = {
    'varchar': 'varchar2',
    'datetime': 'date',
    'datetime(6)': 'timestamp',
    'tinyint(1)': 'number(1)',
    'text': 'clob',
    'decimal': 'number',
    'int': 'number',
    'bigint': 'number',
}

def canonicalize_type(db_type: str, db_kind: str) -> str:
    """Convert database-specific type to canonical form for comparison."""
    if db_kind == 'mysql':
        # Normalize MySQL types
        db_type = db_type.lower()
        if db_type == 'varchar':
            return 'varchar'
        elif db_type in ('datetime', 'timestamp'):
            return 'datetime'
        # ... more mappings
    elif db_kind == 'oracle':
        # Normalize Oracle types
        db_type = db_type.lower()
        if db_type == 'varchar2':
            return 'varchar'  # Map to canonical
        elif db_type == 'date':
            return 'datetime'
        # ... more mappings
    return db_type
```

**Phase:** Phase 2

---

### Pitfall 4: Character Set and Collation Differences

**Problem:**
MySQL utf8mb4 with case-insensitive collation vs Oracle AL32UTF8 with case-sensitive comparison leads to false mismatches.

**Example:**
```sql
-- MySQL: 'Hello' = 'hello' with utf8mb4_general_ci
-- Oracle: 'Hello' != 'hello' (case-sensitive by default)
```

**Impact:**
- String comparisons report false differences
- Confusing results for users

**Prevention:**
```python
# Normalize string comparison based on collation
def compare_strings(a: str, b: str, collation: str) -> bool:
    if 'ci' in collation.lower():  # Case-insensitive
        return a.lower() == b.lower()
    elif 'bin' in collation.lower():  # Binary
        return a.encode() == b.encode()
    else:
        return a == b

# Fetch collation metadata
def get_column_collation(mysql_conn, table, column):
    result = mysql_conn.execute("""
        SELECT COLLATION_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (table, column))
    return result.fetchone()['COLLATION_NAME']
```

**Phase:** Phase 2

---

### Pitfall 5: NULL Handling in Comparisons

**Problem:**
NULL != NULL in SQL (and most programming languages). Naive comparison reports all NULL values as different.

**Impact:**
- False positive differences
- Unreliable comparison results

**Prevention:**
```python
# NULL-safe comparison
def safe_equals(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return a == b

# For database queries, use IS NOT DISTINCT FROM (PostgreSQL)
# or equivalent NULL-safe comparison
SELECT * FROM table1 t1
FULL OUTER JOIN table2 t2
  ON t1.id = t2.id
  AND (t1.value = t2.value OR (t1.value IS NULL AND t2.value IS NULL))
```

**Phase:** Phase 3

---

### Pitfall 6: Oracle Driver Deployment Complexity

**Problem:**
Oracle's `oracledb` thick mode requires Oracle Instant Client libraries, which are:
- Large downloads (~50MB)
- Platform-specific
- Require environment configuration (LD_LIBRARY_PATH, PATH)

**Impact:**
- Deployment failures
- "Cannot load OCI library" errors
- Support burden

**Prevention:**
```python
# Start with thin mode (pure Python, no Oracle client)
import oracledb

# Thin mode by default (oracledb 2.0+)
connection = oracledb.connect(
    user="username",
    password="password",
    host="hostname",
    port=1521,
    service_name="service"
)

# Document thick mode setup for advanced features:
# https://oracle.github.io/python-oracledb/thin thick.html
```

**Recommendation:** Use thin mode for Phase 2. Provide documentation for thick mode if advanced features (CLOB/BLOB streaming, advanced types) are needed.

**Phase:** Phase 2

---

### Pitfall 7: Primary Key Assumption

**Problem:**
Assuming all tables have primary keys. Tables without PKs cannot use key-based comparison.

**Impact:**
- Data comparison fails or produces incorrect results
- No way to match rows between source and target

**Prevention:**
```python
def compare_data(source_conn, target_conn, table):
    pk_columns = get_primary_key_columns(source_conn, table)

    if not pk_columns:
        # Fallback strategies:
        # 1. Use all columns as composite key
        # 2. Use ROWID (Oracle) or internal ID
        # 3. Report "Cannot compare: No primary key"
        pk_columns = get_all_columns(source_conn, table)
        # Or:
        raise ComparisonError(f"Table {table} has no primary key, cannot compare")

    # Proceed with PK-based comparison
```

**Phase:** Phase 3

---

### Pitfall 8: Timezone and Timestamp Handling

**Problem:**
MySQL TIMESTAMP converts to UTC, DATETIME does not. Oracle TIMESTAMP WITH TIME ZONE vs TIMESTAMP WITHOUT TIME ZONE. Comparing timestamps across databases with different timezone handling leads to apparent differences.

**Impact:**
- Timestamp columns always show as different
- Confusing results for users

**Prevention:**
```python
# Normalize timestamps to UTC for comparison
from datetime import datetime, timezone

def normalize_timestamp(dt: datetime, has_tz: bool) -> datetime:
    if dt is None:
        return None
    if has_tz and dt.tzinfo is None:
        # Assume UTC if no timezone but column expects it
        return dt.replace(tzinfo=timezone.utc)
    elif not has_tz and dt.tzinfo is not None:
        # Strip timezone for columns without TZ
        return dt.replace(tzinfo=None)
    return dt

# Document: "Timestamp comparisons are normalized to UTC"
```

**Phase:** Phase 2

---

## Moderate Pitfalls (Plan For)

### Pitfall 9: Float Precision Differences

**Problem:**
MySQL FLOAT/DOUBLE vs Oracle FLOAT/BINARY_DOUBLE may have slight precision differences due to IEEE 754 representation.

**Impact:**
- False positive differences on floating-point columns
- 1.00000001 vs 1.00000000

**Prevention:**
```python
import math

def float_equals(a: float, b: float, epsilon: float = 1e-9) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=epsilon)
```

**Phase:** Phase 3

---

### Pitfall 10: Schema Case Sensitivity

**Problem:**
MySQL table names are case-insensitive on Windows, case-sensitive on Linux. Oracle identifiers are uppercase by default unless quoted.

**Impact:**
- "Table not found" errors
- Inconsistent behavior across environments

**Prevention:**
```python
# Normalize table names based on database
def normalize_table_name(table: str, db_kind: str) -> str:
    if db_kind == 'oracle':
        return table.upper()  # Oracle default
    elif db_kind == 'mysql':
        return table  # Preserve case, depends on OS
    return table

# Always use consistent quoting in queries
# MySQL: Use backticks
# Oracle: Use double quotes for case-sensitive identifiers
```

**Phase:** Phase 1

---

## Pitfall Priority by Phase

| Phase | Pitfall | Severity |
|-------|---------|----------|
| Phase 1 | #1 Metadata Query Performance | HIGH |
| Phase 1 | #10 Schema Case Sensitivity | MEDIUM |
| Phase 2 | #3 MySQL-Oracle Type Mapping | HIGH |
| Phase 2 | #4 Character Set/Collation | MEDIUM |
| Phase 2 | #6 Oracle Driver Deployment | MEDIUM |
| Phase 2 | #8 Timezone Handling | MEDIUM |
| Phase 3 | #2 Memory Exhaustion | CRITICAL |
| Phase 3 | #5 NULL Handling | HIGH |
| Phase 3 | #7 Primary Key Assumption | HIGH |
| Phase 3 | #9 Float Precision | LOW |

---

## Security Pitfalls

### Pitfall 11: Credential Exposure in Logs

**Problem:**
Logging database connection strings or query results may expose passwords and sensitive data.

**Prevention:**
```python
import structlog

logger = structlog.get_logger()

# BAD: Logs credentials
logger.info("Connecting to DB", connection_string=str(config))

# GOOD: Redact sensitive fields
def redact_connection_info(config):
    return {
        "host": config.host,
        "port": config.port,
        "database": config.database,
        "username": config.username,
        "password": "***REDACTED***"
    }

logger.info("Connecting to DB", **redact_connection_info(config))
```

**Phase:** Phase 1

---

### Pitfall 12: SQL Injection in Dynamic Queries

**Problem:**
Building table names dynamically without validation allows SQL injection.

**Prevention:**
```python
# BAD: SQL injection vulnerability
def get_table_metadata_bad(table_name):
    query = f"SELECT * FROM information_schema.COLUMNS WHERE TABLE_NAME = '{table_name}'"
    cursor.execute(query)  # Vulnerable!

# GOOD: Validate table name, use parameterized queries
def get_table_metadata_good(table_name):
    # Validate table name format (alphanumeric + underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    # Use parameterized query where possible
    query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_NAME = %s"
    cursor.execute(query, (table_name,))
```

**Phase:** Phase 1

---

*Last updated: 2026-03-28*
