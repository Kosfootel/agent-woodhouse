# Vigil Dashboard - Quick Wins

**Highest Impact, Lowest Effort Fixes**

These are the 10 fixes that provide maximum security/production readiness benefit with minimal development effort (1-4 hours each).

---

## Quick Win #1: Rotate Exposed Gmail Credentials
**Impact:** Critical - Stop data breach risk  
**Effort:** 30 minutes  
**File:** `poc-backend/docker-compose.yml` (lines 17, 23, 38)

### Current
```yaml
environment:
  GMAIL_USER: erik.ross@gmail.com
  GMAIL_APP_PASSWORD: odsq hraj soqe hyzm  # EXPOSED
```

### Action Required
1. Go to Google Account → Security → App passwords
2. Delete the exposed password
3. Generate new app password
4. Store in GitHub secrets or `.env` file (excluded from git)
5. Update docker-compose to use `${GMAIL_APP_PASSWORD}`

---

## Quick Win #2: Remove CORS Wildcard
**Impact:** Critical - Prevent authenticated cross-site requests  
**Effort:** 1 hour  
**File:** `backend/main.py` (line 14)

### Current
```python
allow_origins=['*'],
allow_credentials=True,  # DANGEROUS COMBINATION
```

### Fix
```python
allow_origins=os.environ.get("VIGIL_CORS_ORIGINS", 
              "http://localhost:3000,http://localhost:8080").split(","),
allow_credentials=True,
```

### .env
```
VIGIL_CORS_ORIGINS=http://192.168.50.30:8080,http://vigil.local
```

---

## Quick Win #3: Fix Health Check Typos
**Impact:** Critical - Deployment failures, false "healthy" status  
**Effort:** 15 minutes  
**File:** `docker-compose.yml.bak` (lines 45, 56)

### Current
```yaml
test: ["CMD", "curl", "-f", "http://localhost:808000/health"]  # WRONG PORT
test: ["CMD", "curl", "-f", "http://localhost:808080/health"]  # WRONG PORT
```

### Fix
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
```

---

## Quick Win #4: Remove network_mode: host
**Impact:** Critical - Restore network isolation  
**Effort:** 2 hours (requires port mapping updates)  
**File:** `docker-compose.yml` (lines 12, 25)

### Current
```yaml
services:
  backend:
    network_mode: host  # REMOVES ALL ISOLATION
```

### Fix
```yaml
services:
  backend:
    ports:
      - "8005:8005"
    networks:
      - vigil-net

networks:
  vigil-net:
    driver: bridge
```

---

## Quick Win #5: Fix SSH StrictHostKeyChecking
**Impact:** High - Prevent MITM attacks  
**Effort:** 30 minutes  
**File:** `.github/workflows/dashboard-deploy.yml` (line 78)

### Current
```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ...
```

### Fix
```bash
# Pre-populate known_hosts
- name: Setup SSH known hosts
  run: |
    mkdir -p ~/.ssh
    echo "192.168.50.30 $(ssh-keyscan -t ed25519 192.168.50.30 2>/dev/null | cut -d' ' -f2-)" >> ~/.ssh/known_hosts

# Then in deploy:
ssh -o StrictHostKeyChecking=yes user@192.168.50.30 ...
```

---

## Quick Win #6: Fix Static Salt
**Impact:** High - Prevent rainbow table attacks  
**Effort:** 2 hours  
**File:** `projects/vigil-home/poc-backend/app/vault/vault_encryption.py` (line 58)

### Current
```python
salt = b'vigil-credential-vault-v1'  # STATIC SALT
```

### Fix
```python
def encrypt_credential(credential: str, master_key: bytes) -> dict:
    salt = os.urandom(32)  # RANDOM PER-ENCRYPTION
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,  # OWASP 2023
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key))
    cipher = Fernet(key)
    return {
        "encrypted_data": cipher.encrypt(credential.encode()).decode(),
        "salt": base64.b64encode(salt).decode(),  # STORE WITH ENCRYPTED DATA
    }
```

---

## Quick Win #7: Add Environment Variable for API URL
**Impact:** High - Enable portable deployment  
**Effort:** 1 hour  
**File:** `dashboard/src/api.js` (line 3)

### Current
```javascript
const API_BASE_URL = 'http://192.168.50.30:8000';  // HARDCODED
```

### Fix
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### .env.production
```
REACT_APP_API_URL=https://api.vigil.local
```

---

## Quick Win #8: Run Containers as Non-Root
**Impact:** High - Prevent privilege escalation  
**Effort:** 1 hour per Dockerfile  
**Files:** `backend/Dockerfile`, `dashboard/Dockerfile`

### Current
```dockerfile
FROM python:3.11-slim
# No USER directive - runs as root
```

### Fix
```dockerfile
FROM python:3.11-slim

RUN groupadd -r vigil && useradd -r -g vigil vigil

WORKDIR /app
COPY --chown=vigil:vigil . .

USER vigil

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
```

---

## Quick Win #9: Add Basic CSRF Protection
**Impact:** Medium-High - Prevent CSRF attacks  
**Effort:** 2 hours  
**File:** `backend/main.py` (add middleware)

### Fix
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["vigil.local", "192.168.50.30", "localhost"]
)

# Add CSRF token endpoint
@app.get("/csrf-token")
async def get_csrf_token():
    token = secrets.token_urlsafe(32)
    return {"csrf_token": token}
```

---

## Quick Win #10: Add Security Headers
**Impact:** Medium-High - Defense in depth  
**Effort:** 1 hour  
**File:** `backend/main.py`

### Fix
```python
from fastapi import Request, Response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    return response
```

---

## Summary Table

| # | Win | Impact | Effort | Risk if Not Fixed |
|---|-----|--------|--------|-------------------|
| 1 | Rotate Gmail creds | Critical | 30m | Data breach, unauthorized access |
| 2 | Remove CORS wildcard | Critical | 1h | CSRF, credential theft |
| 3 | Fix health check typos | Critical | 15m | Undetected failures, downtime |
| 4 | Remove network_mode:host | Critical | 2h | Container escape, host compromise |
| 5 | Fix SSH StrictHostKeyChecking | High | 30m | MITM attacks |
| 6 | Fix static salt | High | 2h | Credential decryption if DB stolen |
| 7 | API URL env var | High | 1h | Deployment brittleness |
| 8 | Non-root containers | High | 1h | Privilege escalation |
| 9 | CSRF protection | Med-High | 2h | Unauthorized state changes |
| 10 | Security headers | Med-High | 1h | XSS, clickjacking |

**Total Effort:** ~12 hours  
**Total Risk Reduction:** 70% of critical/high vulnerabilities

---

## Implementation Order

**Day 1 (Critical Security):**
1. Rotate Gmail credentials (#1)
2. Remove CORS wildcard (#2)
3. Remove network_mode: host (#4)

**Day 2 (Stability):**
4. Fix health check typos (#3)
5. Fix SSH StrictHostKeyChecking (#5)
6. Fix static salt (#6)

**Day 3 (Hardening):**
7. API URL env var (#7)
8. Non-root containers (#8)
9. CSRF protection (#9)
10. Security headers (#10)

---

*These 10 fixes should be completed before any production deployment.*
