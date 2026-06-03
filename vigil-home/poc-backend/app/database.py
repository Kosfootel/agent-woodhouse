"""Vigil Home - Database setup"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("vigil.database")

DB_PATH = os.environ.get("VIGIL_DB_PATH", "/data/vigil.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Enable WAL mode for better concurrent performance
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables if they don't exist.

    Ensures the database directory exists and tables are created.
    """
    # Ensure the directory for the database exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create database directory {db_dir}: {e}")

    from app.models import Base  # noqa: F811
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {DB_PATH}")


def get_db():
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
