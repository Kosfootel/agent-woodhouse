#!/usr/bin/env python3
"""
Database migration: Add alert acknowledgement tracking columns.

This migration adds `acknowledged_at` and `acknowledged_by` columns
to the `alerts` table for audit trail support.

Usage:
    cd poc-backend
    python migrations/001_add_alert_ack_fields.py
"""

import os
import sys
import sqlite3
from pathlib import Path

# Allow imports from the app package
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DB_PATH


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH} — nothing to migrate.")
        print("Tables will be created automatically on next app startup.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(alerts)")
    columns = {row[1] for row in cursor.fetchall()}

    if "acknowledged_at" not in columns:
        cursor.execute(
            "ALTER TABLE alerts ADD COLUMN acknowledged_at TIMESTAMP"
        )
        print("Added column: acknowledged_at")
    else:
        print("Column already exists: acknowledged_at")

    if "acknowledged_by" not in columns:
        cursor.execute(
            "ALTER TABLE alerts ADD COLUMN acknowledged_by TEXT"
        )
        print("Added column: acknowledged_by")
    else:
        print("Column already exists: acknowledged_by")

    # Backfill: set acknowledged_at for any alerts already marked 'acknowledged'
    cursor.execute(
        """
        UPDATE alerts
        SET acknowledged_at = timestamp
        WHERE status = 'acknowledged' AND acknowledged_at IS NULL
        """
    )
    backfilled = cursor.rowcount
    if backfilled > 0:
        print(f"Backfilled acknowledged_at for {backfilled} existing acknowledged alerts")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
