# Vigil Home — Code Review Coronation Brief

**Prepared:** 2026-05-09  
**Review Scope:** Dashboard (Next.js/React/TypeScript), Backend (FastAPI/Python), AI Modules (poc-ai)  
**Project:** Vigil Home — AI-powered consumer security appliance for IoT threat detection

---

## Executive Summary

Vigil Home is a well-architected IoT security monitoring platform comprising a Next.js dashboard, a FastAPI backend with SQLite persistence, and a standalone AI module for trust scoring, anomaly detection, narrative generation, and device classification. The codebase demonstrates strong engineering discipline — typed interfaces, clean module boundaries, comprehensive unit tests on the AI layer, and thoughtful UX design. The primary risk areas are in production readiness (no authentication, no rate limiting on API endpoints, synchronous alert email sending in request paths, simulated data in the frontend) rather than in code quality or architecture decisions.

**Overall Code Health:** ✅ Strong — structured for growth, with clear areas to address before production deployment.

---

## 1. Architecture Overview

### 1.1 System Context

```
┌──────────────────────┐      Suricata eve.json      ┌──────────────────────┐
│   Dashboard (Next.js) │ ◄────── SSE / REST ───────► │  Backend (FastAPI)  │
│   port 3000            │                            │  port 8000           │
│   nginx proxy /api/*   │                            │                      │
└──────────────────────┘                              │  ┌────────────────┐  │
                                                      │  │  AI Modules    │  │
┌──────────────────────┐    eve.json tail (daemon)    │  │  - Trust Model  │  │
│  Suricata (optional)  │ ──────────────────────────► │  │  - Anomaly Det. │  │
│  /var/log/suricata/   │                            │  │  - Narrative    │  │
│  eve.json             │                            │  │  - Classifier   │  │
└──────────────────────┘                              │  └────────────────┘  │
                                                      │                      │
┌──────────────────────┐                              │  ┌────────────────┐  │
│  Simulator (dev)      │                             │  │  SQLite (pers.)│  │
│  synthetic eve.json   │                             │  │  /data/vigil.db│  │
└──────────────────────┘                              │  └────────────────┘  │
                                                      └──────────────────────┘
```

### 1.2 Frontend (Dashboard)

| Aspect | Detail |
|---|---|
| **Framework** | Next.js 14+ with App Router (client components) |
| **Language** | TypeScript with strict interface types |
| **State/Data** | TanStack React Query (`@tanstack/react-query`) with 30s/60s polling |
| **UI Styling** | Tailwind CSS with custom dark theme (slate/sky palette) |
| **Charts** | Recharts (Line, Bar, Pie) |
| **Icons** | Lucide React |
| **Real-time** | SSE via `EventSource` for live alert push |
| **Routing** | 4 pages: Overview, Devices (list + detail), Alerts, Analytics |

### 1.3 Backend (FastAPI)

| Aspect | Detail |
|---|---|
| **Framework** | FastAPI 0.100+ with auto-generated OpenAPI docs |
| **Database** | SQLAlchemy ORM with SQLite (`/data/vigil.db`) |
| **Models** | Device, Event, Alert — clean declarative base |
| **AI Integration** | In-process Python modules (no GPU/LLM dependency) |
| **Background Tasks** | Daemon thread tailing Suricata eve.json |
| **Email** | SMTP with sliding-window rate limiter, multi-provider support |
| **Synthetic Testing** | Simulator generates realistic eve.json traffic |

### 1.4 AI Layer (poc-ai)

| Module | Purpose | Algorithm |
|---|---|---|
| `trust.py` | Bayesian trust scoring | Beta distribution (α/α+ω) with exponential time decay |
| `anomaly.py` | Statistical outlier detection | Sliding-window z-score with adaptive baseline |
| `narrative.py` | Human-readable alert text | Template-based generator with severity-appropriate recommendations |
| `classifier.py` | IoT device type identification | MAC OUI lookup + behavioural signature matching |

The AI modules are **deterministic statistical models** — no neural networks, no GPU dependency, no LLM. This is a pragmatic choice for an edge appliance. The TrustModel and AnomalyDetector are particularly well-engineered: clean API surfaces, correct math, well-tested.

---

## 2. Code Quality Assessment

### 2.1 Frontend — Dashboard

**Strengths:**
- **TypeScript hygiene** — All API responses have typed interfaces (`Device`, `Alert`, `Event`, etc.). No `any` or unchecked casts in the key files reviewed.
- **Component isolation** — UI primitives (`Card`, `Button`, `Badge`, `StatCard`, `TrustScore`) are clean, single-purpose components with consistent prop APIs.
- **Custom hooks pattern** — Data fetching is neatly abstracted into `useDevices.ts` hooks wrapping React Query. Each hook has a clear query key, query function, and polling interval.
- **Server component awareness** — Root layout uses `next/font` with `display: swap` and separates metadata/viewport exports properly.
- **Utility functions** (`utils.ts`) — Well-factored helpers for formatting, colors, and CSS class merging.

**Concerns:**
- **All pages are `"use client"`** — No server components or React Server Components (RSC) leverage. The entire app is client-rendered. This is fine for a dashboard, but means no SSR/SEO benefits and a heavier initial JS bundle.
- **`fetchNetworkSummary` aggregates client-side** — The overview page fetches all devices and alerts separately, then computes the summary in the browser. This means pagination isn't used, and the client pays the cost of aggregating data that the backend could serve directly.
- **`fetchTrustTrend` generates simulated data** — Returns `Math.random()` values instead of real data. This is a POC shortcut that must be replaced with a real backend endpoint before production.
- **`useSSE` reconnects every 5s on error** — No exponential backoff. A temporary network blip causes repeated reconnection attempts.
- **No loading skeleton in `useDevice` detail page** — The `devices/[id]/page.tsx` skips the skeleton and shows a raw device-not-found state if data hasn't loaded yet (the `isLoading` check does show a skeleton, but there's a brief gap).
- **`Acknowledge` is client-side only** — Clicking acknowledge on alerts updates a React `Set` state but never calls the backend. A page refresh restores unacknowledged alerts.

### 2.2 Backend — FastAPI

**Strengths:**
- **Clean module boundaries** — `main.py` (routes), `models.py` (ORM), `database.py` (engine/session), `detection.py` (Suricata consumer), separate AI modules, separate email module.
- **Well-structured route design** — RESTful endpoints with query parameter filtering, skip/limit pagination, consistent response shapes.
- **Proper error handling** — 404s for missing devices/alerts, 409 for duplicate MACs, try/catch on email sending that doesn't crash the request.
- **Dependency injection** — `Depends(get_db)` for session management.
- **Type annotations** — Pydantic models for request bodies (`BaselineRequest`, `EventIngest`), Optional/Union types throughout.

**Concerns:**
- **No authentication/authorization** — Every endpoint is fully open. No API keys, no JWT, no session. This is the single biggest security gap.
- **No rate limiting on API endpoints** — Attackers can hammer `/events` or `/devices` with no throttling.
- **`_anomaly_detectors` and `_trust_models` are in-memory dicts** — Lost on server restart. No persistence. This means historical trust scores are rebuilt from scratch on restart.
- **`detection.py` has significant code duplication** with `main.py` — Both instantiate `NarrativeGenerator`, `DeviceClassifier`, `_get_anomaly_detector`, `_get_trust_model`, `_severity_to_severity_enum`. This should be refactored into a shared module.
- **`_build_classification_features` is duplicated** — The same hostname-keyword-to-features logic appears in both `main.py` and `detection.py`.
- **Email sending is synchronous in request path** — `send_alert_email()` makes an SMTP connection inside the POST /events handler. This can block the request for seconds. Should be background-tasked.
- **`create_device` has an `except` pass** when email sending fails, but the logging import is inline (`import logging` inside the except block).
- **Pydantic regex validation uses deprecated `pattern` kwarg** — FastAPI/Pydantic V2 prefers `pattern=` on the Field, but `Query(pattern="...")` still works; just worth noting for version bumps.

### 2.3 AI Modules

**Strengths:**
- **Exceptional documentation** — Every module has detailed module-level docstrings explaining the algorithm, usage examples, and a `__main__` demo block.
- **Clean API design** — `TrustModel(score, update, decay, reset)`, `AnomalyDetector(record, is_anomaly)`, `NarrativeGenerator(alert)` — each class has a minimal, intuitive surface.
- **Edge case handling** — `AnomalyDetector` handles std=0 (returns z=0), insufficient samples (returns None), and sliding-window adaptation is tested.
- **Type safety** — Named tuples (`AnomalyResult`), dataclasses (`Alert`, `Classification`, `BehavioralSignature`), enums (`Severity`).
- **Test coverage** — 17 unit tests for trust, 15 for anomaly detection. Covers init, updates, decay, reset, edge cases.

**Concerns:**
- **No tests for `classifier.py` or `narrative.py`** — The two largest AI modules (classifier with OUI database and behavioural signatures, narrative with template system) have zero tests. The classification scoring logic in `BehavioralSignature.score()` has complex weighted math that would benefit from unit tests.
- **`random.choice` in narrative generation** — The `NarrativeGenerator` uses `random.choice()` for templates, causes, and recommendations. This means identical inputs can produce different outputs, which is fine for UX variety but makes testing and alert deduplication harder.
- **No alert deduplication** — If the same anomaly triggers repeatedly, a new narrative and new database alert is created each time. No suppression window or dedup key.
- **Classifier's `_types_for_vendor` is O(n*m)** — Fine for the current small OUI DB, but should be indexed if OUI grows significantly.

---

## 3. Security Considerations

### 3.1 Critical Gaps

| Issue | Severity | Location |
|---|---|---|
| **No authentication** on any API endpoint | 🔴 Critical | All `app/main.py` routes |
| **No API rate limiting** | 🔴 High | All endpoints |
| **No input sanitization** on MAC/IP/hostname | 🟡 Medium | `POST /devices`, `GET /classify/{mac}` |
| **SSE endpoint unauthenticated** | 🔴 Critical | `/events/stream` (via proxy) |
| **No CORS configuration** demonstrated | 🟡 Medium | Backend doesn't show CORS middleware |
| **Hardcoded dashboard URL** in email | 🟡 Medium | `email_notifier.py` line with `192.168.50.30:8000` |

### 3.2 Observations

- The Suricata `eve.json` tailer runs as a daemon thread in the same process. If an attacker can write to `eve.json`, they can inject arbitrary data into the system.
- SQLite is appropriate for a single-appliance deployment but has no built-in access control beyond filesystem permissions.
- The `ALERT_EMAIL_FROM` and `ALERT_EMAIL_TO` are configured via environment variables, which is good practice.
- No secrets or credentials are hardcoded in source — all config comes from environment variables.
- The `simulate.py` script writes to `eve.json` without any validation — this is a dev tool but should not be accessible in production.

### 3.3 Recommendations

1. **Add API key or JWT authentication** — Even a simple shared-secret header (`X-Vigil-Api-Key`) would provide basic protection.
2. **Add rate limiting middleware** — FastAPI has `slowapi` or a simple custom dependency.
3. **Validate and sanitize MAC addresses and IPs** in `POST /devices` and `GET /classify/{mac}`.
4. **Make the dashboard URL configurable** via environment variable rather than hardcoded in the email template.
5. **Add CORS middleware** (`fastapi.middleware.cors`) configured for the dashboard origin only.

---

## 4. Performance Observations

### 4.1 Frontend

- **30s polling interval** is reasonable for a home security dashboard, but means up to 30s latency on new alerts (mitigated by SSE).
- **Client-side aggregation** (`fetchNetworkSummary`) fetches all devices and all alerts then reduces in JS. For networks with 100+ devices and thousands of alerts, this will become slow. Should be a dedicated backend endpoint.
- **Recharts rendering** — The analytics page renders 4 chart components (Line, Bar, Pie) simultaneously. For a POC this is fine, but for battery-constrained mobile devices, consider lazy loading or intersection observer.
- **No virtualization** on the devices list. For networks with 200+ devices, DOM rendering could lag.
- **Good** — Skeletons are used consistently during loading states across all pages.
- **Good** — `useMemo` is used appropriately for filtered/sorted lists in the devices and alerts pages.

### 4.2 Backend

- **SQLite** is sufficient for single-appliance deployment but will struggle with concurrent reads/writes under heavy Suricata traffic. Consider `WAL` mode (set via `PRAGMA journal_mode=WAL`).
- **No database indexes** beyond the default primary key indexes. The `device_id` column on events and alerts should be indexed (it already has `index=True` in the model, which is correct). But querying events by `timestamp` (for date-range filters) would benefit from an additional index.
- **Inline email sending** — SMTP connections are synchronous in the request path. For a critical alert, this adds 1-5 seconds of latency. Should be dispatched to a background thread or task queue.
- **`process_eve_line` parses JSON per line** — For a busy Suricata instance generating hundreds of lines/second, the JSON parsing is negligible overhead, but the per-line DB commit pattern is not batch-optimized.
- **No pagination on `fetchDevices` in the frontend** — The backend supports `skip`/`limit` but the frontend ignores them and fetches everything. For large networks, this is wasteful.

### 4.3 AI

- **TrustModel.decay uses `time.time()` internally** — but `update()` also calls `time.time()`. The decay should ideally use the event timestamp rather than wall clock, otherwise delayed event processing can skew decay calculations.
- **`AnomalyDetector.window_size=100`** is hardcoded in both `main.py` and `detection.py`. Should be configurable per device type.
- **`NarrativeGenerator` template rendering** uses `str.format()` which is fast, but `import random` is inside the method (already at module level due to top-level usage).

---

## 5. Test Coverage Analysis

### 5.1 Current Coverage

| Module | Test File | Tests | Coverage Estimate |
|---|---|---|---|
| `trust.py` | `tests/test_trust.py` | 17 | ~95% (all paths covered) |
| `anomaly.py` | `tests/test_anomaly.py` | 15 | ~90% (edge cases covered) |
| `classifier.py` | **None** | 0 | 0% |
| `narrative.py` | **None** | 0 | 0% |
| Backend (`main.py`, etc.) | **None** | 0 | 0% |
| Dashboard (React) | **None** | 0 | 0% |

### 5.2 Trust Model Tests ✅ (Strong)

The trust model tests are thorough: initial state, positive/negative updates, mixed evidence, certainty calculation, decay toward neutral, half-life effects, reset, custom weights, edge cases. A model of test quality.

### 5.3 Anomaly Detection Tests ✅ (Strong)

Similarly thorough: empty state, min samples, normal vs. extreme values, custom z-threshold, window sliding/adaptation, std=0 edge case, negative z-scores, field completeness.

### 5.4 Critical Gaps

1. **No backend tests** — `main.py`, `detection.py`, `models.py`, `database.py` have zero test coverage. The `POST /events` endpoint has complex logic (anomaly detection + trust update + alert creation + narrative generation + email) that should be tested.
2. **No classifier tests** — The `BehavioralSignature.score()` weighting logic, OUI lookup, classification merging, and `_types_for_vendor` are untested.
3. **No narrative tests** — Template selection, severity-based recommendations, context rendering.
4. **No frontend tests** — No React Testing Library or Playwright tests for any component or hook.
5. **No integration tests** — No tests that exercise the full backend+AI pipeline.

---

## 6. Key Recommendations

### Tier 1 — Production Readiness (Do Before Launch)

1. **🔴 Add authentication** — Minimum: shared API key header on all endpoints + session-based auth on the dashboard.
2. **🔴 Replace simulated data** — `fetchTrustTrend` generates `Math.random()` values. Wire it to a real backend endpoint (or remove the feature behind a feature flag until the endpoint exists).
3. **🔴 Add backend tests** — At minimum, integration tests for `POST /events` and the Suricata event processing pipeline.
4. **🔴 Persist AI state** — `_anomaly_detectors` and `_trust_models` are in-memory. Serialize to DB on shutdown or store per-device trust model parameters in the `Device` model.
5. **🔴 Fix client-side-only acknowledge** — Wire the acknowledge button to a `PATCH /alerts/{id}/acknowledge` backend endpoint.

### Tier 2 — Structural Improvements

6. **🟡 Refactor shared code** — Move duplicated `_get_anomaly_detector`, `_get_trust_model`, `_severity_to_severity_enum`, and `_build_classification_features` into a shared module.
7. **🟡 Background email sending** — Use `asyncio.create_task` or a thread pool for SMTP calls so they don't block the API.
8. **🟡 Add a dedicated `/summary` endpoint** — Move `fetchNetworkSummary` client-side aggregation to the backend.
9. **🟡 Add classifier and narrative tests** — These modules have complex logic and zero coverage.
10. **🟡 Add SSE authentication** — If using SSE for real-time alerts, the stream should authenticate.

### Tier 3 — Polish & Monitoring

11. **🟢 Add rate limiting** to all write endpoints.
12. **🟢 Add proper logging** — `detection.py` has an undefined `logger` reference; `except: pass` in the tail loop swallows errors silently.
13. **🟢 Add DB indexes** on `alerts.timestamp`, `events.timestamp` for common query patterns.
14. **🟢 Implement SSE exponential backoff** instead of fixed 5s reconnect.
15. **🟢 Add alert deduplication** — Suppress repeated identical alerts within a configurable window.
16. **🟢 Make `VIGIL_DB_PATH` directory configurable** — Currently resolves to `/data/vigil.db` but the `/data` directory may not exist; the simulator does `os.makedirs` but the main app doesn't.
17. **🟢 Add a health check endpoint** (`GET /health`) returning DB connectivity, AI module status, and last eve.json line processed timestamp.

### Tier 4 — Future Considerations

18. **Replace SQLite with PostgreSQL** for multi-appliance or cloud deployment.
19. **Evaluate WebSockets over SSE** for bidirectional real-time communication (device control commands).
20. **Add device name persistence** — The frontend allows editing device names but it's client-side only.
21. **Consider LLM-enhanced narratives** — The current template system is functional but deterministic. For production, a lightweight LLM (Phi-3, Llama 3.2 1B, etc.) could generate richer, context-aware narratives.

---

## 7. Conclusion

Vigil Home is a **well-engineered POC** with a clean architecture, strong type discipline, and excellent AI module design. The Bayesian trust model and sliding-window anomaly detector are production-quality code with proper tests. The dashboard is visually polished and thoughtfully structured.

The gaps are typical of a POC-to-production transition: **authentication, test coverage on the backend and frontend, and persistent state management for the AI models** are the three critical areas to address. The duplicated code in `detection.py` vs `main.py` is the highest-impact refactoring target.

With authentication added, shared code consolidated, and backend tests written, Vigil Home is ready for alpha deployment on a single appliance.

---

## Appendix: File Inventory Analyzed

| File | Lines | Role |
|---|---|---|
| `dashboard/src/app/page.tsx` | ~150 | Overview page (stats, alerts, quick actions) |
| `dashboard/src/app/layout.tsx` | ~45 | Root layout (fonts, metadata, AppShell) |
| `dashboard/src/app/AppShell.tsx` | ~45 | QueryClient provider, service worker, layout shell |
| `dashboard/src/app/devices/page.tsx` | ~175 | Device list with search/filter/sort |
| `dashboard/src/app/devices/[id]/page.tsx` | ~165 | Device detail (trust, classification, events) |
| `dashboard/src/app/alerts/page.tsx` | ~165 | Alert list with severity filter & acknowledge |
| `dashboard/src/app/analytics/page.tsx` | ~210 | Charts (trust trend, device types, alert volume, top talkers) |
| `dashboard/src/lib/types.ts` | ~55 | TypeScript interfaces (Device, Alert, Event, etc.) |
| `dashboard/src/lib/api.ts` | ~155 | API client (fetch wrappers, aggregation helpers) |
| `dashboard/src/lib/utils.ts` | ~85 | Formatting, icons, color helpers |
| `dashboard/src/hooks/useDevices.ts` | ~85 | React Query hooks (8 hooks) |
| `dashboard/src/hooks/useSSE.ts` | ~55 | Server-Sent Events hook |
| `dashboard/src/components/ui/` | ~180 | 6 UI primitives (Card, Button, Badge, StatCard, TrustScore, TrendIndicator) |
| `dashboard/src/components/layout/` | ~70 | Sidebar + MobileNav |
| `poc-backend/app/main.py` | ~330 | FastAPI app (12 endpoints) |
| `poc-backend/app/models.py` | ~80 | SQLAlchemy models (Device, Event, Alert) |
| `poc-backend/app/database.py` | ~25 | SQLite engine/session setup |
| `poc-backend/app/detection.py` | ~280 | Suricata eve.json consumer + AI integration |
| `poc-backend/app/email_notifier.py` | ~300 | SMTP email with rate limiting |
| `poc-backend/app/email_poller.py` | ~150 | Standalone email poller daemon |
| `poc-backend/app/simulate.py` | ~180 | Synthetic eve.json generator |
| `poc-backend/app/ai/__init__.py` | ~15 | AI module re-exports |
| `poc-ai/vigil/trust.py` | ~190 | Bayesian trust model |
| `poc-ai/vigil/anomaly.py` | ~170 | Z-score anomaly detector |
| `poc-ai/vigil/narrative.py` | ~290 | Template-based alert narrative generator |
| `poc-ai/vigil/classifier.py` | ~370 | MAC OUI + behavioural device classifier |
| `poc-ai/tests/test_trust.py` | ~100 | 17 unit tests for trust model |
| `poc-ai/tests/test_anomaly.py` | ~110 | 15 unit tests for anomaly detector |
