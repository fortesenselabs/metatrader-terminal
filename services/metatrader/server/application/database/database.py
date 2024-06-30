import sqlite3
from typing import List, Any, Optional


class Database:
    """
    Database Interface.

    Use sqlite as the default implementation.
    """

    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connect to the database."""
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def create(self, table_name: str, schema: str):
        """Create a table with the given schema."""
        self.connect()
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
        self.connection.commit()
        self.close()

    def insert(self, table_name: str, columns: str, values: List[Any]):
        """Insert a new record into the table."""
        self.connect()
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.connection.commit()
        self.close()

    def update(
        self, table_name: str, set_clause: str, condition: str, values: List[Any]
    ):
        """Update records in the table."""
        self.connect()
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.cursor.execute(query, values)
        self.connection.commit()
        self.close()

    def find_by_id(
        self, table_name: str, id_column: str, id_value: Any
    ) -> Optional[sqlite3.Row]:
        """Find a record by ID."""
        self.connect()
        self.cursor.execute(
            f"SELECT * FROM {table_name} WHERE {id_column} = ?", (id_value,)
        )
        result = self.cursor.fetchone()
        self.close()
        return result

    def find_all(self, table_name: str) -> List[sqlite3.Row]:
        """Find all records in a table."""
        self.connect()
        self.cursor.execute(f"SELECT * FROM {table_name}")
        results = self.cursor.fetchall()
        self.close()
        return results

    def delete_by_id(self, table_name: str, id_column: str, id_value: Any):
        """Delete a record by ID."""
        self.connect()
        self.cursor.execute(
            f"DELETE FROM {table_name} WHERE {id_column} = ?", (id_value,)
        )
        self.connection.commit()
        self.close()

    def delete_all(self, table_name: str):
        """Delete all records in a table."""
        self.connect()
        self.cursor.execute(f"DELETE FROM {table_name}")
        self.connection.commit()
        self.close()

    def execute_custom_query(
        self, query: str, parameters: Optional[List[Any]] = None
    ) -> Any:
        """Execute a custom query."""
        self.connect()
        if parameters:
            self.cursor.execute(query, parameters)
        else:
            self.cursor.execute(query)
        results = self.cursor.fetchall()
        self.connection.commit()
        self.close()
        return results


# Example usage:
# db = Database("example.db")
# db.create("users", "id INTEGER PRIMARY KEY, name TEXT, age INTEGER")
# db.insert("users", "name, age", ["Alice", 30])
# user = db.find_by_id("users", "id", 1)
# print(user)
