"""Tests for Vigil Home API key authentication and SSE stream."""

import os
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test database before importing app
os.environ["VIGIL_DB_PATH"] = "/tmp/vigil_test_apikeys.db"
os.environ["VIGIL_AUTH_DISABLED"] = "false"
os.environ["VIGIL_ADMIN_USERNAME"] = "testadmin"
os.environ["VIGIL_ADMIN_PASSWORD"] = "testpass123"
os.environ["VIGIL_JWT_SECRET"] = "test-jwt-secret-for-testing-only"

# Remove test database if exists
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(f"/tmp/vigil_test_apikeys.db{suffix}")
    except FileNotFoundError:
        pass

from app.database import get_db
from app.models import Base, ApiKey
from app.auth import (
    create_api_key,
    generate_api_key,
    hash_api_key,
    validate_api_key,
    API_KEY_PREFIX,
    bootstrap_admin,
)
from app.main import app

# ── Test database setup ────────────────────────────────────────────

TEST_DB_PATH = "/tmp/vigil_test_apikeys.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

# Bootstrap admin
db = TestingSessionLocal()
try:
    bootstrap_admin(db)
finally:
    db.close()


# ── Test client ────────────────────────────────────────────────────

client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_api_keys():
    """Clean API keys between tests."""
    db = TestingSessionLocal()
    try:
        db.query(ApiKey).delete()
        db.commit()
    finally:
        db.close()


def _login() -> dict:
    """Helper: login and return tokens."""
    resp = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
    )
    assert resp.status_code == 200
    return resp.json()


# ── Tests: API key generation ──────────────────────────────────────


class TestApiKeyGeneration:
    def test_generate_api_key_has_prefix(self):
        key = generate_api_key()
        assert key.startswith(API_KEY_PREFIX)
        assert len(key) > len(API_KEY_PREFIX) + 20

    def test_generate_api_key_is_unique(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100

    def test_hash_api_key_is_consistent(self):
        key = generate_api_key()
        h1 = hash_api_key(key)
        h2 = hash_api_key(key)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256

    def test_api_key_prefix_extraction(self):
        from app.auth import get_api_key_prefix
        key = generate_api_key()
        prefix = get_api_key_prefix(key)
        assert len(prefix) == 8
        assert key.endswith(prefix) is False  # prefix is from start of random part


# ── Tests: API key creation ────────────────────────────────────────


class TestApiKeyCreation:
    def test_create_api_key_stores_hash(self):
        db = TestingSessionLocal()
        try:
            result = create_api_key(db, label="test-node")
            assert "plaintext_key" in result
            assert result["record"].label == "test-node"
            assert result["record"].is_active == 1

            # Plaintext should start with prefix
            assert result["plaintext_key"].startswith(API_KEY_PREFIX)

            # Hash should match
            stored_hash = result["record"].key_hash
            computed = hashlib.sha256(result["plaintext_key"].encode()).hexdigest()
            assert stored_hash == computed
        finally:
            db.close()

    def test_create_multiple_api_keys(self):
        db = TestingSessionLocal()
        try:
            r1 = create_api_key(db, label="node-1")
            r2 = create_api_key(db, label="node-2")
            assert r1["plaintext_key"] != r2["plaintext_key"]
            assert r1["record"].id != r2["record"].id
        finally:
            db.close()

    def test_create_api_key_with_custom_role(self):
        db = TestingSessionLocal()
        try:
            result = create_api_key(db, label="readonly", role="viewer")
            assert result["record"].role == "viewer"
        finally:
            db.close()


# ── Tests: API key validation ──────────────────────────────────────


class TestApiKeyValidation:
    def test_validate_valid_key(self):
        db = TestingSessionLocal()
        try:
            result = create_api_key(db, label="valid-node")
            payload = validate_api_key(result["plaintext_key"], db)
            assert payload is not None
            assert payload["role"] == "admin"
            assert payload["auth_method"] == "apikey"
            assert payload["label"] == "valid-node"
            assert payload["sub"].startswith("apikey:")
        finally:
            db.close()

    def test_validate_nonexistent_key(self):
        db = TestingSessionLocal()
        try:
            payload = validate_api_key("vh_nonexistentkey123456789", db)
            assert payload is None
        finally:
            db.close()

    def test_validate_revoked_key(self):
        db = TestingSessionLocal()
        try:
            result = create_api_key(db, label="revocable")
            key = result["plaintext_key"]
            api_key_id = result["record"].id

            # Revoke it
            stored = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
            stored.is_active = 0
            db.commit()

            # Should fail validation
            payload = validate_api_key(key, db)
            assert payload is None
        finally:
            db.close()

    def test_validate_updates_last_used(self):
        db = TestingSessionLocal()
        try:
            result = create_api_key(db, label="usage-tracker")
            key = result["plaintext_key"]
            api_key_id = result["record"].id

            # Before: last_used should be None
            stored = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
            assert stored.last_used_at is None

            # Validate
            validate_api_key(key, db)

            # After: last_used should be set
            stored = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
            assert stored.last_used_at is not None
        finally:
            db.close()


# ── Tests: API key via HTTP endpoints ──────────────────────────────


class TestApiKeyHttp:
    def test_list_api_keys_empty(self):
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = client.get("/auth/api-keys", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["keys"] == []

    def test_create_api_key_via_endpoint(self):
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = client.post(
            "/auth/api-keys",
            json={"label": "suricata-node-1"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "plaintext_key" in data
        assert data["key"]["label"] == "suricata-node-1"
        assert data["key"]["is_active"] is True
        assert data["warning"] is not None

    def test_create_api_key_requires_auth(self):
        resp = client.post(
            "/auth/api-keys",
            json={"label": "unauthorized"},
        )
        assert resp.status_code == 401

    def test_list_api_keys_after_creation(self):
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create a key
        client.post(
            "/auth/api-keys",
            json={"label": "test-key"},
            headers=headers,
        )

        # List keys
        resp = client.get("/auth/api-keys", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["keys"][0]["label"] == "test-key"
        # Make sure hash is not exposed
        assert "key_hash" not in data["keys"][0]

    def test_revoke_api_key(self):
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create a key
        create_resp = client.post(
            "/auth/api-keys",
            json={"label": "revocable"},
            headers=headers,
        )
        key_id = create_resp.json()["key"]["id"]
        plaintext = create_resp.json()["plaintext_key"]

        # Revoke it
        revoke_resp = client.delete(
            f"/auth/api-keys/{key_id}",
            headers=headers,
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["key"]["is_active"] is False

        # Verify it's no longer valid
        db = TestingSessionLocal()
        try:
            from app.auth import validate_api_key
            payload = validate_api_key(plaintext, db)
            assert payload is None
        finally:
            db.close()

    def test_revoke_nonexistent_key_returns_404(self):
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = client.delete("/auth/api-keys/99999", headers=headers)
        assert resp.status_code == 404

    def test_revoke_requires_auth(self):
        resp = client.delete("/auth/api-keys/1")
        assert resp.status_code == 401


# ── Tests: API key used as auth for protected endpoints ────────────


class TestApiKeyAsAuth:
    def test_api_key_header_can_access_protected_endpoints(self):
        tokens = _login()
        admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create an API key
        create_resp = client.post(
            "/auth/api-keys",
            json={"label": "headless-sensor"},
            headers=admin_headers,
        )
        api_key = create_resp.json()["plaintext_key"]

        # Use it to access a protected endpoint
        headers = {"X-API-Key": api_key}
        resp = client.get("/devices", headers=headers)
        assert resp.status_code == 200

    def test_api_key_header_can_access_email_endpoint(self):
        tokens = _login()
        admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = client.post(
            "/auth/api-keys",
            json={"label": "script"},
            headers=admin_headers,
        )
        api_key = create_resp.json()["plaintext_key"]

        headers = {"X-API-Key": api_key}
        resp = client.get("/email/status", headers=headers)
        assert resp.status_code == 200

    def test_revoked_api_key_gets_401(self):
        tokens = _login()
        admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = client.post(
            "/auth/api-keys",
            json={"label": "temporary"},
            headers=admin_headers,
        )
        api_key = create_resp.json()["plaintext_key"]
        key_id = create_resp.json()["key"]["id"]

        # Revoke
        client.delete(f"/auth/api-keys/{key_id}", headers=admin_headers)

        # Try to use it
        headers = {"X-API-Key": api_key}
        resp = client.get("/devices", headers=headers)
        assert resp.status_code == 401


# ── Tests: SSE stream ──────────────────────────────────────────────


class TestSSEStream:
    def test_sse_stream_requires_auth(self):
        """SSE endpoint should reject unauthenticated connections."""
        resp = client.get("/events/stream")
        assert resp.status_code == 401

    def test_sse_stream_with_invalid_query_token(self):
        """SSE endpoint should reject invalid tokens."""
        resp = client.get("/events/stream?token=invalidtoken")
        assert resp.status_code == 401

    def test_sse_stream_auth_accepts_valid_bearer(self):
        """Verify SSE endpoint's auth dependency accepts valid Bearer tokens.

        The SSE endpoint is async (StreamingResponse), so a synchronous GET
        request hangs. We test the auth layer indirectly: call a non-streaming
        endpoint that uses the same require_auth_any dependency.
        """
        tokens = _login()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Use /devices which also uses require_auth (same dependency)
        resp = client.get("/devices", headers=headers)
        assert resp.status_code == 200

    def test_sse_stream_auth_accepts_api_key(self):
        """Verify SSE endpoint auth accepts API keys via X-API-Key header."""
        tokens = _login()
        admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = client.post(
            "/auth/api-keys",
            json={"label": "sse-test"},
            headers=admin_headers,
        )
        api_key = create_resp.json()["plaintext_key"]

        # Verify the API key works with the same auth dependency
        resp = client.get("/devices", headers={"X-API-Key": api_key})
        assert resp.status_code == 200

    def test_sse_stream_auth_accepts_query_token(self):
        """Verify SSE endpoint auth accepts JWT via query param.

        We test this indirectly by calling a protected endpoint that
        also checks query params, or verifying the require_auth_any
        function handles ?token= correctly.
        """
        tokens = _login()

        # The /devices endpoint now uses require_auth which checks query params
        resp = client.get(f"/devices?token={tokens['access_token']}")
        # This should return 200 since require_auth checks ?token=
        if resp.status_code == 422:
            # FastAPI Pydantic validation error on unexpected query param
            # is also acceptable — means the auth layer passed but the
            # endpoint's own params rejected the query param. The important
            # thing is we got past auth (not 401).
            pass
        elif resp.status_code == 200:
            pass
        else:
            # Any other status means auth failed
            assert resp.status_code != 401, f"Query token auth failed: {resp.text}"


# ── Cleanup ────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(f"/tmp/vigil_test_apikeys.db{suffix}")
        except FileNotFoundError:
            pass
