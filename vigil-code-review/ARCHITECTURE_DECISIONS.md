# Vigil Dashboard - Architecture Decisions

**Key Decisions Required for Redesign/Re-Architecture**

Based on the code review findings, these are the critical architectural decisions that must be made before proceeding with the redesign.

---

## ADR-001: Frontend State Management Strategy

### Context
Current implementation uses only local component state (useState) with prop drilling. No global state management.

### Options

| Option | Pros | Cons |
|--------|------|------|
| **Zustand** (Recommended) | Minimal boilerplate, small bundle, great TypeScript | Less ecosystem than Redux |
| **React Query + Context** | Server state handled, simple client state | Context limitations at scale |
| **Redux Toolkit** | Mature, predictable, devtools | Boilerplate, larger bundle |
| **Jotai/Recoil** | Atomic approach, fine-grained | Newer, smaller ecosystem |

### Decision: **Zustand + React Query**

**Rationale:**
- Compact design principle: minimal overhead
- Zustand for global UI state (sidebar, filters, user preferences)
- React Query for server state (caching, background sync)
- ~2KB added vs Redux's ~15KB

### Implementation
```typescript
// stores/uiStore.ts
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  activeFilters: Filter[]
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeFilters: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))
```

---

## ADR-002: API Client Standardization

### Context
Current codebase mixes `fetch()`, `axios`, and direct XMLHttpRequest. Inconsistent error handling.

### Decision: **Standardize on Axios with Interceptors**

**Rationale:**
- Single source of truth for API configuration
- Request/response interceptors for auth, logging, error handling
- Automatic CSRF token handling
- Request cancellation support

### Implementation Pattern
```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor - handle errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(err)
  }
)
```

---

## ADR-003: Backend Router Organization

### Context
`security.py` (600+ lines) and `setup.py` (800+ lines) are monolithic routers mixing concerns.

### Decision: **Domain-Driven Router Split**

**New Structure:**
```
app/routers/
├── __init__.py
├── devices/
│   ├── __init__.py
│   ├── routes.py      # Device CRUD endpoints
│   ├── models.py      # Device Pydantic models
│   └── service.py     # Device business logic
├── security/
│   ├── __init__.py
│   ├── scanning.py    # Scan endpoints
│   ├── policies.py    # Policy management
│   └── alerts.py      # Alert endpoints
├── setup/
│   ├── __init__.py
│   ├── discovery.py   # Router discovery
│   ├── wizard.py      # Setup wizard steps
│   └── credentials.py # Credential management
└── common/
    ├── deps.py        # Shared dependencies
    ├── models.py      # Shared Pydantic models
    └── exceptions.py  # Custom exceptions
```

**Max file size:** 200 lines per module

---

## ADR-004: Database Strategy

### Context
Currently using SQLite with no migrations. Hardcoded paths. Two competing database locations.

### Options

| Option | Pros | Cons |
|--------|------|------|
| **SQLite + Alembic** (Short-term) | Simple, single file, no deps | No concurrent writes, scaling limits |
| **PostgreSQL** (Long-term) | Production-grade, concurrent, JSON | Requires separate container, more RAM |

### Decision: **Two-Phase Migration**

**Phase 1 (Immediate):**
- Keep SQLite for now
- Add Alembic migrations
- Fix path configuration (env var, not hardcoded)
- Add database connection pooling

**Phase 2 (Future):**
- Evaluate PostgreSQL if scale requires
- Keep migration compatibility

### Implementation
```python
# database.py - SQLAlchemy with connection pooling
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./data/vigil.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

---

## ADR-005: Container Security Model

### Context
Containers run as root, use `network_mode: host`, no resource limits on some services.

### Decision: **Defense in Depth Container Model**

**Requirements:**
1. **Non-root user** for all containers
2. **Read-only root filesystem** where possible
3. **Drop all capabilities** except required
4. **Resource limits** on all services
5. **Health checks** on all services
6. **No host networking** (use bridge networks)

### Implementation
```yaml
# docker-compose.yml
services:
  backend:
    user: "1000:1000"  # Non-root
    read_only: true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding low ports
    security_opt:
      - no-new-privileges:true
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## ADR-006: Authentication Architecture

### Context
JWT with auto-generated secrets, tokens in URL params, no refresh mechanism.

### Decision: **Cookie-Based Session + CSRF Protection**

**Rationale:**
- XSS-resistant (HttpOnly cookies)
- No token storage in JavaScript
- Automatic browser handling
- CSRF protection via SameSite + token

### Implementation
```python
# auth.py - FastAPI cookie-based sessions
from fastapi import Response, Request
from itsdangerous import URLSafeSerializer

serializer = URLSafeSerializer(SECRET_KEY)

@app.post("/login")
async def login(response: Response, credentials: LoginRequest):
    user = authenticate(credentials)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    session_data = {"user_id": user.id, "exp": time() + 3600}
    token = serializer.dumps(session_data)
    
    response.set_cookie(
        "session",
        token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600
    )
    return {"status": "ok"}
```

---

## ADR-007: Configuration Management

### Context
Hardcoded values scattered across 15+ files. No single source of truth.

### Decision: **Pydantic Settings with Environment Variables**

**Principles:**
1. All configuration via environment variables
2. Pydantic validation with types
3. Sensible defaults for development
4. Strict validation for production

### Implementation
```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./data/vigil.db"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_user: str | None = None
    smtp_password: str | None = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## ADR-008: Testing Strategy

### Context
0% frontend coverage, ~10% backend coverage.

### Decision: **Pyramid Testing Approach**

**Distribution:**
- **70% Unit tests** - Fast, isolated, cheap
- **20% Integration tests** - API contracts, database
- **10% E2E tests** - Critical user flows

**Backend Stack:**
- pytest with pytest-asyncio
- pytest-cov for coverage (target: 80%)
- Factory Boy for test data
- pytest-xdist for parallel execution

**Frontend Stack:**
- Vitest (fast, native ESM)
- React Testing Library
- MSW (Mock Service Worker) for API mocking
- Playwright for E2E

---

## ADR-009: Error Handling Strategy

### Context
Inconsistent error formats, full exception details exposed to clients.

### Decision: **Unified Error Response Format**

**Structure:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid MAC address format",
    "field": "mac_address",
    "request_id": "req-123-abc"
  }
}
```

**Exception Hierarchy:**
```python
class VigilException(Exception):
    """Base exception with HTTP status code"""
    status_code = 500
    code = "INTERNAL_ERROR"
    
class ValidationError(VigilException):
    status_code = 422
    code = "VALIDATION_ERROR"
    
class AuthenticationError(VigilException):
    status_code = 401
    code = "AUTHENTICATION_ERROR"

# Exception handler
@app.exception_handler(VigilException)
async def vigil_exception_handler(request: Request, exc: VigilException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "request_id": request.state.request_id
            }
        }
    )
```

---

## ADR-010: Deployment Strategy

### Context
Manual deployment scripts, no GitOps, SSH key issues.

### Decision: **GitHub Actions → Docker → SSH Deployment**

**Pipeline:**
1. **Build** - Multi-arch Docker images
2. **Test** - Automated test suite
3. **Scan** - Trivy security scan (fail on CRITICAL)
4. **Push** - Registry with image signing
5. **Deploy** - SSH to GX-10 with verification

**Security:**
- GitHub Environments with protection rules
- Deployment review required for production
- Automated rollback on health check failure

### Health-Based Deployment
```yaml
# .github/workflows/deploy.yml
- name: Deploy with zero-downtime
  run: |
    # Deploy new version
    docker-compose up -d --no-deps --build backend
    
    # Verify health
    for i in {1..10}; do
      if curl -sf http://localhost:8005/health; then
        echo "✅ Deployment healthy"
        exit 0
      fi
      sleep 5
    done
    
    # Rollback on failure
    echo "❌ Health check failed, rolling back..."
    docker-compose down
    docker-compose up -d
    exit 1
```

---

## Decision Summary Table

| ID | Decision | Status | Priority |
|----|----------|--------|----------|
| ADR-001 | State: Zustand + React Query | ⏳ Pending | P1 |
| ADR-002 | API: Axios with interceptors | ⏳ Pending | P0 |
| ADR-003 | Routers: Domain-driven split | ⏳ Pending | P1 |
| ADR-004 | DB: SQLite + Alembic (now), PostgreSQL (later) | ⏳ Pending | P0 |
| ADR-005 | Containers: Non-root, read-only, no host | ⏳ Pending | P0 |
| ADR-006 | Auth: Cookie-based sessions | ⏳ Pending | P0 |
| ADR-007 | Config: Pydantic Settings | ⏳ Pending | P0 |
| ADR-008 | Testing: Pyramid approach | ⏳ Pending | P1 |
| ADR-009 | Errors: Unified format | ⏳ Pending | P1 |
| ADR-010 | Deploy: GitHub Actions + Health checks | ⏳ Pending | P0 |

**P0 = Required for production**  
**P1 = Required for maintainability**

---

*These decisions must be made and documented before Phase 2 (Implementation) begins.*
