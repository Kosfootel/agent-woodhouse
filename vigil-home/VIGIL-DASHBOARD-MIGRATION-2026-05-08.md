# Vigil Dashboard Migration — 2026-05-08

## Completed Steps

### Dashboard Moved to 192.168.50.32
- **Code location:** `/opt/vigil-dashboard/` on 192.168.50.32 (bettermachine-host)
- **Source:** Copied from `~/.openclaw/workspace/projects/vigil-home/dashboard/` (Woodhouse local)
- **Node.js:** v22.22.2 already installed on target
- **Build:** `npm run build` successful

### Code Changes Made
- **`src/lib/api.ts`** — Changed `API_BASE` from hardcoded `http://192.168.50.30:8000` to empty string `""` (relative paths). API calls now go through nginx proxy.
- **`src/hooks/useSSE.ts`** — Changed `SSE_URL` from hardcoded `http://192.168.50.30:8000/events/stream` to `/events/stream` (relative path). SSE goes through nginx proxy.

### Systemd Service Created
- **Service name:** `vigil-dashboard.service`
- **Status:** Active (running), enabled on boot
- **Port:** 3000
- **User:** erik-ross
- **Working directory:** `/opt/vigil-dashboard`

### Nginx Config Updated (192.168.50.32)
- **Config:** `/etc/nginx/sites-enabled/dashboard`
- **Server name:** `vigil.local`, `vigil.agentcy.services`, `192.168.50.32`
- **`/`** → proxy to localhost:3000 (Next.js dashboard)
- **`/api/`** → proxy to GX-10 (192.168.50.30:8000)
- **`/events/`** → proxy to GX-10 SSE endpoint (192.168.50.30:8000/events/)

### Verification Results
| Check | Result |
|-------|--------|
| Dashboard via nginx (http://192.168.50.32/) | ✅ HTTP 200 |
| Dashboard direct (http://192.168.50.32:3000/) | ✅ HTTP 200 |
| API proxy via nginx (http://192.168.50.32/api/devices) | ✅ Returns 43 devices |
| API direct on GX-10 (http://192.168.50.30:8000/devices) | ✅ HTTP 200 |
| Service status | ✅ Active (running) |

## Blockers / Not Completed

### Step 6: Update CORS on GX-10 API
**BLOCKED** — No SSH access to 192.168.50.30 (GX-10)
- Current CORS allows only `http://192.168.50.30:3000` and `http://localhost:3000`
- **Workaround applied:** Dashboard now uses relative API paths proxied through nginx, eliminating the need for cross-origin requests from the browser. No CORS errors expected.
- **Action required:** When SSH access is available, edit `/opt/vigil/app/main.py` on GX-10 to add `"http://192.168.50.32"` to `allow_origins`, then rebuild.

### Step 7: Remove/Stop Old Dashboard on GX-10
**BLOCKED** — No SSH access to GX-10
- The old Next.js dashboard is still running on GX-10:3000
- **Action required:** When SSH access is available, run:
  ```bash
  sudo systemctl stop vigil-dashboard
  sudo systemctl disable vigil-dashboard
  ```

### SSE Endpoint Not Available
- `/events/stream` endpoint returns 404 from the GX-10 API (pre-existing, not migration-related)
- Dashboard's `useSSE.ts` hook handles this gracefully (sets `online: false`)
- May need to be implemented in the API or endpoint path corrected

## Summary

| Component | Location | Port | Status |
|-----------|----------|------|--------|
| Dashboard (Next.js) | 192.168.50.32 | 80 (nginx) / 3000 (direct) | ✅ Live |
| API (Vigil) | 192.168.50.30 | 8000 | ✅ Running |
| API Proxy (nginx) | 192.168.50.32 | 80 | ✅ Working |
