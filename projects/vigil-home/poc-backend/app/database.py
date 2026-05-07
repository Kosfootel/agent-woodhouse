"""Vigil Home - Database setup"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = os.environ.get("VIGIL_DB_PATH", "/data/vigil.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    from app.models import Base  # noqa: F811

    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
