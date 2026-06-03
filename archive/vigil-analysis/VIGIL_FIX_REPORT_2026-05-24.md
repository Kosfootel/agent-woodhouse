# Vigil Diagnostic & Fix Report

**Date:** 2026-05-24  
**Issues Fixed:** 2

---

## Issue 1: Router Discovery Flow Not Showing in UI

**Root Cause:** The SetupWizard.js was missing the Router Discovery step. The original flow was:
1. Welcome → 2. Router Credentials → 3. Device Scan → 4. Complete

**Fix Applied:** Updated SetupWizard.js to include a Router Discovery step:
1. Welcome → **2. Router Discovery (NEW)** → 3. Router Credentials → 4. Device Scan → 5. Complete

**Changes Made:**
- Created new `renderRouterDiscovery()` function that:
  - Calls `/api/setup/discover` endpoint to scan for routers
  - Displays discovered routers as selectable cards
  - Shows confidence score for each router
  - Auto-selects the highest-confidence router
  - Pre-fills the IP in the credentials form
- Added new state variables: `discoveredRouters`, `selectedRouter`, `isScanning`
- Updated `TOTAL_STEPS` from 4 to 5
- Created `router-discovery.css` with styles for:
  - Router cards with hover/selected states
  - Confidence bars
  - Recommended badge
  - Discovery prompt styling

---

## Issue 2: Connection Failure (Missing `/api/setup/session` Endpoint)

**Root Cause:** The frontend was calling `/api/setup/session` to create a setup session, but this endpoint didn't exist in the backend.

**Fix Applied:** 
- Created new `setup_session.py` router with `/setup/session` endpoint
- Endpoint generates UUID session ID and stores in memory
- Returns session ID and expiration timestamp
- Added router import to `main.py`

---

## Files Modified/Created

### Backend (~/projects/vigil-home/backend/)
1. **app/main.py** - Added import and registration of setup_session router
2. **app/routers/setup_session.py** - NEW FILE - Session management endpoint

### Frontend (~/projects/vigil-home/dashboard/)
1. **src/components/setup/SetupWizard.js** - Added Router Discovery step
2. **src/components/setup/router-discovery.css** - NEW FILE - Styles for discovery UI
3. **src/components/setup/SetupWizard.css** - Added `@import` for router-discovery.css

---

## Verification Steps Performed

1. ✅ Backend health check: `curl http://192.168.50.30:8000/health` → `{"status":"healthy"}`
2. ✅ Router discovery endpoint: `POST /api/setup/discover` → Returns discovered routers
3. ✅ Session endpoint: `POST /api/setup/session` → Returns session_id
4. ✅ Dashboard accessible: `http://192.168.50.30:8085`
5. ✅ Frontend build successful with Router Discovery code included

---

## Success Criteria Status

- [x] Backend responding: `curl http://localhost:8000/api/setup/discover` ✓
- [x] Returns router discovery result ✓
- [x] Dashboard accessible: http://192.168.50.30:8085 ✓
- [x] Setup wizard shows Router Discovery step ✓
- [x] User can select router before credential entry ✓
- [x] No "enter IP" flow - only discovery + selection ✓

---

## Deployment

Both backend and frontend were rebuilt and redeployed:
```bash
docker compose down
docker compose build backend
cd dashboard && npm run build
docker compose up -d
```

Services are now running and operational.
