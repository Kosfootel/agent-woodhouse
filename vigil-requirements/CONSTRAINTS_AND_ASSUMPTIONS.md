# Vigil Dashboard - Constraints and Assumptions

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Based on:** Code Review Findings (DEVOPS_CODE_REVIEW.md, MASTER_CODE_REVIEW.md, ARCHITECTURE_DECISIONS.md)

---

## Table of Contents

1. [Hardware Constraints](#1-hardware-constraints)
2. [Network Constraints](#2-network-constraints)
3. [Technology Stack Decisions](#3-technology-stack-decisions)
4. [Security Compliance Requirements](#4-security-compliance-requirements)
5. [Operational Constraints](#5-operational-constraints)
6. [Assumptions](#6-assumptions)

---

## 1. Hardware Constraints

### HC-001: Jetson Orin Nano 8GB as Target Platform
**Constraint:** The primary deployment target is a Jetson Orin Nano with 8GB RAM.

**Implications:**
- Memory usage must stay within 6GB available for containers (OS reserves ~2GB)
- CPU is ARM64 architecture (not x86_64)
- Limited GPU acceleration available for ML workloads
- Storage likely constrained to SD card or USB SSD

**Requirements:**
- Backend container memory limit: 1GB maximum
- Frontend container memory limit: 256MB maximum
- Database size must be managed (SQLite with cleanup/purge)
- Multi-arch Docker images required (linux/arm64 + linux/amd64)

**Source:** DEVOPS_CODE_REVIEW.md (Jetson Orin references), MASTER_CODE_REVIEW.md (Deployment context)

---

### HC-002: Local Network Deployment Only
**Constraint:** The system is designed for local/home network deployment, not cloud.

**Implications:**
- No cloud dependencies allowed (no AWS S3, Azure services, etc.)
- No external API calls except for email/SMTP
- All data remains on-premise
- No CDN usage for assets

**Requirements:**
- All services containerized and self-contained
- Offline-capable where possible
- Local email relay or Gmail SMTP only
- Local logging, no cloud log aggregation

**Source:** MASTER_CODE_REVIEW.md (Context), DEVOPS_CODE_REVIEW.md (Local deployment focus)

---

### HC-003: Single-Node Deployment
**Constraint:** The system runs on a single node (no Kubernetes cluster).

**Implications:**
- No high availability through clustering
- No horizontal scaling
- Single point of failure for hardware
- SQLite acceptable (no concurrent writes from multiple nodes)

**Requirements:**
- Docker Compose deployment model
- Single database instance
- Local volume mounts for persistence
- Backup/restore handled via scripts

**Source:** DEVOPS_CODE_REVIEW.md (docker-compose.yml analysis)

---

## 2. Network Constraints

### NC-001: 192.168.50.0/24 Network Segment
**Constraint:** The target network uses 192.168.50.0/24 addressing.

**Implications:**
- Router expected at 192.168.50.1
- Dashboard deployed at 192.168.50.30
- Device discovery scans limited to this subnet
- Hardcoded IPs must be configurable

**Requirements:**
- Network range configurable via environment variable
- No hardcoded IP addresses in source code
- CIDR notation support for scan configuration
- Subnet validation before scanning

**Source:** FRONTEND_CODE_REVIEW.md (9 hardcoded API URLs), BACKEND_CODE_REVIEW.md (CORS hardcoded IPs)

---

### NC-002: No Public Internet Exposure
**Constraint:** The system shall not be exposed to the public internet.

**Implications:**
- No public DNS names required
- TLS certificates can be self-signed or from private CA
- No DDoS protection required
- Simpler firewall rules

**Requirements:**
- Access restricted to RFC1918 private addresses
- Optional Tailscale/ZeroTier integration for remote access
- No public ingress rules in firewall
- Optional VPN-based remote access

**Source:** MASTER_CODE_REVIEW.md (Security context), DEVOPS_CODE_REVIEW.md (Tailscale mention in docker-compose.bak)

---

### NC-003: Home Router Integration Required
**Constraint:** The system integrates with consumer-grade home routers.

**Implications:**
- Router protocols: UPnP, SNMP, HTTP admin interface
- Authentication: Basic Auth, cookie-based sessions
- Limited API documentation from router manufacturers
- Firmware version variations

**Requirements:**
- Support ASUS routers (primary)
- Support generic UPnP routers
- Credential storage for router authentication
- Fallback manual configuration

**Source:** BACKEND_CODE_REVIEW.md (routers/implementations/), FRONTEND_CODE_REVIEW.md (routerDiscovery.js)

---

### NC-004: Network Mode Host Removal Required
**Constraint:** `network_mode: host` must be removed for security.

**Implications:**
- Port mapping required for all exposed services
- Docker DNS service discovery replaces localhost references
- Container-to-container communication via Docker network
- Suricata IDS requires special handling (may need host networking)

**Requirements:**
- Explicit port mappings in docker-compose.yml
- Docker bridge network for inter-service communication
- Backend accessible at `http://backend:8000` internally
- Frontend accessible at `http://dashboard:8080` internally

**Source:** DEVOPS_CODE_REVIEW.md (network_mode: host - CRITICAL), MASTER_CODE_REVIEW.md (SEC-004)

---

## 3. Technology Stack Decisions

### TS-001: FastAPI + SQLAlchemy Backend
**Decision:** Continue using FastAPI with SQLAlchemy ORM.

**Rationale:**
- Existing expertise in codebase
- Good async/await support
- Automatic OpenAPI generation
- Active community

**Constraints:**
- Python 3.11+ required
- SQLAlchemy 2.0 patterns
- Pydantic v2 for validation
- Async database operations preferred

**Migration Notes:**
- Standardize on `app/main.py` entry point
- Remove alternative `backend/main.py`
- Consolidate database patterns (SQLAlchemy ORM, not raw SQLite3)

**Source:** BACKEND_CODE_REVIEW.md (FastAPI analysis), ARCHITECTURE_DECISIONS.md

---

### TS-002: React 18 Frontend
**Decision:** Continue using React 18 with functional components.

**Rationale:**
- Modern React patterns established
- Large ecosystem
- Good TypeScript support (when adopted)
- React Router v7 already in use

**Constraints:**
- React 18.2+ required
- React Router v7 patterns
- No class components (functional only)
- Hooks pattern throughout

**Migration Notes:**
- Consider Zustand for state management (ADR-001)
- Add React Query for server state
- Implement lazy loading for routes

**Source:** FRONTEND_CODE_REVIEW.md (React 18 analysis), ARCHITECTURE_DECISIONS.md (ADR-001)

---

### TS-003: SQLite Database (Phase 1)
**Decision:** Retain SQLite for Phase 1, evaluate PostgreSQL for Phase 2.

**Rationale:**
- Zero configuration deployment
- Single file backup
- Sufficient for home network scale
- Lower resource usage

**Constraints:**
- Write concurrency limitations
- No multi-node deployment
- File-based backup/restore
- Manual migration path

**Migration Notes:**
- Add Alembic for migrations (ADR-004)
- Design schema for PostgreSQL compatibility
- Connection pooling with SQLAlchemy
- JSON column support where needed

**Source:** BACKEND_CODE_REVIEW.md (Database review), ARCHITECTURE_DECISIONS.md (ADR-004)

---

### TS-004: Docker + Docker Compose
**Decision:** Continue using Docker Compose for deployment.

**Rationale:**
- Simple deployment model
- Works on Jetson Orin
- Multi-arch support (amd64/arm64)
- No Kubernetes complexity

**Constraints:**
- Docker Engine 24.0+
- Docker Compose v2 plugin
- Linux host required (Jetson/Linux server)
- Container resource limits enforced

**Migration Notes:**
- Consolidate 5+ compose files to 2 (docker-compose.yml, docker-compose.prod.yml)
- Remove network_mode: host
- Add health checks to all services
- Non-root container execution

**Source:** DEVOPS_CODE_REVIEW.md (Configuration drift), MASTER_CODE_REVIEW.md

---

### TS-005: GitHub Actions CI/CD
**Decision:** Continue using GitHub Actions for CI/CD.

**Rationale:**
- Existing workflows functional
- Free for public repositories
- Multi-arch build support
- Good integration with GitHub

**Constraints:**
- Workflow run time limits (6 hours)
- Concurrent job limits
- Secrets stored in GitHub
- Self-hosted runner not required

**Migration Notes:**
- Fix SSH StrictHostKeyChecking
- Add Trivy failure on CRITICAL vulnerabilities
- Pin action versions to SHA
- Add Cosign image signing

**Source:** DEVOPS_CODE_REVIEW.md (CI/CD analysis), MASTER_CODE_REVIEW.md

---

## 4. Security Compliance Requirements

### SC-001: Home Network Security Focus
**Constraint:** System focuses on home network security, not enterprise.

**Implications:**
- Single administrator (home owner)
- No RBAC complexity needed initially
- No LDAP/AD integration required
- Local authentication sufficient

**Requirements:**
- Simple authentication model
- Admin/user distinction (if multi-user)
- No SSO/SAML required
- Optional guest view mode

**Source:** MASTER_CODE_REVIEW.md (Project scope)

---

### SC-002: GDPR/CCPA Not Required
**Constraint:** Home use exempts system from GDPR/CCPA compliance.

**Implications:**
- No data subject rights automation required
- No privacy impact assessment needed
- No data processing agreements required
- Simpler data retention policies

**Requirements:**
- Still implement data minimization
- Allow data export for user
- Implement data deletion capability
- Document what data is collected

**Source:** MASTER_CODE_REVIEW.md (Home network context)

---

### SC-003: Security Hardening Before Production
**Constraint:** Phase 1 security blockers must be resolved before any production use.

**Requirements (from QUICK_WINS.md):**
1. Rotate exposed Gmail credentials
2. Remove network_mode: host
3. Fix CORS wildcard configuration
4. Implement random salt in crypto
5. Replace hardcoded API URLs with env vars
6. Remove credentials from LocalStorage
7. Fix JWT secret auto-generation
8. Validate IP addresses before subprocess
9. Fix XXE vulnerability in XML parsing

**Source:** MASTER_CODE_REVIEW.md (Executive Summary), QUICK_WINS.md

---

### SC-004: OWASP ASVS Alignment
**Constraint:** Security controls aligned with OWASP ASVS Level 2 (Application Verification Standard).

**Requirements:**
- Input validation (ASVS 5)
- Authentication (ASVS 2)
- Session management (ASVS 3)
- Access control (ASVS 4)
- Cryptography (ASVS 6)
- Error handling (ASVS 7)
- Data protection (ASVS 8)

**Source:** SECURITY_AUDIT.md (Various CWE references)

---

## 5. Operational Constraints

### OC-001: Linux-Hosted Deployment
**Constraint:** The system runs on Linux hosts only.

**Implications:**
- No Windows Server support required
- No macOS server support required
- Shell scripts can use bash
- systemd available for service management

**Requirements:**
- Deployment scripts use bash
- Container runtime: Docker Engine on Linux
- File paths use forward slashes
- systemd service files if needed

**Source:** DEVOPS_CODE_REVIEW.md (deploy.sh, deployment/gx10/)

---

### OC-002: Manual Deployment Process
**Constraint:** Deployment currently requires manual steps.

**Implications:**
- No fully automated zero-downtime deployment
- Some downtime during updates expected
- Human approval required for production deployments
- Rollback capability required

**Requirements:**
- Documented deployment runbook
- Health checks before marking deployment complete
- Automatic rollback on failure
- Backup before deployment

**Source:** DEVOPS_CODE_REVIEW.md (Deployment scripts), MASTER_CODE_REVIEW.md (Phase 4)

---

### OC-003: Limited Monitoring Infrastructure
**Constraint:** No existing Prometheus/Grafana infrastructure.

**Implications:**
- Metrics export optional (Prometheus format)
- Logs are file-based, not centralized
- Alerting via email only
- Manual health checking

**Requirements:**
- Basic health endpoint sufficient initially
- Structured logging for future parsing
- Metrics endpoint as optional enhancement
- Email-based alerting

**Source:** DEVOPS_CODE_REVIEW.md (Monitoring section), MASTER_CODE_REVIEW.md

---

### OC-004: Email as Primary Notification
**Constraint:** Email is the primary alerting mechanism.

**Implications:**
- SMTP configuration required
- Gmail SMTP support needed
- Rate limiting to avoid spam
- No SMS/push notification initially

**Requirements:**
- SMTP configuration via environment variables
- TLS required for SMTP connections
- Queue-based email sending
- Retry logic for failed sends

**Source:** SECURITY_AUDIT.md (Gmail credentials), DEVOPS_CODE_REVIEW.md

---

## 6. Assumptions

### A-001: Single Administrator
**Assumption:** The system has a single administrator user (home owner).

**Implications:**
- No multi-tenant considerations
- No complex user management
- Admin has full system access
- No need for RBAC initially

**Risk:** If assumption changes, auth system redesign required.

**Source:** MASTER_CODE_REVIEW.md (Context)

---

### A-002: Private Network Trust
**Assumption:** The local network (192.168.50.0/24) is trusted.

**Implications:**
- Internal API authentication may be relaxed
- mTLS not required internally
- Focus on external threat protection
- Agent authentication still required

**Risk:** If network compromised, additional authentication needed.

**Mitigation:** Defense in depth - authenticate even internally.

**Source:** MASTER_CODE_REVIEW.md (Security context)

---

### A-003: Static IP Addresses
**Assumption:** Devices maintain static IP addresses or DHCP reservations.

**Implications:**
- IP-based device tracking acceptable
- Re-scanning needed when IPs change
- MAC address is primary identifier
- Router provides stable DHCP assignments

**Risk:** Dynamic IPs may cause device duplication.

**Mitigation:** Deduplication by MAC address, not IP.

**Source:** BACKEND_CODE_REVIEW.md (Device discovery)

---

### A-004: Router Admin Access Available
**Assumption:** Administrator has router admin credentials.

**Implications:**
- Router integration features require credentials
- Fallback to manual device entry available
- Setup wizard can configure router connection
- Credential storage required

**Risk:** If router credentials lost, some features unavailable.

**Mitigation:** Graceful degradation without router access.

**Source:** FRONTEND_CODE_REVIEW.md (SetupWizard.js)

---

### A-005: Development on Separate Machine
**Assumption:** Development occurs on machines separate from Jetson deployment.

**Implications:**
- Docker multi-arch builds required
- Remote deployment via SSH
- Cross-platform development support needed
- Development environment differs from production

**Risk:** "Works on my machine" issues.

**Mitigation:** CI/CD builds match production environment.

**Source:** DEVOPS_CODE_REVIEW.md (CI/CD workflow)

---

### A-006: Internet Access for Email Only
**Assumption:** System has internet access only for SMTP/email functionality.

**Implications:**
- No cloud dependencies
- Updates pulled manually or via CI/CD
- Offline operation is primary mode
- Email alerts require internet

**Risk:** No alerts during internet outages.

**Mitigation:** Local logging and queue for deferred sending.

**Source:** MASTER_CODE_REVIEW.md (Architecture context)

---

### A-007: Moderate Scale (≤100 Devices)
**Assumption:** Target deployment has ≤100 network devices.

**Implications:**
- SQLite sufficient for storage
- Single backend instance adequate
- No sharding required
- Simple indexing sufficient

**Risk:** Scaling beyond 100 devices.

**Mitigation:** Architecture supports PostgreSQL migration.

**Source:** BACKEND_CODE_REVIEW.md (Database), MASTER_CODE_REVIEW.md

---

### A-008: No High Availability Requirement
**Assumption:** System can tolerate brief downtime during updates.

**Implications:**
- No active-active clustering
- Updates may cause brief outage
- Single node deployment acceptable
- Backup/restore for disaster recovery

**Risk:** Extended outages for hardware failure.

**Mitigation:** Regular backups, documented restore process.

**Source:** DEVOPS_CODE_REVIEW.md (Single-node deployment)

---

## Constraint Summary Matrix

| Category | Constraint ID | Impact Level | Flexibility |
|----------|---------------|--------------|-------------|
| Hardware | HC-001 | High | Low |
| Hardware | HC-002 | High | Low |
| Hardware | HC-003 | Medium | Low |
| Network | NC-001 | High | Medium |
| Network | NC-002 | High | Low |
| Network | NC-003 | Medium | Medium |
| Network | NC-004 | Critical | None |
| Technology | TS-001 | High | Low |
| Technology | TS-002 | High | Low |
| Technology | TS-003 | Medium | Medium |
| Technology | TS-004 | High | Low |
| Technology | TS-005 | Medium | Medium |
| Security | SC-001 | Medium | Medium |
| Security | SC-002 | Low | Low |
| Security | SC-003 | Critical | None |
| Security | SC-004 | High | Low |
| Operational | OC-001 | Medium | Low |
| Operational | OC-002 | Medium | Medium |
| Operational | OC-003 | Low | High |
| Operational | OC-004 | Medium | Medium |

**Legend:**
- **Impact Level:** How much the constraint affects design decisions
- **Flexibility:** How negotiable the constraint is (None/Low/Medium/High)

---

## Assumption Risk Register

| Assumption | Risk if Invalid | Mitigation | Priority |
|------------|-----------------|------------|----------|
| A-001: Single Admin | Redesign auth system | Keep auth modular | Medium |
| A-002: Trusted Network | Compromise propagation | Authenticate internally | High |
| A-003: Static IPs | Device duplication | MAC-based dedup | Medium |
| A-004: Router Access | Reduced functionality | Manual entry fallback | Low |
| A-005: Dev on Separate | Platform bugs | CI/CD multi-arch | Medium |
| A-006: Internet for Email | No remote alerts | Local logging + queue | Medium |
| A-007: ≤100 Devices | Performance issues | PostgreSQL path | Medium |
| A-008: No HA Required | Extended downtime | Backup/restore docs | Low |

---

*Document generated based on comprehensive code review findings.*
