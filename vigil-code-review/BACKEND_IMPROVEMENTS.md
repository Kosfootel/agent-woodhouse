# Vigil Dashboard Backend - Recommended Improvements

**Prioritized by Impact and Effort**

---

## 🔴 Critical Priority (Fix Immediately)

### 1. Fix Cryptographic Security
**Impact:** Prevents credential theft if database is compromised  
**Effort:** 2 hours  
**Files:** `app/utils/crypto.py`

```python
# BEFORE (INSECURE):
salt = b'vigil-static-salt-32bytes-long!'
key_env = os.getenv('VIGIL_KEY', 'fallback-key-32bytes-long!!!!!')

# AFTER (SECURE):
def encrypt_password(password: str) -> str:
    """Encrypt with random salt per entry."""
    if not password:
        return ""
    
    key_env = os.getenv('VIGIL_KEY')
    if not key_env:
        raise ValueError("VIGIL_KEY environment variable must be set")
    
    # Generate random salt
    salt = secrets.token_bytes(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommended minimum
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    
    # Store salt + encrypted together
    return base64.urlsafe_b64encode(salt + encrypted).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt with extracted salt."""
    if not encrypted_password:
        return ""
    
    try:
        key_env = os.getenv('VIGIL_KEY')
        if not key_env:
            raise ValueError("VIGIL_KEY environment variable must be set")
        
        data = base64.urlsafe_b64decode(encrypted_password.encode())
        salt = data[:16]
        encrypted = data[16:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
        f = Fernet(key)
        return f.decrypt(encrypted).decode()
    except Exception:
        return ""
```

---

### 2. Fix Database Path Configuration
**Impact:** Prevents deployment failures  
**Effort:** 1 hour  
**Files:** `app/routers/admin.py`, `app/routers/discovery_scan.py`, `app/routers/events.py`

```python
# BEFORE:
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"

# AFTER:
import os
DB_PATH = os.getenv("DATABASE_PATH", "/app/data/vigil.db")

# Add validation
def validate_db_path(path: str) -> str:
    """Ensure path is safe and within allowed directories."""
    allowed_prefixes = ["/app/data/", "/tmp/", "/var/lib/vigil/"]
    resolved = os.path.realpath(path)
    if not any(resolved.startswith(p) for p in allowed_prefixes):
        raise ValueError(f"Database path {path} is not in allowed directory")
    return resolved

DB_PATH = validate_db_path(os.getenv("DATABASE_PATH", "/app/data/vigil.db"))
```

---

### 3. Fix CORS Configuration
**Impact:** Prevents CSRF attacks  
**Effort:** 1 hour  
**Files:** `app/main.py`, `main.py`

```python
# BEFORE:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.50.30:8085", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER:
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cors_origins: str = "http://localhost:3000"
    
    class Config:
        env_prefix = "VIGIL_"

settings = Settings()

origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 🟠 High Priority (Fix This Week)

### 4. Implement Rate Limiting
**Impact:** Prevents abuse and DoS  
**Effort:** 3 hours  
**Files:** `app/main.py`, all routers

```python
# Install and configure slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Use in routers:
@router.post("/setup/connect")
@limiter.limit("5/minute")
async def connect_router(request: Request, credentials: RouterCredentialsInput, db: Session = Depends(get_db)):
    ...
```

---

### 5. Add Input Validation Layer
**Impact:** Prevents injection attacks  
**Effort:** 4 hours  
**Files:** All routers

```python
# validators.py
import re
import ipaddress
from pydantic import validator

class Validators:
    MAC_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    
    @staticmethod
    def validate_mac(value: str) -> str:
        if not value:
            raise ValueError("MAC address required")
        value = value.upper().replace('-', ':')
        if not Validators.MAC_PATTERN.match(value):
            raise ValueError(f"Invalid MAC address format: {value}")
        return value
    
    @staticmethod
    def validate_ip(value: str) -> str:
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid IP address: {value}")

# Usage in models:
class DeviceUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    hostname: Optional[str] = None
    
    @validator('hostname')
    def validate_hostname(cls, v):
        if v and len(v) > 255:
            raise ValueError("Hostname too long")
        if v and not re.match(r'^[\w\-\.]+$', v):
            raise ValueError("Invalid hostname format")
        return v
```

---

### 6. Implement Proper Error Handling
**Impact:** Prevents information disclosure  
**Effort:** 3 hours  
**Files:** All routers

```python
# exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class VigilException(Exception):
    """Base exception for Vigil."""
    pass

class ValidationError(VigilException):
    """Input validation failed."""
    pass

class DatabaseError(VigilException):
    """Database operation failed."""
    pass

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions without exposing details."""
    if exc.status_code >= 500:
        logger.error(f"Server error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": "Internal server error"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Usage in routers:
@router.get("/events")
async def get_events(db: Session = Depends(get_db)):
    try:
        return db.query(Event).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")
```

---

### 7. Split Monolithic Routers
**Impact:** Improves maintainability  
**Effort:** 6 hours  
**Files:** `app/routers/security.py`, `app/routers/setup.py`

**Proposed Structure:**
```
app/routers/security/
    __init__.py
    scanning.py      # Prompt/tool/access scanning
    logging.py       # Log retrieval and management
    anomalies.py     # Anomaly detection endpoints
    dashboard.py     # Dashboard data endpoints

app/routers/setup/
    __init__.py
    discovery.py     # Router discovery
    devices.py       # Device import
    agents.py        # Agent registration
    credentials.py   # Credential management
```

---

## 🟡 Medium Priority (Fix This Month)

### 8. Add Database Migrations
**Impact:** Enables safe schema evolution  
**Effort:** 4 hours

```bash
# Install Alembic
pip install alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Add to startup
# In main.py:
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

@app.on_event("startup")
async def startup():
    run_migrations()
```

---

### 9. Add Security Headers Middleware
**Impact:** Defense in depth  
**Effort:** 2 hours

```python
# middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict transport security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content security policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

# In main.py:
app.add_middleware(SecurityHeadersMiddleware)
```

---

### 10. Add Comprehensive Testing
**Impact:** Prevents regressions  
**Effort:** 16 hours (aim for 70% coverage)

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# tests/test_devices.py
def test_list_devices(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert "devices" in response.json()

def test_create_device_invalid_mac(client):
    response = client.post("/api/devices", json={
        "mac": "invalid-mac",
        "ip": "192.168.1.1"
    })
    assert response.status_code == 422

def test_block_device(client, db):
    # Create device first
    from app.models import Device
    device = Device(mac="AA:BB:CC:DD:EE:FF", ip="192.168.1.100")
    db.add(device)
    db.commit()
    
    response = client.post(f"/api/devices/{device.id}/block")
    assert response.status_code == 200
    assert response.json()["success"] is True
```

---

### 11. Implement Async Database Operations
**Impact:** Better concurrency  
**Effort:** 6 hours

```python
# Use databases library for async SQLAlchemy
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./vigil.db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

# In routers:
@router.get("/devices")
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    return {"devices": devices}
```

---

### 12. Add Structured Logging
**Impact:** Better observability  
**Effort:** 3 hours

```python
# logging_config.py
import logging
import json
import sys
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "vigil-backend"
        log_record["environment"] = os.getenv("ENV", "development")

def setup_logging():
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    log_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers = [log_handler]
    root_logger.setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

# Usage:
logger.info("Device discovered", extra={
    "device_mac": device.mac,
    "device_ip": device.ip,
    "discovery_method": "mdns"
})
```

---

## 🟢 Low Priority (Nice to Have)

### 13. Add API Versioning
**Impact:** Enables backward compatibility  
**Effort:** 4 hours

```python
# Versioned router structure
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

# Or use header-based versioning
@app.middleware("http")
async def version_middleware(request: Request, call_next):
    version = request.headers.get("X-API-Version", "1")
    request.state.api_version = version
    return await call_next(request)
```

---

### 14. Add Health Check Endpoints
**Impact:** Better monitoring  
**Effort:** 2 hours

```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    checks = {
        "database": False,
        "disk_space": False,
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Disk check
    try:
        stat = os.statvfs("/app/data")
        checks["disk_space"] = stat.f_bavail / stat.f_blocks > 0.1
    except Exception:
        pass
    
    healthy = all(checks.values())
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

### 15. Add Metrics Endpoint
**Impact:** Observability  
**Effort:** 3 hours

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter('vigil_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('vigil_request_duration_seconds', 'Request latency')
DB_QUERY_COUNT = Counter('vigil_db_queries_total', 'Database queries')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(duration)
    
    return response

@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Summary Table

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 🔴 Critical | Fix crypto salt | 2h | Security |
| 🔴 Critical | Fix DB paths | 1h | Deployability |
| 🔴 Critical | Fix CORS | 1h | Security |
| 🟠 High | Rate limiting | 3h | Security |
| 🟠 High | Input validation | 4h | Security |
| 🟠 High | Error handling | 3h | Security |
| 🟠 High | Split routers | 6h | Maintainability |
| 🟡 Medium | DB migrations | 4h | Maintainability |
| 🟡 Medium | Security headers | 2h | Security |
| 🟡 Medium | Tests | 16h | Quality |
| 🟡 Medium | Async DB | 6h | Performance |
| 🟡 Medium | Structured logging | 3h | Observability |
| 🟢 Low | API versioning | 4h | Maintainability |
| 🟢 Low | Health checks | 2h | Observability |
| 🟢 Low | Metrics | 3h | Observability |

**Total Critical/High Effort:** ~20 hours  
**Total Medium Effort:** ~31 hours  
**Total Effort:** ~55 hours

---

*Prioritize based on your security requirements and deployment timeline.*
