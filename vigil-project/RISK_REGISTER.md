# Vigil Dashboard - Risk Register

**Project:** Vigil Dashboard Security Monitoring System  
**Version:** 1.0  
**Date:** 2026-05-26  
**Status:** 🔴 CRITICAL - PRODUCTION DEPLOYMENT BLOCKED

---

## Executive Summary

This risk register documents **22 identified risks** across technical, security, schedule, and resource categories. **7 P0 (Critical) risks** must be resolved before production deployment. The project currently has an overall risk score of **8.7/10** (Critical), with security risks being the highest concern.

---

## Risk Classification Legend

### Probability
| Rating | Likelihood | Description |
|--------|------------|-------------|
| VH | Very High (81-100%) | Almost certain to occur |
| H | High (61-80%) | Likely to occur |
| M | Medium (41-60%) | May occur |
| L | Low (21-40%) | Unlikely to occur |
| VL | Very Low (0-20%) | Rare occurrence |

### Impact
| Rating | Description |
|--------|-------------|
| C | Critical - Business shutdown, data breach, regulatory fines |
| H | High - Significant delays, major rework, reputation damage |
| M | Medium - Minor delays, moderate costs, workarounds needed |
| L | Low - Minimal impact, easily mitigated |

### Risk Score
- **Risk Score = Probability × Impact**
- **Scale:** 1 (VL×L) to 25 (VH×C)
- **P0:** Score ≥ 15 (Critical - Block Production)
- **P1:** Score 8-14 (High - Resolve Before Launch)
- **P2:** Score 4-7 (Medium - Monitor)
- **P3:** Score 1-3 (Low - Accept)

---

## Risk Inventory

### 🔴 P0 CRITICAL RISKS (Block Production)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|------------|-------------|-------------|--------|-------|------------|-------|
| **R-SEC-001** | Security | **Exposed Gmail Credentials** - Hardcoded app password in docker-compose.yml (CVSS 9.8). Active credential visible in version control. | VH | C | 25 | 1. Rotate Gmail password immediately 2. Use Docker secrets/env vars 3. Scrub git history with BFG | Security Lead |
| **R-SEC-002** | Security | **Wildcard CORS with Credentials** - `allow_origins=['*']` + `allow_credentials=True` enables CSRF attacks from any domain (CVSS 9.1) | VH | C | 25 | 1. Restrict origins to explicit whitelist 2. Use environment-specific configs 3. Add preflight validation | Backend Lead |
| **R-SEC-003** | Security | **Static PBKDF2 Salt** - Hardcoded salt `vigil-static-salt-32bytes-long!` enables rainbow table attacks if DB compromised (CWE-759) | VH | C | 25 | 1. Generate random salt per encryption 2. Store salt alongside encrypted data 3. Migrate existing encrypted data | Security Lead |
| **R-DEV-001** | Technical | **network_mode: host** - Removes Docker network isolation, exposing containers to host network stack (CVSS 8.1) | VH | C | 25 | 1. Remove network_mode: host 2. Use explicit port mapping 3. Configure Docker internal DNS | DevOps Lead |
| **R-FRN-001** | Technical | **9 Hardcoded API URLs** - Internal IP (192.168.50.30) hardcoded in 9 frontend files prevents deployment flexibility | H | C | 20 | 1. Replace with env vars (REACT_APP_API_URL) 2. Use relative URLs as fallback 3. Update build pipeline | Frontend Lead |
| **R-FRN-002** | Security | **LocalStorage Credential Storage** - Router credentials stored in browser localStorage, XSS exposure risk | H | C | 20 | 1. Remove localStorage persistence 2. Use sessionStorage with cleanup 3. Implement secure token storage | Frontend Lead |
| **R-SEC-004** | Security | **JWT Auto-Generation Race Condition** - Secret file existence checked before write, permissions set after (CVSS 8.5) | H | C | 20 | 1. Remove auto-generation 2. Require explicit env var 3. Validate file ownership before use | Security Lead |

### 🟠 P1 HIGH RISKS (Resolve Before Launch)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|------------|-------------|-------------|--------|-------|------------|-------|
| **R-SEC-005** | Security | **Command Injection** - User-controlled IP addresses passed to subprocess without validation (CVSS 8.1) | M | C | 15 | 1. Validate IPs with ipaddress module 2. Reject non-private ranges 3. Use allowlist for commands | Backend Lead |
| **R-SEC-006** | Security | **XXE Vulnerability** - ET.fromstring() parses UPnP XML without security config (CWE-611) | M | C | 15 | 1. Use defusedxml.ElementTree 2. Disable external entities 3. Validate XML before parsing | Security Lead |
| **R-DEV-002** | Technical | **Containers Run as Root** - No USER directive in Dockerfiles enables privilege escalation (CVSS 7.1) | H | H | 16 | 1. Add non-root user (UID 1000) 2. Set proper file ownership 3. Test with read-only root fs | DevOps Lead |
| **R-DEV-003** | Technical | **Invalid Health Check Ports** - Typos (808000, 808080) cause health checks to fail, services marked unhealthy | VH | H | 20 | 1. Fix to valid ports (8000, 8080) 2. Add health check validation in CI 3. Use environment variables | DevOps Lead |
| **R-SEC-007** | Security | **Weak Fallback Encryption Key** - Predictable fallback key used if VIGIL_KEY not set | H | H | 16 | 1. Remove fallback key 2. Fail fast on startup if key missing 3. Add key validation | Security Lead |
| **R-FRN-003** | Security | **XSS via Unsanitized Content** - event.details, alert.description rendered without sanitization | M | C | 15 | 1. Implement DOMPurify sanitization 2. Use React's built-in escaping 3. Add CSP headers | Frontend Lead |
| **R-DEV-004** | Technical | **SSH Security Disabled** - StrictHostKeyChecking=no in CI/CD enables MITM attacks (CVSS 7.4) | H | H | 16 | 1. Remove SSH flags 2. Use ssh-keyscan for known_hosts 3. Use webfactory/ssh-agent action | DevOps Lead |
| **R-BCK-001** | Technical | **Hardcoded Database Paths** - Absolute paths to /home/erik-ross/ in 3+ files | H | H | 16 | 1. Use DATABASE_PATH env var 2. Validate path is within allowed directories 3. Add path constraints | Backend Lead |
| **R-SEC-008** | Security | **No CSRF Protection** - API client lacks CSRF tokens, cookie-based auth vulnerable | M | C | 15 | 1. Add CSRF token header 2. Implement cookie-based protection 3. Use SameSite=Strict | Security Lead |
| **R-SCH-001** | Schedule | **Phase 1 Security Blockers** - 15 hours of critical fixes may delay launch by 1-2 weeks | M | H | 12 | 1. Parallelize fix efforts 2. Add temporary compensating controls 3. Consider phased rollout | Project Manager |
| **R-RES-001** | Resource | **Zero Test Coverage** - Frontend has 0% tests, backend ~10% with production DB usage | H | H | 16 | 1. Add testing framework 2. Write critical path tests first 3. Use in-memory SQLite for tests | QA Lead |
| **R-SEC-009** | Security | **Authentication Bypass** - VIGIL_AUTH_DISABLED env var can disable auth in production | M | H | 12 | 1. Add production check 2. Log critical warning 3. Require explicit confirmation | Security Lead |
| **R-FRN-004** | Technical | **Dev Server in Production** - Dockerfile runs npm start instead of production build | M | H | 12 | 1. Use multi-stage build 2. Serve static files with nginx 3. Remove dev dependencies | Frontend Lead |
| **R-BCK-002** | Technical | **Monolithic Routers** - setup.py (800+ lines), security.py (600+ lines) violate SRP | M | H | 12 | 1. Split into focused modules 2. Extract shared utilities 3. Add interface contracts | Backend Lead |

### 🟡 P2 MEDIUM RISKS (Monitor)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|------------|-------------|-------------|--------|-------|------------|-------|
| **R-BCK-003** | Technical | **No Rate Limiting** - slowapi installed but unused, DoS risk | M | M | 9 | 1. Implement @limiter decorators 2. Add per-endpoint limits 3. Monitor for abuse | Backend Lead |
| **R-FRN-005** | Technical | **Inefficient Polling** - 10s intervals create unnecessary load, memory leaks | M | M | 9 | 1. Implement exponential backoff 2. Add AbortController 3. Consider WebSockets | Frontend Lead |
| **R-DEV-005** | Technical | **Unpinned Dependencies** - GitHub Actions @master, Docker images without digest | M | M | 9 | 1. Pin to specific versions/SHAs 2. Use dependabot for updates 3. Verify before deploy | DevOps Lead |
| **R-SCH-002** | Schedule | **Architecture Refactoring** - Phase 3 estimated 47 hours may extend timeline | M | M | 9 | 1. Prioritize critical modules 2. Defer non-essential splits 3. Incremental refactoring | Project Manager |
| **R-RES-002** | Resource | **Skill Gaps** - Security hardening requires specialized expertise | L | H | 8 | 1. Security training 2. External security audit 3. Hire security consultant | Project Manager |

### 🟢 P3 LOW RISKS (Accept)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|------------|-------------|-------------|--------|-------|------------|-------|
| **R-BCK-004** | Technical | **SQLite for Production** - Not suitable for concurrent workloads | L | M | 6 | 1. Plan PostgreSQL migration 2. Monitor performance 3. Add connection pooling | Backend Lead |
| **R-DEV-006** | Technical | **Multiple Compose Files** - 5+ competing configurations | L | M | 6 | 1. Consolidate configurations 2. Use environment-specific files 3. Document differences | DevOps Lead |
| **R-FRN-006** | Technical | **Accessibility Issues** - Missing labels, keyboard navigation | L | M | 6 | 1. Add ARIA attributes 2. Run axe-core audits 3. Manual accessibility testing | Frontend Lead |

---

## Risk Distribution

### By Category
```
Security:  ████████████████████████████ 9 risks (41%)
Technical: ████████████████████ 11 risks (50%)
Schedule:  ██ 2 risks (9%)
Resource:  ██ 2 risks (9%)
```

### By Priority
```
P0 Critical: ████████████████████████ 7 risks (32%)
P1 High:     ████████████████████████████████ 11 risks (50%)
P2 Medium:   █████ 5 risks (23%)
P3 Low:      ███ 3 risks (14%)
```

### By Probability
```
Very High: ████████████████ 5 risks (23%)
High:      ████████████████████████████ 9 risks (41%)
Medium:    ████████████████████ 7 risks (32%)
Low:       ██ 3 risks (14%)
```

---

## Risk Trends

### Pre-Mitigation (Current State)
- **Overall Risk Score:** 8.7/10 (Critical)
- **Critical Risks:** 7 open
- **Security Posture:** 4/10
- **Production Readiness:** NOT READY

### Post Phase 1 Mitigation (Target)
- **Overall Risk Score:** 5.2/10 (Moderate)
- **Critical Risks:** 0 open
- **Security Posture:** 6/10
- **Production Readiness:** CONDITIONAL

### Post Phase 2+ Mitigation (Target)
- **Overall Risk Score:** 2.8/10 (Low)
- **Critical Risks:** 0 open
- **Security Posture:** 8/10
- **Production Readiness:** READY

---

## Risk Owners

| Role | Responsibilities |
|------|------------------|
| **Security Lead** | All security-related risks (R-SEC-*) |
| **Backend Lead** | Backend architecture, database, API risks (R-BCK-*) |
| **Frontend Lead** | Frontend security, performance, UX risks (R-FRN-*) |
| **DevOps Lead** | Infrastructure, deployment, CI/CD risks (R-DEV-*) |
| **Project Manager** | Schedule, resource, dependency risks (R-SCH-*, R-RES-*) |
| **QA Lead** | Testing, quality assurance risks (R-RES-*) |

---

## Risk Review Schedule

| Review Type | Frequency | Participants |
|-------------|-----------|--------------|
| Daily Standup | Daily | All leads - blockers, new risks |
| Risk Review | Weekly | PM, Security, DevOps - trend analysis |
| Deep Dive | Bi-weekly | Full team - mitigation effectiveness |
| Pre-Release | Per milestone | All stakeholders - go/no-go decisions |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-26 | Risk Management Engineer | Initial risk register created based on code review findings |

---

## Related Documents

- [RISK_MITIGATION_PLAN.md](RISK_MITIGATION_PLAN.md) - Detailed mitigation strategies
- [SECURITY_RISKS.md](SECURITY_RISKS.md) - Security-specific risk analysis
- [CONTINGENCY_PLANS.md](CONTINGENCY_PLANS.md) - What-if scenario responses
- [MASTER_CODE_REVIEW.md](../vigil-code-review/MASTER_CODE_REVIEW.md) - Source findings
