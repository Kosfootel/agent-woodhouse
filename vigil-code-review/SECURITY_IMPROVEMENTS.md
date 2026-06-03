# Vigil Dashboard Security Improvements

**Document:** Security Hardening Recommendations  
**Priority:** Risk-based prioritization  
**Target:** Vigil Security Platform v0.4.0+

---

## Immediate Actions (Critical - Address within 24 hours)

### 1. Rotate Exposed Credentials

**Priority:** P0 - CRITICAL

**Issue:** Gmail app password exposed in docker-compose.yml

**Actions:**
1. Immediately revoke the exposed Gmail app password at https://myaccount.google.com/apppasswords
2. Generate new app password
3. Remove from docker-compose.yml and store in `.env` file
4. Add `.env` to `.gitignore` if not already present
5. Scan git history for other exposed secrets: `git log --all --full-history -- .env docker-compose.yml`

**Verification:**
```bash
git log --all -p -- docker-compose.yml | grep -i "password\|secret\|key"
```

---

### 2. Fix CORS Configuration

**Priority:** P0 - CRITICAL

**Issue:** Wildcard CORS with credentials enabled

**Current (Vulnerable):**
```python
allow_origins=["*"],
allow_credentials=True,
```

**Recommended Fix:**
```python
import os
from fastapi.middleware.cors import CORSMiddleware

# Load from environment, with safe defaults
ALLOWED_ORIGINS = os.environ.get(
    "VIGIL_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Validate no wildcards with credentials
if "*" in ALLOWED_ORIGINS and os.environ.get("VIGIL_ENV") == "production":
    raise RuntimeError("Wildcard CORS not allowed in production with credentials")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)
```

**Environment Variables:**
```bash
# .env.production
VIGIL_CORS_ORIGINS=http://192.168.50.30:8085,http://dashboard.vigil.local
VIGIL_ENV=production
```

---

### 3. Secure JWT Secret Handling

**Priority:** P0 - CRITICAL

**Issue:** Auto-generated JWT secret with race conditions

**Recommended Implementation:**

Create `app/config.py`:
```python
import os
import secrets
import logging
from pathlib import Path

logger = logging.getLogger("vigil.config")

class JWTConfig:
    @classmethod
    def get_secret(cls) -> str:
        # Priority 1: Direct environment variable
        secret = os.environ.get("VIGIL_JWT_SECRET")
        if secret:
            if len(secret) < 32:
                raise ValueError("VIGIL_JWT_SECRET must be at least 32 characters")
            return secret
        
        # Priority 2: File-based secret
        file_path = os.environ.get("VIGIL_JWT_SECRET_FILE")
        if file_path:
            return cls._read_secret_file(file_path)
        
        # Priority 3: Docker secrets
        docker_secret = Path("/run/secrets/jwt_secret")
        if docker_secret.exists():
            return cls._read_secret_file(str(docker_secret))
        
        raise RuntimeError(
            "JWT secret not configured. Set one of:\n"
            "  - VIGIL_JWT_SECRET environment variable\n"
            "  - VIGIL_JWT_SECRET_FILE file path\n"
            "  - Docker secret at /run/secrets/jwt_secret\n"
            "Generate a secure secret: openssl rand -hex 32"
        )
    
    @classmethod
    def _read_secret_file(cls, path: str) -> str:
        import pwd
        import grp
        
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"JWT secret file not found: {path}")
        
        # Check ownership
        stat = p.stat()
        current_uid = os.getuid()
        if stat.st_uid != current_uid:
            owner = pwd.getpwuid(stat.st_uid).pw_name
            current = pwd.getpwuid(current_uid).pw_name
            raise PermissionError(
                f"JWT secret file {path} owned by {owner}, "
                f"but running as {current}"
            )
        
        # Check permissions (should be 0o600)
        if stat.st_mode & 0o077:
            raise PermissionError(
                f"JWT secret file {path} has overly permissive permissions. "
                f"Run: chmod 600 {path}"
            )
        
        secret = p.read_text().strip()
        if len(secret) < 32:
            raise ValueError(f"JWT secret in {path} must be at least 32 characters")
        
        return secret
```

Update `app/auth.py`:
```python
from app.config import JWTConfig

JWT_SECRET = JWTConfig.get_secret()
```

**Docker Compose Update:**
```yaml
secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt

services:
  vigil-api:
    secrets:
      - jwt_secret
    environment:
      - VIGIL_JWT_SECRET_FILE=/run/secrets/jwt_secret
```

---

## Short-term Actions (High Priority - Address within 1 week)

### 4. Implement Proper CSRF Protection

**Priority:** P1 - HIGH

**Current State:** No CSRF protection on state-changing endpoints.

**Recommended Implementation:**

For API-first applications, use Double Submit Cookie pattern:

```python
# app/middleware/csrf.py
import secrets
import hmac
import hashlib
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_routes=None):
        super().__init__(app)
        self.exempt_routes = exempt_routes or []
    
    async def dispatch(self, request: Request, call_next):
        # Skip for GET, HEAD, OPTIONS
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)
        
        # Skip exempt routes
        if any(request.url.path.startswith(r) for r in self.exempt_routes):
            return await call_next(request)
        
        # Check CSRF token for state-changing requests
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        if not csrf_cookie or not csrf_header:
            raise HTTPException(403, "CSRF token missing")
        
        if not hmac.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(403, "CSRF token mismatch")
        
        return await call_next(request)

# Add to main.py
app.add_middleware(
    CSRFMiddleware,
    exempt_routes=["/api/auth/login", "/api/auth/refresh", "/api/health"]
)
```

Frontend Axios configuration:
```javascript
// Read CSRF cookie and set header
axios.defaults.headers.common['X-CSRF-Token'] = getCookie('csrf_token');
```

---

### 5. Secure API Key Storage

**Priority:** P1 - HIGH

**Current:** SHA-256 hashing (fast, vulnerable to brute force)

**Recommended:** Migrate to Argon2id

```python
# app/auth.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_api_key(key: str) -> str:
    """Hash API key using Argon2id (slow hash)."""
    return ph.hash(key)

def verify_api_key(key: str, hash: str) -> bool:
    """Verify API key against Argon2id hash."""
    try:
        ph.verify(hash, key)
        # Rehash if parameters changed
        if ph.check_needs_rehash(hash):
            # Update hash in database
            pass
        return True
    except VerifyMismatchError:
        return False

# Migration script for existing keys
async def migrate_api_keys():
    """One-time migration from SHA-256 to Argon2id."""
    db = SessionLocal()
    try:
        keys = db.query(ApiKey).all()
        for key in keys:
            # Mark for re-generation (can't migrate hash)
            key.needs_rotation = True
        db.commit()
    finally:
        db.close()
```

---

### 6. Fix Vault Encryption

**Priority:** P1 - HIGH

**Current:** Static salt enables rainbow tables

**Recommended:** Random per-credential salt

```python
# app/vault/vault_encryption.py
import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class VaultEncryptionService:
    SALT_SIZE = 32
    NONCE_SIZE = 12
    KEY_SIZE = 32
    PBKDF2_ITERATIONS = 600000  # OWASP 2023 recommendation
    
    def __init__(self, master_key: str):
        self._master_key = master_key.encode()
    
    def encrypt(self, plaintext: str) -> bytes:
        # Generate random salt for this credential
        salt = secrets.token_bytes(self.SALT_SIZE)
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )
        key = kdf.derive(self._master_key)
        
        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Format: [salt (32)] [nonce (12)] [ciphertext]
        return salt + nonce + ciphertext
    
    def decrypt(self, encrypted_data: bytes) -> str:
        if len(encrypted_data) < self.SALT_SIZE + self.NONCE_SIZE:
            raise ValueError("Invalid encrypted data")
        
        # Extract components
        salt = encrypted_data[:self.SALT_SIZE]
        nonce = encrypted_data[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
        ciphertext = encrypted_data[self.SALT_SIZE + self.NONCE_SIZE:]
        
        # Derive key with stored salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )
        key = kdf.derive(self._master_key)
        
        # Decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
```

---

### 7. Add Content Security Policy

**Priority:** P1 - HIGH

**Nginx Configuration:**
```nginx
# /etc/nginx/conf.d/security-headers.conf
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' http://192.168.50.30:8000; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```

**For development (meta tag):**
```html
<!-- dashboard/public/index.html -->
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' http://192.168.50.30:8000;">
```

---

## Medium-term Actions (Address within 1 month)

### 8. Container Security Hardening

**Priority:** P2 - MEDIUM

**Updated Dockerfile:**
```dockerfile
FROM python:3.12-slim

# Install security updates
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash vigil \
    && mkdir -p /app /data /var/log/suricata \
    && chown -R vigil:vigil /app /data /var/log/suricata

WORKDIR /app

# Copy and install requirements
COPY --chown=vigil:vigil requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Copy application
COPY --chown=vigil:vigil app/ ./app/

# Security: read-only root filesystem
RUN chmod -R 755 /app \
    && chmod -R 750 /data

USER vigil

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

**Docker Compose Security:**
```yaml
services:
  vigil-api:
    build: .
    read_only: true
    security_opt:
      - no-new-privileges:true
      - seccomp:./seccomp-profile.json
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

---

### 9. Implement Audit Logging

**Priority:** P2 - MEDIUM

```python
# app/audit.py
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request

audit_logger = logging.getLogger("vigil.audit")

class AuditLogger:
    @staticmethod
    def log_event(
        event_type: str,
        request: Optional[Request],
        user_id: Optional[str],
        resource: str,
        action: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "client_ip": request.client.host if request else None,
            "user_agent": request.headers.get("user-agent") if request else None,
            "resource": resource,
            "action": action,
            "result": result,
            "details": details or {},
        }
        audit_logger.info(json.dumps(event))

# Usage in endpoints
@router.delete("/auth/api-keys/{key_id}")
def revoke_api_key(...):
    # ... existing logic ...
    AuditLogger.log_event(
        event_type="api_key_revoked",
        request=request,
        user_id=auth.get("sub"),
        resource=f"api_key:{key_id}",
        action="revoke",
        result="success",
        details={"key_prefix": api_key.key_prefix}
    )
```

---

### 10. Add Security Headers to API

**Priority:** P2 - MEDIUM

```python
# app/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server identification
        response.headers.pop("Server", None)
        
        return response

# Add to main.py
app.add_middleware(SecurityHeadersMiddleware)
```

---

### 11. Implement IP Allowlisting

**Priority:** P2 - MEDIUM

```python
# app/middleware/ip_filter.py
import ipaddress
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_networks=None):
        super().__init__(app)
        self.allowed_networks = [
            ipaddress.ip_network(n) for n in (allowed_networks or ["127.0.0.1/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"])
        ]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = ipaddress.ip_address(request.client.host)
        
        if not any(client_ip in network for network in self.allowed_networks):
            raise HTTPException(403, "Access denied from this IP address")
        
        return await call_next(request)

# Optional: Add for sensitive endpoints only
```

---

## Long-term Actions (Address within 3 months)

### 12. Implement Mutual TLS (mTLS)

**Priority:** P3 - LOW

For agent-to-server communication:
```python
# In uvicorn/SSL configuration
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("server.crt", "server.key")
context.load_verify_locations("ca.crt")
context.verify_mode = ssl.CERT_REQUIRED  # Require client cert

uvicorn.run(app, ssl=context)
```

---

### 13. Add Rate Limiting Improvements

**Priority:** P3 - LOW

```python
# Enhanced rate limiting with Redis backend
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379",
    strategy="moving-window",  # More accurate than fixed window
)
```

---

### 14. Implement Secrets Rotation

**Priority:** P3 - LOW

```python
# app/rotation.py
from datetime import datetime, timedelta
from typing import Optional

class SecretRotation:
    """Automated secrets rotation for credentials."""
    
    ROTATION_INTERVAL_DAYS = 90
    
    @staticmethod
    def check_rotation_needed(credential) -> bool:
        if not credential.last_rotated:
            return True
        
        rotation_due = credential.last_rotated + timedelta(
            days=SecretRotation.ROTATION_INTERVAL_DAYS
        )
        return datetime.utcnow() >= rotation_due
    
    @staticmethod
    def generate_new_credential(credential_type: str) -> str:
        if credential_type == "api_key":
            return secrets.token_urlsafe(32)
        elif credential_type == "password":
            # Generate strong password
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + "!@#$%^*&*"
            return ''.join(secrets.choice(alphabet) for _ in range(32))
        # ... etc
```

---

### 15. Security Monitoring Dashboard

**Priority:** P3 - LOW

Add security metrics to dashboard:
- Failed login attempts
- Rate limit hits
- Suspicious IP activity
- Credential access patterns
- Certificate expiration

---

## Verification Checklist

Use this checklist after implementing changes:

- [ ] No hardcoded secrets in repository
- [ ] CORS configured with explicit origins only
- [ ] JWT secret requires manual configuration (no auto-gen)
- [ ] Vault uses random salt per credential
- [ ] API keys use Argon2id hashing
- [ ] Input validation on all user-controlled parameters
- [ ] CSP headers configured
- [ ] Container runs as non-root user
- [ ] CSRF protection enabled
- [ ] Security headers present on all responses
- [ ] Audit logging implemented
- [ ] Rate limiting active on auth endpoints
- [ ] TLS/HTTPS configured
- [ ] Docker security options applied

---

## References

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Docker Security Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

*End of Document*
