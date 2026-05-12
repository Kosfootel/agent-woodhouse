"""
Shared test fixtures and infrastructure for Vigil Home tests.

Provides:
- In-memory SQLite database per test session
- Clean database between test functions
- Authenticated test client helpers
- Cleanup of AI in-memory caches
"""

import os
import json
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment before any app imports
os.environ["VIGIL_DB_PATH"] = "/tmp/vigil_test_shared.db"
os.environ["VIGIL_AUTH_DISABLED"] = "false"
os.environ["VIGIL_ADMIN_USERNAME"] = "testadmin"
os.environ["VIGIL_ADMIN_PASSWORD"] = "testpass123"
os.environ["VIGIL_JWT_SECRET"] = "test-jwt-secret-for-testing-only"
os.environ["VIGIL_RATE_LIMIT_ENABLED"] = "false"

# Clean database files before import
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(f"/tmp/vigil_test_shared.db{suffix}")
    except FileNotFoundError:
        pass

from app.database import get_db, init_db
from app.models import Base, User, ApiKey, RefreshToken, Device, Event, Alert
from app.auth import bootstrap_admin
from app.main import app
from app.ai_persistence import clear_ai_cache

# ── Test database engine ───────────────────────────────────────────

TEST_DB_URL = "sqlite:////tmp/vigil_test_shared.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

# Bootstrap admin user
db = TestingSessionLocal()
try:
    bootstrap_admin(db)
finally:
    db.close()


# ── Test client ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


# ── Database cleanup between tests ─────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """Clean all tables and AI caches between tests."""
    db = TestingSessionLocal()
    try:
        # Delete in dependency order (FK-safe for SQLite with no FK enforcement)
        db.query(Alert).delete()
        db.query(Event).delete()
        db.query(Device).delete()
        db.query(RefreshToken).delete()
        db.query(ApiKey).delete()
        # Don't delete User — bootstrap_admin creates it once
        db.commit()
    finally:
        db.close()

    # Clear AI in-memory caches
    clear_ai_cache()

    # Re-assert the admin user exists (bootstrap_admin is idempotent)
    db = TestingSessionLocal()
    try:
        bootstrap_admin(db)
    finally:
        db.close()

    yield


# ── Auth helpers ───────────────────────────────────────────────────

def login(client: TestClient, username: str = "testadmin",
          password: str = "testpass123") -> dict:
    """Log in and return the response JSON."""
    resp = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


def auth_headers(client: TestClient, username: str = "testadmin",
                 password: str = "testpass123") -> dict:
    """Log in and return Authorization headers with Bearer token."""
    tokens = login(client, username, password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ── Device fixtures ────────────────────────────────────────────────

@pytest.fixture
def headers(client: TestClient) -> dict:
    """Authenticated headers for protected endpoints."""
    return auth_headers(client)


def create_device_via_api(client: TestClient, headers: dict,
                          mac: str = "aa:bb:cc:dd:ee:01",
                          ip: str = "192.168.1.10",
                          hostname: str = "test-cam-01",
                          device_type: str | None = None) -> dict:
    """Helper: create a device via POST /devices and return the response JSON."""
    payload = {"mac": mac, "ip": ip, "hostname": hostname}
    if device_type:
        payload["device_type"] = device_type
    resp = client.post("/devices", json=payload, headers=headers)
    assert resp.status_code == 200, f"Device creation failed: {resp.text}"
    return resp.json()["device"]


def create_event_via_api(client: TestClient, headers: dict,
                         device_id: int,
                         event_type: str = "generic",
                         severity: str = "info",
                         value: float | None = None,
                         details: dict | None = None) -> dict:
    """Helper: ingest an event via POST /events and return the response JSON."""
    payload = {
        "device_id": device_id,
        "event_type": event_type,
        "severity": severity,
    }
    if value is not None:
        payload["value"] = value
    if details:
        payload["details"] = details
    resp = client.post("/events", json=payload, headers=headers)
    assert resp.status_code == 200, f"Event ingest failed: {resp.text}"
    return resp.json()


# ── Test-level cleanup ─────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    # Clean up test database files
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(f"/tmp/vigil_test_shared.db{suffix}")
        except FileNotFoundError:
            pass
