# Vigil Dashboard - Security Risk Assessment

**Project:** Vigil Dashboard Security Monitoring System  
**Version:** 1.0  
**Date:** 2026-05-26  
**Classification:** CONFIDENTIAL - Contains Security Findings

---

## Executive Summary

The Vigil Dashboard security assessment has identified **9 critical security risks** and **11 high-severity vulnerabilities** that must be addressed before production deployment. The current security posture is **4/10** with an overall risk score of **CRITICAL**.

**Immediate Actions Required:**
1. Rotate exposed Gmail credentials within 24 hours
2. Remove wildcard CORS configuration
3. Implement random salt generation
4. Validate all user inputs before subprocess execution
5. Remove network_mode: host from all deployments

---

## Security Risk Matrix

```
                    IMPACT
              Low    Med    High   Critical
         ┌──────┬──────┬──────┬─────────┐
    High │      │      │ SEC5 │ SEC1-4 │  Credentials, CORS, Salt, JWT
         ├──────┼──────┼──────┼─────────┤
Prob Med │      │ SEC9 │ SEC6 │ SEC7-8 │  XXE, Injection
         ├──────┼──────┼──────┼─────────┤
    Low  │      │      │ SEC10│ SEC11  │  Auth bypass
         └──────┴──────┴──────┴─────────┘
```

---

## Critical Security Risks (P0)

### SEC-001: Exposed Gmail Credentials

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-001 |
| **CWE** | CWE-798: Use of Hard-coded Credentials |
| **CVSS Score** | 9.8 (Critical) |
| **Location** | `projects/vigil-home/poc-backend/docker-compose.yml:17` |
| **Probability** | Very High |
| **Impact** | Critical |

**Description:**
Gmail App Password `odsq hraj soqe hyzm` is hardcoded in docker-compose.yml and committed to version control. This is an active credential that can be used to access the Gmail account.

**Attack Scenario:**
1. Attacker discovers credentials in public/private repository
2. Attacker gains access to Gmail account
3. Attacker can read emails, send phishing, or pivot to linked accounts
4. Potential for lateral movement within the organization

**Remediation Priority:**
- [ ] **P0 - Immediate (0-24 hours):** Rotate credential
- [ ] **P0 - Immediate (0-24 hours):** Remove from version control
- [ ] **P1 - High (1-3 days):** Scrub git history
- [ ] **P1 - High (1-3 days):** Implement secrets management

**Compensating Controls (Temporary):**
- Enable 2FA on Gmail account
- Review Gmail security audit log
- Monitor for unauthorized access
- Consider Gmail IP allowlisting

**Verification:**
```bash
# Verify credential removal
grep -r "odsq hraj soqe hyzm" .
git log --all --full-history -- "**/docker-compose.yml"
```

---

### SEC-002: Wildcard CORS with Credentials

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-002 |
| **CWE** | CWE-942: Permissive Cross-domain Policy |
| **CVSS Score** | 9.1 (Critical) |
| **Location** | `backend/main.py:14` |
| **Probability** | Very High |
| **Impact** | Critical |

**Description:**
CORS configuration allows origins `["*"]` with `allow_credentials=True`, allowing any website to make authenticated cross-origin requests to the API.

**Attack Scenario:**
1. Attacker creates malicious website
2. Victim visits malicious site while authenticated to Vigil Dashboard
3. Malicious site makes authenticated requests to Vigil API
4. Attacker exfiltrates data or performs actions as victim

**Remediation Priority:**
- [ ] **P0 - Immediate (0-24 hours):** Replace wildcard with explicit origins
- [ ] **P1 - High (1-3 days):** Implement environment-specific CORS configs

**Fix Implementation:**
```python
# Before (VULNERABLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)

# After (SECURE)
import os
allowed_origins = os.getenv("VIGIL_CORS_ORIGINS", 
    "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### SEC-003: Static Salt in PBKDF2

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-003 |
| **CWE** | CWE-759: Use of One-Way Hash without Salt |
| **CVSS Score** | 7.5 (High) |
| **Location** | `app/utils/crypto.py:17` |
| **Probability** | Very High |
| **Impact** | Critical |

**Description:**
Static salt `vigil-static-salt-32bytes-long!` defeats the purpose of PBKDF2 key derivation. If database is compromised, rainbow table attacks become possible.

**Attack Scenario:**
1. Database breach exposes encrypted credentials
2. Attacker pre-computes rainbow tables using known salt
3. Attacker rapidly decrypts credentials
4. Credential stuffing attacks against other systems

**Remediation:**
```python
import secrets
import base64

def encrypt_credential(plaintext: str, key: bytes) -> str:
    """Encrypt with random salt per credential."""
    salt = secrets.token_bytes(16)  # Random salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,  # OWASP 2023 recommendation
    )
    derived_key = kdf.derive(key)
    
    # Encrypt and store salt alongside ciphertext
    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv))
    ciphertext = cipher.encrypt(plaintext.encode())
    
    # Format: base64(salt + iv + ciphertext + tag)
    return base64.b64encode(salt + iv + ciphertext + tag).decode()
```

**Migration Plan:**
1. Backup all encrypted data
2. Decrypt with old static salt
3. Re-encrypt with random salt
4. Update storage format to include salt
5. Test decryption round-trip

---

### SEC-004: JWT Auto-Generation Race Condition

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-004 |
| **CWE** | CWE-362: Concurrent Execution using Shared Resource |
| **CVSS Score** | 8.5 (High) |
| **Location** | `projects/vigil-home/poc-backend/app/auth.py:47` |
| **Probability** | High |
| **Impact** | Critical |

**Description:**
JWT secret file creation has a race condition. File existence is checked before write, permissions set after write. Multi-container startup can create multiple secrets.

**Remediation:**
```python
# Before (VULNERABLE - auto-generation)
if not os.path.exists(secret_file):
    with open(secret_file, 'w') as f:
        f.write(secrets.token_urlsafe(32))
    os.chmod(secret_file, 0o600)

# After (SECURE - explicit configuration)
import sys

JWT_SECRET = os.getenv("VIGIL_JWT_SECRET")
if not JWT_SECRET:
    print("ERROR: VIGIL_JWT_SECRET environment variable required", 
          file=sys.stderr)
    sys.exit(1)
    
if len(JWT_SECRET) < 32:
    print("ERROR: VIGIL_JWT_SECRET must be at least 32 characters",
          file=sys.stderr)
    sys.exit(1)
```

---

## High Severity Security Risks (P1)

### SEC-005: Command Injection via Subprocess

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-005 |
| **CWE** | CWE-78: OS Command Injection |
| **CVSS Score** | 8.1 (High) |
| **Location** | `app/device_discovery.py:158, 276, 341` |

**Vulnerable Code:**
```python
# VULNERABLE - user-controlled IP passed directly
subprocess.run(["avahi-browse", "-t", "-r", f"_ssh._tcp,{ip}"])
subprocess.run(["nmblookup", "-A", ip])
subprocess.run(["snmpget", "-v2c", "-c", "public", ip, "1.3.6.1.2.1.1.1.0"])
```

**Attack Scenario:**
```python
# Malicious input
device_ip = "192.168.1.1; cat /etc/passwd"
# Results in command injection
```

**Remediation:**
```python
import ipaddress
from typing import Optional

def validate_private_ip(ip: str) -> Optional[str]:
    """Validate IP is private and well-formed."""
    try:
        addr = ipaddress.ip_address(ip)
        if not addr.is_private:
            return None
        return str(addr)
    except ValueError:
        return None

def safe_scan_ip(ip: str):
    """Scan with validated IP only."""
    validated = validate_private_ip(ip)
    if not validated:
        raise ValueError(f"Invalid or non-private IP: {ip}")
    
    # Now safe to use in subprocess
    subprocess.run(["ping", "-c", "1", "-W", "2", validated], 
                   capture_output=True, check=True)
```

---

### SEC-006: XXE Vulnerability

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-006 |
| **CWE** | CWE-611: XML External Entity Processing |
| **CVSS Score** | 8.1 (High) |
| **Location** | `app/device_discovery.py:550` |

**Vulnerable Code:**
```python
# VULNERABLE - parses XML without security config
root = ET.fromstring(xml_content)
```

**Remediation:**
```python
# Option 1: Use defusedxml (recommended)
from defusedxml import ElementTree as ET
root = ET.fromstring(xml_content)

# Option 2: Configure secure parser
import xml.etree.ElementTree as ET
parser = ET.XMLParser(resolve_entities=False, 
                      forbid_external=True,
                      forbid_dtd=True)
root = ET.fromstring(xml_content, parser=parser)
```

---

### SEC-007: Weak Fallback Encryption Key

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-007 |
| **CWE** | CWE-798: Hard-coded Credentials |
| **CVSS Score** | 7.5 (High) |
| **Location** | `app/utils/crypto.py:20` |

**Remediation:**
```python
# Before (VULNERABLE)
key_env = os.getenv('VIGIL_KEY', 'fallback-key-32bytes-long!!!!!')

# After (SECURE)
key_env = os.getenv('VIGIL_KEY')
if not key_env:
    raise RuntimeError(
        "VIGIL_KEY environment variable is required. "
        "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
```

---

### SEC-008: No CSRF Protection

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-008 |
| **CWE** | CWE-352: Cross-Site Request Forgery |
| **CVSS Score** | 6.5 (Medium) |
| **Location** | Frontend API client |

**Remediation:**
```javascript
// Add CSRF token to API client
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'X-CSRF-Token': getCsrfToken(), // From cookie or meta tag
  },
  withCredentials: true,
});

// Backend: Validate CSRF token
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

async def validate_csrf(request: Request):
    token = request.headers.get("X-CSRF-Token")
    cookie_token = request.cookies.get("csrf_token")
    if token != cookie_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
```

---

### SEC-009: Authentication Bypass

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-009 |
| **CWE** | CWE-287: Improper Authentication |
| **CVSS Score** | 6.5 (Medium) |
| **Location** | `app/auth.py:32` |

**Vulnerable Code:**
```python
if os.getenv("VIGIL_AUTH_DISABLED"):
    return True  # Authentication bypass
```

**Remediation:**
```python
import os

# Secure implementation
VIGIL_ENV = os.getenv("VIGIL_ENV", "production")
AUTH_DISABLED = os.getenv("VIGIL_AUTH_DISABLED", "false").lower() == "true"

if AUTH_DISABLED:
    if VIGIL_ENV == "production":
        logger.critical("AUTH_DISABLED attempted in production - rejected")
        raise RuntimeError("Cannot disable auth in production")
    logger.warning("Authentication disabled - development mode only")
```

---

### SEC-010: XSS via Unsanitized Content

| Attribute | Details |
|-----------|---------|
| **Risk ID** | R-SEC-010 |
| **CWE** | CWE-79: Cross-site Scripting |
| **CVSS Score** | 6.1 (Medium) |
| **Location** | `EventTimeline.js:83`, `AlertsPage.js:81`, `AlertPanel.js:115` |

**Remediation:**
```javascript
// Install: npm install dompurify
import DOMPurify from 'dompurify';

// Before (VULNERABLE)
<div>{event.details}</div>

// After (SECURE)
<div dangerouslySetInnerHTML={{ 
  __html: DOMPurify.sanitize(event.details) 
}} />

// Or better - use React's automatic escaping
<div>{event.details}</div> // Safe by default in React
```

---

### SEC-011: JWT Transmission via URL Parameter

| Attribute | Details |
|-----------|---------|
| **CWE** | CWE-598: Information Exposure in Query String |
| **CVSS Score** | 5.3 (Medium) |
| **Location** | `app/auth.py:180` |

**Risk:** Token exposed in server logs, browser history, referer headers.

**Remediation:**
```python
# Use cookies with HttpOnly, Secure, SameSite for SSE
response.set_cookie(
    "access_token",
    token,
    httponly=True,
    secure=True,
    samesite="Strict",
    max_age=3600
)
```

---

## Security Testing Gates

### Pre-Commit Gate
- [ ] No credentials in code (git-secrets)
- [ ] No hardcoded IPs
- [ ] Bandit security scan passes
- [ ] ESLint security rules pass

### CI/CD Gate
- [ ] Trivy container scan - no critical/high vulnerabilities
- [ ] Snyk dependency scan passes
- [ ] OWASP ZAP baseline scan
- [ ] SonarQube security hotspots reviewed

### Pre-Production Gate
- [ ] Penetration test completed
- [ ] Security review sign-off
- [ ] Incident response plan ready
- [ ] Security monitoring configured

### Production Gate
- [ ] WAF rules active
- [ ] SIEM integration complete
- [ ] Security dashboards operational
- [ ] On-call rotation established

---

## Vulnerability Remediation Priorities

### Immediate (24 hours)
1. **SEC-001:** Rotate Gmail credentials
2. **SEC-002:** Fix CORS wildcard
3. **SEC-004:** Remove JWT auto-generation

### Short-term (1 week)
4. **SEC-003:** Implement random salt
5. **SEC-005:** Fix command injection
6. **SEC-006:** Fix XXE vulnerability
7. **SEC-007:** Remove fallback encryption key

### Medium-term (2-4 weeks)
8. **SEC-008:** Add CSRF protection
9. **SEC-009:** Prevent auth bypass
10. **SEC-010:** Add XSS protection
11. **SEC-011:** Secure token transmission

---

## Compensating Controls

Until vulnerabilities are remediated:

| Risk | Compensating Control | Effectiveness |
|------|---------------------|---------------|
| SEC-001 | Gmail 2FA + IP allowlisting | Medium |
| SEC-002 | WAF with CORS rules | Low |
| SEC-003 | Database encryption at rest | Low |
| SEC-004 | File permissions monitoring | Medium |
| SEC-005 | Network segmentation | Medium |
| SEC-006 | XML input size limits | Low |
| SEC-007 | Env var validation | Medium |

---

## Security Metrics Dashboard

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Critical Vulnerabilities | 7 | 0 | 🔴 |
| High Vulnerabilities | 11 | ≤ 2 | 🔴 |
| Security Score | 4/10 | ≥ 7/10 | 🔴 |
| Credentials Exposed | 2 | 0 | 🔴 |
| Test Coverage | ~5% | ≥ 70% | 🔴 |
| Mean Time to Patch | - | ≤ 24h | ⚪ |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-26 | Risk Management Engineer | Initial security risk assessment |

---

## Related Documents

- [RISK_REGISTER.md](RISK_REGISTER.md) - Complete risk inventory
- [RISK_MITIGATION_PLAN.md](RISK_MITIGATION_PLAN.md) - Mitigation strategies
- [CONTINGENCY_PLANS.md](CONTINGENCY_PLANS.md) - Incident response scenarios
