"""
Migration 003: Enrich existing devices with vendor information

This script backfills the vendor column for existing devices by running
MAC OUI lookup using the built-in classifier database.

Usage:
    VIGIL_DB_PATH=/path/to/vigil.db python3 migrations/003_enrich_vendors.py

The script will:
1. Load all devices from the database
2. Look up vendor from MAC OUI using the built-in classifier
3. Update devices with missing vendor info
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import classifier
from app.ai.classifier import DeviceClassifier

# Allow override via environment variable
DB_PATH = os.environ.get("VIGIL_DB_PATH", "/data/vigil.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vendor-enrichment")


def enrich_vendors():
    """Backfill vendor information for all devices."""
    if not Path(DB_PATH).exists():
        logger.error(f"Database not found at {DB_PATH}")
        logger.error("Set VIGIL_DB_PATH environment variable or ensure database exists")
        return

    # Initialize classifier with built-in OUI database
    classifier = DeviceClassifier()

    # Connect to database
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get all devices
        from app.models import Device
        devices = db.query(Device).all()

        logger.info(f"Found {len(devices)} devices to enrich")

        updated = 0
        skipped = 0
        unknown = 0

        for device in devices:
            if device.vendor:
                skipped += 1
                continue

            vendor = classifier.oui_vendor(device.mac)
            if vendor:
                device.vendor = vendor
                updated += 1
                logger.info(f"  {device.mac} → {vendor}")
            else:
                unknown += 1
                logger.debug(f"  {device.mac} → unknown vendor")

        db.commit()

        logger.info(f"\nEnrichment complete:")
        logger.info(f"  Updated: {updated}")
        logger.info(f"  Skipped (already had vendor): {skipped}")
        logger.info(f"  Unknown vendor: {unknown}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during enrichment: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    enrich_vendors()
