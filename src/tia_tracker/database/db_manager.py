"""Database manager for TIA Version Tracker.

Handles database initialization, connection management, and basic operations.
"""

import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: str = "database/tia_tracker.db"):
        """Initialize database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection.

        Returns:
            SQLite connection object
        """
        conn = sqlite3.Connection(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_database(self) -> None:
        """Initialize the database schema."""
        # Get the path to the database directory (sibling to the Python package)
        package_dir = Path(__file__).parent.parent.parent.parent
        schema_path = package_dir / "database" / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
            print(f"[OK] Database initialized at {self.db_path}")
        finally:
            conn.close()

    def execute_query(
        self, query: str, params: Optional[tuple] = None, fetch: bool = False
    ) -> list[sqlite3.Row] | int:
        """Execute a SQL query.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            List of rows if fetch=True, otherwise last row id
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()


def main():
    """CLI entry point for database management."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        db_manager = DatabaseManager()
        db_manager.initialize_database()
    else:
        print("Usage: python -m src.tia_tracker.database.db_manager init")


if __name__ == "__main__":
    main()
