# Vigil Dashboard

Real-time network security observability dashboard for the Vigil Home Security system.

## Overview

The Vigil Dashboard provides a web-based UI for monitoring devices, trust scores, alerts, and network analytics — connecting to the Vigil API running on the GX-10 device (192.168.50.30:8000).

### Views

| Route | View | Description |
|-------|------|-------------|
| `/` | **Overview** | At-a-glance network health: trust score, device count, alert summary, recent activity |
| `/devices` | **Devices** | Filterable device list with trust scores, type icons, status badges |
| `/devices/[id]` | **Device Detail** | Deep-dive on individual device: trust score, classification, event history, actions |
| `/alerts` | **Alerts** | Alert feed with severity badges, acknowledgment, filtering |
| `/analytics` | **Analytics** | Charts: trust trend, device type breakdown, alert volume, top talkers |

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Fonts:** Inter (UI), JetBrains Mono (data) via next/font/google
- **State Management:** TanStack Query (React Query)
- **Charts:** Recharts
- **Icons:** Lucide React
- **PWA:** Manifest + Service Worker

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The dev server runs on `http://localhost:3000`.

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm run start
```

### Deploy to GX-10

1. Build the project:
   ```bash
   npm run build
   ```

2. Copy to GX-10:
   ```bash
   scp -r .next package.json public next.config.mjs node_modules user@gx-10:/opt/vigil/dashboard/
   ```

3. Start on GX-10:
   ```bash
   cd /opt/vigil/dashboard
   npm run start -- -p 3000
   ```

4. (Optional) Configure Nginx reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name vigil.local vigil.agentcy.services;

       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

## API Integration

The dashboard connects to the Vigil API at `http://192.168.50.30:8000`.

### Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /devices` | List all devices |
| `GET /devices/{id}` | Device details |
| `GET /alerts` | Security alerts |
| `GET /events` | Raw events (analytics) |
| `GET /classify/{mac}` | Classify device by MAC |
| `POST /baseline` | Mark device as trusted |

Data is polled every 30 seconds with automatic refetching via React Query.

## PWA

The dashboard is a Progressive Web App:
- **Install prompt:** "Add to Home Screen" on mobile browsers
- **Offline:** Service worker caches pages for offline access
- **Standalone:** Fullscreen app-like experience

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (fonts, theme)
│   ├── page.tsx            # Overview view
│   ├── AppShell.tsx        # Query provider + layout wrapper
│   ├── devices/            # Device list + detail views
│   ├── alerts/             # Alert center
│   └── analytics/          # Analytics view
├── components/
│   ├── ui/                 # Reusable components (Card, Button, Badge, etc.)
│   ├── layout/             # Sidebar, MobileNav
├── hooks/                  # React Query hooks
├── lib/                    # API client, types, utilities
public/
├── manifest.json           # PWA manifest
├── sw.js                   # Service worker
├── icon-192.png            # PWA icons
└── icon-512.png
```

## Design

- **Theme:** Dark mode only (security tooling)
- **Colors:** Slate-900 background, Slate-800 cards, Sky-400 accent
- **Trust score:** Emerald (high), Amber (medium), Rose (low)
- **Typography:** Inter for UI, JetBrains Mono for data/MAC addresses
