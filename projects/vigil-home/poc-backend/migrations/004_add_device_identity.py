"""
Migration 004: Add device identity fields for layperson-friendly UI

Adds:
- nickname: User-defined friendly name (e.g., "Dad's iPhone")
- icon_type: Auto-detected icon category (smartphone, laptop, tv, etc.)
- containment_status: Device security state (trusted, blocked, observing, pending_review)
- user_trust_override: Whether user manually set trust status

Usage:
    VIGIL_DB_PATH=/path/to/vigil.db python3 migrations/004_add_device_identity.py
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Allow override via environment variable
DB_PATH = os.environ.get("VIGIL_DB_PATH", "/data/vigil.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("device-identity-migration")


def migrate():
    """Add device identity columns to devices table."""
    if not Path(DB_PATH).exists():
        logger.error(f"Database not found at {DB_PATH}")
        logger.error("Set VIGIL_DB_PATH environment variable or ensure database exists")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(devices)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        new_columns = []

        # Add nickname column
        if "nickname" not in existing_columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN nickname TEXT")
            new_columns.append("nickname")
            logger.info("Added column: nickname")

        # Add icon_type column
        if "icon_type" not in existing_columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN icon_type TEXT")
            new_columns.append("icon_type")
            logger.info("Added column: icon_type")

        # Add containment_status column with default
        if "containment_status" not in existing_columns:
            cursor.execute(
                "ALTER TABLE devices ADD COLUMN containment_status TEXT DEFAULT 'pending_review'"
            )
            new_columns.append("containment_status")
            logger.info("Added column: containment_status (default: pending_review)")

        # Add user_trust_override column
        if "user_trust_override" not in existing_columns:
            cursor.execute(
                "ALTER TABLE devices ADD COLUMN user_trust_override BOOLEAN DEFAULT 0"
            )
            new_columns.append("user_trust_override")
            logger.info("Added column: user_trust_override (default: 0)")

        # Backfill containment_status based on trust_score
        cursor.execute("""
            UPDATE devices 
            SET containment_status = CASE
                WHEN trust_score > 0.7 THEN 'trusted'
                WHEN trust_score < 0.3 THEN 'blocked'
                ELSE 'observing'
            END
            WHERE containment_status = 'pending_review' OR containment_status IS NULL
        """)
        updated = cursor.rowcount
        logger.info(f"Backfilled containment_status for {updated} devices")

        # Backfill icon_type based on device_type
        icon_mapping = {
            'phone': 'smartphone',
            'mobile': 'smartphone',
            'computer': 'laptop',
            'laptop': 'laptop',
            'desktop': 'desktop',
            'tv': 'tv',
            'media': 'tv',
            'camera': 'camera',
            'security_camera': 'camera',
            'iot': 'device',
            'smart_device': 'device',
            'router': 'router',
            'server': 'server',
        }

        for device_type, icon_type in icon_mapping.items():
            cursor.execute(
                "UPDATE devices SET icon_type = ? WHERE device_type = ? AND icon_type IS NULL",
                (icon_type, device_type)
            )
            if cursor.rowcount > 0:
                logger.info(f"Set icon_type='{icon_type}' for {cursor.rowcount} {device_type} devices")

        conn.commit()

        if new_columns:
            logger.info(f"\nMigration complete! Added columns: {', '.join(new_columns)}")
        else:
            logger.info("\nMigration complete! All columns already exist.")

        # Verify
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"\nCurrent device columns: {', '.join(columns)}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
