"""Database adapters package."""

from app.adapters.base import DatabaseAdapter
from app.adapters.mysql import MySQLAdapter
from app.adapters.oracle import OracleAdapter


def get_adapter(db_type: str, connection_config: dict) -> DatabaseAdapter:
    """Factory function to get appropriate adapter for database type.

    Args:
        db_type: Database type ('mysql' or 'oracle')
        connection_config: Connection configuration dict

    Returns:
        DatabaseAdapter instance

    Raises:
        ValueError: If db_type not supported
    """
    adapters = {
        'mysql': MySQLAdapter,
        'oracle': OracleAdapter,
    }

    if db_type not in adapters:
        raise ValueError(f"Unsupported database type: {db_type}")

    return adapters[db_type](connection_config)


__all__ = ["DatabaseAdapter", "MySQLAdapter", "OracleAdapter", "get_adapter"]
