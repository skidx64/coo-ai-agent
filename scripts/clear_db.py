"""Clear all data from database tables for fresh testing."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config import settings

def clear_database():
    """Clear all tables in the database."""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Disable foreign key constraints
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        conn.commit()

        # Get all table names
        tables_result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ))
        tables = [row[0] for row in tables_result]

        # Delete all data from each table
        for table in tables:
            print(f"Clearing table: {table}")
            conn.execute(text(f"DELETE FROM {table}"))

        conn.commit()

        # Re-enable foreign key constraints
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()

        print("\n✅ Database cleared successfully!")
        print(f"Cleared {len(tables)} tables: {', '.join(tables)}")

if __name__ == "__main__":
    clear_database()
