# Vigil Dashboard - Integration Test Strategy

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Status:** Draft

---

## 1. Executive Summary

This document outlines the integration testing strategy for the Vigil Dashboard system. Integration tests verify end-to-end workflows across the entire application stack, ensuring that all components (frontend, backend, database, cache, and external services) work together correctly.

### Test Scope
- **In Scope:** API-to-database flows, frontend-to-backend interactions, service-to-service communication
- **Out of Scope:** Unit tests (component-level), E2E browser automation (separate suite)
- **Test Environment:** Docker Compose with real PostgreSQL and Redis services

---

## 2. Test Architecture

### 2.1 Test Environment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION TEST ENVIRONMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        TEST RUNNER (pytest)                            │  │
│  │  • Async HTTP client (httpx)                                          │  │
│  │  • Database assertions (SQLAlchemy)                                   │  │
│  │  • Test fixtures and cleanup                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐│
│  │                        DOCKER COMPOSE NETWORK                          ││
│  │                                                                        ││
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       ││
│  │  │ Frontend │────│ Backend  │────│PostgreSQL│────│  Redis   │       ││
│  │  │ (React)  │    │(FastAPI) │    │   (16)   │    │   (7)    │       ││
│  │  └──────────┘    └────┬─────┘    └──────────┘    └──────────┘       ││
│  │                       │                                              ││
│  │              ┌────────┴────────┐                                    ││
│  │              │                 │                                    ││
│  │         ┌────┴────┐       ┌────┴────┐                              ││
│  │         │Mock SMTP│       │Mock Router│                             ││
│  │         └─────────┘       └──────────┘                              ││
│  │                                                                        ││
│  └────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Test Data Flow

```
Test Case Execution Flow:

1. SETUP
   ├── Create test database (isolated)
   ├── Seed test data (fixtures)
   └── Start fresh service containers

2. EXECUTE
   ├── API requests via HTTP client
   ├── Database state verification
   └── Cross-service assertions

3. VERIFY
   ├── Response assertions (status, body)
   ├── Database assertions (row counts, values)
   └── Event/log verification

4. TEARDOWN
   ├── Clean up test data
   ├── Rollback transactions
   └── Remove temporary resources
```

---

## 3. Test Organization

### 3.1 Test Suite Structure

```
INTEGRATION_TEST_SUITE/
├── docker-compose.test.yml          # Full stack test environment
├── Dockerfile.test-runner           # Test runner container
├── conftest.py                      # Shared fixtures and configuration
├── __init__.py                      # Python package marker
│
├── test_device_lifecycle.py         # Device CRUD operations
├── test_security_event_flow.py      # Alert → notification pipeline
├── test_setup_wizard.py             # Multi-step setup process
├── test_scan_and_report.py          # Discovery → dashboard flow
├── test_auth_flow.py                # Login → action → logout
│
└── utils/
    ├── __init__.py
    ├── api_client.py                # HTTP client utilities
    ├── db_helpers.py                # Database assertion helpers
    └── fixtures.py                  # Shared test data
```

### 3.2 Test Categories

| Category | Description | Files |
|----------|-------------|-------|
| **CRUD Operations** | Create, read, update, delete flows | `test_device_lifecycle.py` |
| **Event Processing** | Security event → alert → notification | `test_security_event_flow.py` |
| **Workflow** | Multi-step business processes | `test_setup_wizard.py` |
| **Data Flow** | Cross-component data propagation | `test_scan_and_report.py` |
| **Authentication** | Security and session management | `test_auth_flow.py` |

---

## 4. Data Isolation Strategy

### 4.1 Database Isolation

**Transaction Rollback Pattern:**
```python
@pytest.fixture(scope="function")
async def db_transaction():
    """Each test runs in a transaction that's rolled back."""
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Always rollback
```

**Unique Data Generation:**
```python
# Each test gets unique identifiers to prevent collisions
test_device = {
    "mac": f"AA:BB:CC:{uuid.uuid4().hex[:6].upper()}",
    "ip": f"192.168.50.{random.randint(100, 200)}",
    "name": f"test-device-{uuid.uuid4().hex[:8]}"
}
```

### 4.2 Service State Isolation

| Resource | Isolation Method |
|----------|-----------------|
| PostgreSQL | Unique database per test run + transaction rollback |
| Redis | Key prefixing + selective cleanup |
| Files | Temp directories + cleanup |
| Queues | Test-specific queue names |

### 4.3 Cleanup Strategy

**Automatic Cleanup (Preferred):**
```python
@pytest.fixture
async def created_device(api_client):
    device = await create_device(api_client)
    yield device
    # Cleanup runs after test
    await api_client.delete(f"/devices/{device['id']}")
```

**Test Suite Cleanup (Fallback):**
```python
def pytest_sessionfinish(session, exitstatus):
    """Clean up any remaining test data after suite."""
    cleanup_test_data()
```

---

## 5. Test Execution

### 5.1 Running Tests

```bash
# Run all integration tests
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run specific test file
docker-compose exec test-runner pytest /tests/test_device_lifecycle.py -v

# Run with coverage
docker-compose exec test-runner pytest /tests --cov=/tests --cov-report=html

# Run with markers
docker-compose exec test-runner pytest /tests -m "slow" -v
```

### 5.2 Test Markers

```python
# conftest.py
pytest_plugins = ['pytest_asyncio']

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "auth: marks tests that require authentication")
    config.addinivalue_line("markers", "db: marks tests that modify database")
    config.addinivalue_line("markers", "external: marks tests that use external services")
```

### 5.3 Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
docker-compose exec test-runner pytest /tests -n auto --dist=loadfile
```

---

## 6. CI/CD Integration

### 6.1 GitHub Actions Workflow

```yaml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  integration-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v2
      
      - name: Run integration tests
        run: |
          docker-compose -f INTEGRATION_TEST_SUITE/docker-compose.test.yml \
            up --build --abort-on-container-exit
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: |
            test-results/
            coverage_html/
```

### 6.2 Test Gates

| Gate | Condition |
|------|-----------|
| **Unit Tests** | Pass before integration tests |
| **Integration Tests** | Must pass before merge |
| **Coverage** | Minimum 70% integration coverage |
| **Performance** | API response < 2s for 95th percentile |

### 6.3 Test Reports

- **JUnit XML:** `test-results/junit.xml`
- **HTML Report:** `test-results/report.html`
- **Coverage:** `test-results/coverage_html/index.html`

---

## 7. Mock External Services

### 7.1 Mock SMTP Server

```yaml
mock-smtp:
  image: reachfive/fake-smtp-server:latest
  ports:
    - "1025:1025"  # SMTP port
    - "1080:1080"  # Web UI
```

**Verification:**
```python
async def test_email_sent():
    await trigger_alert()
    emails = await http_client.get("http://mock-smtp:1080/api/emails")
    assert len(emails.json()) > 0
```

### 7.2 Mock Router

```python
# FastAPI mock for UPnP router
@app.get("/upnp/control/DHCPTable")
async def dhcp_table():
    return {
        "devices": [
            {"mac": "AA:BB:CC:DD:EE:01", "ip": "192.168.50.100"},
            {"mac": "AA:BB:CC:DD:EE:02", "ip": "192.168.50.101"},
        ]
    }
```

---

## 8. Performance Considerations

### 8.1 Test Timing Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Single API call | < 200ms | < 1s |
| Database query | < 50ms | < 200ms |
| Full test case | < 5s | < 30s |
| Test suite (all) | < 5 min | < 10 min |

### 8.2 Resource Limits

```yaml
# docker-compose.test.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

---

## 9. Debugging Failed Tests

### 9.1 Logs Collection

```yaml
# docker-compose.test.yml
volumes:
  - test_logs:/app/logs
  - test_results:/test-results
```

### 9.2 Debug Mode

```bash
# Keep containers running after tests
docker-compose -f docker-compose.test.yml up -d

# Run tests manually
docker-compose exec test-runner bash
pytest /tests/test_device_lifecycle.py::test_device_discovery -v --pdb

# Check service logs
docker-compose logs backend
docker-compose logs postgres
```

### 9.3 Database Inspection

```bash
# Connect to test database
docker-compose exec postgres psql -U vigil_test -d vigil_test

# Query test data
SELECT * FROM devices ORDER BY created_at DESC LIMIT 10;
SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;
```

---

## 10. Test Maintenance

### 10.1 Adding New Tests

1. Create test file in `INTEGRATION_TEST_SUITE/`
2. Follow naming convention: `test_<feature>.py`
3. Use existing fixtures from `conftest.py`
4. Add cleanup in fixture teardown
5. Document in this strategy doc if complex

### 10.2 Updating Tests

- **API Changes:** Update request/response schemas
- **Database Changes:** Update fixtures and assertions
- **Dependencies:** Update `docker-compose.test.yml`

### 10.3 Test Data Management

| Data Type | Source | Refresh Frequency |
|-----------|--------|-------------------|
| Static fixtures | `fixtures/` | As needed |
| Generated data | `faker` library | Per test run |
| Reference data | Database seed | Test suite setup |

---

## 11. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky tests | High | Unique data, proper cleanup, wait conditions |
| Slow tests | Medium | Parallel execution, selective markers |
| Resource exhaustion | Medium | Container limits, cleanup guarantees |
| External service failures | Low | Mocks, graceful skip |
| Database state leaks | High | Transaction rollback, unique IDs |

---

## Appendix A: Test Data Reference

### Standard Test Devices

```python
STANDARD_DEVICES = [
    {
        "mac": "AA:BB:CC:DD:EE:01",
        "ip": "192.168.50.100",
        "hostname": "Test-Phone",
        "device_type": "phone",
        "vendor": "Apple"
    },
    {
        "mac": "AA:BB:CC:DD:EE:02",
        "ip": "192.168.50.101",
        "hostname": "Test-Laptop",
        "device_type": "laptop",
        "vendor": "Dell"
    },
]
```

### Test Credentials

```python
TEST_USERS = [
    {"username": "test_admin", "password": "test_admin_pass_123", "role": "admin"},
    {"username": "test_user", "password": "test_user_pass_123", "role": "user"},
    {"username": "test_viewer", "password": "test_viewer_pass_123", "role": "viewer"},
]
```

---

*End of Integration Test Strategy Document*
