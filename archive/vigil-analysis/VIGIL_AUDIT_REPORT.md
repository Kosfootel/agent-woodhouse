# Vigil Device Discovery Codebase Audit Report

**Date:** 2026-05-24  
**Auditor:** Woodhouse (Subagent)  
**Repository:** Kosfootel/agent-woodhouse  
**Branch:** hermes/vigil-playbooks-models  
**Location:** ~/projects/vigil-home/ on GX-10

---

## Executive Summary

The Vigil codebase has a **comprehensive device discovery module (`device_discovery.py`)** that implements multiple discovery protocols (mDNS, NetBIOS, SNMP, UPnP), but it is **NOT integrated** into the current application flow. The system currently relies on ARP-based discovery via `GenericRouter` in the router abstraction layer.

**Key Finding:** Only 12 devices are currently being found because the enhanced discovery service exists as a standalone module but is not wired into the setup flow or device refresh process.

---

## 1. Complete File Inventory

### Backend Python Modules (26 files)

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `app/__init__.py` | 0 | ✅ Present | Module init |
| `app/main.py` | 55 | ✅ Active | FastAPI app entry point |
| `app/models.py` | 154 | ✅ Active | SQLAlchemy models |
| `app/device_discovery.py` | 950 | ⚠️ **ORPHANED** | Multi-protocol discovery (NOT integrated) |
| `app/router_integration.py` | 625 | 🔧 Legacy | Old router integration code |
| `app/routers/__init__.py` | 0 | ✅ Present | Router package init |
| `app/routers/agents.py` | 45 | ✅ Active | Static agents list |
| `app/routers/alerts.py` | 87 | ✅ Active | Security alerts API |
| `app/routers/devices.py` | 158 | ✅ Active | Device CRUD + block/unblock |
| `app/routers/discovery.py` | 178 | ✅ Active | Router discovery (MAC OUI + HTTP) |
| `app/routers/setup.py` | 204 | ✅ Active | **Setup wizard endpoints** |
| `app/routers/stats.py` | 50 | ✅ Active | Dashboard stats |
| `app/routers/security.py` | 430 | ✅ Active | Security scanning |
| `app/routers/base.py` | 236 | ✅ Active | Router abstraction base classes |
| `app/routers/factory.py` | 155 | ✅ Active | Router factory pattern |
| `app/routers/events.py` | 50 | ✅ Active | Event logging |
| `app/routers/discovery_scan.py` | 50 | ⚠️ Minimal | Scan wrapper (mostly empty) |
| `app/routers/admin.py` | 85 | ✅ Active | Admin endpoints |
| `app/routers/implementations/generic.py` | 420 | ✅ **PRIMARY DISCOVERY** | ARP + MAC OUI + reverse DNS |
| `app/routers/implementations/asus.py` | N/A | 🚫 Not implemented | Placeholder only |
| `app/utils/crypto.py` | N/A | ✅ Present | Password encryption |

### Frontend (React Dashboard)

| File | Status | Purpose |
|------|--------|---------|
| `dashboard/src/App.js` | ✅ Active | Main routing + setup check |
| `dashboard/src/pages/SetupPage.js` | ✅ Active | Setup page wrapper |
| `dashboard/src/pages/DevicesPage.js` | ✅ Active | Device list (simple table) |
| `dashboard/src/pages/AlertsPage.js` | ✅ Active | Alerts display |
| `dashboard/src/pages/AgentsPage.js` | ✅ Active | Agent management |
| `dashboard/src/components/setup/SetupWizard.js` | ✅ Active | **3-step setup wizard** |
| `dashboard/src/lib/routerDiscovery.js` | ✅ Active | Frontend discovery helpers |

---

## 2. Discovery Methods Matrix

| Method | Exists | Integrated | Working | Location |
|--------|--------|------------|---------|----------|
| **ARP Scanning** | ✅ Yes | ✅ Yes | ✅ Yes | `routers/implementations/generic.py` |
| **MAC OUI Lookup** | ✅ Yes | ✅ Yes | ✅ Yes | 300+ OUIs in `generic.py` |
| **Reverse DNS** | ✅ Yes | ✅ Yes | ✅ Yes | `get_device_name()` in `generic.py` |
| **mDNS/Bonjour** | ✅ Yes | ❌ **NO** | ⚠️ Partial | `device_discovery.py` (orphaned) |
| **NetBIOS** | ✅ Yes | ❌ **NO** | ⚠️ Partial | `device_discovery.py` (orphaned) |
| **SNMP** | ✅ Yes | ❌ **NO** | ⚠️ Partial | `device_discovery.py` (orphaned) |
| **UPnP/SSDP** | ✅ Yes | ❌ **NO** | ⚠️ Partial | `device_discovery.py` (orphaned) |
| **Router API** | 🏗️ Partial | ❌ No | ❌ No | Factory exists but no implementations |

### Discovery Method Details

#### ✅ Active: ARP + MAC OUI + Reverse DNS (GenericRouter)
- **Method:** Reads Linux ARP table via `ip neigh show`
- **MAC OUI Database:** 300+ entries covering Apple, Samsung, ASUS, TP-Link, Netgear, Amazon, Google, Nintendo, etc.
- **Device Type Inference:** Based on vendor (e.g., Nintendo → gaming, Amazon → IoT)
- **Naming:** Reverse DNS first, then MAC-based fallback

#### ⚠️ Orphaned: Multi-Protocol Discovery (device_discovery.py)
- **mDNS:** Full implementation with avahi-browse fallback
- **NetBIOS:** nmblookup-based with socket fallback
- **SNMP:** snmpget-based system description queries
- **UPnP/SSDP:** Full SSDP multicast implementation with XML parsing
- **Status:** Complete but never imported or called

---

## 3. API Endpoint Catalog

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/setup/discover` | POST | ✅ Working | Returns routers found on network |
| `/api/setup/connect` | POST | ✅ Working | Triggers ARP scan + imports devices |
| `/api/setup/status` | GET | ✅ Working | Returns setup completion status |
| `/api/devices` | GET | ✅ Working | Lists all devices (paginated) |
| `/api/devices/{id}` | GET | ✅ Working | Get specific device |
| `/api/devices/{id}/block` | POST | ✅ Working | Block device |
| `/api/devices/{id}/unblock` | POST | ✅ Working | Unblock device |
| `/api/devices/{id}` | PATCH | ✅ Working | Update device nickname/type |
| `/api/agents` | GET | ✅ Working | List agents (static) |
| `/api/alerts` | GET | ✅ Working | List security alerts |
| `/api/stats` | GET | ✅ Working | Dashboard statistics |
| `/api/security/events` | GET | ✅ Working | Security events |

### Missing Endpoints (Expected but Not Implemented)

| Endpoint | Purpose | Gap |
|----------|---------|-----|
| `/api/devices/{id}/details` | Device detail page | ❌ Not implemented |
| `/api/devices/{id}/trust` | Get/set trust score | ❌ Not implemented |
| `/api/discovery/enhanced` | Multi-protocol discovery | ❌ Not implemented |
| `/api/devices/refresh` | Trigger re-discovery | ❌ Not implemented |

---

## 4. Setup Wizard Flow Analysis

### Current 3-Step Flow (SetupWizard.js)

```
Step 1: Welcome
   ↓ "Get Started" button
Step 2: Device Scan (ARP-based)
   ↓ Calls POST /api/setup/connect
Step 3: Confirmation
   ↓ "Yes, looks good!" → redirect to dashboard
```

### Issues Identified

1. **Step 2 Bug:** The "Get Started" button advances to step 2, but the `handleStartScan` function just sets router info without actually triggering a scan. The scan only happens when "Scan for Devices" is clicked.

2. **No Enhanced Discovery:** Step 2 uses only ARP scanning via `GenericRouter.get_connected_devices()` — it does NOT use the `DeviceDiscoveryService` from `device_discovery.py`.

3. **No Device Detail:** After setup, there's no way to view device details (no detail pages exist).

---

## 5. Gap Analysis: Working State (May 22-23) vs Current

### What Was Working May 22-23

Based on memory records, the following was implemented:
- ✅ Multi-protocol discovery module (`device_discovery.py`) created
- ✅ MAC OUI database with 300+ entries
- ✅ Discovery methods: ARP, mDNS, NetBIOS, SNMP, UPnP
- ✅ Device classification by MAC + hostname patterns
- ✅ Setup wizard with device discovery flow
- ✅ Backend API endpoints for setup

### Current Gaps

| Gap | Impact | Root Cause |
|-----|--------|------------|
| Only 12 devices found | Missing ~7-8 devices | Only ARP scanning active; mDNS/UPnP not wired in |
| No agent detection | Agents show as regular devices | Agent identification logic not implemented |
| Setup "Get Started" appears non-functional | User confusion | Actually advances but UI doesn't reflect this well |
| No device detail pages | Can't drill into device | Pages never implemented |
| device_discovery.py unused | Duplicate effort | Module created but never integrated into setup flow |
| No continuous discovery | New devices not auto-detected | No background scanning scheduled |

### Device Count Reconciliation

**Expected:** ~19 devices + 3-4 agents = ~22-23 total  
**Current:** 12 devices  
**Missing:** ~10 devices

**Likely Missing (based on MAC OUI patterns in database):**
- IoT devices (may not respond to ARP but would to UPnP)
- WiFi devices with short ARP timeouts
- Devices on different VLANs/subnets
- Mobile devices in sleep mode

---

## 6. Integration Architecture

### Current Data Flow

```
SetupWizard.js → POST /api/setup/connect
                      ↓
              setup.py:connect_router()
                      ↓
              GenericRouter(credentials)
                      ↓
              get_connected_devices() [ARP only]
                      ↓
              import_devices_from_router()
                      ↓
              Database (Device model)
```

### Missing Integration (device_discovery.py)

```
DeviceDiscoveryService (device_discovery.py)
    ├── MDNSDiscovery (mDNS/Bonjour)
    ├── NetBIOSDiscovery (Windows/Samba names)
    ├── SNMPDiscovery (system descriptions)
    └── UPnPDiscovery (SSDP multicast)
    
    SHOULD BE CALLED BY:
    └── GenericRouter.get_connected_devices()
        OR
    └── New endpoint: POST /api/discovery/enhanced
```

---

## 7. Recommended Integration Order

### Priority 1: Fix Device Count (Immediate)

1. **Wire device_discovery.py into setup flow**
   - Modify `setup.py:connect_router()` to instantiate `DeviceDiscoveryService`
   - After ARP scan, run `discovery_service.scan_network()` for UPnP devices
   - Merge results before importing to database

2. **Add background refresh endpoint**
   - `POST /api/devices/refresh` → triggers re-discovery
   - Call from frontend periodically or on demand

### Priority 2: Agent Detection (This Week)

1. **Identify agents by MAC/IP pattern**
   - Woodhouse: 192.168.50.24
   - Liz: 192.168.50.XX
   - Ray: 192.168.50.XX
   - Store in `devices.is_agent = true`

2. **Update agents.py to query devices table**
   - Instead of static list, query `WHERE is_agent = true`

### Priority 3: Device Detail Pages (Next Sprint)

1. **Create device detail endpoint**
   - `GET /api/devices/{id}/details` → full discovery info

2. **Create DeviceDetailPage.js**
   - Show discovery sources, services, trust history

### Priority 4: Full Discovery Integration (Later)

1. **Merge device_discovery into router abstraction**
   - Move discovery classes into `routers/implementations/` as mixins
   - Or create `EnhancedDeviceRouter` class

2. **Add continuous discovery**
   - Background task runner for periodic scans
   - WebSocket or SSE for real-time device join/leave events

---

## 8. File Paths Summary

```
GX-10 ~/projects/vigil-home/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry
│   │   ├── models.py                  # Database models
│   │   ├── device_discovery.py        # ⚠️ ORPHANED - multi-protocol discovery
│   │   └── routers/
│   │       ├── setup.py                # Setup endpoints
│   │       ├── devices.py              # Device CRUD
│   │       ├── discovery.py            # Router discovery
│   │       ├── base.py                 # Router abstraction
│   │       ├── factory.py              # Router factory
│   │       └── implementations/
│   │           └── generic.py          # ✅ PRIMARY - ARP discovery
│   └── venv/                           # Python environment
├── dashboard/
│   └── src/
│       ├── App.js                      # Main routing
│       ├── pages/
│       │   ├── SetupPage.js            # Setup wrapper
│       │   └── DevicesPage.js          # Device list
│       ├── components/
│       │   └── setup/
│       │       └── SetupWizard.js      # ✅ 3-step wizard
│       └── lib/
│           └── routerDiscovery.js      # Frontend helpers
└── specs/                               # Documentation
```

---

## 9. Quick Wins

### 5-Minute Fix: Import device_discovery in setup.py

Add to `backend/app/routers/setup.py`:
```python
from app.device_discovery import DeviceDiscoveryService

# In connect_router(), after ARP scan:
service = DeviceDiscoveryService()
upnp_devices = await service.scan_network()
# Merge upnp_devices with ARP results
```

### 30-Minute Fix: Add device count refresh

Add button to DevicesPage.js that calls:
```javascript
fetch('/api/setup/connect', { method: 'POST', body: {...} })
```

---

## Appendix: MAC OUI Database Coverage

**Vendors with 10+ OUIs defined:**
- Amazon (Echo, Fire TV): 90+ OUIs
- TP-Link: 70+ OUIs
- Netgear: 60+ OUIs
- Nintendo: 30+ OUIs
- Apple (iPhone, Mac): 10+ OUIs
- Samsung: 20+ OUIs
- Google (Pixel, Nest): 10+ OUIs
- ASUS: 8 OUIs
- Sony (PlayStation): 20+ OUIs
- LG: 10+ OUIs

---

**Report Generated:** 2026-05-24 06:15 EDT  
**Next Steps:** Priority 1 integration recommended for immediate device count improvement
