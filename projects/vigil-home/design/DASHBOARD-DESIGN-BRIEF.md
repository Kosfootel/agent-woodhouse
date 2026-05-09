# Vigil Dashboard — Design Brief
*Real-time observability for your network guardian*

**Version:** 1.0  
**Date:** 2026-05-07  
**Status:** Draft — awaiting review

---

## 1. Purpose

The Vigil Dashboard is the **window into your network's soul** — a real-time observability layer that proves Vigil is working, learning, and protecting.

### Core Promise
> *"Show me what's on my network, tell me what I should worry about, and prove you're worth keeping."*

### Success Criteria
- User can see all devices in 10 seconds
- User understands trust scores without explanation
- Critical alerts demand attention (but don't cry wolf)
- User checks dashboard at least once per day (habit-forming)

---

## 2. User Personas

### Primary: Erik (Technical Owner)
- **Profile:** Runs infrastructure, values control, wants insight not noise
- **Goals:** Know what's on network, catch anomalies early, understand risk
- **Pain points:** Too many false alerts, opaque security tools, vendor lock-in
- **Tech comfort:** High — can read logs, understands networking

### Secondary: Family Member (Non-Technical)
- **Profile:** Sees "security" as insurance — wants to know it's working
- **Goals:** Simple confirmation of safety, easy action on alerts
- **Pain points:** Technical jargon, overwhelming detail
- **Tech comfort:** Low — needs plain language

---

## 3. Key Views

### View A: Network Overview (Dashboard Home)
**Purpose:** At-a-glance network health

**Elements:**
- **Trust Score Summary:** Overall network trust (aggregate) + trend (↑/↓/→)
- **Device Count:** Total devices + new today + offline count
- **Alert Summary:** Critical (red), Warning (amber), Info (blue) — last 24h
- **Recent Activity:** Timeline of last 5 significant events
- **Quick Actions:** "Scan Network," "Review Alerts," "Device List"

**Layout:** Single-column on mobile, 2-column grid on desktop

---

### View B: Device Explorer
**Purpose:** See everything on the network, understand trust

**Elements:**
- **Filter Bar:** By type (camera, phone, IoT, unknown), by trust score, by status
- **Device Cards:** 
  - Device name + icon (auto-classified: 📷, 📱, 💻, ❓)
  - Trust score (0.0-1.0) with color: red (<0.3), amber (0.3-0.7), green (>0.7)
  - Last seen timestamp
  - Quick action: "View Details," "Mark Trusted," "Isolate"
- **List/Grid Toggle:** Dense list vs. visual grid

**Sort defaults:** By trust score (lowest first — risk prioritization)

---

### View C: Device Detail
**Purpose:** Deep-dive on single device

**Elements:**
- **Header:** Device name (editable), MAC address, IP, first seen
- **Trust Score:** Large number + trend graph (7 days)
- **Classification:** Device type (auto) + confidence %
- **Behavior Summary:** 
  - Normal hours (e.g., "Active 6am-11pm")
  - Normal connections (e.g., "Talks to 5 devices")
  - Bandwidth pattern
- **Connection Graph:** What this device talks to (visualized)
- **Event History:** Timeline of all events for this device
- **Actions:** "Mark as Trusted," "Temporarily Isolate," "Report False Positive"

---

### View D: Alert Center
**Purpose:** Security event management

**Elements:**
- **Alert Feed:** Chronological list, newest first
- **Alert Card:**
  - Severity badge (Critical/Warning/Info)
  - Title (plain English: "New device joined network")
  - Description (specifics: "Unknown device AA:BB:CC... at 192.168.50.45")
  - Timestamp
  - Related device (link)
  - Actions: "Acknowledge," "Investigate," "Dismiss"
- **Filter:** By severity, by device, by time range
- **Bulk Actions:** Acknowledge all, export log

**Default view:** Unacknowledged alerts only (inbox-zero mentality)

---

### View E: Trust Analytics
**Purpose:** Understand how Vigil thinks

**Elements:**
- **Network Trust Trend:** Line graph, 7/30/90 day views
- **Device Type Breakdown:** Pie/bar chart of device categories
- **Alert Volume:** Frequency over time (is Vigil learning?)
- **Top Talkers:** Which devices generate most traffic
- **Anomaly Calendar:** Heatmap of unusual activity

---

## 4. Information Architecture

```
Vigil Dashboard
├── 📊 Overview (default)
├── 🔍 Devices
│   ├── List View
│   └── Detail View (per device)
├── 🚨 Alerts
│   ├── Alert Feed
│   └── Alert Detail
├── 📈 Analytics
│   ├── Trust Trends
│   ├── Network Stats
│   └── Anomaly Calendar
└── ⚙️ Settings
    ├── Network Config
    ├── Notification Preferences
    └── Vigil Behavior (sensitivity, etc.)
```

---

## 5. Visual Design Direction

### Mood: Guardian, Not Policeman
- **Trustworthy** — but not corporate/boring
- **Alert without alarm** — serious events feel urgent, not panicked
- **Transparent** — show the work, explain the reasoning

### Color Palette

| Use | Color | Hex |
|-----|-------|-----|
| Background | Deep slate | `#0f172a` |
| Card background | Slate 800 | `#1e293b` |
| Trust: High | Emerald 400 | `#34d399` |
| Trust: Medium | Amber 400 | `#fbbf24` |
| Trust: Low | Rose 500 | `#f43f5e` |
| Accent | Sky 400 | `#38bdf8` |
| Text primary | Slate 100 | `#f1f5f9` |
| Text secondary | Slate 400 | `#94a3b8` |

**Theme:** Dark mode default (security tools work in dim rooms)

### Typography
- **Headings:** Inter (clean, technical but friendly)
- **Body:** Inter or system-ui
- **Monospace (data):** JetBrains Mono (MAC addresses, logs)

### Visual Elements
- **Trust score:** Circular progress indicator or horizontal bar
- **Device icons:** Clean SVGs, color-coded by type
- **Network graph:** Simple node-edge visualization (not overwhelming)
- **Alerts:** Left border color + icon for quick scanning

---

## 6. Key Interactions

### Real-Time Updates
- Server-sent events (SSE) for live data
- Gentle toast notifications for new alerts
- Auto-refresh device list every 30 seconds

### Trust Score Hover
- Hover on any trust score → tooltip explains: "0.72 — Normal behavior, known device type"

### Device Isolation
- "Isolate" button → confirmation modal → immediate action → toast confirmation

### Alert Acknowledgment
- Swipe on mobile, checkbox on desktop
- Acknowledged alerts fade or move to "Resolved" tab

---

## 7. Technical Architecture

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Headless UI
- **State:** React Query (TanStack Query) for server state
- **Real-time:** SSE via EventSource API
- **Charts:** Recharts or Tremor

### Backend Integration
- **API Base:** `http://192.168.50.30:8000`
- **Auth:** None (local network only, for now)
- **Endpoints:** 
  - `GET /devices` — device list
  - `GET /devices/{id}` — device detail
  - `GET /alerts` — alert feed
  - `GET /events` — raw events (for analytics)
  - `POST /baseline` — mark device as trusted
  - `POST /isolate` — (future) network isolation

### Deployment
- **Host:** Same GX-10 (port 3000)
- **Proxy:** Nginx reverse proxy from 80/443 → 3000
- **Domain:** `vigil.agentcy.services` or `vigil.local`

---

## 8. Out of Scope (V1)

These are **explicitly not in the first version**:

- User authentication (local network trust model)
- Mobile app (web-responsive only)
- Push notifications (SSE only)
- Historical data export (view only)
- Multi-network support (single Vigil instance)
- Advanced threat hunting (Vigil provides, user consumes)

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page load time | <2 seconds | Lighthouse audit |
| Time to first device view | <10 seconds | User testing |
| Daily active users | 1+ (Erik) | Server logs |
| Alert acknowledgment rate | >80% | Database query |
| Feature requests | Track in GitHub | Issues created |

---

## 10. Open Questions

1. **Branding:** "Vigil" is the product name — logo/wordmark needed?
2. **Domain:** `vigil.agentcy.services` or `vigil.local` mDNS?
3. **Notifications:** Email alerts for critical events? (Phase 2)
4. **Mobile:** PWA (add to home screen) acceptable as v1 mobile?
5. **Dark/light:** Dark only, or toggle?

---

## Appendix: Wireframe Sketches

### Overview Page (Desktop)
```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Vigil         Overview | Devices | Alerts | ... │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Network Trust   │  │ Device Summary  │              │
│  │                 │  │                 │              │
│  │     0.87       │  │  23 devices     │              │
│  │    [====>]     │  │  3 new today    │              │
│  │    Trending ↑  │  │  1 offline      │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Alert Summary (last 24h)                        │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
│  │ 🔴 Critical: 0    🟠 Warning: 2    🔵 Info: 12  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Recent Activity                          [Scan Now]    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • 14:32 — New device: "Ring Doorbell" (Trust: 0.45)   │
│  • 12:15 — Alert cleared: Port scan resolved           │
│  • 09:00 — Daily trust baseline updated                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Review requested:** Design brief complete. Ready for feedback before implementation begins.

**Next step:** Revise based on feedback, then create technical specification for frontend build.
