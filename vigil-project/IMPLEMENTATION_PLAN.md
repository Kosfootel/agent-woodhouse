# Vigil Dashboard - Phased Implementation Plan

**Version:** 1.0  
**Date:** 2026-05-26  
**Project:** Vigil Dashboard v2.0 Redesign  
**Duration:** 8 Weeks  
**Status:** Draft - Awaiting Approval

---

## Executive Summary

This document outlines the detailed phased implementation plan for the Vigil Dashboard redesign, addressing all critical security vulnerabilities and architectural issues identified in the comprehensive code review. The plan spans **8 weeks** with realistic effort estimates including **25% buffer time** for unexpected issues.

### Project Statistics

| Metric | Value |
|--------|-------|
| **Total Estimated Effort** | ~420 person-hours |
| **Phases** | 6 |
| **Critical Security Blockers** | 7 (Phase 1) |
| **Team Size Recommended** | 2-3 developers |
| **Risk Level** | Medium-High |
| **Production Ready Target** | Week 8 |

---

## Phase 1: Security Hardening (Week 1)

**Duration:** 5 working days  
**Effort:** 60 hours  
**Goal:** Eliminate all critical security vulnerabilities. **DO NOT DEPLOY without completing this phase.**

### Phase 1 Objectives

1. Remove all P0 security blockers preventing production deployment
2. Establish secure baseline for subsequent phases
3. No new feature development - pure security hardening

### Phase 1 Tasks

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| SEC-001 | Rotate exposed Gmail App Password | Security Lead | 1 | None | Low |
| SEC-002 | Remove Gmail credentials from version control | Security Lead | 2 | SEC-001 | Low |
| SEC-003 | Remove `network_mode: host` from Docker Compose files | DevOps | 4 | None | Medium |
| SEC-004 | Configure proper Docker bridge networks with port mappings | DevOps | 3 | SEC-003 | Medium |
| SEC-005 | Fix CORS wildcard configuration - implement environment-based origins | Backend | 3 | None | Low |
| SEC-006 | Replace static PBKDF2 salt with random salt per encryption | Backend | 4 | None | Medium |
| SEC-007 | Update vault encryption to store salt with encrypted data | Backend | 3 | SEC-006 | Low |
| SEC-008 | Implement random JWT secret generation (32+ chars) on first run | Backend | 4 | None | Medium |
| SEC-009 | Remove JWT auto-generation race condition | Backend | 3 | SEC-008 | Low |
| SEC-010 | Replace hardcoded API URLs with environment variables | Frontend | 4 | None | Low |
| SEC-011 | Update 9 locations with hardcoded internal IPs | Frontend | 4 | SEC-010 | Low |
| SEC-012 | Remove credential storage from LocalStorage | Frontend | 3 | None | Medium |
| SEC-013 | Implement secure credential storage (memory-only + encrypted cookie) | Frontend | 4 | SEC-012 | Medium |
| SEC-014 | Add IP address validation before subprocess execution | Security | 3 | None | Low |
| SEC-015 | Fix XXE vulnerability in UPnP XML parsing | Security | 4 | None | Medium |
| SEC-016 | Disable external entity processing in XML parser | Security | 2 | SEC-015 | Low |
| SEC-017 | Fix health check port typos (808000 → 8080, 808080 → 8080) | DevOps | 1 | None | Low |
| SEC-018 | Document all security changes in security runbook | Security Lead | 2 | All Phase 1 | Low |
| SEC-019 | Run security scan and verify no critical findings | Security Lead | 4 | All Phase 1 | Low |

### Phase 1 Dependencies Diagram

```
SEC-001 (Rotate Gmail)
    |
    ▼
SEC-002 (Remove from VCS)

SEC-003 (Remove network_mode: host)
    |
    ▼
SEC-004 (Configure networks)

SEC-006 (Random salt)
    |
    ▼
SEC-007 (Store salt)

SEC-008 (JWT secret)
    |
    ▼
SEC-009 (Fix race condition)

SEC-010 (Env API URLs)
    |
    ▼
SEC-011 (Replace 9 locations)

SEC-012 (Remove LocalStorage)
    |
    ▼
SEC-013 (Secure storage)

SEC-015 (XXE fix)
    |
    ▼
SEC-016 (Disable entities)

[All tasks] ───► SEC-019 (Final scan)
```

### Phase 1 Deliverables

- [ ] All 7 critical vulnerabilities eliminated
- [ ] Security scan report showing zero critical/high findings
- [ ] Updated credentials (Gmail rotated, new JWT secret)
- [ ] Docker network isolation configured
- [ ] Updated configuration documentation

### Phase 1 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JWT secret change breaks existing sessions | Medium | Medium | Plan for re-authentication |
| Credential removal breaks dev workflow | High | Low | Document new `.env` setup |
| Network changes break device discovery | Medium | High | Test with actual hardware |

---

## Phase 2: Backend Refactor (Weeks 2-3)

**Duration:** 10 working days  
**Effort:** 100 hours  
**Goal:** Modernize backend architecture, split monoliths, add database migrations.

### Phase 2 Objectives

1. Split monolithic routers (`security.py` 600+ lines, `setup.py` 800+ lines)
2. Add Alembic database migrations
3. Implement proper error handling and logging
4. Establish service layer pattern

### Phase 2 Tasks

#### Week 2: Router Split & Database Setup

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| BE-001 | Set up Alembic migration framework | Backend | 6 | Phase 1 complete | Low |
| BE-002 | Create initial database migration | Backend | 4 | BE-001 | Low |
| BE-003 | Split `security.py` into domain modules | Backend | 12 | Phase 1 | Medium |
| BE-004 | Split `setup.py` into domain modules | Backend | 14 | Phase 1 | Medium |
| BE-005 | Create service layer for device operations | Backend | 8 | BE-003 | Medium |
| BE-006 | Create service layer for security operations | Backend | 8 | BE-003, BE-005 | Low |
| BE-007 | Create service layer for setup operations | Backend | 8 | BE-004, BE-006 | Low |
| BE-008 | Implement unified error response format | Backend | 6 | BE-005 | Low |

#### Week 3: Configuration & Testing

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| BE-009 | Implement Pydantic Settings for all configuration | Backend | 6 | Phase 1 | Low |
| BE-010 | Remove all hardcoded database paths | Backend | 4 | BE-009 | Low |
| BE-011 | Implement structured logging with JSON format | Backend | 6 | Phase 1 | Low |
| BE-012 | Add security headers middleware | Backend | 4 | Phase 1 | Low |
| BE-013 | Add input validation layer (Pydantic v2) | Backend | 8 | BE-009 | Medium |
| BE-014 | Implement CSRF token endpoint | Backend | 4 | Phase 1 | Medium |
| BE-015 | Add rate limiting with slowapi | Backend | 6 | Phase 1 | Medium |
| BE-016 | Add proper database indexes for common queries | Backend | 4 | BE-002 | Low |
| BE-017 | Fix N+1 query patterns | Backend | 6 | BE-005 | Medium |
| BE-018 | Write unit tests for service layer (target: 50%) | Backend | 16 | BE-005 to BE-007 | High |

### Phase 2 Dependencies Diagram

```
BE-001 (Alembic setup)
    |
    ▼
BE-002 (Initial migration)
    |
    ▼
BE-016 (Add indexes)

BE-003 (Split security.py)
    |
    ▼
BE-005 (Device service layer)
    |
    ├──► BE-006 (Security service)
    │         |
    │         ▼
    │    BE-008 (Error format)
    │
    └──► BE-018 (Unit tests)

BE-004 (Split setup.py)
    |
    ▼
BE-007 (Setup service layer)
    |
    ▼
BE-017 (Fix N+1 queries)

BE-009 (Pydantic Settings)
    |
    ▼
BE-010 (Remove hardcoded paths)
    |
    ▼
BE-013 (Input validation)
```

### Phase 2 Deliverables

- [ ] Backend test coverage ≥ 50%
- [ ] All routers under 200 lines
- [ ] Alembic migrations configured and tested
- [ ] Service layer implemented for all domains
- [ ] Unified error handling across all endpoints
- [ ] Pydantic Settings for configuration
- [ ] Rate limiting operational

### Phase 2 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Router split breaks existing API contracts | Medium | High | Maintain backward compatibility, version API |
| Database migration fails on production data | Low | Critical | Test migrations on production-like data |
| Service layer adds latency | Low | Low | Benchmark before/after |
| Test coverage takes longer than expected | High | Medium | Prioritize critical paths |

---

## Phase 3: Frontend Rewrite (Weeks 4-5)

**Duration:** 10 working days  
**Effort:** 120 hours  
**Goal:** Modernize frontend with TypeScript, new state management, and proper API client.

### Phase 3 Objectives

1. Migrate to TypeScript
2. Implement Zustand + React Query state management
3. Replace hardcoded URLs with environment variables
4. Add DOMPurify content sanitization
5. Split monolithic components

### Phase 3 Tasks

#### Week 4: TypeScript Migration & State Management

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| FE-001 | Set up TypeScript configuration | Frontend | 4 | Phase 2 | Low |
| FE-002 | Migrate API client to TypeScript with Axios interceptors | Frontend | 8 | FE-001, SEC-010 | Medium |
| FE-003 | Implement Zustand stores (uiStore, authStore, filterStore) | Frontend | 8 | FE-001 | Medium |
| FE-004 | Implement React Query for server state | Frontend | 10 | FE-002 | Medium |
| FE-005 | Set up Tailwind CSS and design tokens | Frontend | 6 | Phase 2 | Low |
| FE-006 | Migrate core components to TypeScript | Frontend | 12 | FE-001, FE-005 | Medium |
| FE-007 | Add DOMPurify content sanitization | Frontend | 4 | FE-006 | Low |
| FE-008 | Implement CSRF protection in API client | Frontend | 4 | BE-014 | Low |

#### Week 5: Component Refactor & Testing

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| FE-009 | Split SetupWizard.js (600+ lines) into smaller components | Frontend | 12 | FE-006 | Medium |
| FE-010 | Split EventTimeline.js into focused components | Frontend | 6 | FE-006 | Low |
| FE-011 | Implement component lazy loading | Frontend | 6 | FE-006 | Low |
| FE-012 | Add Vitest testing framework | Frontend | 4 | Phase 2 | Low |
| FE-013 | Write unit tests for critical components (target: 40%) | Frontend | 16 | FE-012, FE-009 | High |
| FE-014 | Implement proper error boundaries | Frontend | 4 | FE-006 | Low |
| FE-015 | Add React Hook Form + Zod for form validation | Frontend | 6 | FE-001 | Low |
| FE-016 | Update Dockerfile for production build | Frontend | 4 | Phase 1 | Low |
| FE-017 | Add accessibility improvements | Frontend | 6 | FE-005 | Low |
| FE-018 | Implement responsive design fixes | Frontend | 4 | FE-005 | Low |

### Phase 3 Dependencies Diagram

```
FE-001 (TypeScript config)
    |
    ├──► FE-005 (Tailwind)
    │         |
    │         ▼
    │    FE-006 (Core components)
    │         |
    │         ├──► FE-007 (DOMPurify)
    │         ├──► FE-009 (Split SetupWizard)
    │         ├──► FE-010 (Split EventTimeline)
    │         ├──► FE-011 (Lazy loading)
    │         ├──► FE-014 (Error boundaries)
    │         └──► FE-017 (Accessibility)
    │
    ├──► FE-002 (Axios client)
    │         |
    │         ├──► FE-004 (React Query)
    │         │         |
    │         │         └──► FE-013 (Unit tests)
    │         |
    │         └──► FE-008 (CSRF protection)
    │
    └──► FE-003 (Zustand stores)
```

### Phase 3 Deliverables

- [ ] Frontend fully migrated to TypeScript
- [ ] Zustand + React Query state management operational
- [ ] Component files under 300 lines
- [ ] Test coverage ≥ 40%
- [ ] DOMPurify sanitizing all user content
- [ ] Production-optimized Docker build

### Phase 3 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| TypeScript migration reveals hidden bugs | High | Medium | Incremental migration, keep tests green |
| State management change breaks existing features | Medium | High | Thorough manual testing |
| Component split causes UI inconsistencies | Medium | Low | Design review, Storybook |
| Testing takes longer than expected | High | Medium | Focus on critical user paths |

---

## Phase 4: Integration (Week 6)

**Duration:** 5 working days  
**Effort:** 60 hours  
**Goal:** Integrate all components, set up reverse proxy, ensure end-to-end functionality.

### Phase 4 Objectives

1. Set up Caddy reverse proxy with TLS
2. Configure secure networking between services
3. Implement health checks and monitoring
4. Complete end-to-end integration testing

### Phase 4 Tasks

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| INT-001 | Set up Caddy reverse proxy container | DevOps | 6 | Phase 3 | Low |
| INT-002 | Configure Caddy for automatic TLS (Let's Encrypt/Tailscale) | DevOps | 4 | INT-001 | Medium |
| INT-003 | Configure routing rules (/api/* → backend, /* → frontend) | DevOps | 4 | INT-001 | Low |
| INT-004 | Set up isolated Docker networks | DevOps | 4 | SEC-004 | Low |
| INT-005 | Configure container security contexts (non-root, read-only) | DevOps | 6 | Phase 3 | Medium |
| INT-006 | Implement Redis for sessions and caching | DevOps | 6 | Phase 2 | Low |
| INT-007 | Set up PostgreSQL container with persistent volumes | DevOps | 6 | BE-002 | Low |
| INT-008 | Configure environment variables for all services | DevOps | 4 | Phase 3 | Low |
| INT-009 | Implement health check endpoints for all services | DevOps | 6 | Phase 2 | Low |
| INT-010 | Create unified Docker Compose file | DevOps | 4 | All above | Low |
| INT-011 | Write integration tests (API + frontend) | QA/Dev | 10 | All above | High |

### Phase 4 Dependencies Diagram

```
INT-004 (Docker networks)
    |
    ▼
INT-001 (Caddy proxy)
    |
    ├──► INT-002 (TLS config)
    │
    ├──► INT-003 (Routing rules)
    │
    └──► INT-010 (Unified compose)
            |
            ├──► INT-005 (Security contexts)
            ├──► INT-006 (Redis)
            ├──► INT-007 (PostgreSQL)
            ├──► INT-008 (Env vars)
            ├──► INT-009 (Health checks)
            │
            ▼
        INT-011 (Integration tests)
```

### Phase 4 Deliverables

- [ ] Caddy reverse proxy operational with TLS
- [ ] All services communicating via secure internal networks
- [ ] Redis caching and session store operational
- [ ] PostgreSQL database with persistent storage
- [ ] Unified Docker Compose configuration
- [ ] Health checks passing for all services
- [ ] Integration tests passing

### Phase 4 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Container networking issues | Medium | High | Test with actual deployment |
| TLS certificate issues | Low | Medium | Use staging Let's Encrypt first |
| Database connection failures | Low | High | Connection pooling, retries |
| Integration test flakiness | Medium | Medium | Idempotent tests, proper waits |

---

## Phase 5: Testing & Hardening (Week 7)

**Duration:** 5 working days  
**Effort:** 60 hours  
**Goal:** Comprehensive testing, security scanning, performance validation.

### Phase 5 Objectives

1. Achieve target test coverage (Backend ≥ 70%, Frontend ≥ 60%)
2. Complete security scanning with zero critical findings
3. Validate performance requirements
4. Complete user acceptance testing

### Phase 5 Tasks

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| TST-001 | Write additional backend unit tests to reach 70% coverage | Backend | 16 | Phase 4 | Medium |
| TST-002 | Write additional frontend unit tests to reach 60% coverage | Frontend | 16 | Phase 4 | Medium |
| TST-003 | Write E2E tests with Playwright for critical paths | QA/Dev | 12 | Phase 4 | Medium |
| TST-004 | Run Trivy security scan on all images | Security | 2 | Phase 4 | Low |
| TST-005 | Run SAST scan (Semgrep/Bandit) on codebase | Security | 4 | Phase 4 | Low |
| TST-006 | Perform penetration testing on API | Security | 8 | Phase 4 | Medium |
| TST-007 | Load test API endpoints (target: 100ms p95) | QA/Dev | 6 | Phase 4 | Medium |
| TST-008 | Load test device discovery (100 devices in 5 min) | QA/Dev | 4 | Phase 4 | Medium |
| TST-009 | Document security scan results | Security | 2 | TST-004 to TST-006 | Low |

### Phase 5 Dependencies Diagram

```
Phase 4 Complete
    |
    ├──► TST-001 (Backend coverage)
    │
    ├──► TST-002 (Frontend coverage)
    │
    ├──► TST-003 (E2E tests)
    │
    ├──► TST-004 (Trivy scan)
    │         |
    │         └──► TST-009 (Security docs)
    │
    ├──► TST-005 (SAST scan)
    │         |
    │         └──► TST-009
    │
    ├──► TST-006 (Penetration testing)
    │         |
    │         └──► TST-009
    │
    ├──► TST-007 (API load testing)
    │
    └──► TST-008 (Discovery load testing)
```

### Phase 5 Deliverables

- [ ] Backend test coverage ≥ 70%
- [ ] Frontend test coverage ≥ 60%
- [ ] E2E tests for critical user paths
- [ ] Security scan report with zero critical/high findings
- [ ] Performance test report meeting all NFRs
- [ ] Penetration test report

### Phase 5 Testing Thresholds (Exit Criteria)

| Category | Requirement | Threshold |
|----------|-------------|-----------|
| Security Scan | Trivy container scan | 0 Critical, 0 High |
| SAST | Semgrep/Bandit | 0 Critical, 0 High |
| Test Coverage | Backend | ≥ 70% |
| Test Coverage | Frontend | ≥ 60% |
| E2E Tests | Critical paths | 100% pass rate |
| Performance | API response p95 | ≤ 100ms |
| Performance | Page load TTI | ≤ 3 seconds |
| Load | Concurrent users | ≥ 10 supported |

### Phase 5 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test coverage takes longer than expected | High | Medium | Prioritize critical paths |
| Security scan finds new critical issues | Medium | Critical | Buffer time for fixes |
| Performance requirements not met | Medium | Medium | Performance tuning |
| E2E tests flaky in CI | Medium | Medium | Robust test design |

---

## Phase 6: Production Readiness (Week 8)

**Duration:** 5 working days  
**Effort:** 40 hours  
**Goal:** Final preparations for production deployment.

### Phase 6 Objectives

1. Set up observability (metrics, logging, alerting)
2. Implement backup strategy
3. Complete documentation
4. Create runbooks
5. Final production deployment

### Phase 6 Tasks

| ID | Task | Owner | Effort (hrs) | Dependencies | Risk |
|----|------|-------|--------------|--------------|------|
| PROD-001 | Set up Prometheus for metrics collection | DevOps | 6 | Phase 5 | Low |
| PROD-002 | Set up Grafana dashboards | DevOps | 4 | PROD-001 | Low |
| PROD-003 | Configure structured logging with Loki | DevOps | 4 | Phase 5 | Low |
| PROD-004 | Set up alerting rules (email/ntfy) | DevOps | 4 | PROD-001, PROD-003 | Low |
| PROD-005 | Implement automated database backups | DevOps | 6 | Phase 5 | Medium |
| PROD-006 | Configure backup retention and verification | DevOps | 4 | PROD-005 | Low |
| PROD-007 | Write deployment runbook | DevOps | 4 | Phase 5 | Low |
| PROD-008 | Write incident response runbook | DevOps | 4 | Phase 5 | Low |
| PROD-009 | Write rollback procedures | DevOps | 2 | Phase 5 | Low |
| PROD-010 | Final production deployment to GX-10 | DevOps | 2 | All above | Medium |

### Phase 6 Dependencies Diagram

```
Phase 5 Complete
    |
    ├──► PROD-001 (Prometheus)
    │         |
    │         ├──► PROD-002 (Grafana dashboards)
    │         |
    │         └──► PROD-004 (Alerting)
    │
    ├──► PROD-003 (Loki logging)
    │         |
    │         └──► PROD-004
    │
    ├──► PROD-005 (DB backups)
    │         |
    │         └──► PROD-006 (Retention)
    │
    ├──► PROD-007 (Deployment runbook)
    │
    ├──► PROD-008 (Incident response)
    │
    ├──► PROD-009 (Rollback procedures)
    │
    └──► PROD-010 (Final deployment)
```

### Phase 6 Deliverables

- [ ] Prometheus operational collecting metrics
- [ ] Grafana dashboards configured
- [ ] Centralized logging with Loki
- [ ] Alerting configured for critical conditions
- [ ] Automated daily backups operational
- [ ] Backup verification process documented
- [ ] Deployment runbook complete
- [ ] Incident response runbook complete
- [ ] Rollback procedures tested
- [ ] Production deployment successful

### Phase 6 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backup strategy fails on first run | Low | Critical | Test before production |
| Monitoring gaps | Medium | Medium | Review checklist |
| Deployment issues | Low | High | Staged rollout, rollback ready |

---

## Resource Allocation Summary

### By Phase

| Phase | Effort (hrs) | % of Total | Primary Focus |
|-------|--------------|------------|---------------|
| Phase 1: Security Hardening | 60 | 14% | Security blockers |
| Phase 2: Backend Refactor | 100 | 24% | Architecture |
| Phase 3: Frontend Rewrite | 120 | 29% | Modernization |
| Phase 4: Integration | 60 | 14% | Connectivity |
| Phase 5: Testing & Hardening | 60 | 14% | Quality assurance |
| Phase 6: Production Readiness | 40 | 10% | Operations |
| **Total** | **420** | **100%** | |

### By Role

| Role | Effort (hrs) | % of Total |
|------|--------------|------------|
| Backend Developer | 110 | 26% |
| Frontend Developer | 130 | 31% |
| DevOps Engineer | 110 | 26% |
| Security Lead | 40 | 10% |
| QA/Testing | 30 | 7% |
| **Total** | **420** | **100%** |

### Weekly Distribution

```
Week    Phase           Backend  Frontend  DevOps  Security  QA
─────────────────────────────────────────────────────────────────
Week 1  Security        20%      25%       35%     15%       5%
Week 2  Backend         70%       0%       20%      5%       5%
Week 3  Backend         60%      10%      15%      5%      10%
Week 4  Frontend        10%      70%      10%      5%       5%
Week 5  Frontend         5%      75%      10%      5%       5%
Week 6  Integration     10%      20%      60%      5%       5%
Week 7  Testing         20%      30%      20%     15%      15%
Week 8  Production      10%      10%      60%      5%      15%
```

---

## Critical Path Analysis

The critical path represents the minimum time to complete the project if all tasks on this path are executed optimally.

### Critical Path Tasks

```
Phase 1: Security Blockers (Week 1)
├── SEC-003: Remove network_mode: host (4 hrs)
├── SEC-004: Configure Docker networks (3 hrs)
└── SEC-019: Final security scan (4 hrs)

Phase 2: Backend Foundation (Week 2)
├── BE-001: Alembic setup (6 hrs)
├── BE-002: Initial migration (4 hrs)
└── BE-003: Split security.py (12 hrs)

Phase 2: Backend Services (Week 3)
├── BE-005: Device service layer (8 hrs)
├── BE-006: Security service layer (8 hrs)
└── BE-018: Unit tests (16 hrs)

Phase 3: Frontend Core (Week 4)
├── FE-001: TypeScript config (4 hrs)
├── FE-002: Axios client (8 hrs)
└── FE-006: Core components (12 hrs)

Phase 3: Frontend Polish (Week 5)
├── FE-009: Split SetupWizard (12 hrs)
└── FE-013: Unit tests (16 hrs)

Phase 4: Integration (Week 6)
├── INT-001: Caddy proxy (6 hrs)
├── INT-007: PostgreSQL (6 hrs)
└── INT-011: Integration tests (10 hrs)

Phase 5: Testing (Week 7)
├── TST-001: Backend coverage (16 hrs)
├── TST-002: Frontend coverage (16 hrs)
└── TST-003: E2E tests (12 hrs)

Phase 6: Go Live (Week 8)
├── PROD-005: DB backups (6 hrs)
└── PROD-010: Final deployment (2 hrs)
```

### Critical Path Duration: 8 weeks (40 working days)

---

## Risk Management

### Project-Level Risks

| Risk | Likelihood | Impact | Owner | Mitigation | Contingency |
|------|------------|--------|-------|------------|-------------|
| Security scan finds new critical issues late | Medium | Critical | Security Lead | Weekly security scans | Extend Phase 5, delay launch |
| Team member unavailable | Low | High | Project Lead | Knowledge sharing, documentation | Adjust scope, extend timeline |
| GX-10 hardware issues | Low | Critical | DevOps | Regular health checks | Use backup hardware |
| Third-party dependency breaks | Low | Medium | DevOps | Pinned versions | Rollback, fix |
| Scope creep | Medium | Medium | Project Lead | Strict change control | Defer to Phase 7 |

### Mitigation Strategies

1. **Security First:** Phase 1 must complete before any deployment
2. **Regular Syncs:** Daily standups, weekly retrospectives
3. **Documentation:** All major decisions documented in ADRs
4. **Testing:** Automated tests run on every commit
5. **Rollback Ready:** Maintain ability to revert to v1.0 if needed

---

## Dependencies & External Factors

### External Dependencies

| Dependency | Owner | Required By | Status |
|------------|-------|-------------|--------|
| GX-10 hardware access | DevOps | Phase 4 | Confirmed |
| Tailscale network | DevOps | Phase 4 | Configured |
| Domain/DNS | DevOps | Phase 4 | TBD |
| Gmail account for alerts | Security | Phase 1 | Confirmed |
| ntfy account | DevOps | Phase 6 | TBD |

### Internal Dependencies

| Dependency | Required For |
|------------|--------------|
| Phase 1 complete | Phases 2, 3, 4, 5, 6 |
| Phase 2 complete | Phase 4 |
| Phase 3 complete | Phase 4 |
| Phase 4 complete | Phase 5 |
| Phase 5 complete | Phase 6 |

---

## Success Criteria

The project is considered successful when:

1. ✅ All 7 critical security vulnerabilities eliminated
2. ✅ Security scan shows 0 critical, 0 high findings
3. ✅ Backend test coverage ≥ 70%
4. ✅ Frontend test coverage ≥ 60%
5. ✅ API response time p95 ≤ 100ms
6. ✅ Page load TTI ≤ 3 seconds
7. ✅ Production deployment successful on GX-10
8. ✅ All P0 requirements implemented and tested
9. ✅ Monitoring and alerting operational
10. ✅ Documentation and runbooks complete

---

## Appendix A: Task Details by ID

### Security Tasks (SEC-*)

**SEC-003: Remove network_mode: host**
- Replace with proper Docker bridge networks
- Update service-to-service communication
- Test device discovery still works
- Risk: May break UPnP discovery

**SEC-005: Fix CORS wildcard**
- Implement VIGIL_CORS_ORIGINS environment variable
- Parse comma-separated origins
- Reject wildcard with credentials enabled
- Risk: Breaking existing CORS assumptions

**SEC-006: Fix static salt**
- Generate random 32-byte salt per encryption
- Store salt with encrypted data
- Migration strategy for existing data
- Risk: Existing encrypted data becomes unreadable (needs migration)

### Backend Tasks (BE-*)

**BE-003: Split security.py**
- New structure:
  - routers/security/scanning.py
  - routers/security/policies.py
  - routers/security/alerts.py
- Maintain same API contracts
- Risk: Breaking existing integrations

**BE-018: Unit tests**
- Focus on service layer
- Mock external dependencies
- Async test patterns
- Risk: Takes longer than expected

### Frontend Tasks (FE-*)

**FE-002: Axios client**
- Implement request/response interceptors
- Handle token refresh
- Request cancellation support
- Risk: Breaking existing fetch-based code

**FE-009: Split SetupWizard**
- Break into components:
  - WelcomeStep
  - RouterDiscoveryStep
  - CredentialsStep
  - DeviceImportStep
  - CompleteStep
- Maintain wizard state
- Risk: Complex state management

---

## Appendix B: Weekly Milestones

| Week | Milestone | Key Deliverables |
|------|-----------|------------------|
| 1 | Security Baseline | 0 critical vulnerabilities, secure config |
| 2 | Backend Foundation | Alembic, router split started |
| 3 | Backend Complete | Service layer, 50% test coverage |
| 4 | Frontend Foundation | TypeScript, Zustand, React Query |
| 5 | Frontend Complete | Component split, 40% coverage |
| 6 | Integration Complete | Caddy, TLS, all services talking |
| 7 | Quality Gates | 70% backend, 60% frontend, 0 security findings |
| 8 | Production Live | Monitoring, backups, deployment |

---

*Document generated by Project Planning Engineer*  
*Based on Vigil Dashboard Code Review and Requirements Analysis*
