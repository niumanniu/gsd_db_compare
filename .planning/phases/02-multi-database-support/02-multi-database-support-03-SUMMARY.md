---
phase: 02-multi-database-support
plan: 03
wave: 2
title: Type Mapping + Enhanced Comparison
completed: 2026-03-28
---

# Plan 03 Summary: Type Mapping + Enhanced Comparison

## Overview

Successfully implemented database type mapping infrastructure and enhanced SchemaComparator with database-aware comparison capabilities.

## Implementation Details

### 1. Type Mapping Module (`backend/app/comparison/type_mapping.py`)

**Purpose:** Provide canonical type mappings for cross-database comparison.

**Type Sets:**
```python
MYSQL_TYPES = {
    'tinyint', 'smallint', 'mediumint', 'int', 'integer', 'bigint',
    'decimal', 'numeric', 'float', 'double', 'real',
    'char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext',
    # ... and more
}

ORACLE_TYPES = {
    'char', 'nchar', 'varchar2', 'nvarchar2',
    'number', 'float', 'binary_float', 'binary_double',
    'clob', 'nclob', 'blob', 'bfile',
    # ... and more
}
```

**Canonical Type Mapping:**
```python
CANONICAL_TYPES = {
    # Integer types
    'tinyint': 'integer', 'smallint': 'integer', 'int': 'integer',
    'number': 'integer',  # Oracle

    # Decimal types
    'decimal': 'decimal', 'numeric': 'decimal',

    # String types
    'varchar': 'string', 'varchar2': 'string',
    'text': 'string', 'clob': 'string',

    # Date/time types
    'date': 'datetime', 'datetime': 'datetime', 'timestamp': 'datetime',

    # Binary types
    'blob': 'binary', 'bfile': 'binary', 'raw': 'binary',
}
```

**Normalization Function:**
```python
def normalize_database_type(type_str: str, db_type: str = 'mysql') -> str:
    """Normalize database type to canonical form."""
    # Extract base type (remove precision/scale)
    # Map to canonical type via CANONICAL_TYPES
```

### 2. Enhanced SchemaComparator (`backend/app/comparison/schema.py`)

**New Constructor Parameters:**
```python
class SchemaComparator:
    def __init__(
        self,
        source_db_type: str = 'mysql',
        target_db_type: str = 'mysql',
    ):
        self.source_db_type = source_db_type
        self.target_db_type = target_db_type
        self.same_db_type = source_db_type == target_db_type
```

**Enhanced compare() Method:**
```python
def compare(
    self,
    source_metadata: dict,
    target_metadata: dict,
    source_db_type: str | None = None,
    target_db_type: str | None = None,
) -> SchemaDiff:
    # Use instance defaults or provided values
    # Pass db types to compare_columns for type-aware comparison
```

**Comparison Modes:**

| Mode | Behavior |
|------|----------|
| Same Database (MySQL vs MySQL) | Strict type matching, normalize only precision/scale |
| Cross Database (MySQL vs Oracle) | Canonical type matching via type_mapping module |

**New Methods:**
- `_normalize_type_strict(type_str)` - Same-db normalization (preserves DECIMAL precision)
- `_normalize_type(type_str, db_type)` - Cross-db normalization using type_mapping

### 3. Adapter Database Type Methods

**Base Adapter (`backend/app/adapters/base.py`):**
Added abstract methods:
```python
@abstractmethod
def get_database_type(self) -> str:
    """Return database type identifier ('mysql' or 'oracle')."""

@abstractmethod
def get_database_version(self) -> str:
    """Return database version string."""
```

**MySQLAdapter (`backend/app/adapters/mysql.py`):**
```python
def get_database_type(self) -> str:
    return 'mysql'

def get_database_version(self) -> str:
    cursor = self._connection.cursor()
    cursor.execute("SELECT VERSION()")
    return cursor.fetchone()[0]
```

**OracleAdapter (`backend/app/adapters/oracle.py`):**
```python
def get_database_type(self) -> str:
    return 'oracle'

def get_database_version(self) -> str:
    cursor = self._connection.cursor()
    cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
    return cursor.fetchone()[0]
```

### 4. Comparison API Update (`backend/app/api/compare.py`)

**Adapter Factory Usage:**
```python
from app.adapters import get_adapter

source_adapter = get_adapter(source_conn.db_type, source_config)
target_adapter = get_adapter(target_conn.db_type, target_config)
```

**Database Type Awareness:**
```python
source_db_type = source_adapter.get_database_type()
target_db_type = target_adapter.get_database_type()

comparator = SchemaComparator(
    source_db_type=source_db_type,
    target_db_type=target_db_type,
)
```

**Response Enhancement:**
```python
comparison_mode = 'same-database' if source_db_type == target_db_type else 'cross-database'

return SchemaDiffResponse(
    # ... existing fields
    source_db_type=source_db_type,
    target_db_type=target_db_type,
    comparison_mode=comparison_mode,
)
```

### 5. Schema Response Update (`backend/app/schemas/api.py`)

**Extended SchemaDiffResponse:**
```python
class SchemaDiffResponse(BaseModel):
    # ... existing fields
    source_db_type: Optional[str] = None
    target_db_type: Optional[str] = None
    comparison_mode: Optional[str] = None

    def __post_init__(self):
        if self.comparison_mode is None and self.source_db_type and self.target_db_type:
            self.comparison_mode = 'same-database' if self.source_db_type == self.target_db_type else 'cross-database'
```

## Files Created/Modified

| File | Change |
|------|--------|
| `backend/app/comparison/type_mapping.py` | Created - Type mapping infrastructure |
| `backend/app/comparison/schema.py` | Enhanced - Database-aware comparison |
| `backend/app/adapters/base.py` | Added abstract methods |
| `backend/app/adapters/mysql.py` | Implemented db type methods |
| `backend/app/adapters/oracle.py` | Implemented db type methods |
| `backend/app/api/compare.py` | Updated to use factory + db types |
| `backend/app/schemas/api.py` | Extended response schema |

## Type Normalization Examples

### Same Database Mode (Strict)
```
VARCHAR(255) vs VARCHAR(100) → Both normalize to 'varchar' → MATCH
DECIMAL(10,2) vs DECIMAL(12,4) → Keep full spec → DIFFER
INT(11) vs INT → Both normalize to 'int' → MATCH
```

### Cross Database Mode (Canonical)
```
MySQL VARCHAR(255) vs Oracle VARCHAR2(255) → Both 'string' → MATCH
MySQL INT vs Oracle NUMBER → Both 'integer' → MATCH
MySQL DATETIME vs Oracle TIMESTAMP → Both 'datetime' → MATCH
MySQL BLOB vs Oracle BLOB → Both 'binary' → MATCH
```

## Verification

- [x] MYSQL_TYPES set defined
- [x] ORACLE_TYPES set defined
- [x] CANONICAL_TYPES mapping defined
- [x] normalize_database_type() function works
- [x] SchemaComparator accepts db_type parameters
- [x] compare() method handles different db types
- [x] _normalize_type uses type_mapping module
- [x] Adapters return correct db type identifiers
- [x] API responses include db type metadata

## Type Mapping Decisions

1. **Precision Handling:** DECIMAL/NUMERIC types keep full precision specification for strict comparison
2. **Case Insensitivity:** All type strings normalized to lowercase
3. **Base Type Extraction:** Precision/scale removed before canonical mapping
4. **Unknown Types:** Return as-is if not in CANONICAL_TYPES

## Comparison Mode Behavior

**Same-Database Mode (Default):**
- Uses strict type matching
- Normalizes only precision/scale differences
- More sensitive to type definition changes

**Cross-Database Mode:**
- Uses canonical type matching
- Maps database-specific types to common canonical forms
- Enables MySQL vs Oracle comparison (future use)
