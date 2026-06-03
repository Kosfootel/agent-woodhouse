"""
Migration 002: Add vendor column to devices table

This migration adds a vendor column to store manufacturer information
derived from MAC OUI lookup during device classification.

Usage:
    VIGIL_DB_PATH=/path/to/vigil.db python3 migrations/002_add_vendor_column.py

For existing devices, run the enrichment script after migration:
    VIGIL_DB_PATH=/path/to/vigil.db python3 migrations/003_enrich_vendors.py
"""

import os
import sqlite3
from pathlib import Path

# Allow override via environment variable
DB_PATH = os.environ.get("VIGIL_DB_PATH", "/data/vigil.db")


def migrate():
    """Add vendor column to devices table."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(devices)")
    columns = [row[1] for row in cursor.fetchall()]

    if "vendor" in columns:
        print("Column 'vendor' already exists in devices table. Skipping.")
        conn.close()
        return

    # Add vendor column
    cursor.execute("""
        ALTER TABLE devices
        ADD COLUMN vendor TEXT
    """)

    conn.commit()
    conn.close()

    print("Migration 002 complete: Added 'vendor' column to devices table")


if __name__ == "__main__":
    migrate()
