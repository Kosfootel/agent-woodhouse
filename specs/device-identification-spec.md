# Vigil Device Identification Enhancement - Specification

**Date:** 2026-05-22  
**Status:** Ready for Implementation  
**Hermes Handoff:** Yes

---

## Overview

This specification defines enhancements to Vigil's device identification capabilities, moving from passive OUI-based classification to active discovery and user-assisted identification.

## Background

### Current State
- Device classification relies primarily on MAC OUI lookup
- Most devices show as "unknown" type
- No active communication with devices to gather more information
- Users must manually cross-reference router data with Vigil

### Goals
1. **Active Discovery**: Poll devices via mDNS, NetBIOS, SNMP, UPnP to gather metadata
2. **Better Classification**: Use discovery data to infer device types with confidence scores
3. **User Control**: Allow users to edit device types and nicknames
4. **Router Integration**: Enrich device data with information from router APIs

---

## Deliverables

### 1. Database Schema Updates

Add tables to store discovery results and user-provided metadata:

```sql
-- Device discovery sources (mDNS, NetBIOS, SNMP, UPnP results)
CREATE TABLE device_discovery_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('mdns', 'netbios', 'snmp', 'upnp', 'router_api')),
    ip_at_time TEXT NOT NULL,
    hostname TEXT,
    device_name TEXT,
    device_type_hint TEXT,
    vendor TEXT,
    model TEXT,
    services TEXT, -- JSON array of discovered services
    raw_data TEXT, -- JSON blob with raw discovery data
    confidence REAL DEFAULT 0.0,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_discovery_sources_device ON device_discovery_sources(device_id);
CREATE INDEX idx_discovery_sources_type ON device_discovery_sources(source_type);

-- IP to MAC history tracking (for static IP devices)
CREATE TABLE mac_ip_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT NOT NULL,
    ip TEXT NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT, -- 'dhcp', 'arp', 'router_api', 'discovery'
    FOREIGN KEY (mac) REFERENCES devices(mac) ON DELETE CASCADE
);

CREATE INDEX idx_mac_ip_history_mac ON mac_ip_history(mac);
CREATE INDEX idx_mac_ip_history_ip ON mac_ip_history(ip);
CREATE INDEX idx_mac_ip_history_last_seen ON mac_ip_history(last_seen);

-- Add columns to existing devices table
ALTER TABLE devices ADD COLUMN user_nickname TEXT;
ALTER TABLE devices ADD COLUMN user_notes TEXT;
ALTER TABLE devices ADD COLUMN user_device_type TEXT; -- User override
ALTER TABLE devices ADD COLUMN device_type_confidence REAL DEFAULT 0.0;
ALTER TABLE devices ADD COLUMN discovery_sources TEXT; -- JSON array
ALTER TABLE devices ADD COLUMN last_discovery_attempt DATETIME;
ALTER TABLE devices ADD COLUMN is_static_ip BOOLEAN DEFAULT FALSE;
```

### 2. Enhanced Device Discovery Service

**Location:** `/app/device_discovery.py` (already created)

This module provides:
- mDNS/Bonjour scanning for hostnames and services
- NetBIOS name resolution for Windows/Samba devices
- SNMP read-only queries for system descriptions
- UPnP/SSDP discovery for IoT devices

**Key Classes:**
- `DeviceDiscoveryService`: Main service class
- `MDNSDiscovery`: mDNS service discovery
- `NetBIOSDiscovery`: NetBIOS name resolution
- `SNMPDiscovery`: SNMP system queries
- `UPnPDiscovery`: UPnP/SSDP discovery

### 3. API Endpoints

Add to FastAPI routers:

```python
# GET /devices/{id}/discover
# Trigger discovery for a specific device
# Returns: DiscoveryResult with aggregated information

# POST /devices/{id}/nickname
# Set user nickname for device
# Body: {"nickname": "Living Room TV", "notes": "Samsung Smart TV"}

# POST /devices/{id}/type
# Set user-defined device type
# Body: {"device_type": "smart_tv", "override_auto": true}

# GET /devices/{id}/discovery-history
# Get discovery history for device
# Returns: List of DeviceDiscoverySource records

# GET /devices/{id}/ip-history
# Get IP address history for device
# Returns: List of MacIpHistory records

# POST /devices/{id}/classify
# Trigger re-classification based on discovery data
# Uses discovery sources + behavioral signatures

# GET /discovery/suggestions
# Get device type suggestions for all unknown devices
# Returns: List of {device_id, suggested_type, confidence, reasons}

# POST /discovery/scan
# Trigger network-wide discovery scan
# Body: {"method": "upnp" | "mdns" | "all", "subnet": "192.168.1.0/24"}
```

### 4. Router Integration Updates

Update the existing router integration (`router_integration.py`) to:
1. Store discovered device information in `device_discovery_sources`
2. Update `mac_ip_history` with router client list data
3. Enrich device records with router-provided hostnames and names

### 5. Classification Enhancements

Extend the existing classifier (`app/ai/classifier.py`) to:
1. Use discovery source data as additional features
2. Provide confidence scores for classifications
3. Support user overrides

**Classification Logic:**
```python
def classify_device(device: Device) -> Tuple[str, float]:
    # Priority order:
    # 1. User-defined type (if override_auto = true)
    if device.user_device_type and device.override_auto:
        return device.user_device_type, 1.0
    
    # 2. Discovery source type hints (high confidence)
    for source in device.discovery_sources:
        if source.confidence > 0.8:
            return source.device_type_hint, source.confidence
    
    # 3. Behavioral signature matching
    behavioral_result = classifier.classify(device.mac, device.behavioral_features)
    
    # 4. OUI-based vendor inference (lowest confidence)
    oui_result = classifier.oui_vendor(device.mac)
    
    # Combine and return best match
    ...
```

---

## Implementation Order

1. **Database Schema** (30 min)
   - Create migration script
   - Add new tables and columns

2. **Discovery Service Integration** (1 hour)
   - Integrate `device_discovery.py` into FastAPI app
   - Add discovery endpoints

3. **Router Integration Update** (45 min)
   - Update sync service to populate discovery tables
   - Add IP history tracking

4. **Classification Enhancement** (1 hour)
   - Update classifier to use discovery data
   - Add confidence scoring

5. **API Endpoints** (1 hour)
   - Implement all new endpoints
   - Add validation and error handling

6. **Dashboard Updates** (2 hours)
   - Add device type editor
   - Show discovery sources
   - Display confidence indicators

---

## Testing

### Unit Tests
- Discovery service with mocked network calls
- Classification with known device signatures
- Database operations for new tables

### Integration Tests
- End-to-end device discovery flow
- Router sync with discovery enrichment
- API endpoint testing

### Manual Testing
- Verify discovery on actual network devices
- Test user override functionality
- Validate confidence scoring accuracy

---

## Security Considerations

1. **SNMP**: Use only read-only community strings (default: "public")
2. **mDNS/SSDP**: Passive listening only, no aggressive scanning
3. **Rate Limiting**: Limit discovery frequency per device (max 1/minute)
4. **Privacy**: Store only necessary metadata, not sensitive device data

---

## Files to Create/Modify

### New Files
- `/app/routers/discovery.py` - Discovery API endpoints
- `/app/routers/devices_enhanced.py` - Extended device endpoints
- `/migrations/add_discovery_schema.sql` - Database migration

### Modified Files
- `/app/models.py` - Add DeviceDiscoverySource, MacIpHistory models
- `/app/main.py` - Integrate discovery service and new routers
- `/app/ai/classifier.py` - Enhance with discovery data
- `/app/router_integration.py` - Update to populate discovery tables
- `/app/device_discovery.py` - Already created, may need minor adjustments

---

## Acceptance Criteria

- [ ] mDNS discovery finds devices with .local hostnames
- [ ] NetBIOS discovery resolves Windows device names
- [ ] SNMP queries retrieve system descriptions
- [ ] UPnP discovery identifies IoT and media devices
- [ ] Device type suggestions appear for unknown devices
- [ ] Users can set custom nicknames
- [ ] Users can override automatic device type classification
- [ ] Discovery sources visible in device detail view
- [ ] IP history tracked for static IP detection
- [ ] Router data enriches device records

---

## Hermes Handoff

**Ready for Implementation:** Yes

**Spec Location:** `~/projects/vigil-home/specs/device-identification-spec.md`

**Dependencies:**
- Database access (`vigil.db`)
- FastAPI app structure
- Existing classifier module

**Expected Output:**
- Working discovery service
- New API endpoints
- Database migration applied
- Updated device classification

**On Blocked:** Return specific questions about:
- SNMP community strings (use "public" or user-configured?)
- Discovery frequency settings
- Confidence threshold for auto-classification

---

## Appendix: Discovery Method Details

### mDNS Services
Queries for common service types to identify device capabilities:
- `_airplay._tcp` → Apple TV, HomePod
- `_googlecast._tcp` → Chromecast, Nest speakers
- `_hap._tcp` → HomeKit devices
- `_printer._tcp` → Network printers
- `_scanner._tcp` → Network scanners

### SNMP OIDs
Standard MIB-II system group:
- `1.3.6.1.2.1.1.1.0` (sysDescr) - System description
- `1.3.6.1.2.1.1.5.0` (sysName) - System name
- `1.3.6.1.2.1.1.4.0` (sysContact) - Contact info

### UPnP Service Types
Key device type indicators:
- `MediaRenderer` → Smart TV, media player
- `MediaServer` → NAS, media server
- `Printer` → Network printer
- `Camera` → IP camera
- `InternetGatewayDevice` → Router
