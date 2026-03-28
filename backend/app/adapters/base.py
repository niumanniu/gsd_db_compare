"""Database Adapter abstract base class."""

from abc import ABC, abstractmethod
from typing import Any


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    Provides a common interface for extracting metadata from different database types.
    """

    def __init__(self, connection_config: dict):
        """Initialize adapter with connection configuration.

        Args:
            connection_config: Database connection parameters (host, port, database, etc.)
        """
        self.config = connection_config
        self._connection = None

    @abstractmethod
    def connect(self) -> Any:
        """Establish database connection.

        Returns:
            Database connection object
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def get_tables(self) -> list[dict]:
        """List all tables in database.

        Returns:
            List of table metadata dicts with table_name, table_type, etc.
        """
        pass

    @abstractmethod
    def get_table_metadata(self, table_name: str) -> dict:
        """Get metadata for a specific table.

        Args:
            table_name: Name of table to inspect

        Returns:
            Dict with columns, indexes, constraints, primary_key information
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_database_type(self) -> str:
        """Return database type identifier (e.g., 'mysql', 'oracle').

        Returns:
            Database type string
        """
        pass

    @abstractmethod
    def get_database_version(self) -> str:
        """Return database version string.

        Returns:
            Database version string
        """
        pass
