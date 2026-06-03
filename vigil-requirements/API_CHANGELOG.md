# Vigil Dashboard API Changelog

## Version 2.0.0 (Redesigned API)

This document tracks changes from the current Vigil API (v1.x) to the redesigned API (v2.0.0).

---

## Breaking Changes

### Base URL Change

| Old | New |
|-----|-----|
| `/api/*` | `/api/v2/*` |

**Migration:** Update all client requests to include the `/v2` path segment.

```javascript
// Old
const API_BASE = 'http://localhost:8000/api';

// New
const API_BASE = 'http://localhost:8000/api/v2';
```

### Authentication Requirement

| Endpoint Group | Old | New |
|----------------|-----|-----|
| Health | No auth | No auth |
| All others | No auth | **Bearer token required** |

**Migration:** Implement JWT token authentication for all protected endpoints.

```javascript
// Add Authorization header
headers: {
  'Authorization': 'Bearer <token>',
  'X-CSRF-Token': '<csrf-token>'  // For state-changing operations
}
```

### Device Response Format Changes

#### `GET /devices` and `GET /devices/{id}`

**Old Response:**
```json
{
  "devices": [...],
  "total_count": 10
}
```

**New Response:**
```json
{
  "devices": [...],
  "total_count": 10,
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_more": false
  }
}
```

**Breaking Changes:**
- Device `id` field now required (was sometimes missing)
- `trust_score` changed from `0-100` integer to `0-100.0` float
- `containment_status` enum values changed:
  - Old: `["active", "blocked", "quarantined"]`
  - New: `["observing", "blocked", "trusted", "quarantined"]`
- `online` field added (was previously calculated client-side)

### Alert Response Format Changes

#### `GET /alerts`

**Old Response:**
```json
{
  "count": 10,
  "alerts": [...]
}
```

**New Response:**
```json
{
  "count": 10,
  "alerts": [...],
  "new_count": 5,
  "acknowledged_count": 5
}
```

**Breaking Changes:**
- `message` field renamed to `narrative` (to distinguish from `title`)
- `title` field added (shortened version)
- `alert_type` field renamed from `type` (to avoid TypeScript conflicts)
- `timestamp` field format standardized to ISO 8601

### Event Response Format Changes

#### `GET /events`

**Old Response:**
```json
{
  "count": 10,
  "events": [...]
}
```

**New Response:**
```json
{
  "count": 10,
  "events": [...],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_more": false
  }
}
```

**Breaking Changes:**
- `type` field renamed to `event_type` (consistency)
- `timestamp` field standardized to ISO 8601
- `details` field changed from string to object

### Security Event Endpoint Consolidation

**Old Endpoints:**
- `GET /security/events`
- `GET /security/get-security-events` (duplicate)

**New Endpoint:**
- `GET /security/events` (consolidated)

**Breaking Changes:**
- `id` field now prefixed: `sec_` for security events, `evt_` for regular events
- Response structure unified with camelCase keys

### Removed Endpoints

| Old Endpoint | Replacement | Reason |
|--------------|-------------|--------|
| `GET /security/get-security-events` | `GET /security/events` | Duplicate functionality |
| `POST /setup/session` (duplicate) | `POST /setup/session` | Consolidated to one endpoint |
| `GET /agents/{id}/details` | `GET /agents/{id}` | Simplified endpoint naming |

---

## New Endpoints

### Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/devices/{id}/trust` | Mark device as trusted |
| `PATCH` | `/devices/{id}` | Partial device update (replaces PUT) |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts/{id}` | Get single alert details |

### Setup

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/setup/router-status` | Check router configuration status |
| `DELETE` | `/setup/router-credentials` | Remove stored credentials |

---

## Deprecated Endpoints

These endpoints will be removed in v3.0.0 (6 months notice).

| Endpoint | Replacement | Deprecation Date |
|----------|-------------|------------------|
| `PUT /devices/{id}` | `PATCH /devices/{id}` | 2026-08-01 |
| `GET /security/get-security-events` | `GET /security/events` | 2026-08-01 |
| `POST /alerts/acknowledge` | `POST /alerts/{id}/acknowledge` | 2026-08-01 |

---

## Non-Breaking Changes

### Added Query Parameters

#### `GET /devices`

| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | integer | Pagination offset |

#### `GET /alerts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | integer | Pagination offset |
| `acknowledged` | boolean | Filter by status |

#### `GET /events`

| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | integer | Pagination offset |
| `hours` | integer | Time window filter |

### Added Response Fields

#### Device Response

| Field | Type | Description |
|-------|------|-------------|
| `first_seen` | datetime | When device was first discovered |
| `discovery_method` | string | How the device was discovered |

#### Alert Response

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Short alert title (first 50 chars) |

---

## Migration Guide

### Step 1: Update Base URL

Update all API client configurations:

```javascript
// api.js - Before
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.50.30:8000/api';

// api.js - After
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.50.30:8000/api/v2';
```

### Step 2: Add Authentication

Implement JWT token handling:

```javascript
// api.js - Add interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vigil_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Step 3: Update Device Status Handling

```javascript
// Before
const statusMap = {
  'active': 'Active',
  'blocked': 'Blocked',
  'quarantined': 'Quarantined'
};

// After
const statusMap = {
  'observing': 'Observing',
  'blocked': 'Blocked',
  'trusted': 'Trusted',
  'quarantined': 'Quarantined'
};
```

### Step 4: Update Alert Handling

```javascript
// Before
const alertTitle = alert.message.substring(0, 50) + '...';

// After
const alertTitle = alert.title; // Server now provides this
const fullMessage = alert.narrative;
```

### Step 5: Update Event Handling

```javascript
// Before
const eventType = event.type;
const timestamp = new Date(event.timestamp).toLocaleString();

// After
const eventType = event.event_type; // Field renamed
const timestamp = event.timestamp; // Already ISO 8601 format
```

### Step 6: Handle Prefixed IDs

```javascript
// Before
const eventId = event.id; // 123

// After
const eventId = event.id; // "sec_123" or "evt_123"
// Strip prefix for display if needed
const displayId = event.id.replace(/^(sec_|evt_)/, '');
```

### Step 7: Add Pagination Handling

```javascript
// Before
const hasMore = false; // Not available

// After
const hasMore = response.data.pagination?.has_more ?? false;
```

### Step 8: Update Error Handling

```javascript
// Before
catch (error) {
  console.error(error.message);
}

// After
catch (error) {
  const errorData = error.response?.data;
  console.error(errorData?.detail || error.message);
  console.error(errorData?.error_code); // New field
}
```

---

## Backward Compatibility

### Sunset Schedule

| Version | Status | End of Support |
|---------|--------|----------------|
| v1.x | Deprecated | 2026-11-01 |
| v2.0 | Current | 2027-11-01 |

### Compatibility Layer

A compatibility shim is available at `/api/v1-compat/` that translates:
- Old endpoint paths to new
- Old response formats to new
- Removes new required fields

**Usage:**
```javascript
// Temporary compatibility mode
const API_BASE_URL = 'http://localhost:8000/api/v1-compat';
```

**Warning:** Compatibility layer adds ~50ms latency per request and may not support all new features.

---

## Schema Validation

OpenAPI 3.1 specification now enforces:

### Device MAC Address
```yaml
pattern: "^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
```

### IP Addresses
```yaml
format: ipv4
```

### Timestamps
```yaml
format: date-time
# Example: 2024-01-15T10:30:00Z
```

### Severity Levels
```yaml
enum: [critical, high, medium, low]
```

---

## Client SDK Updates

### JavaScript/TypeScript

```bash
npm install @vigil/sdk@^2.0.0
```

**Breaking changes in SDK:**
- All methods now require authentication
- Response types updated to match new schema
- Pagination is now automatic with `autoPaginate` option

### Python

```bash
pip install vigil-sdk>=2.0.0
```

**Breaking changes:**
- Client initialization now requires token
- Response models use Pydantic v2

---

## Testing Migration

### Updated Test Data

```json
// test/fixtures/device.json
{
  "id": 1,
  "mac": "AA:BB:CC:DD:EE:FF",
  "ip": "192.168.1.100",
  "hostname": "Test-Device",
  "nickname": null,
  "vendor": "Test Vendor",
  "device_type": "laptop",
  "trust_score": 75.5,
  "containment_status": "observing",
  "online": true,
  "last_seen": "2024-01-15T10:30:00Z",
  "first_seen": "2024-01-10T08:00:00Z"
}
```

### Updated Test Headers

```javascript
const headers = {
  'Authorization': 'Bearer test-token',
  'X-CSRF-Token': 'test-csrf-token',
  'Content-Type': 'application/json'
};
```

---

## API Version Discovery

### Check Version

```http
GET / HTTP/1.1
Host: localhost:8000
```

Response:
```json
{
  "service": "Vigil Security",
  "version": "2.0.0",
  "status": "operational"
}
```

### Version Header

All responses include API version:

```http
X-API-Version: 2.0.0
```

---

## Security Improvements

### Authentication Required

All endpoints except health checks now require authentication.

### CSRF Protection

State-changing operations require CSRF token:

```http
POST /api/v2/devices/1/block HTTP/1.1
X-CSRF-Token: <token-from-cookie>
Authorization: Bearer <jwt-token>
```

### Rate Limiting

Default limits:
- 100 requests per minute per IP
- 1000 requests per hour per user

Headers included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315800
```

---

## Questions?

For migration support:
- Documentation: https://docs.vigil.local/api/v2
- Migration guide: https://docs.vigil.local/migration/v2
- Support: api-support@vigil.local

---

*Last updated: 2026-05-26*
