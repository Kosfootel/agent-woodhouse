# Vigil Dashboard - Master Code Review Report

**Date:** 2026-05-26  
**Scope:** Backend, Frontend, DevOps/Infrastructure, Security  
**Status:** 🔴 **CRITICAL - IMMEDIATE ACTION REQUIRED**

---

## Executive Summary

The Vigil Dashboard project is a security-focused home network monitoring system with significant security vulnerabilities, architectural inconsistencies, and production readiness gaps. This consolidated review covers findings from 4 specialized code reviews spanning the entire codebase.

### Overall Assessment: ⚠️ **NOT PRODUCTION READY**

| Domain | Rating | Status | Critical Issues |
|--------|--------|--------|-----------------|
| **Security** | 4/10 | 🔴 Critical | 7 critical vulnerabilities |
| **Backend** | 6/10 | 🟡 Fair | 5 critical issues |
| **Frontend** | 6/10 | 🟡 Fair | 4 critical issues |
| **DevOps** | 5/10 | 🟡 Fair | 6 critical issues |

### Critical Findings Summary

- **7 CRITICAL security vulnerabilities** including exposed credentials, permissive CORS, and weak cryptography
- **20+ high-severity issues** across all domains
- **Multiple exposed credentials** in version control
- **Network isolation compromised** by `network_mode: host`
- **Zero test coverage** on frontend, minimal on backend

---

## 1. Critical Issues Summary (All Domains)

### 🔴 P0 - Block Production Deployment

| # | Issue | Domain | Severity | CVSS |
|---|-------|--------|----------|------|
| 1 | **Exposed Gmail App Password** in docker-compose.yml | Security/DevOps | Critical | 9.8 |
| 2 | **Wildcard CORS with credentials** - allows any origin | Security/Backend | Critical | 9.1 |
| 3 | **Hardcoded API URLs** with internal IPs (9 locations) | Frontend | Critical | - |
| 4 | **Static salt in PBKDF2** - enables rainbow tables | Security | High | 7.5 |
| 5 | **network_mode: host** - no network isolation | DevOps | Critical | 8.1 |
| 6 | **JWT auto-generation** with race conditions | Security | Critical | 8.5 |
| 7 | **Command injection** via subprocess in discovery | Security | High | 8.1 |
| 8 | **XXE vulnerability** in UPnP XML parsing | Security | High | 8.1 |
| 9 | **Health check typos** (808000/808080 ports) | DevOps | Critical | 7.5 |
| 10 | **Containers run as root** | DevOps | High | 7.1 |

---

## 2. Domain-Specific Findings

### 2.1 Backend (FastAPI + SQLAlchemy)

**Strengths:**
- ✅ FastAPI with dependency injection
- ✅ Abstract base classes for router implementations
- ✅ Async/await patterns used where appropriate

**Critical Issues:**
1. **Static salt in crypto.py** - `b'vigil-static-salt-32bytes-long!'` defeats PBKDF2
2. **Hardcoded database paths** - 3 files with `/home/erik-ross/...`
3. **Insecure CORS** - wildcard origins with credentials
4. **No rate limiting** - slowapi in requirements but unused
5. **SQL injection risk** - raw SQL with string concatenation

**Key Metrics:**
| Metric | Score | Notes |
|--------|-------|-------|
| Security | 4/10 | Multiple critical vulnerabilities |
| Code Quality | 6/10 | PEP 8 issues, inconsistent patterns |
| Architecture | 5/10 | Mixed patterns, tight coupling |
| Testing | 3/10 | ~10% coverage, test uses production DB |

**Files Requiring Immediate Attention:**
- `app/utils/crypto.py` - Static salt (CRITICAL)
- `app/main.py` - CORS wildcard (CRITICAL)
- `app/routers/admin.py` - Hardcoded DB path (CRITICAL)
- `app/routers/setup.py` - 800+ lines, mixed concerns (HIGH)
- `app/routers/security.py` - 600+ lines, monolithic (HIGH)

---

### 2.2 Frontend (React 18)

**Strengths:**
- ✅ React 18 with hooks
- ✅ React Router v7
- ✅ Clean component separation

**Critical Issues:**
1. **9 hardcoded API URLs** with internal IP (192.168.50.30)
2. **LocalStorage stores credentials** - setup progress may include router passwords
3. **No content sanitization** - XSS risk in EventTimeline, AlertPanel
4. **No CSRF protection** in API client

**Key Metrics:**
| Metric | Score | Notes |
|--------|-------|-------|
| Security | 5/10 | Hardcoded URLs, XSS risk, no CSRF |
| Performance | 6/10 | No lazy loading, inefficient polling |
| Accessibility | 4/10 | Missing labels, contrast issues |
| Testing | 0/10 | No tests found |

**Files Requiring Immediate Attention:**
- `api.js` - Hardcoded API_BASE_URL (CRITICAL)
- `SetupWizard.js` - 600+ lines, 5 hardcoded IPs (CRITICAL)
- `routerDiscovery.js` - LocalStorage credential storage (CRITICAL)
- `EventTimeline.js` - Unsanitized content rendering (HIGH)
- `Dockerfile` - Runs dev server, not production build (HIGH)

---

### 2.3 DevOps/Infrastructure

**Strengths:**
- ✅ Working CI/CD with GitHub Actions
- ✅ Multi-arch builds (amd64 + arm64)
- ✅ Automated rollback on deployment failure
- ✅ Trivy security scanning

**Critical Issues:**
1. **Exposed Gmail credentials** in docker-compose.yml (line 17)
2. **network_mode: host** - removes all network isolation
3. **Invalid healthcheck ports** - 808000 and 808080 (typos)
4. **SSH security disabled** - `StrictHostKeyChecking=no`
5. **Containers run as root** - privilege escalation risk
6. **No TLS/HTTPS** - all traffic unencrypted

**Key Metrics:**
| Metric | Score | Notes |
|--------|-------|-------|
| Security | 5/10 | Credentials exposed, host networking |
| Reliability | 6/10 | Health checks broken |
| Observability | 4/10 | No metrics, minimal logging |
| Maintainability | 4/10 | 5+ competing compose files |

**Files Requiring Immediate Attention:**
- `docker-compose.yml` - network_mode: host (CRITICAL)
- `poc-backend/docker-compose.yml` - Exposed credentials (CRITICAL)
- `docker-compose.yml.bak` - Invalid ports (CRITICAL)
- `.github/workflows/dashboard-deploy.yml` - SSH security disabled (HIGH)
- `backend/Dockerfile` - No USER directive (HIGH)

---

### 2.4 Security Deep-Dive

**Summary:**
7 critical vulnerabilities, 11 high-severity issues identified. Most severe are credential exposure and cryptographic weaknesses.

**Critical Vulnerabilities:**

| ID | CWE | Description | CVSS |
|----|-----|-------------|------|
| SEC-001 | CWE-798 | Hardcoded Gmail App Password | 9.8 |
| SEC-002 | CWE-942 | Wildcard CORS with credentials | 9.1 |
| SEC-003 | CWE-287 | JWT auto-generation race condition | 8.5 |
| SEC-004 | CWE-284 | network_mode: host | 8.1 |
| SEC-005 | CWE-78 | Command injection in device discovery | 8.1 |
| SEC-006 | CWE-611 | XXE in UPnP XML parsing | 8.1 |
| SEC-007 | CWE-759 | Static salt in PBKDF2 | 7.5 |

**Attack Vectors:**
1. **Credential Theft** - Exposed Gmail password, weak crypto
2. **CSRF/XSS** - Missing CSRF tokens, no CSP, unsanitized content
3. **Privilege Escalation** - Root containers, host network
4. **Man-in-the-Middle** - No TLS, SSH verification disabled
5. **Authentication Bypass** - VIGIL_AUTH_DISABLED env var

---

## 3. Cross-Cutting Concerns

### 3.1 Configuration Management

**Problem:** Inconsistent environment variable usage, hardcoded values scattered across codebase

**Impact:** 15+ files with hardcoded IPs, paths, or credentials

**Affected Areas:**
- Backend: CORS origins, database paths, fallback encryption key
- Frontend: API URLs in 9+ locations
- DevOps: SSH settings, health check URLs

### 3.2 Error Handling

**Problem:** Inconsistent error handling, information disclosure

**Examples:**
- `events.py:89` - Full exception details exposed to client
- Frontend errors only logged to console, users see empty states
- No standardized error response format

### 3.3 Testing

**Problem:** Near-zero test coverage

| Component | Coverage | Issues |
|-----------|----------|--------|
| Backend | ~10% | Tests use production database |
| Frontend | 0% | No test files found |
| E2E | 0% | No automated testing |

### 3.4 Documentation

**Problem:** Missing architectural documentation, inconsistent setup guides

- No high-level architecture diagram
- Multiple competing README files
- No API documentation beyond OpenAPI

### 3.5 Dependency Management

**Problem:** Unused dependencies, missing security updates

- **redis** - Installed but unused
- **slowapi** - In requirements but not implemented
- **argon2-cffi** - Not used (bcrypt preferred)
- Trivy scans don't fail pipeline on vulnerabilities

---

## 4. Risk Assessment Matrix

### Probability vs Impact

```
                    IMPACT
                Low    Med    High   Critical
            ┌──────┬──────┬──────┬─────────┐
       High │      │      │ ████ │ ███████ │  Command Injection
            ├──────┼──────┼──────┼─────────┤
Probability Med  │      │ ████ │ ██████ │ ███████ │  CORS, Static Salt
            ├──────┼──────┼──────┼─────────┤
       Low  │ ████ │ ████ │      │ ███████ │  Exposed Credentials
            └──────┴──────┴──────┴─────────┘
```

### Risk Scores

| Risk | Score | Items |
|------|-------|-------|
| **Data Breach** | 9.5/10 | Exposed creds, weak crypto, no TLS |
| **Unauthorized Access** | 8.5/10 | Wildcard CORS, auth bypass env var |
| **Privilege Escalation** | 7.5/10 | Root containers, host network |
| **Denial of Service** | 6.0/10 | No rate limiting, inefficient polling |
| **Data Integrity** | 5.5/10 | SQLite, no migrations |

---

## 5. Consolidated Priority Backlog

### Phase 1: Security Lockdown (Week 1) - BLOCKERS

| # | Task | Owner | Effort | Risk |
|---|------|-------|--------|------|
| 1.1 | Rotate exposed Gmail credentials | Security | 30m | Critical |
| 1.2 | Remove network_mode: host from all compose files | DevOps | 2h | Critical |
| 1.3 | Fix CORS wildcard configuration | Backend | 1h | Critical |
| 1.4 | Implement random salt in crypto.py | Backend | 2h | Critical |
| 1.5 | Replace hardcoded API URLs with env vars | Frontend | 2h | Critical |
| 1.6 | Remove credentials from LocalStorage | Frontend | 1h | Critical |
| 1.7 | Fix JWT secret auto-generation | Security | 2h | Critical |
| 1.8 | Validate IP addresses before subprocess | Security | 2h | High |
| 1.9 | Fix XXE vulnerability in XML parsing | Security | 2h | High |

**Phase 1 Total Effort:** ~15 hours

### Phase 2: Hardening (Weeks 2-3)

| # | Task | Owner | Effort |
|---|------|-------|--------|
| 2.1 | Run containers as non-root | DevOps | 2h |
| 2.2 | Implement TLS/HTTPS with Caddy | DevOps | 3h |
| 2.3 | Add CSRF protection | Security | 3h |
| 2.4 | Add content sanitization (DOMPurify) | Frontend | 2h |
| 2.5 | Implement rate limiting (slowapi) | Backend | 3h |
| 2.6 | Add input validation layer | Backend | 4h |
| 2.7 | Fix SSH security in CI/CD | DevOps | 1h |
| 2.8 | Standardize error handling | Backend | 3h |

**Phase 2 Total Effort:** ~21 hours

### Phase 3: Architecture & Quality (Weeks 4-6)

| # | Task | Owner | Effort |
|---|------|-------|--------|
| 3.1 | Split monolithic routers (security.py, setup.py) | Backend | 8h |
| 3.2 | Add Alembic database migrations | Backend | 4h |
| 3.3 | Refactor SetupWizard component | Frontend | 6h |
| 3.4 | Standardize Docker compose files | DevOps | 4h |
| 3.5 | Add comprehensive testing framework | All | 16h |
| 3.6 | Implement React Query for data fetching | Frontend | 4h |
| 3.7 | Add security headers middleware | Backend | 2h |
| 3.8 | Configure structured logging | Backend | 3h |

**Phase 3 Total Effort:** ~47 hours

### Phase 4: Production Readiness (Weeks 7-8)

| # | Task | Owner | Effort |
|---|------|-------|--------|
| 4.1 | Add Prometheus metrics | Backend | 4h |
| 4.2 | Set up Grafana dashboards | DevOps | 3h |
| 4.3 | Implement automated backups | DevOps | 4h |
| 4.4 | Add image signing with Cosign | DevOps | 3h |
| 4.5 | Create deployment runbook | DevOps | 3h |
| 4.6 | Load testing & performance tuning | All | 8h |

**Phase 4 Total Effort:** ~25 hours

---

## 6. Recommendations

### Immediate Actions (Before Any Deployment)

1. **🔴 ROTATE EXPOSED CREDENTIALS** - Gmail app password is compromised
2. **🔴 REMOVE network_mode: host** - Critical security boundary violation
3. **🔴 FIX CORS CONFIGURATION** - Never use wildcard with credentials
4. **🔴 IMPLEMENT RANDOM SALT** - Current static salt defeats encryption
5. **🔴 SANITIZE ALL USER INPUT** - XSS and command injection risks

### Short-term (1-2 Weeks)

6. Run all containers as non-root users
7. Implement TLS/HTTPS for all endpoints
8. Add CSRF protection to all state-changing endpoints
9. Standardize on environment variables for all configuration
10. Add security headers middleware

### Medium-term (1 Month)

11. Split monolithic routers into focused modules
12. Add database migrations with Alembic
13. Implement comprehensive test coverage (target 70%)
14. Add Prometheus metrics and Grafana dashboards
15. Create automated backup strategy

### Long-term (2-3 Months)

16. Migrate to PostgreSQL for production workloads
17. Implement full async database operations
18. Add WebSocket support for real-time updates
19. Consider microservices architecture for scale
20. Implement GitOps with ArgoCD or Flux

---

## 7. Appendix: Quick Reference

### Critical Files by Domain

**Backend:**
- `app/utils/crypto.py` - Encryption (CRITICAL)
- `app/main.py` - CORS, entry point
- `app/routers/setup.py` - Monolithic router
- `app/routers/security.py` - Monolithic router

**Frontend:**
- `src/api.js` - API client (CRITICAL)
- `src/components/setup/SetupWizard.js` - Wizard (CRITICAL)
- `src/lib/routerDiscovery.js` - LocalStorage (CRITICAL)
- `src/components/EventTimeline.js` - XSS risk

**DevOps:**
- `docker-compose.yml` - Network config (CRITICAL)
- `poc-backend/docker-compose.yml` - Credentials (CRITICAL)
- `.github/workflows/dashboard-deploy.yml` - SSH (HIGH)
- `backend/Dockerfile` - USER directive (HIGH)

### Environment Variables Required

```bash
# Security
VIGIL_JWT_SECRET=<32+ char random>
VIGIL_KEY=<encryption key>
VIGIL_CORS_ORIGINS=https://dashboard.example.com

# Database
DATABASE_PATH=/app/data/vigil.db

# Email
GMAIL_USER=<service account>
GMAIL_APP_PASSWORD=<app password>

# Frontend
REACT_APP_API_URL=https://api.example.com
```

---

## 8. Conclusion

The Vigil Dashboard project shows promise with its security-focused monitoring features, but **requires significant hardening before production deployment**. The combination of exposed credentials, weak cryptography, and network isolation violations creates unacceptable risk.

**Recommendation:** 
- **DO NOT DEPLOY** to production until Phase 1 security blockers are resolved
- Allocate 2-3 weeks for security hardening before any public exposure
- Budget 2-3 months for full production readiness

---

*Report compiled by Technical Lead Agent*  
*Based on reviews by: Backend Reviewer, Frontend Reviewer, DevOps Reviewer, Security Auditor*