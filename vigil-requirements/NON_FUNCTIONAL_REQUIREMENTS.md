# Vigil Dashboard - Non-Functional Requirements Specification

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Based on:** Code Review Findings (SECURITY_AUDIT.md, DEVOPS_CODE_REVIEW.md, MASTER_CODE_REVIEW.md)

---

## Table of Contents

1. [Performance Requirements](#1-performance-requirements)
2. [Security Requirements](#2-security-requirements)
3. [Reliability Requirements](#3-reliability-requirements)
4. [Scalability Requirements](#4-scalability-requirements)
5. [Maintainability Requirements](#5-maintainability-requirements)
6. [Compliance Requirements](#6-compliance-requirements)

---

## 1. Performance Requirements

### NFR-001: API Response Time
**Requirement:** API endpoints shall respond within defined latency targets under normal load.

**Priority:** P0  
**Measurable:**
- AC1: Simple CRUD operations (GET/POST/PUT/DELETE): ≤ 100ms (p95)
- AC2: Complex queries with filters: ≤ 500ms (p95)
- AC3: Device discovery scans: ≤ 30 seconds for /24 subnet
- AC4: Database write operations: ≤ 50ms (p95)
- AC5: Static asset serving: ≤ 50ms (p95)

**Source:** BACKEND_CODE_REVIEW.md (Performance Bottlenecks section), MASTER_CODE_REVIEW.md

---

### NFR-002: Concurrent User Support
**Requirement:** The system shall support multiple concurrent dashboard users.

**Priority:** P0  
**Measurable:**
- AC1: Minimum 10 concurrent dashboard users
- AC2: API rate limit: 100 requests/minute per user
- AC3: WebSocket connections: Minimum 50 concurrent SSE streams
- AC4: No degradation of response time under concurrent load

**Source:** DEVOPS_CODE_REVIEW.md (No rate limiting), SECURITY_AUDIT.md (Section 3.5)

---

### NFR-003: Frontend Load Performance
**Requirement:** The dashboard shall load and become interactive within acceptable time limits.

**Priority:** P1  
**Measurable:**
- AC1: Initial page load: ≤ 2 seconds on broadband (≥ 10 Mbps)
- AC2: Time to Interactive (TTI): ≤ 3 seconds
- AC3: First Contentful Paint (FCP): ≤ 1 second
- AC4: Bundle size: ≤ 500KB gzipped (initial load)
- AC5: Component lazy loading for routes not in initial bundle

**Source:** FRONTEND_CODE_REVIEW.md (Performance Issues section)

---

### NFR-004: Database Query Performance
**Requirement:** Database queries shall execute efficiently with proper indexing.

**Priority:** P0  
**Measurable:**
- AC1: All frequent queries use appropriate indexes
- AC2: No N+1 query patterns in API responses
- AC3: Query execution time: ≤ 100ms for paginated results (100 records)
- AC4: Full table scans logged and flagged for review
- AC5: Database size growth: ≤ 1GB per month with 100 devices

**Source:** BACKEND_CODE_REVIEW.md (Section 6.2 - Missing Indexes, Section 4.2 - N+1 Query Risk)

---

### NFR-005: Network Efficiency
**Requirement:** The system shall minimize network traffic through efficient data transfer.

**Priority:** P1  
**Measurable:**
- AC1: API responses support compression (gzip/brotli)
- AC2: Dashboard uses HTTP/2 or HTTP/3 where available
- AC3: SSE events use filtering to reduce unnecessary traffic
- AC4: Images and assets cached with appropriate headers (1 year for versioned assets)
- AC5: API pagination: default 50 records, max 500 records per request

**Source:** FRONTEND_CODE_REVIEW.md (Polling Instead of WebSockets), MASTER_CODE_REVIEW.md

---

## 2. Security Requirements

### NFR-006: Authentication Security
**Requirement:** User authentication shall follow security best practices.

**Priority:** P0  
**Measurable:**
- AC1: JWT tokens expire after 30 minutes maximum
- AC2: Refresh tokens expire after 7 days
- AC3: Passwords hashed using Argon2id (not bcrypt alone)
- AC4: Failed login attempts rate-limited: 5 attempts per 15 minutes per IP
- AC5: Session tokens bound to client fingerprint (IP + User-Agent hash)
- AC6: No plaintext credential storage in LocalStorage

**Source:** SECURITY_AUDIT.md (Sections 1.2, 1.3, 4.3), MASTER_CODE_REVIEW.md (SEC-003)

---

### NFR-007: Cryptographic Standards
**Requirement:** All cryptographic operations shall use industry-standard algorithms.

**Priority:** P0  
**Measurable:**
- AC1: Encryption uses AES-256-GCM (not Fernet)
- AC2: Key derivation uses PBKDF2 with ≥ 600,000 iterations (OWASP 2023)
- AC3: Random salts generated per encryption (32 bytes minimum)
- AC4: JWT uses RS256 or ES256 (not HS256)
- AC5: API keys hashed using Argon2id (not SHA-256)
- AC6: All random values generated using `secrets` module, not `random`

**Source:** SECURITY_AUDIT.md (Sections 4.1, 4.2, 4.3), MASTER_CODE_REVIEW.md (SEC-007)

---

### NFR-008: Transport Security
**Requirement:** All network communications shall be encrypted.

**Priority:** P0  
**Measurable:**
- AC1: HTTPS/TLS 1.3 for all external endpoints
- AC2: HTTP Strict Transport Security (HSTS) header: max-age=31536000
- AC3: Certificate validation: no insecure skip verify
- AC4: Internal service communication uses TLS where feasible
- AC5: SSH connections use StrictHostKeyChecking=yes

**Source:** SECURITY_AUDIT.md (Section 9.2), DEVOPS_CODE_REVIEW.md (SSH StrictHostKeyChecking=no)

---

### NFR-009: Input Validation
**Requirement:** All user input shall be validated and sanitized.

**Priority:** P0  
**Measurable:**
- AC1: Pydantic models validate all API inputs
- AC2: SQL injection: 0 vulnerabilities (verified by SAST)
- AC3: XSS prevention: Content escaped or sanitized (DOMPurify)
- AC4: Command injection: Input validated before subprocess
- AC5: XML external entity (XXE): disabled in all XML parsers
- AC6: File path traversal: blocked using absolute path validation

**Source:** SECURITY_AUDIT.md (Sections 3.2, 3.3, 3.4, 3.5), MASTER_CODE_REVIEW.md (SEC-005, SEC-006)

---

### NFR-010: Container Security
**Requirement:** Containers shall run with minimal privileges and proper isolation.

**Priority:** P0  
**Measurable:**
- AC1: All containers run as non-root user (UID ≥ 1000)
- AC2: Container filesystems read-only where possible
- AC3: No `network_mode: host` in production deployments
- AC4: Container capabilities: drop ALL, add only required
- AC5: Security scanning: 0 CRITICAL vulnerabilities in final images
- AC6: Image signing with Cosign for verification

**Source:** DEVOPS_CODE_REVIEW.md (network_mode: host), SECURITY_AUDIT.md (Section 8), MASTER_CODE_REVIEW.md

---

### NFR-011: Secret Management
**Requirement:** Secrets shall be managed securely and never exposed.

**Priority:** P0  
**Measurable:**
- AC1: Zero hardcoded credentials in source code
- AC2: Secrets stored in Docker secrets or external vault
- AC3: JWT secret: 32+ character random string, not auto-generated
- AC4: Credential rotation: supported and documented
- AC5: Secrets never logged (masked in logs)
- AC6: `.env` files excluded from version control

**Source:** SECURITY_AUDIT.md (Section 1.1 - Hardcoded Gmail), DEVOPS_CODE_REVIEW.md (Exposed credentials), MASTER_CODE_REVIEW.md (SEC-001)

---

### NFR-012: CORS Security
**Requirement:** Cross-Origin Resource Sharing shall be configured securely.

**Priority:** P0  
**Measurable:**
- AC1: CORS origins configured via environment variable
- AC2: Wildcard (`*`) never used with `allow_credentials=True`
- AC3: Production CORS: specific origins only, no wildcards
- AC4: CORS preflight requests cached appropriately
- AC5: Invalid CORS attempts logged with origin information

**Source:** SECURITY_AUDIT.md (Section 2.1 - CORS wildcard), BACKEND_CODE_REVIEW.md, MASTER_CODE_REVIEW.md (SEC-002)

---

### NFR-013: Security Headers
**Requirement:** Security headers shall be present on all HTTP responses.

**Priority:** P0  
**Measurable:**
- AC1: `X-Content-Type-Options: nosniff` present
- AC2: `X-Frame-Options: DENY` present
- AC3: `Content-Security-Policy` configured (no `unsafe-inline` scripts)
- AC4: `Referrer-Policy: strict-origin-when-cross-origin` present
- AC5: `Permissions-Policy` restricting unnecessary features

**Source:** SECURITY_AUDIT.md (Section 5.1 - Missing CSP), FRONTEND_CODE_REVIEW.md

---

### NFR-014: CSRF Protection
**Requirement:** State-changing operations shall be protected against CSRF attacks.

**Priority:** P0  
**Measurable:**
- AC1: CSRF tokens required for POST/PUT/DELETE operations
- AC2: SameSite=Strict cookie attribute on session cookies
- AC3: Double-submit cookie pattern implemented
- AC4: CSRF token validation on all state-changing endpoints
- AC5: CSRF token rotation on authentication

**Source:** SECURITY_AUDIT.md (Section 6 - Missing CSRF Protection), MASTER_CODE_REVIEW.md

---

### NFR-015: Audit Logging
**Requirement:** Security-relevant events shall be logged for audit purposes.

**Priority:** P1  
**Measurable:**
- AC1: All authentication attempts logged (success and failure)
- AC2: Privileged operations logged with user and timestamp
- AC3: Data modification events logged with before/after state
- AC4: Failed access attempts logged with IP and reason
- AC5: Audit logs retained for minimum 90 days
- AC6: Audit logs protected from tampering (append-only)

**Source:** MASTER_CODE_REVIEW.md (Section 3.3 - Testing), SECURITY_AUDIT.md

---

## 3. Reliability Requirements

### NFR-016: System Availability
**Requirement:** The system shall maintain high availability for critical operations.

**Priority:** P0  
**Measurable:**
- AC1: Target uptime: 99.9% (excluding planned maintenance)
- AC2: Maximum planned downtime: 4 hours per month (maintenance windows)
- AC3: Health check endpoint responds within 5 seconds
- AC4: Graceful degradation: dashboard works if agent data unavailable
- AC5: Automatic restart on failure (Docker restart policy)

**Source:** DEVOPS_CODE_REVIEW.md (Health check typos), MASTER_CODE_REVIEW.md

---

### NFR-017: Health Monitoring
**Requirement:** The system shall expose health metrics for monitoring.

**Priority:** P0  
**Measurable:**
- AC1: Health endpoint (`/health`) returns 200 when all dependencies OK
- AC2: Health check includes: database connectivity, disk space, memory
- AC3: Detailed health metrics at `/health/detailed` (authenticated)
- AC4: Health check interval: 30 seconds
- AC5: Failed health checks trigger automatic restart

**Source:** DEVOPS_CODE_REVIEW.md (No HEALTHCHECK defined), MASTER_CODE_REVIEW.md

---

### NFR-018: Error Handling
**Requirement:** The system shall handle errors gracefully without exposing sensitive information.

**Priority:** P0  
**Measurable:**
- AC1: API errors return consistent JSON format (no stack traces)
- AC2: HTTP 500 errors logged with full details for debugging
- AC3: Client receives generic error message (no internal details)
- AC4: Error responses include request ID for tracking
- AC5: Frontend displays user-friendly error messages

**Source:** BACKEND_CODE_REVIEW.md (Section 2.6 - Information Disclosure), FRONTEND_CODE_REVIEW.md (Error Handling)

---

### NFR-019: Data Durability
**Requirement:** Data shall be protected against loss.

**Priority:** P0  
**Measurable:**
- AC1: Automated database backups: daily minimum
- AC2: Backup retention: 30 days minimum
- AC3: Backup verification: weekly test restore
- AC4: Point-in-time recovery capability (if using PostgreSQL)
- AC5: Database transactions atomic for multi-step operations

**Source:** DEVOPS_CODE_REVIEW.md (No backup strategy), MASTER_CODE_REVIEW.md

---

### NFR-020: Graceful Degradation
**Requirement:** The system shall degrade gracefully when dependencies fail.

**Priority:** P1  
**Measurable:**
- AC1: Dashboard displays cached data if backend unavailable
- AC2: Device discovery continues if one protocol fails
- AC3: Email alerts queue if SMTP unavailable
- AC4: Clear user notification when operating in degraded mode
- AC5: Circuit breaker pattern for external dependencies

**Source:** BACKEND_CODE_REVIEW.md (Section 3.4 - Error Handling), MASTER_CODE_REVIEW.md

---

## 4. Scalability Requirements

### NFR-021: Device Scaling
**Requirement:** The system shall scale to support home network sizes.

**Priority:** P1  
**Measurable:**
- AC1: Support minimum 100 devices per deployment
- AC2: Support maximum 500 devices (Jetson Orin 8GB constraint)
- AC3: Device discovery completes within 5 minutes for 100 devices
- AC4: Event processing: 100 events/second sustained
- AC5: Database queries remain performant at maximum device count

**Source:** MASTER_CODE_REVIEW.md (Hardware limits), DEVOPS_CODE_REVIEW.md (Jetson Orin)

---

### NFR-022: Event Retention
**Requirement:** The system shall manage event data retention appropriately.

**Priority:** P1  
**Measurable:**
- AC1: Events retained: 90 days online
- AC2: Events archived: 1 year total
- AC3: Automatic purge of events older than retention period
- AC4: Archive export capability before deletion
- AC5: Configurable retention per event severity

**Source:** BACKEND_CODE_REVIEW.md (Database concerns), MASTER_CODE_REVIEW.md

---

### NFR-023: Horizontal Scaling Considerations
**Requirement:** The system architecture shall not prevent future horizontal scaling.

**Priority:** P2  
**Measurable:**
- AC1: Stateless API design (session data externalized)
- AC2: Database migrations support PostgreSQL (not SQLite-only)
- AC3: Configuration externalized (not in container image)
- AC4: No filesystem-based coordination between instances

**Source:** DEVOPS_CODE_REVIEW.md (SQLite limitations), ARCHITECTURE_DECISIONS.md (ADR-004)

---

## 5. Maintainability Requirements

### NFR-024: Code Organization
**Requirement:** The codebase shall follow consistent organization patterns.

**Priority:** P0  
**Measurable:**
- AC1: Backend routers max 200 lines per file
- AC2: Frontend components max 300 lines per file
- AC3: Single Responsibility Principle: one concern per module
- AC4: Consistent file naming conventions (snake_case for Python, camelCase/PascalCase for JS)
- AC5: No duplicate code (DRY principle) - max 5% code duplication

**Source:** BACKEND_CODE_REVIEW.md (Section 2.3 - security.py/setup.py monolithic), FRONTEND_CODE_REVIEW.md (SetupWizard.js 600+ lines)

---

### NFR-025: Documentation
**Requirement:** The system shall be adequately documented.

**Priority:** P1  
**Measurable:**
- AC1: API documentation: OpenAPI/Swagger spec with examples
- AC2: Architecture Decision Records (ADRs) for major decisions
- AC3: Deployment guide with troubleshooting section
- AC4: Inline code comments for complex logic (min 20% comment coverage)
- AC5: README with quick start instructions

**Source:** BACKEND_CODE_REVIEW.md (Section 10 - Documentation), MASTER_CODE_REVIEW.md

---

### NFR-026: Testing Coverage
**Requirement:** The system shall have automated test coverage.

**Priority:** P0  
**Measurable:**
- AC1: Backend unit test coverage: ≥ 70%
- AC2: Frontend unit test coverage: ≥ 60%
- AC3: Critical paths have integration tests
- AC4: Security-focused tests for auth, input validation
- AC5: Tests run in CI/CD pipeline (block deployment on failure)

**Source:** BACKEND_CODE_REVIEW.md (Section 8 - Test Coverage ~10%), FRONTEND_CODE_REVIEW.md (Testing - 0% coverage), MASTER_CODE_REVIEW.md

---

### NFR-027: Dependency Management
**Requirement:** Dependencies shall be managed securely and kept current.

**Priority:** P0  
**Measurable:**
- AC1: Dependency versions pinned in requirements/package files
- AC2: Security scanning: weekly automated checks
- AC3: No unused dependencies in production builds
- AC4: License compatibility check for all dependencies
- AC5: Dependency update process documented

**Source:** BACKEND_CODE_REVIEW.md (Section 7 - redis, slowapi unused), MASTER_CODE_REVIEW.md

---

### NFR-028: Configuration Management
**Requirement:** Configuration shall be externalized and manageable.

**Priority:** P0  
**Measurable:**
- AC1: Zero hardcoded configuration values
- AC2: Environment-specific config files (.env.development, .env.production)
- AC3: Configuration validation at startup (fail fast on invalid config)
- AC4: Secrets separated from non-sensitive configuration
- AC5: Configuration changes do not require rebuild

**Source:** BACKEND_CODE_REVIEW.md (Section 9 - hardcoded paths), ARCHITECTURE_DECISIONS.md (ADR-007)

---

## 6. Compliance Requirements

### NFR-029: Privacy Compliance
**Requirement:** The system shall respect user privacy and data protection regulations.

**Priority:** P1  
**Measurable:**
- AC1: PII (MAC addresses, device names) encrypted at rest
- AC2: Data retention limits enforced
- AC3: No unnecessary data collection
- AC4: User notification for data collection (privacy policy)
- AC5: Data export capability for user data portability

**Source:** SECURITY_AUDIT.md (Section 10.2 - PII in Email Logs)

---

### NFR-030: Audit Compliance
**Requirement:** The system shall maintain audit trails for compliance.

**Priority:** P1  
**Measurable:**
- AC1: All security events logged with timestamp and actor
- AC2: Audit logs immutable (append-only)
- AC3: Audit log access restricted to authorized personnel
- AC4: Audit log retention: minimum 1 year
- AC5: Tamper-evident logging (hash chain)

**Source:** SECURITY_AUDIT.md, MASTER_CODE_REVIEW.md

---

## Requirements Summary

### By Category

| Category | P0 | P1 | P2 | Total |
|----------|----|----|----|-------|
| Performance | 2 | 3 | 0 | 5 |
| Security | 11 | 1 | 0 | 12 |
| Reliability | 4 | 1 | 0 | 5 |
| Scalability | 0 | 2 | 1 | 3 |
| Maintainability | 4 | 1 | 0 | 5 |
| Compliance | 0 | 2 | 0 | 2 |
| **Total** | **21** | **10** | **1** | **32** |

### By Priority

**P0 (Critical for Production):** 21 requirements  
**P1 (Required for Maintainability):** 10 requirements  
**P2 (Future Enhancement):** 1 requirement

---

## Verification Methods

| Requirement Type | Verification Method |
|------------------|---------------------|
| Performance | Load testing (k6, Locust), query EXPLAIN analysis |
| Security | SAST (Semgrep, Bandit), penetration testing, dependency scanning |
| Reliability | Chaos engineering, failure injection testing |
| Scalability | Load testing to device/event limits |
| Maintainability | Code review, linting (ruff, ESLint), coverage reports |
| Compliance | Audit log review, data classification assessment |

---

*Document generated based on comprehensive code review findings.*
