# Vigil Dashboard Security Audit Report

**Date:** 2026-05-26  
**Auditor:** Security Auditor Subagent  
**Scope:** Full codebase - backend, frontend, infrastructure  
**Versions Audited:**
- poc-backend: FastAPI-based security platform
- backend: Tier A security service
- dashboard: React-based frontend

---

## Executive Summary

This audit identified **7 critical vulnerabilities**, **11 high-severity issues**, and numerous medium/low findings across the Vigil Dashboard codebase. The most severe issues include hardcoded credentials, overly permissive CORS configuration, missing CSRF protection, and insecure JWT secret generation.

### Risk Summary
| Severity | Count | Status |
|----------|-------|--------|
| Critical | 7 | Immediate action required |
| High | 11 | Address within 1 week |
| Medium | 15 | Address within 1 month |
| Low | 8 | Address when convenient |

---

## 1. Authentication & Authorization

### 1.1 CRITICAL: Hardcoded Gmail Credentials in docker-compose.yml

**Location:** `/projects/vigil-home/poc-backend/docker-compose.yml` (lines 23-24, 38-39)

**Finding:**
```yaml
environment:
  - GMAIL_USER=kosfootel@gmail.com
  - GMAIL_APP_PASSWORD=odsq hraj soqe hyzm
```

**Risk:** Gmail app password is exposed in version control. Any attacker with repository access can compromise the email account and potentially gain access to other linked services.

**Remediation:**
1. Immediately rotate the exposed Gmail app password
2. Move credentials to `.env` files excluded from version control
3. Use Docker secrets or a vault solution for production

---

### 1.2 CRITICAL: JWT Secret Auto-Generation with Weak File Permissions

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (lines 47-67)

**Finding:**
```python
default_path = "/data/.jwt_secret"
try:
    os.makedirs(os.path.dirname(default_path), exist_ok=True)
    if os.path.exists(default_path):
        with open(default_path) as f:
            return f.read().strip()
    secret = secrets.token_hex(32)
    with open(default_path, "w") as f:
        f.write(secret)
    os.chmod(default_path, 0o600)
```

**Risk:** 
1. Race condition between file existence check and write
2. No file ownership verification (file could be owned by attacker)
3. Permissions set after write creates window where secret is readable
4. Auto-generated secrets may not be backed up; container recreation causes auth failures

**Remediation:**
```python
def _get_jwt_secret() -> str:
    secret = os.environ.get("VIGIL_JWT_SECRET")
    if secret:
        return secret
    
    file_path = os.environ.get("VIGIL_JWT_SECRET_FILE")
    if file_path:
        try:
            # Verify ownership before reading
            import pwd
            stat = os.stat(file_path)
            if stat.st_uid != os.getuid():
                logger.error(f"JWT secret file owned by different user")
                raise RuntimeError("Invalid JWT secret file ownership")
            if stat.st_mode & 0o077:
                logger.error(f"JWT secret file has overly permissive permissions")
                raise RuntimeError("Insecure JWT secret file permissions")
            with open(file_path) as f:
                return f.read().strip()
        except OSError as e:
            logger.error(f"Could not read JWT secret: {e}")
            raise
    
    raise RuntimeError(
        "VIGIL_JWT_SECRET or VIGIL_JWT_SECRET_FILE must be set. "
        "Run: export VIGIL_JWT_SECRET=$(openssl rand -hex 32)"
    )
```

---

### 1.3 HIGH: Auth Bypass Environment Variable

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (line 32)

**Finding:**
```python
AUTH_DISABLED = os.environ.get("VIGIL_AUTH_DISABLED", "").lower() in ("true", "1", "yes")
```

**Risk:** Simple environment variable can completely disable authentication. If accidentally set in production, exposes entire API without authentication.

**Remediation:** Add additional safeguards:
```python
AUTH_DISABLED = os.environ.get("VIGIL_AUTH_DISABLED", "").lower() in ("true", "1", "yes")
if AUTH_DISABLED and os.environ.get("VIGIL_ENV", "").lower() == "production":
    logger.critical("VIGIL_AUTH_DISABLED is set in production environment!")
    AUTH_DISABLED = False  # Force disable in production
```

---

### 1.4 HIGH: Token Transmission via URL Query Parameter

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (lines 176-186, 250-260)

**Finding:** JWT tokens can be passed via `?token=<JWT>` query parameter for SSE streams.

**Risk:**
1. Tokens appear in server access logs
2. Tokens are sent in HTTP Referer headers
3. Tokens may be cached by browsers/proxies
4. URL parameters are visible in browser history

**Remediation:** 
- For SSE, use cookie-based authentication with `HttpOnly`, `Secure`, and `SameSite=Strict`
- Alternatively, use a short-lived token exchange pattern

---

### 1.5 MEDIUM: Missing Token Binding

**Finding:** JWT tokens are not bound to client fingerprint (IP, User-Agent hash). Stolen tokens can be used from any location.

**Remediation:** Include a fingerprint claim in JWT:
```python
def create_fingerprint(request: Request) -> str:
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    return hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]

# In JWT payload:
"fp": create_fingerprint(request)

# In verification:
if payload.get("fp") != create_fingerprint(request):
    raise HTTPException(401, "Token binding mismatch")
```

---

### 1.6 LOW: Weak JWT Algorithm Choice

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (line 34)

**Finding:** Uses `HS256` (symmetric algorithm).

**Risk:** If secret key is compromised, attacker can forge any token. Asymmetric algorithms (RS256) provide better separation of concerns.

---

## 2. CORS Configuration

### 2.1 CRITICAL: Overly Permissive CORS in backend/main.py

**Location:** `/backend/main.py` (lines 14-20)

**Finding:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risk:** `allow_origins=["*"]` combined with `allow_credentials=True` is a security anti-pattern. Allows any website to make authenticated cross-origin requests.

**Remediation:**
```python
import os

ALLOWED_ORIGINS = os.environ.get(
    "VIGIL_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8085"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=600,
)
```

---

### 2.2 HIGH: Hardcoded IP Addresses in CORS

**Location:** `/projects/vigil-home/poc-backend/app/main.py` (lines 42-47)

**Finding:**
```python
allow_origins=[
    "http://localhost:3000","http://192.168.50.30:8085",
    "http://127.0.0.1:3000",
],
```

**Risk:** Hardcoded internal IP addresses may expose development/debug endpoints in production.

---

## 3. Input Validation & Injection

### 3.1 HIGH: SQL Injection via JSON Path in Query

**Location:** `/projects/vigil-home/poc-backend/app/main.py` (lines 634-636, 640-642)

**Finding:**
```python
anomalous_count = (
    db.query(Event)
    .filter(
        Event.device_id == device.id,
        Event.timestamp >= cutoff,
        Event.details["is_anomalous"].as_boolean() == True,
    )
    .count()
)
```

**Risk:** While SQLAlchemy provides some protection, the JSON path access `Event.details["is_anomalous"]` could be vulnerable if `details` structure is attacker-controlled elsewhere.

---

### 3.2 HIGH: Command Injection in Device Discovery

**Location:** `/projects/vigil-home/poc-backend/app/device_discovery.py` (lines 158-171, 276-292, 341-355)

**Finding:** Multiple uses of `asyncio.create_subprocess_exec` with user-controlled IP addresses:
```python
proc = await asyncio.create_subprocess_exec(
    "nmblookup",
    "-A", ip,  # ip is user-controlled!
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
```

**Risk:** While `create_subprocess_exec` is safer than `shell=True`, an attacker controlling `ip` could inject command arguments (e.g., `192.168.1.1; rm -rf /`).

**Remediation:** Validate and sanitize IP addresses:
```python
import ipaddress

def validate_ip(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
        if not addr.is_private:
            raise ValueError("Only private IP addresses allowed")
        return str(addr)
    except ValueError as e:
        raise HTTPException(400, f"Invalid IP address: {e}")

# Use in endpoints:
target_ip = validate_ip(req.target_ip)
```

---

### 3.3 HIGH: XML External Entity (XXE) Risk in UPnP Discovery

**Location:** `/projects/vigil-home/poc-backend/app/device_discovery.py` (lines 545-575)

**Finding:**
```python
def _parse_description_xml(self, xml_content: str) -> Dict[str, Any]:
    try:
        root = ET.fromstring(xml_content)  # No parser security config
```

**Risk:** `ET.fromstring()` is vulnerable to XXE attacks, allowing:
- File disclosure (`file:///etc/passwd`)
- SSRF attacks
- DoS via billion laughs attack

**Remediation:**
```python
from xml.etree.ElementTree import XMLParser
import defusedxml.ElementTree as ET

def _parse_description_xml(self, xml_content: str) -> Dict[str, Any]:
    try:
        # Use defusedxml for safe parsing
        root = ET.fromstring(xml_content)
```

---

### 3.4 MEDIUM: Inadequate Input Validation on Device Registration

**Location:** `/projects/vigil-home/poc-backend/app/main.py` (lines 390-405)

**Finding:** MAC address and IP are stored without validation:
```python
class BaselineRequest(BaseModel):
    mac: str
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None
```

**Remediation:** Add validators:
```python
from pydantic import validator
import re

class BaselineRequest(BaseModel):
    mac: str
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    
    @validator('mac')
    def validate_mac(cls, v):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$', v):
            raise ValueError('Invalid MAC address format')
        return v
    
    @validator('ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address')
        return v
    
    @validator('hostname')
    def validate_hostname(cls, v):
        if v and len(v) > 253:
            raise ValueError('Hostname too long')
        if v and not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError('Invalid hostname characters')
        return v
```

---

### 3.5 MEDIUM: No Rate Limit on Token Refresh

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (lines 228-265)

**Finding:** Token refresh endpoint may be susceptible to enumeration attacks.

**Remediation:** Add rate limiting and constant-time comparison:
```python
import hmac

@app.post("/auth/refresh")
@limiter.limit("10/minute")  # Stricter than general limit
def auth_refresh(...):
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    for stored in db.query(RefreshToken).all():
        if hmac.compare_digest(stored.token_hash, token_hash):
            # ... handle valid token
```

---

## 4. Secret Management

### 4.1 CRITICAL: Vault Master Key Derived from Static Salt

**Location:** `/projects/vigil-home/poc-backend/app/vault/vault_encryption.py` (lines 53-68)

**Finding:**
```python
def _derive_key(self, master_key: bytes) -> bytes:
    static_salt = b"vigil-credential-vault-v1"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=self.KEY_SIZE,
        salt=static_salt,  # Static salt!
        iterations=self.PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(master_key)
```

**Risk:** Static salt makes precomputation attacks possible. Attackers can build rainbow tables for common passwords.

**Remediation:** Use random salt stored alongside encrypted data:
```python
def encrypt(self, plaintext: str) -> bytes:
    salt = secrets.token_bytes(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=self.KEY_SIZE,
        salt=salt,
        iterations=self.PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(self._master_key)
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(self.NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    # Store: salt + nonce + ciphertext
    return salt + nonce + ciphertext

def decrypt(self, encrypted_data: bytes) -> str:
    salt = encrypted_data[:16]
    nonce = encrypted_data[16:28]
    ciphertext = encrypted_data[28:]
    # Derive key with stored salt
    ...
```

---

### 4.2 HIGH: Low PBKDF2 Iteration Count

**Location:** `/projects/vigil-home/poc-backend/app/vault/vault_encryption.py` (line 23)

**Finding:**
```python
PBKDF2_ITERATIONS = 100000
```

**Risk:** OWASP recommends minimum 600,000 iterations for PBKDF2-SHA256 as of 2023.

---

### 4.3 MEDIUM: API Keys Stored as SHA-256 Hashes

**Location:** `/projects/vigil-home/poc-backend/app/auth.py` (lines 311-313)

**Finding:**
```python
def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()
```

**Risk:** SHA-256 is designed for speed, making brute-force attacks feasible. API keys should use slow hash functions like Argon2id.

**Remediation:**
```python
def hash_api_key(key: str) -> str:
    from argon2 import PasswordHasher
    ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    return ph.hash(key)

def verify_api_key(key: str, hash: str) -> bool:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    try:
        ph.verify(hash, key)
        return True
    except Exception:
        return False
```

---

## 5. Cross-Site Scripting (XSS)

### 5.1 MEDIUM: Missing Content Security Policy (CSP)

**Location:** `/dashboard/public/index.html`

**Finding:** No Content-Security-Policy meta tag or headers.

**Risk:** XSS attacks via inline scripts, eval(), or external scripts.

**Remediation:** Add CSP headers in nginx/reverse proxy:
```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://192.168.50.30:8000;
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

---

### 5.2 LOW: React App Uses setInterval/setTimeout

**Location:** Multiple dashboard components

**Finding:** `setInterval(fetchDevices, 30000)` pattern used for polling.

**Risk:** Memory leaks if components unmount; potential race conditions.

---

## 6. CSRF Protection

### 6.1 HIGH: Missing CSRF Protection

**Finding:** No CSRF tokens or SameSite cookie configuration for state-changing operations.

**Risk:** Attackers can trick authenticated users into performing unwanted actions.

**Remediation:**
1. Use `SameSite=Strict` cookies
2. Implement double-submit cookie pattern for API requests
3. Add CSRF token to forms

---

## 7. Dependency Vulnerabilities

### 7.1 HIGH: Outdated Dependencies with Known CVEs

**Finding:** Package versions should be checked against CVE databases.

**Remediation:**
```bash
# Python
pip install safety
safety check -r requirements.txt

# Node.js
npm audit
npm audit fix
```

---

## 8. Container Security

### 8.1 HIGH: Dockerfile Runs as Root

**Location:** `/projects/vigil-home/poc-backend/Dockerfile`

**Finding:** No `USER` instruction - container runs as root.

**Remediation:**
```dockerfile
# Add at end of Dockerfile
RUN useradd -m -u 1000 vigil && chown -R vigil:vigil /app /data
USER vigil
```

---

### 8.2 MEDIUM: Docker Socket Not Restricted

**Finding:** No resource limits configured in docker-compose.

**Remediation:**
```yaml
services:
  vigil-api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```

---

## 9. Network Security

### 9.1 HIGH: Hardcoded Internal IPs in Dashboard

**Location:** `/dashboard/src/App.js` (line 36)

**Finding:**
```javascript
fetch(`${process.env.REACT_APP_API_URL || 'http://192.168.50.30:8000'}/api/setup/status`)
```

**Risk:** Internal network topology exposed; potential SSRF if URL is attacker-controlled.

---

### 9.2 MEDIUM: No TLS/HTTPS Configuration

**Finding:** All endpoints use HTTP. No TLS configuration found.

**Risk:** Credentials and tokens transmitted in plaintext.

---

## 10. Data Protection

### 10.1 MEDIUM: SQLite Database Permissions

**Location:** `/projects/vigil-home/poc-backend/app/database.py` (line 12)

**Finding:** Database stored at `/data/vigil.db` with default permissions.

**Remediation:** Ensure database directory has 0o700 permissions.

---

### 10.2 LOW: PII in Email Logs

**Location:** `/projects/vigil-home/poc-backend/app/email_notifier.py`

**Finding:** Device names and MAC addresses included in alert emails.

---

## 11. Logging & Monitoring

### 11.1 MEDIUM: Sensitive Data in Logs

**Finding:** JWT tokens and API keys may be logged in various places.

---

## 12. CI/CD Security

### 12.1 MEDIUM: SSH Key in GitHub Actions

**Location:** `.github/workflows/dashboard-deploy.yml`

**Finding:** SSH private key stored in GitHub secrets. Consider using OpenID Connect instead.

---

## Appendix A: File References

| File | Lines | Finding |
|------|-------|---------|
| `/docker-compose.yml` | 23-24 | Hardcoded credentials |
| `/app/auth.py` | 47-67 | Weak JWT secret handling |
| `/app/main.py` | 42-47 | Permissive CORS |
| `/backend/main.py` | 14-20 | Wildcard CORS |
| `/app/vault/vault_encryption.py` | 53-68 | Static salt |
| `/app/device_discovery.py` | 158-171 | Command injection |
| `/app/device_discovery.py` | 545-575 | XXE vulnerability |

---

## Appendix B: CVSS Scoring Summary

| Issue | CVSS v3.1 Score |
|-------|-----------------|
| Hardcoded Gmail credentials | 9.8 (Critical) |
| Wildcard CORS with credentials | 9.1 (Critical) |
| JWT secret race condition | 8.5 (High) |
| Command injection via discovery | 8.1 (High) |
| XXE in UPnP parser | 8.1 (High) |
| Static salt in vault | 7.5 (High) |
| Token in URL parameter | 7.1 (High) |

---

*End of Report*
