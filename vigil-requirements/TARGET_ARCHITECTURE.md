# Vigil Dashboard - Target Architecture Specification

**Version:** 2.0  
**Date:** 2026-05-26  
**Status:** Draft - Architecture Design Phase

---

## 1. Executive Summary

This document defines the target architecture for the Vigil Dashboard v2.0, addressing all critical security vulnerabilities and architectural issues identified in the code review. The new architecture follows the **Compact**, **Stable**, **Maintainable**, and **Secure** design principles.

### Key Improvements Over v1.0

| Area | v1.0 State | v2.0 Target |
|------|-----------|-------------|
| **Security** | 7 critical vulnerabilities | Defense in depth, zero critical issues |
| **State Management** | Prop drilling, inconsistent | Zustand + React Query |
| **API Client** | Mixed fetch/axios, hardcoded URLs | Standardized Axios with interceptors |
| **Database** | SQLite, no migrations, hardcoded paths | PostgreSQL with Alembic migrations |
| **Networking** | `network_mode: host` | Isolated Docker networks with TLS |
| **Authentication** | JWT in localStorage | Cookie-based sessions (HttpOnly) |
| **Testing** | 0% frontend, ~10% backend | 70%+ coverage pyramid |
| **Deployment** | Manual SSH, no rollback | GitHub Actions + health-verified rollback |

---

## 2. Architecture Principles

### 2.1 Compact
- Minimize dependencies - remove unused (redis, slowapi initially)
- Bundle/container size optimization
- Single-responsibility components
- Eliminate code duplication

### 2.2 Stable
- Stateless services where possible
- Clear failure modes and graceful degradation
- Health checks on all services
- Circuit breakers for external calls

### 2.3 Maintainable
- Clear boundaries between components
- Domain-driven module organization
- Consistent patterns across codebase
- Comprehensive documentation

### 2.4 Secure
- Defense in depth - multiple security layers
- Minimal attack surface
- No hardcoded credentials or IPs
- Principle of least privilege

---

## 3. System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL USERS                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Admin     │  │   Analyst   │  │   Viewer    │  │  Setup User │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CADDY REVERSE PROXY                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  • TLS termination (auto HTTPS via Let's Encrypt or Tailscale certs)  │
│  │  • Request routing /api/* → Backend, /* → Frontend                    │
│  │  • Rate limiting (per IP)                                             │
│  │  • Security headers injection                                         │
│  │  • Static asset caching                                               │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   REACT FRONTEND    │    │   FASTAPI BACKEND   │    │  GRAFANA (Optional) │
│   (Nginx serving)   │    │   (Uvicorn/Gunicorn)│    │  (Observability)   │
│                     │    │                     │    │                     │
│  • Static SPA       │    │  • REST API         │    │  • Metrics          │
│  • React Router     │    │  • JWT/Session Auth │    │  • Dashboards       │
│  • Zustand State    │    │  • Business Logic   │    │  • Alerts           │
└──────────┬──────────┘    └──────────┬──────────┘    └─────────────────────┘
           │                          │
           │    ┌─────────────────────┘
           │    │
           │    ▼
           │  ┌──────────────────────────────────────────────────────────────┐
           │  │                    DATA LAYER                                  │
           │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
           │  │  │ PostgreSQL  │  │   Redis     │  │  Prometheus │          │
           │  │  │  (Primary)  │  │  (Sessions) │  │  (Metrics)  │          │
           │  │  └─────────────┘  └─────────────┘  └─────────────┘          │
           │  └──────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Router    │  │  Tailscale  │  │   SMTP      │  │   ntfy      │         │
│  │  (UPnP/SSH) │  │  (Network)  │  │  (Alerts)   │  │ (Push)      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Architecture

### 4.1 Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REACT APPLICATION                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        APP LAYER                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   App.jsx   │  │  Router.jsx │  │ ErrorBoundary│                    │  │
│  │  │ (Entry)     │  │ (Routes)    │  │ (Global)    │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│  ┌───────────────────────────┼───────────────────────────────────────────┐│
│  │                      PAGE LAYER                                        ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │ Dashboard   │ │  Devices    │ │   Alerts    │ │    Setup    │      ││
│  │  │   Page      │ │   Page      │ │    Page     │ │    Page     │      ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                              │                                            │
│  ┌───────────────────────────┼───────────────────────────────────────────┐│
│  │                   COMPONENT LAYER                                      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    ││
│  │  │  Layout/    │ │  Device/    │ │   Alert/    │ │   Setup/    │    ││
│  │  │  Header/    │ │  List/Card/ │ │   List/     │ │   Wizard/   │    ││
│  │  │  Sidebar/   │ │  Form/      │ │   Detail/   │ │   Steps/    │    ││
│  │  │  Footer     │ │  Chart      │ │   Actions   │ │   Form      │    ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                              │                                            │
│  ┌───────────────────────────┼───────────────────────────────────────────┐│
│  │                      HOOK LAYER                                        ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     ││
│  │  │  useAuth    │ │  useDevices │ │ useAlerts   │ │  useSetup   │     ││
│  │  │  useApi     │ │  usePolling │ │ useForm     │ │  useWizard  │     ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                              │                                            │
│  ┌───────────────────────────┼───────────────────────────────────────────┐│
│  │                     STATE LAYER                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────┐ ││
│  │  │              ZUSTAND (Global UI State)                           │ ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ ││
│  │  │  │  uiStore    │ │  authStore  │ │  filterStore│ │ prefsStore  │ │ ││
│  │  │  │  (sidebar)  │ │  (user)     │ │  (filters)  │ │ (settings)  │ │ ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ ││
│  │  └─────────────────────────────────────────────────────────────────┘ ││
│  │                                                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐  ││
│  │  │           REACT QUERY (Server State)                           │  ││
│  │  │  • Automatic caching                                           │  ││
│  │  │  • Background refetching                                       │  ││
│  │  │  • Optimistic updates                                          │  ││
│  │  │  • Request deduplication                                       │  ││
│  │  └─────────────────────────────────────────────────────────────────┘  ││
│  └───────────────────────────────────────────────────────────────────────┘│
│                              │                                            │
│  ┌───────────────────────────┼───────────────────────────────────────────┐│
│  │                     API LAYER                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────┐  ││
│  │  │              AXIOS CLIENT                                        │  ││
│  │  │  ┌─────────────────────────────────────────────────────────────┐  ││
│  │  │  │ • Base URL from env (REACT_APP_API_URL)                    │  ││
│  │  │  │ • Request interceptor: CSRF token, request ID               │  ││
│  │  │  │ • Response interceptor: Error handling, token refresh       │  ││
│  │  │  │ • Request cancellation support                              │  ││
│  │  │  └─────────────────────────────────────────────────────────────┘  ││
│  │  └─────────────────────────────────────────────────────────────────┘  ││
│  └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Backend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI APPLICATION                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ENTRY LAYER                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   main.py   │  │   config    │  │ lifespan    │  │ middleware  │  │  │
│  │  │ (app init)  │  │ (settings)  │  │ (startup)   │  │ (security)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐│
│  │                        ROUTER LAYER                                      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │  /devices   │ │  /security  │ │   /alerts   │ │   /admin    │      ││
│  │  │  (CRUD)     │ │  (scan/pol) │ │  (mgmt)     │ │  (config)   │      ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │   /setup    │ │  /discovery │ │   /auth     │ │   /health   │      ││
│  │  │  (wizard)   │ │  (network)  │ │  (login)    │ │  (status)   │      ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐│
│  │                      SERVICE LAYER                                     ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        ││
│  │  │  Device     │ │  Security   │ │   Alert     │ │  Discovery  │        ││
│  │  │  Service    │ │  Service    │ │   Service   │ │  Service    │        ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        ││
│  │  │   Auth      │ │  Crypto     │ │  Notification│ │   Router    │      ││
│  │  │  Service    │ │  Service    │ │   Service    │   Service    │      ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────────┐│
│  │                      DATA LAYER                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────┐  ││
│  │  │              REPOSITORY PATTERN                                    │  ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │  ││
│  │  │  │ DeviceRepo  │ │ SecurityRepo│ │  AlertRepo  │ │  EventRepo  │ │  ││
│  │  │  │ (SQLAlchemy)│ │ (SQLAlchemy)│ │ (SQLAlchemy)│ │ (SQLAlchemy)│ │  ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │  ││
│  │  └─────────────────────────────────────────────────────────────────┘  ││
│  │                                                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────┐  ││
│  │  │              DATABASE MODELS                                     │  ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │  ││
│  │  │  │   Device    │ │   Alert     │ │   Event     │ │    User     │ │  ││
│  │  │  │   Model     │ │   Model     │ │   Model     │ │   Model     │ │  ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │  ││
│  │  └─────────────────────────────────────────────────────────────────┘  ││
│  └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER NETWORKS                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      TRAEFIK/CADDY NETWORK                             │  │
│  │  External-facing, TLS terminated                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│         ┌────────────────────────┼────────────────────────┐                │
│         │                        │                        │                │
│  ┌──────┴───────┐         ┌──────┴───────┐         ┌──────┴───────┐       │
│  │   CADDY      │         │   BACKEND     │         │   FRONTEND   │       │
│  │   Network    │─────────│   Network     │─────────│   Network    │       │
│  │  (proxy)     │         │  (internal)   │         │  (internal)  │       │
│  └──────────────┘         └──────┬───────┘         └──────────────┘       │
│                                  │                                         │
│                    ┌─────────────┼─────────────┐                         │
│                    │             │             │                         │
│             ┌──────┴─────┐ ┌────┴────┐ ┌─────┴────┐                     │
│             │ PostgreSQL │ │  Redis  │ │ Prometheus│                     │
│             │  Network   │ │ Network │ │ Network  │                     │
│             └────────────┘ └─────────┘ └──────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONTAINER SECURITY                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SECURITY CONTEXT                                   │  │
│  │                                                                       │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │   │   Non-root  │  │ Read-only   │  │  Drop ALL   │  │ No new      │   │  │
│  │   │   User      │  │   FS        │  │ capabilities│  │ privileges  │   │  │
│  │   │  (UID 1000) │  │ (tmpfs rw)  │  │  (except)   │  │             │   │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                       │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │   │  Resource │  │  Security   │  │   Health    │  │   Seccomp   │   │  │
│  │   │   Limits  │  │   Headers   │  │   Checks    │  │   Profile   │   │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagrams

### 5.1 Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │ Frontend │     │  Axios   │     │ Backend  │     │  Redis   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │  Login (user/pwd)               │                │                │
     │────────────────>│               │                │                │
     │                │  POST /auth/login               │                │
     │                │────────────────>│               │                │
     │                │                │  POST /auth/login               │
     │                │                │────────────────>│                │
     │                │                │                │ Verify password│
     │                │                │                │───────────────>│
     │                │                │                │<───────────────│
     │                │                │                │ Create session │
     │                │                │                │───────────────>│
     │                │                │                │<───────────────│
     │                │                │  Set-Cookie: session=...       │
     │                │                │<────────────────│                │
     │                │  Set-Cookie: session=...                        │
     │                │<───────────────│                │                │
     │                │ Store in Zustand              │                │
     │                │ (auth state only)             │                │
     │<────────────────│                │                │                │
     │                │                │                │                │
     │                │                              [Cookie automatically │
     │                │                               sent by browser]   │
     │                │                │                │                │
     │  Access protected route         │                │                │
     │────────────────>│               │                │                │
     │                │ GET /api/devices (cookie auto-sent)            │
     │                │────────────────>│                │                │
     │                │                │ GET /api/devices (cookie auto-sent)
     │                │                │────────────────>│                │
     │                │                │                │ Validate session│
     │                │                │                │───────────────>│
     │                │                │                │<───────────────│
     │                │                │                │ Query DB       │
     │                │                │ 200 OK + data  │<───────────────│
     │                │  200 OK + data │<───────────────│                │
     │                │<───────────────│                │                │
     │  Display data  │                │                │                │
     │<────────────────│                │                │                │
```

### 5.2 Device Discovery Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │ Frontend │     │ Backend  │     │ Discovery│     │ Network  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │  Initiate discovery                              │                │
     │────────────────>│               │                │                │
     │                │ POST /discovery/scan            │                │
     │                │────────────────>│                │                │
     │                │                │ Queue async task│                │
     │                │                │───────────────>│                │
     │                │                │                │ Scan UPnP/ARP   │
     │                │                │                │────────────────>│
     │                │                │                │<───────────────│
     │                │                │                │ Scan complete  │
     │                │                │<───────────────│                │
     │                │                │ Save results  │                │
     │                │                │───────────────>│                │
     │                │                │ (to DB)        │                │
     │                │                │<───────────────│                │
     │                │  202 Accepted (async)            │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │  Poll for results (React Query polling)         │                │
     │────────────────>│               │                │                │
     │                │ GET /discovery/status (poll)    │                │
     │                │────────────────>│                │                │
     │                │                │ Check task status               │
     │                │                │<───────────────│                │
     │                │  Progress updates (SSE/WebSocket)                │
     │                │<───────────────│                │                │
     │  Show progress │                │                │                │
     │<────────────────│                │                │                │
     │                │                │                │                │
```

### 5.3 Alert Processing Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Security │     │ Backend  │     │  Alert   │     │  SMTP    │     │  ntfy    │
│  Event   │     │ Service  │     │ Service  │     │ Service  │     │ Service  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ Security event detected          │                │                │
     │────────────────>│               │                │                │
     │                │ Create alert   │                │                │
     │                │────────────────>│                │                │
     │                │                │ Classify severity               │
     │                │                │────────────────────>│           │
     │                │                │ Check notification rules        │
     │                │                │───────────────┐                │
     │                │                │               │                │
     │                │                │  Email enabled│                │
     │                │                │───────────────>│                │
     │                │                │                │ Send email     │
     │                │                │                │───────────────>│
     │                │                │                │<───────────────│
     │                │                │<───────────────│                │
     │                │                │               │                │
     │                │                │  Push enabled │                │
     │                │                │────────────────>│                │
     │                │                │                │ POST to ntfy   │
     │                │                │                │────────────────>│
     │                │                │                │<───────────────│
     │                │                │<─────────────────────│        │
     │                │                │               │                │
     │                │                │ Store in DB   │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │                │ WebSocket/SSE push to frontend  │                │
     │                │───────────────────────────────────────────────────>│
     │                │                │                │                │
```

---

## 6. Technology Stack

### 6.1 Frontend Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Framework | React 18 | Familiar, proven, good ecosystem |
| Language | TypeScript | Type safety, better DX, fewer bugs |
| Routing | React Router v7 | Latest, type-safe, data loaders |
| State (Client) | Zustand | Minimal boilerplate, small bundle (~2KB) |
| State (Server) | React Query (TanStack Query) | Caching, synchronization, background updates |
| HTTP Client | Axios | Interceptors, request cancellation, wide browser support |
| Styling | Tailwind CSS | Utility-first, small bundle, consistent design system |
| Icons | Lucide React | Tree-shakeable, consistent style |
| Forms | React Hook Form + Zod | Performance, validation, type safety |
| Charts | Recharts | Existing dependency, sufficient for needs |
| Testing | Vitest + RTL + MSW | Fast, native ESM, good mocking |

### 6.2 Backend Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Framework | FastAPI | Async, type-safe, auto OpenAPI docs |
| Language | Python 3.12 | Performance, modern features |
| Database | PostgreSQL 16 | Production-grade, JSON support, concurrent |
| ORM | SQLAlchemy 2.0 | Async support, type hints, Alembic integration |
| Migrations | Alembic | Industry standard, versioned migrations |
| Auth | Starlette Sessions + CSRF | XSS-resistant (HttpOnly cookies) |
| Crypto | cryptography (Python) | Modern, well-audited |
| Password Hashing | bcrypt | Secure, widely used |
| Session Store | Redis | Fast, TTL support, pub/sub for real-time |
| Caching | Redis | Reuse existing Redis for caching |
| Task Queue | Celery + Redis | Async tasks, scheduling, retries |
| Validation | Pydantic v2 | Fast, strict, great error messages |
| Config | Pydantic Settings | Env var validation, type safety |
| Testing | pytest + pytest-asyncio + pytest-cov | Async support, coverage reporting |

### 6.3 Infrastructure Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Reverse Proxy | Caddy | Auto HTTPS, simple config, Tailscale integration |
| Container Runtime | Docker | Ubiquitous, good tooling |
| Orchestration | Docker Compose | Sufficient for single-host, simple |
| CI/CD | GitHub Actions | Integrated, free for public repos, good marketplace |
| Registry | GitHub Container Registry (GHCR) | Integrated with Actions, free for public |
| Monitoring | Prometheus + Grafana | Industry standard, good alerting |
| Logs | Loki + Grafana | Integrated with Grafana, cost-effective |
| Secrets | Docker Secrets / GitHub Secrets | Native integration, no extra infrastructure |
| Backup | restic | Encrypted, deduplicated, multiple backends |

---

## 7. Integration Points

### 7.1 External Integrations

| Service | Protocol | Purpose | Security |
|---------|----------|---------|----------|
| Home Router | UPnP/SSH | Device discovery | SSH keys, no passwords in storage |
| Gmail SMTP | SMTPS (TLS) | Email alerts | App password, env var only |
| ntfy | HTTPS | Push notifications | Token auth, env var |
| Tailscale | WireGuard | Private networking | Tailscale ACLs, ephemeral keys |

### 7.2 Internal Integration Contracts

```yaml
# API Contract Example
paths:
  /api/v1/devices:
    get:
      summary: List devices
      parameters:
        - name: limit
          in: query
          type: integer
          default: 50
        - name: status
          in: query
          type: string
          enum: [active, inactive, quarantine]
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  count: { type: integer }
                  devices:
                    type: array
                    items: { $ref: '#/components/schemas/Device' }

components:
  schemas:
    Device:
      type: object
      required: [id, mac, ip]
      properties:
        id: { type: string, format: uuid }
        mac: { type: string, pattern: '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$' }
        ip: { type: string, format: ipv4 }
        hostname: { type: string }
        status: { type: string, enum: [active, inactive, quarantine] }
        last_seen: { type: string, format: date-time }
        created_at: { type: string, format: date-time }
```

---

## 8. Migration Strategy

### 8.1 Phase 1: Security Lockdown (Week 1)

1. **Immediate Fixes**
   - Rotate exposed Gmail credentials
   - Fix CORS configuration (no wildcard with credentials)
   - Implement random salt in crypto.py
   - Replace hardcoded API URLs with environment variables
   - Remove credentials from LocalStorage

2. **Network Security**
   - Remove `network_mode: host`
   - Implement proper Docker networks
   - Add Caddy reverse proxy with TLS

3. **Container Security**
   - Run containers as non-root
   - Add read-only filesystem where possible
   - Drop unnecessary capabilities

### 8.2 Phase 2: Architecture Refactor (Weeks 2-4)

1. **Database Migration**
   - Add Alembic migrations
   - Migrate SQLite to PostgreSQL
   - Fix hardcoded database paths

2. **Frontend Modernization**
   - Add TypeScript
   - Implement Zustand + React Query
   - Standardize on Axios
   - Add Tailwind CSS

3. **Backend Restructure**
   - Split monolithic routers
   - Implement service layer
   - Add proper error handling

### 8.3 Phase 3: Production Readiness (Weeks 5-8)

1. **Testing**
   - Add comprehensive test coverage (70%+)
   - Implement E2E tests with Playwright

2. **Observability**
   - Add Prometheus metrics
   - Set up Grafana dashboards
   - Implement structured logging

3. **CI/CD**
   - Standardize Docker compose files
   - Add image signing with Cosign
   - Implement automated backups

---

## 9. Key Architectural Decisions

### 9.1 Why Cookie-Based Sessions Over JWT?

**JWT (v1.0 approach):**
- Stored in localStorage (vulnerable to XSS)
- No built-in revocation
- Larger payload size
- Complex refresh logic

**Cookie-Based Sessions (v2.0):**
- HttpOnly cookies (XSS-resistant)
- Server-side session store (Redis)
- Automatic CSRF protection via SameSite
- Simpler client code
- Easy revocation (delete from Redis)

### 9.2 Why PostgreSQL Over SQLite?

**SQLite limitations:**
- Single-writer bottleneck
- No built-in replication
- Limited concurrent connections
- No advanced features (JSONB, full-text search)

**PostgreSQL advantages:**
- True multi-user concurrency
- JSONB for flexible schemas
- Rich indexing options
- Production-proven at scale
- Better backup/restore tools

### 9.3 Why Docker Compose Over Kubernetes?

**Current requirements:**
- Single host deployment (GX-10)
- Simple architecture (4-5 services)
- No need for auto-scaling
- Team familiar with Docker

**Docker Compose advantages:**
- Simpler mental model
- No orchestration complexity
- Sufficient for single-node HA
- Easier local development

**Future path:**
- Can migrate to K3s/k3d if multi-node needed
- Kompose can convert compose files

### 9.4 Why Zustand Over Redux?

**Bundle size:**
- Zustand: ~2KB
- Redux Toolkit: ~15KB

**Boilerplate:**
- Zustand: Minimal
- Redux: Slices, reducers, actions, selectors

**For Vigil Dashboard:**
- Simple state needs (sidebar, filters, auth)
- No complex side effects
- Team already familiar with React patterns

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Migration data loss | Medium | High | Full backup before migration, rollback plan |
| Performance regression | Medium | Medium | Load testing, gradual rollout |
| Breaking API changes | Low | High | API versioning, backward compatibility |
| Third-party service downtime | Low | Medium | Circuit breakers, graceful degradation |
| Security misconfiguration | Medium | Critical | Security scanning, code review, automated tests |

---

## 11. Appendix

### 11.1 Port Mapping

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Caddy | 80/443 | HTTP/HTTPS | Reverse proxy entry |
| Frontend | 3000 (dev) / 8085 (prod) | HTTP | React SPA |
| Backend | 8000 (dev) / 8005 (prod) | HTTP | FastAPI |
| PostgreSQL | 5432 | TCP | Database (internal) |
| Redis | 6379 | TCP | Session/cache (internal) |
| Prometheus | 9090 | HTTP | Metrics (internal) |
| Grafana | 3000 | HTTP | Dashboards (internal) |

### 11.2 Environment Variables

See `DEPLOYMENT_ARCHITECTURE.md` for complete environment variable reference.

---

*End of Target Architecture Specification*
