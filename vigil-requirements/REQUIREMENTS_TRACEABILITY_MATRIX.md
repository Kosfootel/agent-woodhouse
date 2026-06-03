# Vigil Dashboard - Requirements Traceability Matrix

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Status:** Draft - Implementation Pending

---

## Table of Contents

1. [Matrix Legend](#1-matrix-legend)
2. [Functional Requirements Traceability](#2-functional-requirements-traceability)
3. [Non-Functional Requirements Traceability](#3-non-functional-requirements-traceability)
4. [Security Requirements Traceability](#4-security-requirements-traceability)
5. [Quick Wins Mapping](#5-quick-wins-mapping)
6. [Implementation Status Summary](#6-implementation-status-summary)

---

## 1. Matrix Legend

### Priority Codes
| Code | Meaning |
|------|---------|
| P0 | Critical - Blocks Production |
| P1 | Required - Needed for Maintainability |
| P2 | Enhancement - Future Improvement |

### Implementation Status
| Status | Description |
|--------|-------------|
| 🔴 NOT_STARTED | No work done |
| 🟡 IN_PROGRESS | Actively being developed |
| 🟢 COMPLETE | Implemented and tested |
| ⚪ BLOCKED | Waiting on dependency |
| 🔵 VERIFIED | Tested in production |

### Test Case Status
| Status | Description |
|--------|-------------|
| TBD | To Be Defined |
| WRITTEN | Test case documented |
| PASSED | Test passed |
| FAILED | Test failed (regression) |

---

## 2. Functional Requirements Traceability

| Req ID | Requirement Description | Source Document | Priority | Test Case ID | Implementation Status |
|--------|------------------------|-----------------|----------|--------------|---------------------|
| **Device Discovery & Management** |
| FR-001 | Multi-Protocol Device Discovery | BACKEND_CODE_REVIEW.md | P0 | TC-DEV-001 | 🔴 NOT_STARTED |
| FR-002 | Device Registration and Baseline | BACKEND_CODE_REVIEW.md | P0 | TC-DEV-002 | 🔴 NOT_STARTED |
| FR-003 | Device Inventory Management | BACKEND_CODE_REVIEW.md | P0 | TC-DEV-003 | 🔴 NOT_STARTED |
| FR-004 | Router Discovery and Integration | FRONTEND_CODE_REVIEW.md | P0 | TC-DEV-004 | 🔴 NOT_STARTED |
| FR-005 | Network Scan Scheduling | BACKEND_CODE_REVIEW.md | P1 | TC-DEV-005 | 🔴 NOT_STARTED |
| **Security Monitoring & Alerting** |
| FR-006 | Security Event Detection | BACKEND_CODE_REVIEW.md | P0 | TC-SEC-001 | 🔴 NOT_STARTED |
| FR-007 | Alert Generation and Management | BACKEND_CODE_REVIEW.md | P0 | TC-SEC-002 | 🔴 NOT_STARTED |
| FR-008 | Email Notification System | DEVOPS_CODE_REVIEW.md | P0 | TC-SEC-003 | 🔴 NOT_STARTED |
| FR-009 | Real-Time Event Stream | SECURITY_AUDIT.md | P1 | TC-SEC-004 | 🔴 NOT_STARTED |
| FR-010 | Security Policy Engine | BACKEND_CODE_REVIEW.md | P1 | TC-SEC-005 | 🔴 NOT_STARTED |
| **Agent Management** |
| FR-011 | Agent Registration | BACKEND_CODE_REVIEW.md | P0 | TC-AGT-001 | 🔴 NOT_STARTED |
| FR-012 | Agent Configuration Management | BACKEND_CODE_REVIEW.md | P1 | TC-AGT-002 | 🔴 NOT_STARTED |
| FR-013 | Agent Health Monitoring | BACKEND_CODE_REVIEW.md | P1 | TC-AGT-003 | 🔴 NOT_STARTED |
| **Dashboard & Reporting** |
| FR-014 | Security Dashboard Overview | FRONTEND_CODE_REVIEW.md | P0 | TC-UI-001 | 🔴 NOT_STARTED |
| FR-015 | Event Timeline Visualization | FRONTEND_CODE_REVIEW.md | P0 | TC-UI-002 | 🔴 NOT_STARTED |
| FR-016 | Device Management Interface | FRONTEND_CODE_REVIEW.md | P0 | TC-UI-003 | 🔴 NOT_STARTED |
| FR-017 | Alert Management Interface | FRONTEND_CODE_REVIEW.md | P0 | TC-UI-004 | 🔴 NOT_STARTED |
| FR-018 | Access Heatmap Visualization | FRONTEND_CODE_REVIEW.md | P2 | TC-UI-005 | 🔴 NOT_STARTED |
| FR-019 | Report Generation | MASTER_CODE_REVIEW.md | P1 | TC-UI-006 | 🔴 NOT_STARTED |
| **Setup & Configuration** |
| FR-020 | Setup Wizard | FRONTEND_CODE_REVIEW.md | P0 | TC-SET-001 | 🔴 NOT_STARTED |
| FR-021 | Environment Configuration | BACKEND_CODE_REVIEW.md | P0 | TC-SET-002 | 🔴 NOT_STARTED |
| FR-022 | CORS Configuration | SECURITY_AUDIT.md | P0 | TC-SET-003 | 🔴 NOT_STARTED |
| FR-023 | Database Configuration | BACKEND_CODE_REVIEW.md | P0 | TC-SET-004 | 🔴 NOT_STARTED |
| FR-024 | Admin Operations | BACKEND_CODE_REVIEW.md | P1 | TC-SET-005 | 🔴 NOT_STARTED |
| FR-025 | Backup and Restore | DEVOPS_CODE_REVIEW.md | P1 | TC-SET-006 | 🔴 NOT_STARTED |

---

## 3. Non-Functional Requirements Traceability

| Req ID | Requirement Description | Source Document | Priority | Test Case ID | Implementation Status |
|--------|------------------------|-----------------|----------|--------------|---------------------|
| **Performance** |
| NFR-001 | API Response Time | BACKEND_CODE_REVIEW.md | P0 | TC-PERF-001 | 🔴 NOT_STARTED |
| NFR-002 | Concurrent User Support | DEVOPS_CODE_REVIEW.md | P0 | TC-PERF-002 | 🔴 NOT_STARTED |
| NFR-003 | Frontend Load Performance | FRONTEND_CODE_REVIEW.md | P1 | TC-PERF-003 | 🔴 NOT_STARTED |
| NFR-004 | Database Query Performance | BACKEND_CODE_REVIEW.md | P0 | TC-PERF-004 | 🔴 NOT_STARTED |
| NFR-005 | Network Efficiency | FRONTEND_CODE_REVIEW.md | P1 | TC-PERF-005 | 🔴 NOT_STARTED |
| **Security** |
| NFR-006 | Authentication Security | SECURITY_AUDIT.md | P0 | TC-SEC-010 | 🔴 NOT_STARTED |
| NFR-007 | Cryptographic Standards | SECURITY_AUDIT.md | P0 | TC-SEC-011 | 🔴 NOT_STARTED |
| NFR-008 | Transport Security | SECURITY_AUDIT.md | P0 | TC-SEC-012 | 🔴 NOT_STARTED |
| NFR-009 | Input Validation | SECURITY_AUDIT.md | P0 | TC-SEC-013 | 🔴 NOT_STARTED |
| NFR-010 | Container Security | DEVOPS_CODE_REVIEW.md | P0 | TC-SEC-014 | 🔴 NOT_STARTED |
| NFR-011 | Secret Management | SECURITY_AUDIT.md | P0 | TC-SEC-015 | 🔴 NOT_STARTED |
| NFR-012 | CORS Security | SECURITY_AUDIT.md | P0 | TC-SEC-016 | 🔴 NOT_STARTED |
| NFR-013 | Security Headers | SECURITY_AUDIT.md | P0 | TC-SEC-017 | 🔴 NOT_STARTED |
| NFR-014 | CSRF Protection | SECURITY_AUDIT.md | P0 | TC-SEC-018 | 🔴 NOT_STARTED |
| NFR-015 | Audit Logging | MASTER_CODE_REVIEW.md | P1 | TC-SEC-019 | 🔴 NOT_STARTED |
| **Reliability** |
| NFR-016 | System Availability | DEVOPS_CODE_REVIEW.md | P0 | TC-REL-001 | 🔴 NOT_STARTED |
| NFR-017 | Health Monitoring | DEVOPS_CODE_REVIEW.md | P0 | TC-REL-002 | 🔴 NOT_STARTED |
| NFR-018 | Error Handling | BACKEND_CODE_REVIEW.md | P0 | TC-REL-003 | 🔴 NOT_STARTED |
| NFR-019 | Data Durability | DEVOPS_CODE_REVIEW.md | P0 | TC-REL-004 | 🔴 NOT_STARTED |
| NFR-020 | Graceful Degradation | BACKEND_CODE_REVIEW.md | P1 | TC-REL-005 | 🔴 NOT_STARTED |
| **Scalability** |
| NFR-021 | Device Scaling | MASTER_CODE_REVIEW.md | P1 | TC-SCL-001 | 🔴 NOT_STARTED |
| NFR-022 | Event Retention | BACKEND_CODE_REVIEW.md | P1 | TC-SCL-002 | 🔴 NOT_STARTED |
| NFR-023 | Horizontal Scaling | DEVOPS_CODE_REVIEW.md | P2 | TC-SCL-003 | 🔴 NOT_STARTED |
| **Maintainability** |
| NFR-024 | Code Organization | BACKEND_CODE_REVIEW.md | P0 | TC-MNT-001 | 🔴 NOT_STARTED |
| NFR-025 | Documentation | BACKEND_CODE_REVIEW.md | P1 | TC-MNT-002 | 🔴 NOT_STARTED |
| NFR-026 | Testing Coverage | BACKEND_CODE_REVIEW.md | P0 | TC-MNT-003 | 🔴 NOT_STARTED |
| NFR-027 | Dependency Management | BACKEND_CODE_REVIEW.md | P0 | TC-MNT-004 | 🔴 NOT_STARTED |
| NFR-028 | Configuration Management | BACKEND_CODE_REVIEW.md | P0 | TC-MNT-005 | 🔴 NOT_STARTED |
| **Compliance** |
| NFR-029 | Privacy Compliance | SECURITY_AUDIT.md | P1 | TC-CMP-001 | 🔴 NOT_STARTED |
| NFR-030 | Audit Compliance | SECURITY_AUDIT.md | P1 | TC-CMP-002 | 🔴 NOT_STARTED |

---

## 4. Security Requirements Traceability

### Critical Security Issues (from Security Audit)

| Security ID | CWE | Requirement | Source | NFR Link | Status |
|-------------|-----|-------------|--------|----------|--------|
| SEC-001 | CWE-798 | Rotate exposed Gmail credentials | SECURITY_AUDIT.md | NFR-011 | 🔴 NOT_STARTED |
| SEC-002 | CWE-942 | Fix wildcard CORS configuration | SECURITY_AUDIT.md | NFR-012 | 🔴 NOT_STARTED |
| SEC-003 | CWE-287 | Fix JWT auto-generation race condition | SECURITY_AUDIT.md | NFR-006, NFR-011 | 🔴 NOT_STARTED |
| SEC-004 | CWE-284 | Remove network_mode: host | SECURITY_AUDIT.md | NFR-010 | 🔴 NOT_STARTED |
| SEC-005 | CWE-78 | Validate IP addresses before subprocess | SECURITY_AUDIT.md | NFR-009 | 🔴 NOT_STARTED |
| SEC-006 | CWE-611 | Fix XXE vulnerability in XML parsing | SECURITY_AUDIT.md | NFR-009 | 🔴 NOT_STARTED |
| SEC-007 | CWE-759 | Fix static salt in PBKDF2 | SECURITY_AUDIT.md | NFR-007 | 🔴 NOT_STARTED |

### High Security Issues

| Security ID | CWE | Requirement | Source | NFR Link | Status |
|-------------|-----|-------------|--------|----------|--------|
| SEC-008 | CWE-352 | Add CSRF protection | SECURITY_AUDIT.md | NFR-014 | 🔴 NOT_STARTED |
| SEC-009 | CWE-319 | Implement HTTPS/TLS | SECURITY_AUDIT.md | NFR-008 | 🔴 NOT_STARTED |
| SEC-010 | CWE-250 | Run containers as non-root | SECURITY_AUDIT.md | NFR-010 | 🔴 NOT_STARTED |
| SEC-011 | CWE-522 | Remove credentials from LocalStorage | SECURITY_AUDIT.md | NFR-006 | 🔴 NOT_STARTED |
| SEC-012 | CWE-200 | Fix information disclosure in errors | SECURITY_AUDIT.md | NFR-018 | 🔴 NOT_STARTED |
| SEC-013 | CWE-918 | Fix hardcoded API URLs | SECURITY_AUDIT.md | NFR-028 | 🔴 NOT_STARTED |
| SEC-014 | CWE-16 | Add security headers | SECURITY_AUDIT.md | NFR-013 | 🔴 NOT_STARTED |
| SEC-015 | CWE-770 | Implement rate limiting | SECURITY_AUDIT.md | NFR-002 | 🔴 NOT_STARTED |
| SEC-016 | CWE-79 | Add content sanitization (DOMPurify) | SECURITY_AUDIT.md | FR-015 | 🔴 NOT_STARTED |
| SEC-017 | CWE-522 | Use Argon2id for API key hashing | SECURITY_AUDIT.md | NFR-007 | 🔴 NOT_STARTED |
| SEC-018 | CWE-326 | Increase PBKDF2 iterations to 600k | SECURITY_AUDIT.md | NFR-007 | 🔴 NOT_STARTED |

---

## 5. Quick Wins Mapping

### Quick Wins to Requirements Mapping

| Quick Win # | Quick Win Description | Related Requirements | Effort | Impact |
|-------------|----------------------|---------------------|--------|--------|
| QW-001 | Rotate exposed Gmail credentials | FR-008, NFR-011 | 30m | Critical |
| QW-002 | Remove CORS wildcard | FR-022, NFR-012 | 1h | Critical |
| QW-003 | Fix health check typos | NFR-017 | 15m | Critical |
| QW-004 | Remove network_mode: host | NFR-010 | 2h | Critical |
| QW-005 | Fix SSH StrictHostKeyChecking | NFR-008 | 30m | High |
| QW-006 | Fix static salt | NFR-007 | 2h | High |
| QW-007 | API URL env var | FR-021, NFR-028 | 1h | High |
| QW-008 | Non-root containers | NFR-010 | 1h | High |
| QW-009 | CSRF protection | NFR-014 | 2h | Med-High |
| QW-010 | Security headers | NFR-013 | 1h | Med-High |

---

## 6. Implementation Status Summary

### By Category

| Category | Total | Complete | In Progress | Not Started | % Complete |
|----------|-------|----------|-------------|-------------|------------|
| **Functional - Device** | 5 | 0 | 0 | 5 | 0% |
| **Functional - Security** | 7 | 0 | 0 | 7 | 0% |
| **Functional - Agents** | 3 | 0 | 0 | 3 | 0% |
| **Functional - Dashboard** | 6 | 0 | 0 | 6 | 0% |
| **Functional - Setup** | 6 | 0 | 0 | 6 | 0% |
| **Non-Functional - Performance** | 5 | 0 | 0 | 5 | 0% |
| **Non-Functional - Security** | 10 | 0 | 0 | 10 | 0% |
| **Non-Functional - Reliability** | 5 | 0 | 0 | 5 | 0% |
| **Non-Functional - Scalability** | 3 | 0 | 0 | 3 | 0% |
| **Non-Functional - Maintainability** | 5 | 0 | 0 | 5 | 0% |
| **Non-Functional - Compliance** | 2 | 0 | 0 | 2 | 0% |
| **TOTAL** | **57** | **0** | **0** | **57** | **0%** |

### By Priority

| Priority | Count | Percentage of Total |
|----------|-------|---------------------|
| P0 (Critical) | 39 | 68% |
| P1 (Required) | 17 | 30% |
| P2 (Enhancement) | 1 | 2% |

### Security Blockers (Must Fix Before Production)

| # | Requirement | Status | Test Case |
|---|-------------|--------|-----------|
| 1 | Rotate Gmail credentials (SEC-001) | 🔴 NOT_STARTED | TBD |
| 2 | Remove network_mode: host (SEC-004) | 🔴 NOT_STARTED | TBD |
| 3 | Fix CORS wildcard (SEC-002) | 🔴 NOT_STARTED | TBD |
| 4 | Fix static salt (SEC-007) | 🔴 NOT_STARTED | TBD |
| 5 | JWT secret management (SEC-003) | 🔴 NOT_STARTED | TBD |
| 6 | IP validation before subprocess (SEC-005) | 🔴 NOT_STARTED | TBD |
| 7 | XXE vulnerability fix (SEC-006) | 🔴 NOT_STARTED | TBD |

---

## Test Case ID Reference

### Test Case Prefixes

| Prefix | Category | Example |
|--------|----------|---------|
| TC-DEV | Device Management | TC-DEV-001 |
| TC-SEC | Security & Alerting | TC-SEC-001 |
| TC-AGT | Agent Management | TC-AGT-001 |
| TC-UI | Dashboard UI | TC-UI-001 |
| TC-SET | Setup & Config | TC-SET-001 |
| TC-PERF | Performance | TC-PERF-001 |
| TC-REL | Reliability | TC-REL-001 |
| TC-SCL | Scalability | TC-SCL-001 |
| TC-MNT | Maintainability | TC-MNT-001 |
| TC-CMP | Compliance | TC-CMP-001 |

---

## Update Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-05-26 | 1.0 | Requirements Engineer | Initial creation based on code review findings |

---

## Notes

1. **Test Case Development:** All test cases marked "TBD" must be defined before implementation begins.

2. **Security First:** All P0 security requirements (NFR-006 through NFR-014) must be implemented before any production deployment.

3. **Traceability Maintenance:** This matrix must be updated as implementation progresses. Each commit should reference the requirement IDs being addressed.

4. **Verification Process:** Each requirement requires:
   - Unit test(s) covering the requirement
   - Integration test where applicable
   - Manual verification for UI requirements
   - Security review for security requirements

5. **Blocked Items:** Any item marked "BLOCKED" must include:
   - Reason for blockage
   - Dependency item ID
   - Expected resolution date

---

*Document generated as part of Vigil Dashboard Redesign Requirements Specification.*
