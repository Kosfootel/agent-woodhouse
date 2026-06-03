# Vigil Dashboard - Project Summary

**Project:** Vigil Dashboard Security Monitoring System v2.0  
**Version:** 1.0  
**Date:** 2026-05-26  
**Status:** 🔴 Planning Phase - Production Deployment Blocked  
**Classification:** CONFIDENTIAL

---

## Executive Overview

The Vigil Dashboard is a home network security monitoring system designed to discover, monitor, and protect IoT devices on local networks. This document summarizes the complete project scope, deliverables, timeline, and success criteria based on a comprehensive code review, requirements analysis, and architectural redesign.

**Current State:** The codebase has significant security vulnerabilities, architectural inconsistencies, and zero production readiness. A complete redesign and phased implementation is required.

**Target State:** A secure, maintainable, and production-ready security monitoring platform deployable on Jetson Orin Nano hardware.

---

## Project Scope

### In Scope

#### Core Features
1. **Device Discovery & Management**
   - Multi-protocol discovery (ARP, Nmap, SNMP, UPnP/SSDP, mDNS)
   - Device registration with baseline configuration
   - Inventory CRUD operations with filtering
   - Router integration (ASUS, Generic UPnP)
   - Scheduled and on-demand network scans

2. **Security Monitoring & Alerting**
   - Real-time security event detection
   - Alert generation with severity levels
   - Email notification system (SMTP/Gmail)
   - Real-time event streaming (SSE)
   - Security policy engine

3. **Agent Management**
   - Agent registration and authentication
   - Configuration distribution
   - Health monitoring with metrics

4. **Dashboard & Reporting**
   - Security dashboard overview
   - Event timeline visualization
   - Device management interface
   - Alert management interface
   - Access heatmap visualization
   - Report generation (PDF, CSV, JSON)

5. **Setup & Configuration**
   - Multi-step setup wizard
   - Environment-based configuration
   - CORS configuration management
   - Database configuration (SQLite → PostgreSQL)
   - Backup and restore operations

#### Technical Scope
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React 18 + TypeScript + Tailwind CSS
- Infrastructure: Docker + Docker Compose + GitHub Actions
- Monitoring: Prometheus + Grafana
- Testing: pytest + Vitest + Playwright

### Out of Scope
- Cloud deployment (AWS/Azure/GCP)
- Multi-tenant support
- Enterprise RBAC/LDAP integration
- Mobile applications
- ML-based threat detection (future phase)
- Automated incident response actions

---

## Deliverables

### Phase 1: Security Lockdown (Week 1)
| Deliverable | Description | Status |
|-------------|-------------|--------|
| SEC-001 Fix | Rotated Gmail credentials, scrubbed git history | 🔴 NOT_STARTED |
| SEC-002 Fix | CORS wildcard replaced with explicit origins | 🔴 NOT_STARTED |
| SEC-003 Fix | JWT auto-generation removed | 🔴 NOT_STARTED |
| SEC-004 Fix | network_mode: host removed | 🔴 NOT_STARTED |
| SEC-005 Fix | IP validation before subprocess | 🔴 NOT_STARTED |
| SEC-006 Fix | XXE vulnerability patched | 🔴 NOT_STARTED |
| SEC-007 Fix | Random salt generation implemented | 🔴 NOT_STARTED |

### Phase 2: Security Hardening (Weeks 2-3)
| Deliverable | Description | Status |
|-------------|-------------|--------|
| Container Security | Non-root users, read-only FS, capability dropping | 🔴 NOT_STARTED |
| CSRF Protection | Token-based CSRF with SameSite cookies | 🔴 NOT_STARTED |
| Content Sanitization | DOMPurify XSS prevention | 🔴 NOT_STARTED |
| Rate Limiting | slowapi implementation | 🔴 NOT_STARTED |
| Input Validation | Pydantic validation layer | 🔴 NOT_STARTED |
| Security Headers | CSP, HSTS, X-Frame-Options | 🔴 NOT_STARTED |

### Phase 3: Architecture & Quality (Weeks 4-6)
| Deliverable | Description | Status |
|-------------|-------------|--------|
| Database Migration | Alembic migrations + PostgreSQL path | 🔴 NOT_STARTED |
| Router Refactoring | Domain-driven router organization | 🔴 NOT_STARTED |
| Frontend Modernization | Zustand + React Query + TypeScript | 🔴 NOT_STARTED |
| Testing Framework | 70%+ coverage backend, 60%+ frontend | 🔴 NOT_STARTED |
| Error Handling | Unified error response format | 🔴 NOT_STARTED |

### Phase 4: Production Readiness (Weeks 7-8)
| Deliverable | Description | Status |
|-------------|-------------|--------|
| Observability | Prometheus metrics + Grafana dashboards | 🔴 NOT_STARTED |
| Automated Backups | Database backup/restore with encryption | 🔴 NOT_STARTED |
| CI/CD Hardening | Image signing, pinned dependencies | 🔴 NOT_STARTED |
| Documentation | API docs, runbooks, user guides | 🔴 NOT_STARTED |
| Load Testing | Performance validation | 🔴 NOT_STARTED |

---

## Timeline & Milestones

### Project Schedule

```
Week 1:  Phase 1 - Security Lockdown (15 hours)
Week 2:  Phase 2 - Security Hardening (Start)
Week 3:  Phase 2 - Security Hardening (Complete)
Week 4:  Phase 3 - Architecture & Quality (Start)
Week 5:  Phase 3 - Architecture & Quality (Continue)
Week 6:  Phase 3 - Architecture & Quality (Complete)
Week 7:  Phase 4 - Production Readiness (Start)
Week 8:  Phase 4 - Production Readiness (Complete)
```

### Key Milestones

| Milestone | Target Date | Dependencies | Success Criteria |
|-----------|-------------|--------------|------------------|
| **M1: Security Lockdown** | Week 1 End | Code review complete | All 7 P0 security blockers resolved |
| **M2: Security Hardened** | Week 3 End | M1 complete | Trivy scan clean, CSRF protection active |
| **M3: Architecture Refactored** | Week 6 End | M2 complete | Test coverage ≥70%, routers split |
| **M4: Production Ready** | Week 8 End | M3 complete | Load tests pass, docs complete |
| **M5: Production Deploy** | Week 8+2d | M4 complete | Zero-downtime deployment successful |

---

## Success Criteria

### Technical Success Criteria

| Criterion | Target | Measurement Method |
|-----------|--------|---------------------|
| Security Vulnerabilities | 0 Critical, ≤2 High | Trivy + Snyk scans |
| Test Coverage | ≥70% backend, ≥60% frontend | pytest-cov + vitest |
| API Response Time | p95 < 200ms | k6 load testing |
| Page Load Time | < 2 seconds (TTI) | Lighthouse CI |
| Uptime | ≥99.9% | Prometheus monitoring |
| Code Quality | A grade | SonarQube analysis |

### Functional Success Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Device Discovery | 100 devices / 5 minutes | Integration test |
| Concurrent Users | 10 simultaneous | Load test |
| Event Processing | 100 events/second | Performance test |
| Alert Delivery | < 30 seconds | E2E test |
| Data Retention | 90 days online, 1 year archive | Policy validation |

### Security Success Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Authentication | JWT + Cookie-based sessions | Penetration test |
| Encryption | AES-256-GCM, PBKDF2 600k+ iterations | Code review |
| Container Security | Non-root, no host networking | CIS benchmark |
| Secrets Management | Zero hardcoded credentials | Secret scanning |
| OWASP ASVS | Level 2 compliance | Security audit |

### Business Success Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Deployment Time | < 10 minutes | CI/CD metrics |
| Rollback Time | < 5 minutes | Drill exercise |
| Mean Time to Recovery | < 30 minutes | Incident simulation |
| Documentation Coverage | 100% critical paths | Doc review |

---

## Resource Requirements

### Personnel

| Role | Allocation | Duration | Responsibilities |
|------|------------|----------|------------------|
| Security Lead | 50% | Weeks 1-3 | Security fixes, hardening |
| Backend Lead | 100% | Weeks 1-8 | API development, refactoring |
| Frontend Lead | 100% | Weeks 1-8 | React modernization |
| DevOps Lead | 50% | Weeks 1-8 | Infrastructure, CI/CD |
| QA Lead | 50% | Weeks 3-8 | Test development, validation |
| Project Manager | 25% | Weeks 1-8 | Coordination, reporting |

### Infrastructure

| Resource | Specification | Purpose |
|----------|---------------|---------|
| Jetson Orin Nano | 8GB RAM, ARM64 | Production deployment target |
| Development Workstation | 16GB+ RAM, x86_64 | Development and testing |
| GitHub Actions Runner | Ubuntu-latest | CI/CD pipeline |
| Docker Hub / GHCR | Container registry | Image storage |

### Tools & Licenses

| Tool | Purpose | Cost |
|------|---------|------|
| GitHub Teams | Repository, Actions | Included |
| Snyk | Dependency scanning | Free tier |
| SonarQube | Code quality | Community edition |
| Tailscale | Private networking | Free tier |

### Budget Estimate

| Category | Estimated Cost |
|----------|----------------|
| Personnel (internal) | ~$25,000 (108 hours @ blended rate) |
| Infrastructure | ~$500 (hardware amortization) |
| Tools & Services | ~$200 (if premium tiers needed) |
| External Security Audit | ~$3,000 (optional) |
| **Total** | **~$28,700** |

---

## Risks & Assumptions

### Critical Risks (P0)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Exposed credentials not rotated | Data breach, account compromise | Immediate rotation, git scrubbing |
| Wildcard CORS not fixed | CSRF attacks, credential theft | Explicit origin whitelist |
| network_mode: host remains | Container escape, host compromise | Docker network isolation |

### Key Assumptions

| Assumption | Impact if Invalid |
|------------|-------------------|
| Single administrator | Requires multi-user auth system redesign |
| Private network deployment | Requires additional security controls |
| ≤100 devices | May require database architecture changes |
| Static IP addresses | May cause device tracking issues |
| Jetson Orin Nano target | Other hardware may have different constraints |

---

## Dependencies

### External Dependencies

| Dependency | Purpose | Risk Level |
|------------|---------|------------|
| GitHub Actions | CI/CD | Low |
| Docker Hub / GHCR | Container registry | Low |
| Gmail SMTP | Email notifications | Medium (rotate credentials) |
| Tailscale | Private networking | Low |

### Internal Dependencies

| Dependency | Required By | Status |
|------------|-------------|--------|
| Phase 1 Security Fixes | All subsequent phases | 🔴 Blocked |
| Database Migration | Testing, production | 🔴 Blocked |
| API Contracts | Frontend integration | 🔴 Blocked |

---

## Current Status

### Completion Summary

| Phase | Status | Complete | In Progress | Blocked |
|-------|--------|----------|-------------|---------|
| Phase 1: Code Review | ✅ Complete | 100% | 0% | 0% |
| Phase 2: Requirements | ✅ Complete | 100% | 0% | 0% |
| Phase 3: Test Strategy | ✅ Complete | 100% | 0% | 0% |
| Phase 4: Project Planning | ✅ Complete | 100% | 0% | 0% |
| Phase 5: Delivery Planning | 🟡 In Progress | 0% | 100% | 0% |
| Phase 6: Implementation | 🔴 Blocked | 0% | 0% | 100% |

### Quality Metrics

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Security Score | 4/10 | 8/10 | -4 |
| Code Coverage | ~5% | 70% | -65% |
| Test Pass Rate | N/A | 100% | - |
| Documentation | 20% | 100% | -80% |

---

## Next Steps

### Immediate Actions (Next 24 Hours)

1. **Rotate Gmail credentials** (SEC-001)
2. **Remove credentials from version control**
3. **Scrub git history** using BFG Repo-Cleaner
4. **Schedule Phase 1 kickoff** with security team

### Week 1 Priorities

1. Complete all 7 P0 security blockers
2. Security review and sign-off
3. Deploy to staging environment for validation
4. Update risk register with mitigation status

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-26 | Delivery Planning Engineer | Initial project summary |

### Related Documents

- [MASTER_CODE_REVIEW.md](../vigil-code-review/MASTER_CODE_REVIEW.md)
- [FUNCTIONAL_REQUIREMENTS.md](../vigil-requirements/FUNCTIONAL_REQUIREMENTS.md)
- [NON_FUNCTIONAL_REQUIREMENTS.md](../vigil-requirements/NON_FUNCTIONAL_REQUIREMENTS.md)
- [TARGET_ARCHITECTURE.md](../vigil-requirements/TARGET_ARCHITECTURE.md)
- [RISK_REGISTER.md](../vigil-project/RISK_REGISTER.md)
- [BACKEND_TEST_STRATEGY.md](../vigil-tests/BACKEND_TEST_STRATEGY.md)

---

*This document is a living document and should be updated as the project progresses.*
