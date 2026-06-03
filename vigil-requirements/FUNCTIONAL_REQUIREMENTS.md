# Vigil Dashboard - Functional Requirements Specification

**Document Version:** 1.0  
**Date:** 2026-05-26  
**Based on:** Code Review Findings (MASTER_CODE_REVIEW.md, BACKEND_CODE_REVIEW.md, FRONTEND_CODE_REVIEW.md, SECURITY_AUDIT.md)

---

## Table of Contents

1. [Device Discovery and Management](#1-device-discovery-and-management)
2. [Security Monitoring and Alerting](#2-security-monitoring-and-alerting)
3. [Agent Management](#3-agent-management)
4. [Dashboard and Reporting](#4-dashboard-and-reporting)
5. [Setup and Configuration](#5-setup-and-configuration)

---

## 1. Device Discovery and Management

### FR-001: Multi-Protocol Device Discovery
**Requirement:** The system shall discover network devices using multiple protocols including ARP scanning, Nmap, SNMP, UPnP/SSDP, and mDNS/Bonjour.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Device discovery initiates via API endpoint (`POST /api/discovery/scan`)
- AC2: Discovery supports configurable IP ranges (CIDR notation)
- AC3: Results include device IP, MAC address, hostname, and device type where available
- AC4: Discovery status is queryable via `GET /api/discovery/status/{scan_id}`
- AC5: Scan results are persisted to the database with timestamp

**Source:** BACKEND_CODE_REVIEW.md (device_discovery.py analysis), SECURITY_AUDIT.md (SEC-005)

---

### FR-002: Device Registration and Baseline
**Requirement:** The system shall allow manual device registration with baseline configuration for security monitoring.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: API endpoint accepts MAC address, IP, hostname, and device type
- AC2: MAC address validated using regex: `^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$`
- AC3: IP address validated using Python `ipaddress` module
- AC4: Hostname validated (max 253 chars, alphanumeric, hyphen, dot)
- AC5: Baseline data stored with device record for anomaly detection
- AC6: Duplicate MAC addresses are rejected with 409 Conflict

**Source:** BACKEND_CODE_REVIEW.md (Section 3.2.5 - Input Validation), SECURITY_AUDIT.md (Section 3.4)

---

### FR-003: Device Inventory Management
**Requirement:** The system shall provide CRUD operations for device inventory.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: `GET /api/devices` returns paginated device list with filtering support
- AC2: `GET /api/devices/{id}` returns detailed device information
- AC3: `PATCH /api/devices/{id}` allows updating device metadata
- AC4: `DELETE /api/devices/{id}` removes device with cascade to related alerts
- AC5: Devices can be filtered by: containment_status, device_type, last_seen range
- AC6: Export device list to CSV/JSON format

**Source:** BACKEND_CODE_REVIEW.md (routers/devices.py), MASTER_CODE_REVIEW.md (Section 2.1)

---

### FR-004: Router Discovery and Integration
**Requirement:** The system shall discover and integrate with network routers for device management.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Auto-discovery of routers on local network via UPnP/SSDP
- AC2: Support for multiple router vendors (ASUS, Generic UPnP)
- AC3: Router credentials securely stored using vault encryption
- AC4: Test connectivity endpoint validates router access
- AC5: Import connected devices from router DHCP/ARP tables
- AC6: Support for router-specific features (QoS, parental controls API)

**Source:** FRONTEND_CODE_REVIEW.md (routerDiscovery.js, SetupWizard.js), BACKEND_CODE_REVIEW.md (routers/implementations/)

---

### FR-005: Network Scan Scheduling
**Requirement:** The system shall support scheduled and on-demand network scans.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Configurable scan frequency (hourly, daily, weekly)
- AC2: Scan can be triggered manually via UI and API
- AC3: Scan results compared to baseline with diff report
- AC4: New devices trigger optional alert notification
- AC5: Scan history retained for 90 days

**Source:** BACKEND_CODE_REVIEW.md (device_discovery.py), MASTER_CODE_REVIEW.md (Phase 3 backlog)

---

## 2. Security Monitoring and Alerting

### FR-006: Security Event Detection
**Requirement:** The system shall detect and log security-related events from devices and agents.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Event types include: unauthorized_access, policy_violation, anomaly_detected, threat_detected
- AC2: Events contain: device_id, event_type, description, severity, timestamp, metadata
- AC3: Events support JSON metadata for extensibility
- AC4: Event ingestion via REST API and agent push
- AC5: Duplicate event detection within configurable time window

**Source:** BACKEND_CODE_REVIEW.md (routers/events.py, models.py), SECURITY_AUDIT.md

---

### FR-007: Alert Generation and Management
**Requirement:** The system shall generate security alerts based on events and policies.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Alert created when security event matches policy rules
- AC2: Alert severity levels: CRITICAL, HIGH, MEDIUM, LOW, INFO
- AC3: Alert states: NEW, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
- AC4: `POST /api/alerts/{id}/acknowledge` requires authenticated user
- AC5: Bulk acknowledge operation supports filtering by severity/date
- AC6: Alert resolution requires comment/reason

**Source:** BACKEND_CODE_REVIEW.md (routers/alerts.py), FRONTEND_CODE_REVIEW.md (AlertPanel.js, AlertsPage.js)

---

### FR-008: Email Notification System
**Requirement:** The system shall send email notifications for critical security events.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: SMTP configuration via environment variables (no hardcoded credentials)
- AC2: Email templates for different alert types
- AC3: Rate limiting: max 10 emails per hour per recipient
- AC4: Email queue with retry logic (3 attempts with exponential backoff)
- AC5: Support for HTML and plain text formats
- AC6: Unsubscribe link in all notification emails

**Source:** DEVOPS_CODE_REVIEW.md (Exposed Gmail credentials - SEC-001), SECURITY_AUDIT.md (Section 1.1)

---

### FR-009: Real-Time Event Stream
**Requirement:** The system shall provide real-time event streaming for dashboard updates.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Server-Sent Events (SSE) endpoint at `/api/events/stream`
- AC2: Connection authenticated via HttpOnly cookie (not URL token)
- AC3: Automatic reconnection with backoff on disconnect
- AC4: Heartbeat/ping every 30 seconds
- AC5: Filter events by device, severity, or event type

**Source:** SECURITY_AUDIT.md (Section 1.4 - Token in URL), FRONTEND_CODE_REVIEW.md (EventTimeline.js)

---

### FR-010: Security Policy Engine
**Requirement:** The system shall enforce security policies for device behavior.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: YAML-based policy configuration
- AC2: Policy rules for: device_containment, network_isolation, access_control
- AC3: Policy evaluation on device activity
- AC4: Policy violation logging with alert generation
- AC5: Policy versioning and rollback capability

**Source:** BACKEND_CODE_REVIEW.md (policy.yaml references), MASTER_CODE_REVIEW.md (Section 2.1)

---

## 3. Agent Management

### FR-011: Agent Registration
**Requirement:** The system shall support registration of security monitoring agents.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Agent registration endpoint with API key authentication
- AC2: Agent metadata: hostname, version, capabilities, location
- AC3: Agent status tracking: ONLINE, OFFLINE, ERROR, UPDATING
- AC4: Heartbeat endpoint with 5-minute timeout
- AC5: Auto-deregistration after 24 hours of no heartbeat

**Source:** BACKEND_CODE_REVIEW.md (routers/agents.py), MASTER_CODE_REVIEW.md

---

### FR-012: Agent Configuration Management
**Requirement:** The system shall distribute configuration to registered agents.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Configuration pushed via API to agents
- AC2: Agent acknowledges configuration receipt
- AC3: Configuration versioning with rollback
- AC4: Per-agent and global configuration templates
- AC5: Configuration change audit log

**Source:** BACKEND_CODE_REVIEW.md (agents.py), MASTER_CODE_REVIEW.md

---

### FR-013: Agent Health Monitoring
**Requirement:** The system shall monitor agent health and report status.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Health metrics: CPU, memory, disk, network latency
- AC2: Health dashboard with agent status grid
- AC3: Alert when agent offline > 5 minutes
- AC4: Agent log collection and storage
- AC5: Remote restart capability via authenticated API

**Source:** BACKEND_CODE_REVIEW.md, MASTER_CODE_REVIEW.md

---

## 4. Dashboard and Reporting

### FR-014: Security Dashboard Overview
**Requirement:** The system shall provide a security dashboard with key metrics.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Dashboard displays: total devices, active alerts, recent events, agent status
- AC2: Time-based filtering (last hour, day, week, month)
- AC3: Auto-refresh every 30 seconds
- AC4: Responsive design for desktop and tablet
- AC5: Dark mode theme support

**Source:** FRONTEND_CODE_REVIEW.md (App.js, components/), MASTER_CODE_REVIEW.md (Section 2.2)

---

### FR-015: Event Timeline Visualization
**Requirement:** The system shall display security events in a timeline view.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Chronological event display with timestamp
- AC2: Event filtering by type, severity, device
- AC3: Infinite scroll pagination
- AC4: Event detail modal with full metadata
- AC5: Export filtered events to CSV/JSON
- AC6: Content sanitization using DOMPurify before rendering

**Source:** FRONTEND_CODE_REVIEW.md (EventTimeline.js - XSS risk), SECURITY_AUDIT.md (Section 5.1)

---

### FR-016: Device Management Interface
**Requirement:** The system shall provide a UI for device management operations.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Paginated device table with sorting
- AC2: Device search by name, IP, or MAC
- AC3: Device detail view with history
- AC4: Device containment controls (isolate/release)
- AC5: Device deletion with confirmation dialog

**Source:** FRONTEND_CODE_REVIEW.md (DevicesPage.js), BACKEND_CODE_REVIEW.md

---

### FR-017: Alert Management Interface
**Requirement:** The system shall provide alert management capabilities in the UI.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Alert list with severity badges
- AC2: Bulk acknowledge with confirmation
- AC3: Alert status change tracking
- AC4: Alert filtering by status, severity, date range
- AC5: Alert detail with related events
- AC6: Alert statistics display (new vs acknowledged counts)

**Source:** FRONTEND_CODE_REVIEW.md (AlertPanel.js, AlertsPage.js), BACKEND_CODE_REVIEW.md (routers/alerts.py)

---

### FR-018: Access Heatmap Visualization
**Requirement:** The system shall visualize file/memory access patterns.

**Priority:** P2  
**Acceptance Criteria:**
- AC1: Heatmap showing access frequency by file/path
- AC2: Time-based heatmap (hour of day vs day of week)
- AC3: Click to filter events by selected area
- AC4: Color-coded intensity scale
- AC5: Responsive chart using Recharts or equivalent

**Source:** FRONTEND_CODE_REVIEW.md (AccessHeatmap.js, ToolChart.js)

---

### FR-019: Report Generation
**Requirement:** The system shall generate security reports on demand and scheduled.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: PDF report generation for security summary
- AC2: Report templates: daily summary, weekly audit, incident report
- AC3: Scheduled report delivery via email
- AC4: Report archival for 1 year
- AC5: Report export to CSV, PDF, JSON formats

**Source:** MASTER_CODE_REVIEW.md (Phase 4 backlog)

---

## 5. Setup and Configuration

### FR-020: Setup Wizard
**Requirement:** The system shall provide a multi-step setup wizard for initial configuration.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: Wizard steps: Welcome → Router Discovery → Credentials → Device Import → Complete
- AC2: Progress indicator showing current step
- AC3: Router auto-discovery with manual entry fallback
- AC4: Credential test before proceeding
- AC5: Device import preview with selection
- AC6: Setup state persistence (without credential storage in LocalStorage)
- AC7: Wizard can be resumed after interruption

**Source:** FRONTEND_CODE_REVIEW.md (SetupWizard.js - 600+ lines), SECURITY_AUDIT.md (LocalStorage credential storage)

---

### FR-021: Environment Configuration
**Requirement:** The system shall support configuration via environment variables.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: All hardcoded values moved to env vars (API URLs, database paths, IPs)
- AC2: `.env.example` file with all required variables documented
- AC3: Pydantic Settings validation with descriptive error messages
- AC4: Sensible defaults for development environment
- AC5: Strict validation for production environment
- AC6: Configuration loaded at startup, not on each request

**Source:** BACKEND_CODE_REVIEW.md (Section 9), FRONTEND_CODE_REVIEW.md (hardcoded API URLs), ARCHITECTURE_DECISIONS.md (ADR-007)

---

### FR-022: CORS Configuration
**Requirement:** The system shall support configurable CORS origins.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: `VIGIL_CORS_ORIGINS` environment variable accepts comma-separated URLs
- AC2: Default to localhost only in development
- AC3: Wildcard (`*`) rejected when `allow_credentials=True`
- AC4: CORS preflight responses cached appropriately
- AC5: CORS errors logged with attempted origin

**Source:** BACKEND_CODE_REVIEW.md (main.py - CORS wildcard), SECURITY_AUDIT.md (SEC-002), MASTER_CODE_REVIEW.md

---

### FR-023: Database Configuration
**Requirement:** The system shall support configurable database connections.

**Priority:** P0  
**Acceptance Criteria:**
- AC1: `DATABASE_URL` environment variable for connection string
- AC2: Support SQLite (single file) and PostgreSQL (connection string)
- AC3: Connection pooling configured automatically
- AC4: Database path validation (no traversal attacks)
- AC5: Migration support via Alembic

**Source:** BACKEND_CODE_REVIEW.md (models.py - hardcoded paths), ARCHITECTURE_DECISIONS.md (ADR-004)

---

### FR-024: Admin Operations
**Requirement:** The system shall provide admin-only operations for system management.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Admin role required for destructive operations
- AC2: Database backup/restore endpoints
- AC3: System log access and download
- AC4: User management (if multi-user supported)
- AC5: Audit log of all admin actions

**Source:** BACKEND_CODE_REVIEW.md (routers/admin.py), MASTER_CODE_REVIEW.md

---

### FR-025: Backup and Restore
**Requirement:** The system shall support automated and manual backup/restore.

**Priority:** P1  
**Acceptance Criteria:**
- AC1: Database backup to configurable location
- AC2: Scheduled backups (daily at configurable time)
- AC3: Backup retention policy (keep last N backups)
- AC4: Restore from backup with verification
- AC5: Backup encryption at rest

**Source:** DEVOPS_CODE_REVIEW.md (No backup strategy), MASTER_CODE_REVIEW.md (Phase 4)

---

## Requirements Summary

| Category | P0 Count | P1 Count | P2 Count | Total |
|----------|----------|----------|----------|-------|
| Device Discovery & Management | 4 | 1 | 0 | 5 |
| Security Monitoring & Alerting | 4 | 3 | 0 | 7 |
| Agent Management | 1 | 2 | 0 | 3 |
| Dashboard & Reporting | 4 | 1 | 1 | 6 |
| Setup & Configuration | 4 | 2 | 0 | 6 |
| **Total** | **17** | **9** | **1** | **27** |

---

## Requirement ID Prefix Key

- **FR-001 to FR-009:** Core security and discovery features
- **FR-010 to FR-019:** Monitoring, alerting, and dashboard
- **FR-020 to FR-027:** Setup, configuration, and administration

---

*Document generated based on comprehensive code review findings.*
