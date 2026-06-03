# Vigil Dashboard Redesign - Requirements Specification

**Project:** Vigil Dashboard Security Monitoring System  
**Version:** 1.0  
**Date:** 2026-05-26  
**Based on:** Comprehensive Code Review Findings

---

## Document Overview

This requirements specification package contains the complete set of requirements for the Vigil Dashboard redesign, derived from a comprehensive code review covering:

- Backend (FastAPI + SQLAlchemy)
- Frontend (React 18)
- DevOps/Infrastructure (Docker, CI/CD)
- Security Audit

### Code Review Sources

| Document | Description |
|----------|-------------|
| `MASTER_CODE_REVIEW.md` | Consolidated findings across all domains |
| `BACKEND_CODE_REVIEW.md` | FastAPI backend detailed review |
| `FRONTEND_CODE_REVIEW.md` | React frontend detailed review |
| `DEVOPS_CODE_REVIEW.md` | Infrastructure and deployment review |
| `SECURITY_AUDIT.md` | Security vulnerability assessment |
| `QUICK_WINS.md` | High-impact, low-effort fixes |
| `ARCHITECTURE_DECISIONS.md` | ADRs for redesign |

---

## Requirements Documents

### 1. FUNCTIONAL_REQUIREMENTS.md
**27 functional requirements** organized by feature area:

- **Device Discovery and Management** (5 requirements)
  - Multi-protocol discovery, device registration, inventory management
  - Router integration, scan scheduling

- **Security Monitoring and Alerting** (7 requirements)
  - Event detection, alert management, email notifications
  - Real-time streaming, policy engine

- **Agent Management** (3 requirements)
  - Agent registration, configuration, health monitoring

- **Dashboard and Reporting** (6 requirements)
  - Dashboard overview, event timeline, device/alert management
  - Heatmap visualization, report generation

- **Setup and Configuration** (6 requirements)
  - Setup wizard, environment config, CORS/database config
  - Admin operations, backup/restore

**Priority Distribution:**
- P0 (Critical): 17 requirements
- P1 (Required): 9 requirements
- P2 (Enhancement): 1 requirement

---

### 2. NON_FUNCTIONAL_REQUIREMENTS.md
**32 non-functional requirements** across six categories:

| Category | P0 | P1 | P2 | Total |
|----------|----|----|----|-------|
| Performance | 2 | 3 | 0 | 5 |
| Security | 11 | 1 | 0 | 12 |
| Reliability | 4 | 1 | 0 | 5 |
| Scalability | 0 | 2 | 1 | 3 |
| Maintainability | 4 | 1 | 0 | 5 |
| Compliance | 0 | 2 | 0 | 2 |

**Key Security Requirements:**
- NFR-006: Authentication Security (JWT, Argon2id)
- NFR-007: Cryptographic Standards (AES-256-GCM, PBKDF2 600k+ iterations)
- NFR-008: Transport Security (TLS 1.3, HSTS)
- NFR-009: Input Validation (SQL injection, XSS prevention)
- NFR-010: Container Security (non-root, no host networking)
- NFR-011: Secret Management (no hardcoded credentials)
- NFR-012: CORS Security (no wildcards with credentials)
- NFR-013: Security Headers (CSP, X-Frame-Options)
- NFR-014: CSRF Protection (SameSite, tokens)

---

### 3. CONSTRAINTS_AND_ASSUMPTIONS.md
Project constraints organized by category:

**Hardware Constraints:**
- Jetson Orin Nano 8GB as target platform
- Local network deployment (no cloud)
- Single-node deployment (no cluster)

**Network Constraints:**
- 192.168.50.0/24 network segment
- No public internet exposure
- Home router integration required
- Removal of `network_mode: host` required

**Technology Stack:**
- FastAPI + SQLAlchemy (backend)
- React 18 (frontend)
- SQLite → PostgreSQL (database)
- Docker Compose (deployment)
- GitHub Actions (CI/CD)

**Security Compliance:**
- OWASP ASVS Level 2 alignment
- 9 critical security blockers must be resolved

**8 Key Assumptions** documented with risk analysis:
- Single administrator
- Trusted private network
- Static IP addresses
- Router admin access available
- ≤100 devices
- No high availability requirement

---

### 4. REQUIREMENTS_TRACEABILITY_MATRIX.md
Complete traceability mapping:

- **57 total requirements** tracked
- Links to source code review findings
- Test case IDs (TBD pending implementation)
- Implementation status tracking
- Security vulnerability mapping (CWE references)
- Quick wins mapping to requirements

**Current Status:** 0% complete (planning phase)

---

## Critical Security Blockers

The following 7 critical vulnerabilities **must** be fixed before production:

| ID | Vulnerability | CVSS | Requirement |
|----|-------------|------|-------------|
| SEC-001 | Exposed Gmail App Password | 9.8 | NFR-011 |
| SEC-002 | Wildcard CORS with credentials | 9.1 | NFR-012 |
| SEC-003 | JWT auto-generation race condition | 8.5 | NFR-006 |
| SEC-004 | network_mode: host | 8.1 | NFR-010 |
| SEC-005 | Command injection via discovery | 8.1 | NFR-009 |
| SEC-006 | XXE in UPnP XML parsing | 8.1 | NFR-009 |
| SEC-007 | Static salt in PBKDF2 | 7.5 | NFR-007 |

---

## Quick Wins (12 hours total effort)

Highest ROI fixes that address 70% of critical/high vulnerabilities:

1. **Rotate Gmail credentials** (30m) - SEC-001
2. **Remove CORS wildcard** (1h) - SEC-002
3. **Fix health check typos** (15m)
4. **Remove network_mode: host** (2h) - SEC-004
5. **Fix SSH StrictHostKeyChecking** (30m)
6. **Fix static salt** (2h) - SEC-007
7. **API URL environment variable** (1h)
8. **Non-root containers** (1h)
9. **CSRF protection** (2h)
10. **Security headers** (1h)

---

## Implementation Phases

### Phase 1: Security Lockdown (Week 1) - BLOCKERS
~15 hours
- All critical security vulnerabilities
- Deployment stability fixes
- Configuration hardening

### Phase 2: Hardening (Weeks 2-3)
~21 hours
- Rate limiting
- CSRF protection
- Content sanitization
- Input validation layer

### Phase 3: Architecture & Quality (Weeks 4-6)
~47 hours
- Router refactoring
- Database migrations (Alembic)
- Testing framework
- React Query integration

### Phase 4: Production Readiness (Weeks 7-8)
~25 hours
- Prometheus metrics
- Grafana dashboards
- Automated backups
- Load testing

**Total Estimated Effort:** ~108 hours (2.5-3 months with 50% allocation)

---

## Test Coverage Requirements

| Component | Target Coverage |
|-------------|-----------------|
| Backend | ≥ 70% |
| Frontend | ≥ 60% |
| Security-critical paths | 100% |
| Integration tests | Critical paths |
| E2E tests | User workflows |

---

## Success Criteria

The Vigil Dashboard redesign will be considered successful when:

1. **All 7 critical security vulnerabilities** are resolved
2. **All P0 requirements** (39 total) are implemented
3. **Test coverage targets** are met
4. **Jetson Orin deployment** passes all integration tests
5. **Zero CRITICAL vulnerabilities** in security scans
6. **<500ms p95 response time** for API calls
7. **99.9% uptime** target (excluding maintenance)

---

## Usage Instructions

### For Developers
1. Review `FUNCTIONAL_REQUIREMENTS.md` for feature specifications
2. Check `NON_FUNCTIONAL_REQUIREMENTS.md` for performance/security targets
3. Reference `CONSTRAINTS_AND_ASSUMPTIONS.md` for design boundaries
4. Update `REQUIREMENTS_TRACEABILITY_MATRIX.md` as implementation progresses

### For QA/Testers
1. Use `REQUIREMENTS_TRACEABILITY_MATRIX.md` to track test case creation
2. Reference specific requirement IDs in bug reports
3. Verify security requirements against `NON_FUNCTIONAL_REQUIREMENTS.md`

### For Project Managers
1. Use Phase 1-4 breakdown for sprint planning
2. Track progress via traceability matrix status column
3. Prioritize P0 requirements for MVP

### For Security Reviewers
1. Review security requirements in `NON_FUNCTIONAL_REQUIREMENTS.md`
2. Verify security blockers are addressed in Phase 1
3. Validate fixes against CVSS scores in traceability matrix

---

## Document Maintenance

This requirements specification should be treated as a living document:

- **Update** requirement status as implementation progresses
- **Add** new requirements via change request process
- **Version** documents when major changes occur
- **Archive** superseded requirements with rationale
- **Review** monthly during active development

---

## References

### Architecture Decisions
- ADR-001: State Management (Zustand + React Query)
- ADR-002: API Standardization (Axios)
- ADR-003: Router Organization (Domain-driven)
- ADR-004: Database (SQLite + Alembic → PostgreSQL)
- ADR-005: Container Security (Non-root, read-only)
- ADR-006: Authentication (Cookie-based sessions)
- ADR-007: Configuration (Pydantic Settings)
- ADR-008: Testing (Pyramid approach)
- ADR-009: Error Handling (Unified format)
- ADR-010: Deployment (GitHub Actions)

### External Standards
- OWASP ASVS Level 2
- NIST Cybersecurity Framework
- Docker Security Best Practices
- React Security Best Practices

---

*End of Requirements Specification Package*
