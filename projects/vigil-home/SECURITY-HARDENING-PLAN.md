# Vigil Home — Security Hardening Plan

**Prepared:** 2026-05-09  
**Based on:** Code Review Coronation Brief + Source Analysis (main.py, detection.py, models.py, database.py, email_notifier.py, api.ts)  
**Target:** Production-ready IoT threat detection appliance

---

## Table of Contents

1. [Critical Fixes Ranked by Severity](#1-critical-fixes-ranked-by-severity)
2. [Authentication Architecture](#2-authentication-architecture)
3. [Secrets Management Strategy](#3-secrets-management-strategy)
4. [Production Readiness Checklist](#4-production-readiness-checklist)
5. [Implementation Order](#5-implementation-order)
6. [Estimated Effort per Item](#6-estimated-effort-per-item)
7. [Appendix: Risk Register](#7-appendix-risk-register)

---

## 1. Critical Fixes Ranked by Severity

| Rank | Issue | Severity | Location | Rationale |
|------|-------|----------|----------|-----------|
| **1** | **No authentication on any API endpoint** | 🔴 Critical | All `main.py` routes | Any device on the network can read all alerts, devices, events, and inject arbitrary events. No confidentiality, no integrity, no access control. Single biggest risk. |
| **2** | **Simulated `Math.random()` trust trend** | 🔴 Critical | `dashboard/src/lib/api.ts:fetchTrustTrend` | The analytics page shows fabricated data. A user making security decisions based on this chart has false confidence. Undermines the entire trust-model value proposition. |
| **3** | **AI state (anomaly detectors, trust models) in-memory only** | 🔴 High | `main.py` lines 28-29, `detection.py` lines 20-21 | Server restart loses all historical AI state. Trust scores are rebuilt from scratch, anomaly baselines are reset. Attackers can exploit the "cold start" window. |
| **4** | **Alert acknowledge not persisted** | 🔴 High | `dashboard/src/app/alerts/page.tsx` (client-side React `Set` only) | Acknowledge is purely cosmetic. Refresh wipes it. No PATCH endpoint exists on the backend. Operators cannot track which alerts have been triaged. |
| **5** | **Synchronous SMTP in request path** | 🟡 High | `main.py` POST `/events` calls `send_alert_email()` synchronously | SMTP connection adds 1-5s latency to the API response. Under Suricata flood, this serialises requests and can exhaust uvicorn workers, creating a DoS vector. |

---

## 2. Authentication Architecture

### 2.1 Design Philosophy

Vigil Home is a consumer/SMB appliance running on a local network. The auth system must be:

- **Simple to set up** — No OAuth provider dependency, no external identity server
- **Secure by default** — All endpoints locked; opt-in only for trusted networks
- **Familiar UX** — Username/password login, session token, "remember me"
- **Self-contained** — No external database for users; single admin account stored in SQLite
- **Upgradeable** — Architecture supports API keys for future headless/integration use

### 2.2 Auth Flow

```
┌──────────────┐          POST /auth/login          ┌──────────────┐
│              │  ────────────────────────────────►  │              │
│   Dashboard   │     { username, password }          │   Backend    │
│  (Next.js)   │                                     │  (FastAPI)   │
│              │  ◄────────────────────────────────  │              │
│              │     { access_token, refresh_token,   │              │
│              │       expires_in, user }             │              │
└──────┬───────┘                                     └──────┬───────┘
       │                                                    │
       │  Subsequent requests:                              │
       │  Authorization: Bearer <access_token>              │
       │──────────────────────────────────────────────────►│
       │                                                    │
       │  When token expires (401):                         │
       │  POST /auth/refresh { refresh_token }              │
       │──────────────────────────────────────────────────►│
       │                                                    │
       │  On logout:                                        │
       │  POST /auth/logout { refresh_token }               │
       │──────────────────────────────────────────────────►│
```

### 2.3 Token Design

| Attribute | Access Token | Refresh Token |
|-----------|-------------|---------------|
| Type | JWT | Opaque random string |
| Storage | `Authorization: Bearer` header | HTTP-only secure cookie + request body |
| Lifetime | 1 hour (configurable) | 30 days (configurable) |
| Rotation | On refresh | Rotated on each use (family-refresh pattern) |
| Revocation | Not needed (short-lived) | Server-side revocation list in DB |
| Payload | `{ sub: user_id, role: "admin", iat, exp }` | N/A (server lookup) |

### 2.4 Endpoint Protection Matrix

| Endpoint | Method | Auth Required | Rate Limit | Notes |
|----------|--------|-------------|------------|-------|
| `/auth/login` | POST | No | 5/min/IP | Login throttle on username |
| `/auth/refresh` | POST | Refresh token | 10/min/IP | |
| `/auth/logout` | POST | Yes | 10/min/IP | Revokes refresh token |
| `/devices` | GET | Yes | 30/min | |
| `/devices/{id}` | GET | Yes | 60/min | |
| `/devices` | POST | Yes | 10/min | Write endpoint — tight rate limit |
| `/events` | POST | Yes | 20/min | Write endpoint |
| `/events` | GET | Yes | 30/min | |
| `/alerts` | GET | Yes | 30/min | |
| `/alerts/{id}` | GET | Yes | 60/min | |
| `/alerts/{id}/acknowledge` | PATCH | Yes | 20/min | **New endpoint** |
| `/classify/{mac}` | GET | Yes | 30/min | |
| `/email/*` | GET/POST | Yes | 5/min | Email operations |
| `/health` | GET | No | 10/min | Read-only, no sensitive data |
| SSE `/events/stream` | — | Yes (token in query/header) | — | Validate on connect |

### 2.5 Implementation Details

**Password:**
- Argon2id for password hashing (via `passlib[bcrypt]` is acceptable, but Argon2id preferred for consumer hardware)
- Single admin account: username and password set via `VIGIL_ADMIN_USERNAME` and `VIGIL_ADMIN_PASSWORD` env vars on first start
- First-start bootstraps the user into the `users` SQLite table
- No registration endpoint — admin is provisioned at deploy time

**JWT:**
- `python-jose` with HS256
- Secret key from `VIGIL_JWT_SECRET` env var (auto-generated if missing, persisted to `/data/.jwt_secret`)
- Token blacklist not needed for access tokens (short-lived), but store revoked refresh tokens in a `refresh_tokens` table

**SSE Authentication:**
- SSE endpoint validates the JWT on connection
- Supports both `Authorization: Bearer` header (EventSource doesn't support custom headers — use token in query param `?token=xxx`)
- **Important:** Token in query string is logged by nginx. Mitigate by:
  1. Using a short-lived JWT (5 min) specifically for SSE
  2. Stripping the token from nginx access logs

**Middleware Implementation:**
```python
# FastAPI dependency
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload
```

**Optional LAN bypass:**
- Some consumer users may want no-auth on LAN. Add `VIGIL_AUTH_DISABLED=true` env var for development/easy-mode, but log a prominent warning on startup.

### 2.6 Frontend Auth Flow

1. Login form at `/login` (no auth → redirected to login)
2. On success, store access token in memory (React state/context) + refresh token in `httpOnly` cookie
3. Axios/fetch interceptor: attach `Authorization: Bearer` to all requests
4. On 401 response: attempt silent refresh, if fails → redirect to `/login`
5. On tab close: refresh token persists in cookie; access token lost (re-obtained via refresh on next page load)
6. Logout: POST `/auth/logout`, clear cookie, clear state, redirect

### 2.7 Required New Backend Endpoints

```python
POST /auth/login        # { username, password } → { access_token, refresh_token, expires_in }
POST /auth/refresh      # { refresh_token } → { access_token, refresh_token, expires_in }
POST /auth/logout       # Revokes refresh token
PATCH /alerts/{id}/acknowledge  # No body, just sets alert.status = "acknowledged"
GET  /trust-trend       # { days: 7 } → [{ date, score }, ...] — replaces Math.random()
GET  /health            # { db: "ok", ai_modules: "ok", last_eve_timestamp: "..." }
```

---

## 3. Secrets Management Strategy

### 3.1 Current State (Good Practices Already Present)

- ✅ SMTP credentials via environment variables (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, etc.)
- ✅ No hardcoded secrets in source code
- ✅ Environment-based configuration throughout

### 3.2 Gaps to Address

| Gap | Risk | Fix |
|-----|------|-----|
| JWT signing key not provisioned | Weak/no JWT auth | `VIGIL_JWT_SECRET` env var; fallback auto-generate & persist to `/data/.jwt_secret` |
| No `.env` file example | Onboarding friction | Ship `.env.example` with all documented env vars |
| Admin password in env var | Visible in `ps aux`, logs | Consider `.env` file or `VIGIL_ADMIN_PASSWORD_FILE` pattern (read from file path) |
| SMTP password in env var | Same issue | Accept `*_FILE` variants: `GMAIL_APP_PASSWORD_FILE` reads from file |
| No encryption at rest | SQLite DB is plaintext | Optional: SQLCipher or encrypt sensitive fields; for consumer appliance, filesystem permissions + full-disk encryption recommended instead |
| `VIGIL_DB_PATH` defaults to `/data/vigil.db` | `/data` may not exist; permissions | Add `os.makedirs` in `init_db()`; validate directory is writable |

### 3.3 Recommendation: Layered Secrets

```
Layer 1: Environment variables (for Docker/k8s)
  VIGIL_ADMIN_PASSWORD=<password>
  GMAIL_APP_PASSWORD=<password>

Layer 2: File-based (for systemd/daemon)
  VIGIL_ADMIN_PASSWORD_FILE=/run/secrets/admin_password
  GMAIL_APP_PASSWORD_FILE=/run/secrets/gmail_password

Layer 3: .env file (for development)
  # Loaded by python-dotenv on startup if file exists
  /etc/vigil/.env  or  /data/.env
```

**Implementation pattern:**
```python
def _get_secret(env_var: str, file_env_var: str = None) -> str:
    """Read a secret from env var, or from a file path in the corresponding _FILE var."""
    value = os.environ.get(env_var)
    if value:
        return value
    file_var = file_env_var or f"{env_var}_FILE"
    path = os.environ.get(file_var)
    if path:
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            pass
    return ""
```

### 3.4 Required Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `VIGIL_ADMIN_USERNAME` | Yes | `admin` | Dashboard login username |
| `VIGIL_ADMIN_PASSWORD` | Yes* | — | Dashboard login password (or `VIGIL_ADMIN_PASSWORD_FILE`) |
| `VIGIL_JWT_SECRET` | No | Auto-generated | JWT signing key (or `VIGIL_JWT_SECRET_FILE`) |
| `VIGIL_DB_PATH` | No | `/data/vigil.db` | SQLite database path |
| `VIGIL_EVE_JSON` | No | `/var/log/suricata/eve.json` | Suricata log path |
| `VIGIL_POLL_INTERVAL` | No | `2.0` | Suricata tail poll interval (seconds) |
| `VIGIL_AUTH_DISABLED` | No | `false` | Disable auth for dev (logs warning) |
| `SMTP_PROVIDER` | No | `gmail` | `gmail`, `icloud`, `m365`, `custom` |
| `GMAIL_USER / GMAIL_APP_PASSWORD` | Conditional | — | Gmail SMTP (or `*_FILE` variants) |
| `VIGIL_ALERT_FROM` | No | `vigil@hockeyops.ai` | Email sender |
| `VIGIL_ALERT_TO` | No | `erik_ross@hockeyops.ai` | Email recipient |
| `VIGIL_HOSTNAME` | No | Hostname | Appliance hostname in email footers |
| `VIGIL_DASHBOARD_URL` | **New** | `http://localhost:3000` | Replaces hardcoded `192.168.50.30` in email templates |

---

## 4. Production Readiness Checklist

### 4.1 Security
- [ ] **P0 — API authentication** implemented (JWT + refresh tokens)
- [ ] **P0 — All existing endpoints** gated behind `require_auth` middleware
- [ ] **P0 — SSE endpoint** authenticated (token in query param or custom header)
- [ ] **P1 — Rate limiting** on all endpoints (slowapi or custom middleware)
- [ ] **P1 — Input validation** on MAC addresses (regex: `^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$`)
- [ ] **P1 — Input validation** on IP addresses (ipaddress module validation)
- [ ] **P1 — Input validation** on hostnames (alphanumeric + hyphens only, length limits)
- [ ] **P1 — CORS middleware** configured for dashboard origin only
- [ ] **P1 — Login rate limiting** (5 attempts/min per IP, account lockout after 10)
- [ ] **P2 — Security headers** (X-Content-Type-Options, X-Frame-Options, CSP)
- [ ] **P2 — File permissions** on `/data/vigil.db` (0600, owned by vigil user)
- [ ] **P2 — `/data` directory** created with secure permissions
- [ ] **P2 — Stack traces** suppressed in production error responses
- [ ] **P3 — eve.json write permissions** restricted (only Suricata daemon + vigil user)

### 4.2 Authentication
- [ ] P0 — JWT issue/verify logic
- [ ] P0 — Login endpoint with Argon2id password verification
- [ ] P0 — Refresh token endpoint with rotation
- [ ] P0 — Logout endpoint (revoke refresh token)
- [ ] P0 — `require_auth` FastAPI dependency
- [ ] P0 — Dashboard login page and auth context
- [ ] P0 — Fetch interceptor for token attachment and 401 handling
- [ ] P0 — SSE auth support (query param or WebSocket upgrade)
- [ ] P1 — Auto-redirect to `/login` on auth failure
- [ ] P1 — Silent token refresh on page load
- [ ] P2 — Session timeout warning modal

### 4.3 Data Integrity
- [ ] **P0 — Real trust trend endpoint** replacing `Math.random()`
- [ ] **P0 — Alert acknowledge persistence** (PATCH endpoint + DB update)
- [ ] **P0 — AI state persistence** (serialize anomaly detectors / trust models to DB)
- [ ] P1 — Database migrations with Alembic
- [ ] P1 — SQLite WAL mode (`PRAGMA journal_mode=WAL`)
- [ ] P1 — Database indexes on `alerts.timestamp`, `events.timestamp`
- [ ] P2 — Database backup/restore script
- [ ] P2 — Health check endpoint

### 4.4 Configuration Management
- [ ] P0 — `.env.example` file with all documented variables
- [ ] P0 — `VIGIL_DASHBOARD_URL` env var in email templates
- [ ] P1 — File-based secret support (`*_FILE` env vars)
- [ ] P1 — Config validation on startup (fail fast on missing required vars)
- [ ] P2 — Config reload (SIGHUP or endpoint for non-sensitive settings)

### 4.5 Logging & Audit
- [ ] P1 — Structured logging (JSON format, `structlog` or `python-json-logger`)
- [ ] P1 — Audit log for sensitive operations (login, logout, acknowledge, device create/delete)
- [ ] P1 — Request ID middleware for traceability
- [ ] P2 — Log rotation configuration
- [ ] P2 — `detection.py` — replace `except: pass` with proper error logging
- [ ] P2 — Separate error/access/audit log files

### 4.6 Error Handling
- [ ] P0 — Production error handler (return generic 500, log details)
- [ ] P1 — Pydantic validation error customisation (don't leak internal schema)
- [ ] P1 — 404 handler returning JSON (not HTML)
- [ ] P2 — Graceful shutdown (persist AI state on SIGTERM/SIGINT)

### 4.7 Performance & Reliability
- [ ] P1 — Background email sending (`asyncio.create_task` or thread pool)
- [ ] P1 — SSE exponential backoff (dashboard side)
- [ ] P1 — Dedicated `/summary` endpoint (move client-side aggregation to backend)
- [ ] P2 — Alert deduplication (suppression window for identical alerts)
- [ ] P2 — Database connection pool tuning
- [ ] P2 — Nginx rate limiting in front of FastAPI

### 4.8 Testing
- [ ] P1 — Backend integration tests for `POST /events` pipeline
- [ ] P1 — Backend integration tests for auth flow (login, refresh, logout)
- [ ] P1 — Backend unit tests for classification and narrative
- [ ] P2 — Frontend component tests (React Testing Library)
- [ ] P2 — End-to-end tests (Playwright) for critical paths
- [ ] P2 — Rate limiter tests

### 4.9 Refactoring
- [ ] P1 — Extract shared AI init code into `app/ai_integration.py` module (eliminate duplication between `main.py` and `detection.py`)
- [ ] P2 — Extract classification features into a shared utility
- [ ] P2 — Remove `POST /baseline` legacy endpoint (or mark deprecated)

---

## 5. Implementation Order

### Phase 0 — Authentication Foundation (Week 1)
**Do this first. Everything depends on it.**

1. Add `VIGIL_JWT_SECRET` / auto-generation logic
2. Create `users` and `refresh_tokens` SQLAlchemy models
3. Implement auth endpoints: `POST /auth/login`, `/auth/refresh`, `/auth/logout`
4. Implement `require_auth` dependency
5. Gate ALL existing endpoints (except `/health`) behind `require_auth`
6. Add optional `VIGIL_AUTH_DISABLED=true` bypass
7. Write backend tests for auth flow

**Why first:** Without auth, nothing is safe. Every other fix assumes an authenticated context. Adding auth last means retrofitting every endpoint — adding it first means testing every new endpoint against auth from day one.

### Phase 1 — Data Integrity (Week 2)

1. Wire `fetchTrustTrend` to real backend endpoint aggregating trust score history from DB
2. Implement `PATCH /alerts/{id}/acknowledge` + wire dashboard acknowledge button to it
3. Persist AI state: add `trust_model_params (JSON)` and `anomaly_detector_params (JSON)` columns to `devices` table; serialize on each update, deserialize on load
4. Backend integration tests for all three

**Why second:** Users cannot make security decisions on simulated data. Acknowledge is a core UX flow. AI state loss on restart is a silent data-loss bug.

### Phase 2 — Production Hardening (Week 3)

1. Database: Alembic init + first migration, enable WAL mode, add indexes
2. Move email sending to background task (asyncio or thread pool)
3. Add rate limiting middleware (`slowapi` or custom)
4. Add input validation (MAC regex, IP validation, hostname sanitization)
5. Add CORS middleware
6. Add proper error handling (no stack traces)
7. Extract shared code into `app/ai_integration.py`
8. Add `/health` endpoint

**Why third:** These are production-readiness items. They matter for reliability but don't block the core security/data integrity fixes.

### Phase 3 — Logging & Config (Week 4)

1. Structured logging with JSON format
2. Audit log for sensitive operations
3. `.env.example` with all documented vars
4. File-based secret support
5. Config validation on startup
6. `VIGIL_DASHBOARD_URL` env var (replace hardcoded `192.168.50.30`)

**Why fourth:** Valuable for operations and debugging but not blocking deployment.

### Phase 4 — Testing & Polish (Week 5+)

1. Backend integration tests for `POST /events` pipeline
2. Classifier and narrative unit tests
3. Rate limiter tests
4. SSE exponential backoff in dashboard
5. Alert deduplication
6. `POST /baseline` deprecation
7. Frontend component tests

---

## 6. Estimated Effort per Item

| Item | Effort | Complexity | Risk if skipped |
|------|--------|-----------|-----------------|
| JWT auth (endpoints, middleware, login/refresh/logout) | 2-3 days | Medium | 🔴 Data breach — anyone on LAN can read/modify all data |
| Auth frontend (login page, context, interceptor, SSE) | 2-3 days | Medium | 🔴 Dashboard unusable without auth flow |
| Real trust trend endpoint | 0.5 day | Low | 🟡 False analytics → bad decisions |
| Alert acknowledge persistence | 0.5 day | Low | 🟡 UX failure — acknowledge doesn't survive refresh |
| AI state persistence (DB columns + serialization) | 1 day | Medium | 🟡 Trust scores reset on restart |
| Background email sending | 0.5 day | Low | 🟢 API latency under load |
| Rate limiting middleware | 0.5 day | Low | 🟢 DoS potential on write endpoints |
| Input validation (MAC/IP/hostname) | 0.5 day | Low | 🟢 Injection surface |
| CORS middleware | 0.25 day | Low | 🟢 Browser-side CSRF |
| Error handling (production 500 handler) | 0.25 day | Low | 🟢 Stack trace exposure |
| Alembic DB migrations | 1 day | Medium | 🟢 Schema changes become risky |
| WAL mode + indexes | 0.5 day | Low | 🟢 Performance under load |
| Extract shared AI code | 1 day | Medium | 🟢 Code duplication (tech debt) |
| Health endpoint | 0.25 day | Low | 🟢 Ops visibility |
| Structured logging | 1 day | Medium | 🟢 Debugging in production |
| Audit log | 0.5 day | Low | 🟢 Incident investigation |
| .env.example + config validation | 0.5 day | Low | 🟢 Onboarding friction |
| Dashboard URL env var | 0.25 day | Low | 🟢 Hardcoded IP in email |
| Backend integration tests | 2-3 days | Medium | 🟢 Regression risk on refactors |
| Classifier/narrative tests | 1 day | Medium | 🟢 Regression risk |
| SSE exponential backoff | 0.25 day | Low | 🟢 Network blip recovery |
| Alert deduplication | 0.5 day | Low | 🟢 Alert fatigue |
| `POST /baseline` deprecation | 0.25 day | Low | 🟢 API surface clarity |

**Total estimated effort:** ~17-22 days (3-4 weeks for one developer)

### Effort Breakdown by Phase

| Phase | Effort | Focus |
|-------|--------|-------|
| Phase 0: Auth Foundation | 5-6 days | JWT, login, middleware, frontend auth, tests |
| Phase 1: Data Integrity | 2-3 days | Trust trend, acknowledge, AI persistence |
| Phase 2: Production Hardening | 4-5 days | DB migrations, rate limiting, input validation, refactoring, background tasks |
| Phase 3: Logging & Config | 2-3 days | Structured logging, audit, env config |
| Phase 4: Testing & Polish | 4-5 days | Integration tests, SSE, dedup, frontend tests |

---

## 7. Appendix: Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Status |
|----|------|-----------|--------|------------|--------|
| R01 | Unauthenticated API access | Certain | High (data breach) | Add JWT auth + middleware | **Phase 0** |
| R02 | Attacker injects events via unauthenticated POST /events | Certain | High (false alerts, trust poisoning) | Auth + rate limiting + input validation | **Phase 0 + 2** |
| R03 | Dashboard URL hardcoded in email templates | High | Medium (wrong dashboard link) | `VIGIL_DASHBOARD_URL` env var | Phase 3 |
| R04 | Stack trace exposure in production | Medium | Medium (info leakage) | Production error handler | Phase 2 |
| R05 | In-memory AI state lost on restart | Certain | Medium (trust reset) | DB persistence | Phase 1 |
| R06 | SMTP credentials visible in `ps aux` | Medium | Medium (credential leak) | File-based secrets | Phase 3 |
| R07 | SQLite corruption under concurrent writes | Low | High (data loss) | WAL mode, connection pooling | Phase 2 |
| R08 | SSE token in query string logged by nginx | High | Low (short-lived token) | Short SSE JWT expiry, strip from logs | Phase 0 |
| R09 | No alert deduplication → notification spam | High | Medium (alert fatigue) | Suppression window | Phase 4 |
| R10 | SQL injection via MAC/IP/hostname fields | Low (SQLAlchemy uses parameterized queries) | High | Verify all `filter()` calls use parameterized; no raw SQL | Phase 2 (validate) |

### SQL Injection Risk Assessment

**SQLAlchemy usage is safe.** The codebase uses:
- `db.query(Model).filter(Model.column == value)` — parameterized by default
- `db.add(instance)` — ORM insertion, parameterized
- No raw SQL strings or `text()` constructs

**Verdict:** Low risk. Validate that no future changes introduce raw SQL. The real injection risk is at the input validation layer (MAC/IP/hostname in Pydantic models), which is addressed by input sanitization in Phase 2.

---

## Summary: Top 5 Security Fixes

| # | Fix | Rationale |
|---|-----|-----------|
| **1** | **Add JWT authentication to all API endpoints** | Every endpoint is currently open. Any device on the network can read alerts, view devices, and POST events. This is the single biggest risk — fixes confidentiality, integrity, and access control in one shot. |
| **2** | **Replace simulated trust trend with real data** | The analytics page shows `Math.random()` values. A user making security decisions (e.g., trusting a device with "high" trust) has false confidence. This undermines the entire trust-model value proposition and could lead to real security mistakes. |
| **3** | **Persist AI state (anomaly detectors + trust models) to database** | On server restart, all historical AI state is lost. Trust scores reset to 0.5, anomaly baselines reset. Attackers who time their activity around a restart will evade detection during the cold-start window. |
| **4** | **Wire alert acknowledge to a backend PATCH endpoint** | Current acknowledge is client-side only (React `Set` state). A page refresh restores all alerts to "unacknowledged." Operators cannot track triage state, making it impossible to distinguish new alerts from already-reviewed ones. |
| **5** | **Move SMTP email sending out of the request path** | `send_alert_email()` makes a synchronous SMTP connection inside `POST /events`. This adds 1-5 seconds per request. Under Suricata flood traffic, this serializes requests, exhausts uvicorn workers, and creates a self-inflicted DoS condition on the only endpoint that processes security events. |
