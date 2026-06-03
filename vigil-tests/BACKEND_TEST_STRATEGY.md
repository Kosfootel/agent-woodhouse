# Vigil Dashboard - Backend Test Strategy

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Target:** 80%+ code coverage

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Pyramid Distribution](#2-test-pyramid-distribution)
3. [Test Architecture](#3-test-architecture)
4. [Mocking Strategy](#4-mocking-strategy)
5. [Test Data Fixtures](#5-test-data-fixtures)
6. [Coverage Targets](#6-coverage-targets)
7. [Test Execution](#7-test-execution)
8. [CI/CD Integration](#8-cicd-integration)

---

## 1. Overview

This test strategy defines the approach for comprehensive backend testing of the Vigil Dashboard API. The test suite covers:

- **Device Management** (FR-001 to FR-005)
- **Security Scanning & Logging** (FR-006, FR-010, NFR-009)
- **Setup & Configuration** (FR-020 to FR-024)
- **Alert Management** (FR-007)
- **Authentication & Authorization** (NFR-006, NFR-014)
- **Rate Limiting** (NFR-002)

### Testing Principles

1. **Shift Left**: Catch bugs early with comprehensive unit and integration tests
2. **Test Behavior, Not Implementation**: Tests verify API contracts, not internal details
3. **Fast Feedback**: Tests run in under 60 seconds locally
4. **Deterministic**: Tests produce consistent results (no flaky tests)
5. **Isolated**: Tests don't depend on each other

---

## 2. Test Pyramid Distribution

```
                    /\
                   /  \
                  / E2E \         5%  (3-5 tests)
                 /--------\
                /          \
               / Integration \   25%  (20-30 tests)
              /--------------\
             /                \
            /     Unit Tests    \  70%  (50-60 tests)
           /____________________\
```

### Distribution by Type

| Test Type | Percentage | Count | Purpose |
|-----------|------------|-------|---------|
| **Unit Tests** | 70% | ~60 | Test individual functions, validators, models |
| **Integration Tests** | 25% | ~25 | Test API endpoints with test database |
| **E2E Tests** | 5% | ~5 | Critical user journey tests |

### Distribution by Component

| Component | Unit | Integration | E2E | Total |
|-----------|------|-------------|-----|-------|
| Devices | 15 | 8 | 2 | 25 |
| Security | 12 | 6 | 1 | 19 |
| Setup | 10 | 5 | 1 | 16 |
| Alerts | 10 | 4 | 1 | 15 |
| Auth | 8 | 4 | 0 | 12 |
| Rate Limiting | 5 | 3 | 0 | 8 |
| **Total** | **60** | **30** | **5** | **95** |

---

## 3. Test Architecture

### File Structure

```
BACKEND_TEST_SUITE/
├── conftest.py              # Shared fixtures and configuration
├── test_devices.py          # Device API tests (25 tests)
├── test_security.py         # Security scanning tests (19 tests)
├── test_setup.py            # Setup wizard tests (16 tests)
├── test_alerts.py           # Alert API tests (15 tests)
├── test_auth.py             # Authentication tests (12 tests)
└── test_rate_limiting.py    # Rate limiting tests (8 tests)

BACKEND_TEST_FIXTURES/
├── devices.json             # Sample device data
├── alerts.json              # Sample alert data
├── scan_results.json        # Sample security scan results
├── agents.json              # Sample agent data
└── events.json              # Sample event data
```

### Technology Stack

| Tool | Purpose | Version |
|------|---------|---------|
| **pytest** | Test framework | ^8.0 |
| **pytest-asyncio** | Async test support | ^0.23 |
| **pytest-cov** | Coverage reporting | ^5.0 |
| **httpx** | Async HTTP client | ^0.27 |
| **FastAPI TestClient** | Sync test client | Built-in |
| **factory-boy** | Test data factories | ^3.3 |
| **faker** | Fake data generation | ^25.0 |
| **freezegun** | Time mocking | ^1.5 |
| **aiosqlite** | In-memory SQLite | ^0.20 |

---

## 4. Mocking Strategy

### What to Mock

| Component | Mock Strategy | Rationale |
|-----------|--------------|-----------|
| **Database** | Use in-memory SQLite | Fast, isolated, no Docker needed |
| **Email/SMTP** | Mock with `unittest.mock` | Avoid external network calls |
| **External APIs** | Mock with `responses`/`respx` | Router discovery, etc. |
| **File System** | Use `tmp_path` fixture | Isolated file operations |
| **Time** | Use `freezegun` | Deterministic time-based tests |
| **Random Values** | Use seeded RNG | Reproducible tests |

### What NOT to Mock

- Pydantic model validation (test the real thing)
- SQLAlchemy queries (use test database)
- FastAPI dependency injection (test the real flow)
- JWT encoding/decoding (use test secrets)

### Mock Examples

```python
# Database mocking - use test fixture
@pytest.fixture
def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Create tables, yield session

# External API mocking
@pytest.fixture
def mock_router_discovery():
    with respx.mock:
        respx.post("http://192.168.1.1/upnp/...").mock(...)
        yield

# Email mocking
@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP") as mock:
        yield mock
```

---

## 5. Test Data Fixtures

### Fixture Hierarchy

```
conftest.py
├── app (FastAPI instance)
├── client (TestClient)
├── async_client (AsyncClient)
├── db_session (AsyncSession)
├── test_user (User model)
├── auth_token (JWT token)
├── authenticated_client (Client with auth header)
├── sample_device (Device model)
├── sample_alert (Alert model)
├── sample_agent (Agent model)
└── factories (factory_boy factories)
```

### JSON Fixture Files

#### devices.json
- 10 sample devices covering all device types
- Various containment statuses (observing, blocked, trusted, quarantined)
- Edge cases: unknown vendor, missing hostname, special characters

#### alerts.json
- 8 sample alerts covering all severity levels
- Mix of acknowledged and unacknowledged
- Related events for testing joins

#### scan_results.json
- 5 security scan results
- Various threat levels and pattern matches
- Injection attempts and benign prompts

#### agents.json
- 4 sample agents in different states
- Online, offline, error states
- Various trust levels

### Factory Pattern

```python
class DeviceFactory(factory.Factory):
    class Meta:
        model = Device
    
    mac = factory.Sequence(lambda n: f"AA:BB:CC:DD:EE:{n:02X}")
    ip = factory.Faker("ipv4", network="192.168.1.0/24")
    hostname = factory.Faker("hostname")
    trust_score = factory.Faker("pyfloat", min_value=0, max_value=100)
    containment_status = factory.Iterator(["observing", "blocked", "trusted"])
```

---

## 6. Coverage Targets

### Overall Targets

| Metric | Target | Minimum |
|--------|--------|---------|
| **Line Coverage** | 85% | 80% |
| **Branch Coverage** | 75% | 70% |
| **Function Coverage** | 90% | 85% |

### By Component

| Component | Line | Branch | Priority |
|-----------|------|--------|----------|
| Authentication | 90% | 85% | P0 |
| Device Management | 85% | 80% | P0 |
| Security Scanning | 85% | 80% | P0 |
| Alert Management | 85% | 75% | P0 |
| Setup & Config | 80% | 70% | P1 |
| Rate Limiting | 90% | 85% | P0 |

### Exclusions

The following are excluded from coverage:
- Database migration files
- Auto-generated code (OpenAPI spec generation)
- Debug/development only code blocks
- Type hints and docstrings

---

## 7. Test Execution

### Running Tests

```bash
# Run all tests
pytest BACKEND_TEST_SUITE/

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
pytest BACKEND_TEST_SUITE/test_devices.py -v

# Run specific test
pytest BACKEND_TEST_SUITE/test_devices.py::TestDeviceAPI::test_get_device

# Run async tests
pytest -m asyncio --asyncio-mode=auto

# Run with verbose output
pytest -vv --tb=short

# Run failed tests only
pytest --lf

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Markers

```python
# Test categories
@pytest.mark.unit           # Fast unit tests
@pytest.mark.integration    # Integration tests with DB
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.slow          # Tests > 1 second
@pytest.mark.security      # Security-focused tests
@pytest.mark.flaky         # Known flaky tests (to be fixed)
```

---

## 8. CI/CD Integration

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest BACKEND_TEST_SUITE/ -x -q
        language: system
        pass_filenames: false
        always_run: true
```

### GitHub Actions Workflow

```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app --cov-fail-under=80
      - uses: codecov/codecov-action@v4
```

### Quality Gates

| Gate | Condition |
|------|-----------|
| **Unit Tests** | Must pass |
| **Coverage** | ≥ 80% |
| **Linting** | ruff, mypy clean |
| **Security Scan** | bandit, safety clean |

---

## Appendix A: Test Case Template

```python
def test_feature_description(self, fixtures):
    """
    Test that [feature] handles [scenario] correctly.
    
    Related Requirements:
        - FR-XXX: Requirement name
        - NFR-XXX: Non-functional requirement
    
    Test Steps:
        1. Setup: [preconditions]
        2. Action: [what to test]
        3. Assert: [expected outcome]
    
    Edge Cases:
        - [edge case 1]
        - [edge case 2]
    """
    pass
```

## Appendix B: Common Test Patterns

### Pattern: API CRUD Test

```python
class TestDeviceCRUD:
    """Standard CRUD pattern for API endpoints."""
    
    async def test_create_device(self, client, auth_token):
        """POST /devices - Create a new device."""
        response = await client.post(
            "/devices",
            json={"mac": "AA:BB:CC:DD:EE:FF", ...},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        assert response.json()["mac"] == "AA:BB:CC:DD:EE:FF"
    
    async def test_read_device(self, client, sample_device, auth_token):
        """GET /devices/{id} - Read existing device."""
        response = await client.get(
            f"/devices/{sample_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["id"] == sample_device.id
    
    async def test_update_device(self, client, sample_device, auth_token):
        """PATCH /devices/{id} - Update device."""
        response = await client.patch(
            f"/devices/{sample_device.id}",
            json={"nickname": "Updated Name"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["nickname"] == "Updated Name"
    
    async def test_delete_device(self, client, sample_device, auth_token):
        """DELETE /devices/{id} - Delete device."""
        response = await client.delete(
            f"/devices/{sample_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 204
        
        # Verify deletion
        response = await client.get(f"/devices/{sample_device.id}")
        assert response.status_code == 404
```

### Pattern: Security Test

```python
class TestSecurityControls:
    """Security-focused test patterns."""
    
    async def test_sql_injection_prevention(self, client):
        """Verify SQL injection is prevented (NFR-009)."""
        malicious_input = "'; DROP TABLE devices; --"
        response = await client.get(f"/devices?search={malicious_input}")
        # Should return 400 or sanitize, never execute SQL
        assert response.status_code in [200, 400]
        # Verify table still exists by making a valid request
    
    async def test_xss_prevention(self, client):
        """Verify XSS payloads are sanitized (NFR-009)."""
        xss_payload = "<script>alert('xss')</script>"
        response = await client.post(
            "/devices",
            json={"nickname": xss_payload}
        )
        # Response should not contain unescaped script tag
        assert "<script>" not in response.text
```

---

*Document generated for Vigil Dashboard Backend Test Suite*
