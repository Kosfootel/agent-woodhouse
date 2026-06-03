# Vigil Dashboard - Risk Mitigation Plan

**Project:** Vigil Dashboard Security Monitoring System  
**Version:** 1.0  
**Date:** 2026-05-26  
**Status:** 🔴 CRITICAL - IMMEDIATE ACTION REQUIRED

---

## Executive Summary

This mitigation plan provides actionable strategies for the **22 identified risks** in the Vigil Dashboard project. The plan is organized by risk category and includes preventive actions, contingency plans, triggers, and monitoring approaches. **Phase 1 (Security Lockdown) must be completed before any production deployment.**

**Mitigation Investment:**
- Phase 1 (Blockers): ~15 hours
- Phase 2 (Hardening): ~21 hours
- Phase 3 (Architecture): ~47 hours
- Phase 4 (Production): ~25 hours
- **Total Estimated Effort:** 108 hours (~3 weeks with 2 engineers)

---

## Phase 1: Security Lockdown (Week 1) - CRITICAL

### Objective
Eliminate all P0 critical risks that block production deployment.

### Preventive Actions

| Risk ID | Action | Owner | Effort | Dependencies |
|---------|--------|-------|--------|--------------|
| R-SEC-001 | **Rotate Gmail Credentials** - Immediately change Gmail App Password in Google Account settings. Remove from all docker-compose files. | Security Lead | 30 min | Google Account access |
| R-SEC-001 | **Scrub Git History** - Use BFG Repo-Cleaner to remove credentials from git history. Force push to remote. | Security Lead | 1 hour | Git history backup |
| R-SEC-001 | **Implement Docker Secrets** - Move all credentials to .env files excluded from .gitignore. Use Docker secrets for production. | DevOps Lead | 2 hours | - |
| R-SEC-002 | **Fix CORS Configuration** - Replace wildcard origins with explicit whitelist from VIGIL_CORS_ORIGINS env var. Separate dev/prod configs. | Backend Lead | 1 hour | Env var setup |
| R-SEC-003 | **Implement Random Salt** - Generate cryptographically secure random salt (16+ bytes) per encryption. Store salt alongside encrypted data. | Security Lead | 2 hours | Crypto module access |
| R-SEC-003 | **Migrate Existing Data** - Decrypt existing data with static salt, re-encrypt with random salt. Requires maintenance window. | Security Lead | 4 hours | Database backup |
| R-DEV-001 | **Remove network_mode: host** - Update all docker-compose files to use explicit port mapping. Configure Docker internal DNS. | DevOps Lead | 2 hours | Network testing |
| R-FRN-001 | **Replace Hardcoded URLs** - Replace 9 hardcoded IP addresses with REACT_APP_API_URL env var. Add build-time validation. | Frontend Lead | 2 hours | Build pipeline update |
| R-FRN-002 | **Remove LocalStorage Credentials** - Replace localStorage with sessionStorage. Clear on setup completion. Add secure token handling. | Frontend Lead | 1 hour | Auth flow review |
| R-SEC-004 | **Remove JWT Auto-Generation** - Require explicit VIGIL_JWT_SECRET env var on startup. Fail fast with clear error if missing. | Security Lead | 2 hours | Startup validation |

### Phase 1 Exit Criteria
- [ ] All 7 P0 risks resolved or mitigated
- [ ] Credentials rotated and removed from version control
- [ ] CORS wildcard replaced with explicit origins
- [ ] Random salt generation implemented
- [ ] Network isolation restored (network_mode: host removed)
- [ ] No hardcoded IPs in frontend code
- [ ] JWT secrets explicitly configured
- [ ] Security review passed

---

## Phase 2: Security Hardening (Weeks 2-3)

### Objective
Address P1 high risks and implement defense-in-depth measures.

### Preventive Actions

| Risk ID | Action | Owner | Effort | Dependencies |
|---------|--------|-------|--------|--------------|
| R-SEC-005 | **Validate IP Addresses** - Use `ipaddress` module to validate IPs before subprocess. Reject non-private ranges. Add allowlist. | Backend Lead | 2 hours | - |
| R-SEC-005 | **Sanitize Command Args** - Use list args instead of shell strings. Escape special characters. Add command logging. | Backend Lead | 2 hours | - |
| R-SEC-006 | **Fix XXE Vulnerability** - Replace ET.fromstring() with defusedxml.ElementTree. Disable external entities. | Security Lead | 2 hours | Dependency review |
| R-DEV-002 | **Run Containers as Non-Root** - Add USER directive (UID 1000) to all Dockerfiles. Set proper file ownership. | DevOps Lead | 2 hours | Permission testing |
| R-DEV-002 | **Read-Only Root FS** - Configure containers with read-only root filesystem where possible. | DevOps Lead | 2 hours | Container testing |
| R-DEV-003 | **Fix Health Check Ports** - Correct typos (808000→8000, 808080→8080). Add health check validation in CI. | DevOps Lead | 1 hour | - |
| R-SEC-007 | **Remove Fallback Encryption Key** - Fail fast on startup if VIGIL_KEY not set. Add key validation (32+ chars). | Security Lead | 1 hour | - |
| R-FRN-003 | **Implement Content Sanitization** - Add DOMPurify for user-generated content. Use React's built-in escaping. | Frontend Lead | 2 hours | Package install |
| R-FRN-003 | **Add CSP Headers** - Configure Content-Security-Policy, X-Frame-Options, X-Content-Type-Options headers. | DevOps Lead | 2 hours | Header testing |
| R-DEV-004 | **Fix SSH Security** - Remove StrictHostKeyChecking=no. Use webfactory/ssh-agent action. Add known_hosts. | DevOps Lead | 1 hour | CI testing |
| R-BCK-001 | **Fix Hardcoded Paths** - Replace absolute paths with DATABASE_PATH env var. Add path validation. | Backend Lead | 2 hours | - |
| R-SEC-008 | **Add CSRF Protection** - Implement CSRF token header for state-changing requests. Set SameSite=Strict cookies. | Security Lead | 3 hours | Frontend integration |
| R-SEC-009 | **Prevent Auth Bypass** - Add check to prevent AUTH_DISABLED=True when VIGIL_ENV=production. Log critical warnings. | Security Lead | 1 hour | - |
| R-FRN-004 | **Production Build** - Implement multi-stage Docker build. Serve static files with nginx. | Frontend Lead | 3 hours | Build optimization |
| R-BCK-002 | **Split Monolithic Routers** - Break setup.py (800+ lines) into setup_discovery.py, setup_devices.py, etc. | Backend Lead | 8 hours | Architecture review |
| R-RES-001 | **Add Testing Framework** - Add Jest + React Testing Library for frontend. Add pytest with in-memory DB for backend. | QA Lead | 8 hours | CI integration |

### Phase 2 Exit Criteria
- [ ] All P1 security risks resolved
- [ ] Containers running as non-root
- [ ] Health checks functioning correctly
- [ ] No hardcoded paths or credentials
- [ ] CSRF protection implemented
- [ ] Production build pipeline working
- [ ] Test framework established
- [ ] Security scan passed (Trivy/Snyk)

---

## Phase 3: Architecture & Quality (Weeks 4-6)

### Objective
Improve code quality, test coverage, and architectural patterns.

### Preventive Actions

| Risk ID | Action | Owner | Effort | Dependencies |
|---------|--------|-------|--------|--------------|
| R-BCK-003 | **Implement Rate Limiting** - Add slowapi @limiter decorators. Configure per-endpoint limits. Add abuse monitoring. | Backend Lead | 3 hours | - |
| R-FRN-005 | **Optimize Polling** - Implement exponential backoff. Add AbortController for cleanup. Evaluate WebSockets. | Frontend Lead | 4 hours | Architecture decision |
| R-DEV-005 | **Pin Dependencies** - Pin GitHub Actions to specific SHAs. Pin Docker images to digests. Add dependabot. | DevOps Lead | 2 hours | - |
| R-SCH-002 | **Prioritized Refactoring** - Focus on critical modules first. Defer non-essential splits to Phase 4. | Backend Lead | 16 hours | Phase 2 complete |
| R-RES-002 | **Security Training** - Schedule secure coding training for team. Review OWASP Top 10. | Project Manager | 8 hours | Training resources |
| R-RES-001 | **Increase Test Coverage** - Target 70% coverage. Focus on critical paths first. Add integration tests. | QA Lead | 16 hours | Test framework ready |
| R-BCK-004 | **PostgreSQL Planning** - Design migration strategy. Set up test environment. Plan cutover window. | Backend Lead | 4 hours | Infrastructure ready |

---

## Phase 4: Production Readiness (Weeks 7-8)

### Objective
Complete observability, documentation, and final hardening.

### Preventive Actions

| Risk ID | Action | Owner | Effort | Dependencies |
|---------|--------|-------|--------|--------------|
| R-DEV-006 | **Consolidate Compose Files** - Merge 5+ compose files into environment-specific configurations. Document differences. | DevOps Lead | 4 hours | - |
| R-FRN-006 | **Accessibility Audit** - Run axe-core. Fix critical issues. Add ARIA attributes. Manual keyboard testing. | Frontend Lead | 4 hours | - |
| R-RES-002 | **External Security Audit** - Hire third-party security firm for penetration testing. Address findings. | Security Lead | 16 hours | Budget approval |
| - | **Add Observability** - Implement Prometheus metrics. Set up Grafana dashboards. Add structured logging. | DevOps Lead | 8 hours | Infrastructure ready |
| - | **Load Testing** - Perform load testing. Identify bottlenecks. Tune performance. | QA Lead | 8 hours | Production-like env |
| - | **Create Runbooks** - Document deployment procedures. Create incident response playbooks. | DevOps Lead | 4 hours | - |

---

## Contingency Plans

### Contingency Triggers

| Trigger ID | Condition | Response Plan |
|------------|-----------|---------------|
| T-001 | Phase 1 exceeds 3 weeks | **Escalate:** Bring in additional security engineer. **Compensate:** Implement temporary WAF rules. **Communicate:** Notify stakeholders of delay. |
| T-002 | Credential compromise detected | **Immediate:** Rotate all credentials. **Audit:** Review access logs. **Notify:** Incident response team. **Document:** Post-mortem analysis. |
| T-003 | Test coverage below 50% at launch | **Decision:** Delay launch or accept risk with compensating controls (manual QA). **Document:** Risk acceptance form. |
| T-004 | Security scan shows new critical vulnerabilities | **Immediate:** Assess impact. **Patch:** Apply fixes within 24 hours. **Rescan:** Verify fix. **Delay:** Launch if needed. |
| T-005 | Team member unavailable | **Reassign:** Redistribute tasks to remaining team. **Extend:** Adjust timeline. **Hire:** Contract specialist if needed. |

---

## Risk Monitoring Approach

### Daily Monitoring
- Security scan results (Trivy in CI)
- Deployment pipeline health
- Blocked tasks in standup

### Weekly Monitoring
- Risk register updates
- Mitigation progress tracking
- Effort vs. estimate variance

### Monthly Monitoring
- Security posture assessment
- Technical debt metrics
- Team velocity trends

### Key Metrics

| Metric | Current | Target | Threshold |
|--------|---------|--------|-----------|
| Critical Open Risks | 7 | 0 | ≤ 0 |
| High Open Risks | 11 | ≤ 2 | ≤ 3 |
| Security Score | 4/10 | ≥ 7/10 | ≥ 6/10 |
| Test Coverage | ~5% | ≥ 70% | ≥ 50% |
| Mean Time to Fix Critical | - | ≤ 24h | ≤ 48h |

---

## Escalation Matrix

| Risk Score | Action | Escalation Path |
|------------|--------|-----------------|
| New P0 discovered | Immediate standup, stop work | PM → Tech Lead → Executive |
| P0 unresolved > 5 days | Daily status, resource reallocation | PM → Tech Lead |
| P1 unresolved > 2 weeks | Weekly review, schedule impact | Tech Lead → PM |
| Security incident | Immediate incident response | Security Lead → CISO → Legal |
| Budget overrun > 20% | Cost analysis, scope adjustment | PM → Executive |

---

## Mitigation Success Criteria

### Phase 1 Success
- Zero exposed credentials in codebase
- No wildcard CORS in production
- Random salt generation implemented
- Network isolation restored
- All P0 risks closed

### Phase 2 Success
- All containers running as non-root
- CSRF protection active
- Health checks passing
- No hardcoded values
- Test framework established

### Phase 3 Success
- 70% test coverage achieved
- Rate limiting implemented
- Monolithic routers split
- Architecture documentation current

### Production Readiness
- Security score ≥ 7/10
- Load testing passed
- Security audit passed
- Runbooks documented
- Team trained on incident response

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-26 | Risk Management Engineer | Initial mitigation plan created |

---

## Related Documents

- [RISK_REGISTER.md](RISK_REGISTER.md) - Risk inventory and scoring
- [SECURITY_RISKS.md](SECURITY_RISKS.md) - Security-specific analysis
- [CONTINGENCY_PLANS.md](CONTINGENCY_PLANS.md) - Detailed what-if scenarios
