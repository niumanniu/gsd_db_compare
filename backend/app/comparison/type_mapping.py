"""Database type mappings for cross-database comparison.

Note: Full cross-database comparison deferred to later phase.
This module provides infrastructure for type normalization.
"""

# MySQL base types
MYSQL_TYPES = {
    'tinyint', 'smallint', 'mediumint', 'int', 'integer', 'bigint',
    'bit', 'decimal', 'numeric', 'float', 'double', 'real',
    'date', 'time', 'datetime', 'timestamp', 'year',
    'char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext',
    'binary', 'varbinary', 'tinyblob', 'blob', 'mediumblob', 'longblob',
    'enum', 'set', 'json', 'geometry', 'point', 'linestring', 'polygon',
}

# Oracle base types
ORACLE_TYPES = {
    'char', 'nchar', 'varchar2', 'nvarchar2',
    'number', 'float', 'binary_float', 'binary_double',
    'date', 'timestamp', 'timestamp with time zone', 'timestamp with local time zone',
    'interval year to month', 'interval day to second',
    'clob', 'nclob', 'blob', 'bfile', 'long', 'long raw', 'raw', 'rowid', 'urowid', 'xmltype',
}

# Common canonical types for comparison
CANONICAL_TYPES = {
    # Integer types
    'tinyint': 'integer',
    'smallint': 'integer',
    'mediumint': 'integer',
    'int': 'integer',
    'integer': 'integer',
    'bigint': 'integer',
    'number': 'integer',  # Oracle NUMBER without precision/scale

    # Decimal/numeric types
    'decimal': 'decimal',
    'numeric': 'decimal',
    'float': 'float',
    'double': 'float',
    'real': 'float',
    'binary_float': 'float',
    'binary_double': 'float',

    # String types
    'char': 'char',
    'nchar': 'char',
    'varchar': 'string',
    'varchar2': 'string',
    'nvarchar2': 'string',
    'tinytext': 'string',
    'text': 'string',
    'mediumtext': 'string',
    'longtext': 'string',
    'clob': 'string',
    'nclob': 'string',

    # Date/time types
    'date': 'datetime',
    'datetime': 'datetime',
    'timestamp': 'datetime',
    'time': 'datetime',
    'year': 'datetime',

    # Binary types
    'binary': 'binary',
    'varbinary': 'binary',
    'blob': 'binary',
    'tinyblob': 'binary',
    'mediumblob': 'binary',
    'longblob': 'binary',
    'bfile': 'binary',
    'long': 'binary',
    'raw': 'binary',

    # Special types
    'json': 'json',
    'xmltype': 'json',
    'enum': 'enum',
    'set': 'set',
    'geometry': 'spatial',
    'point': 'spatial',
    'linestring': 'spatial',
}


def normalize_database_type(type_str: str, db_type: str = 'mysql') -> str:
    """Normalize database type to canonical form.

    Args:
        type_str: Database-specific type string (e.g., 'VARCHAR(255)', 'NUMBER(10,2)')
        db_type: Database type ('mysql' or 'oracle')

    Returns:
        Canonical type string for comparison
    """
    if not type_str:
        return 'unknown'

    # Extract base type (remove precision/scale)
    type_str = type_str.lower().strip()
    if '(' in type_str:
        base_type = type_str.split('(')[0]
    else:
        base_type = type_str

    # Map to canonical type
    return CANONICAL_TYPES.get(base_type, base_type)
