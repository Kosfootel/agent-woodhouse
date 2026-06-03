# Vigil Device Fingerprinting Analysis
## Multi-Homed Mobile Device Detection Problem

---

## Current State Analysis

### How Vigil Currently Detects Device IPs

**Location:** `~/projects/vigil-home/projects/vigil-home/poc-backend/app/detection.py`

**Method:** Suricata eve.json consumer with packet capture

**Key Code Flow:**
```python
# Lines 86-91 in detection.py
def _get_or_create_device(db, src_ip: str, src_mac: str | None, hostname: str | None) -> Device:
    """Find or create a device record for the given IP/MAC."""
    device = db.query(Device).filter(Device.ip == src_ip).first()  # ❌ IP as primary key
    if device:
        device.last_seen = datetime.now(timezone.utc)
        if src_mac and device.mac != src_mac:
            device.mac = src_mac  # ❌ MAC updated after IP match, not used for lookup
```

**Critical Issues Found:**

1. **IP-Centric Lookup:** Device lookup is by IP address first (`filter(Device.ip == src_ip)`). MAC is secondary/optional.

2. **Suricata MAC Capture Limitations:**
   - Suricata captures MAC from Ethernet frames (layer 2)
   - `src_mac = record.get("src_mac")` or from `eth.src`
   - This works only for packets on the **local network segment**
   - For packets from outside (like via NAT), MAC shows gateway/router MAC, not device MAC

3. **Multi-Homing Problem:**
   - Phone on WiFi: Gets local 192.168.x.x IP → MAC captured correctly
   - Phone on 5G: Gets carrier NAT IP → MAC shows as router/gateway MAC
   - Both IPs map to different device records → Same phone appears as two devices

4. **Database Schema Constraint (models.py):**
   ```python
   class Device(Base):
       mac = Column(String(17), unique=True, nullable=False)  # ✅ MAC is unique
       ip = Column(String(45), nullable=False)                # ❌ But lookup is by IP
   ```
   - MAC has `unique=True` but the code queries by IP first

---

## Root Cause Summary

| Layer | Data | Problem |
|-------|------|---------|
| L2 (MAC) | Device MAC | Captured correctly for WiFi, gateway MAC for cellular |
| L3 (IP) | Device IP | Different IPs per interface (WiFi vs 5G) |
| Application | Device Record | Created per-IP, not per-MAC |

**Result:** One physical device creates multiple DB entries, no correlation between them.

---

## Recommended Fingerprinting Techniques

### 1. **MAC Address as Primary Key** (Priority: Critical)

**Change:** Always look up devices by MAC first, IP second.

```python
def _get_or_create_device(db, src_ip: str, src_mac: str | None, hostname: str | None, 
                          user_agent: str | None = None, fingerprint: dict | None = None) -> Device:
    # Primary lookup by MAC
    if src_mac and not _is_gateway_mac(src_mac):
        device = db.query(Device).filter(Device.mac == src_mac).first()
        if device:
            # Update IP history
            if device.ip != src_ip:
                _record_ip_change(device.id, device.ip, src_ip)
                device.ip = src_ip
            device.last_seen = datetime.now(timezone.utc)
            db.commit()
            return device
    
    # Secondary lookup by composite fingerprint
    if fingerprint:
        device = _find_by_fingerprint(db, fingerprint)
        if device:
            # Update MAC if now known
            if src_mac and not device.mac:
                device.mac = src_mac
            return device
    
    # Fallback to IP (with caution)
    # ... existing logic
```

**IP History Table:**
```python
class DeviceIPHistory(Base):
    """Track IP changes for a device over time."""
    __tablename__ = "device_ip_history"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    ip_address = Column(String(45), nullable=False)
    first_seen = Column(DateTime, default=datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=datetime.now(timezone.utc))
    source = Column(String(32))  # 'dhcp', 'suricata', 'mDNS', 'router_api'
```

---

### 2. **DHCP Fingerprinting** (Priority: High)

**Purpose:** Identify device type from DHCP request options even without MAC visibility.

**Implementation:**
- Parse DHCP packets (Suricata captures these)
- Extract DHCP options fingerprint (option 55, 60, 61)
- Compare against known fingerprints (iOS, Android, Windows, etc.)

**Sample DHCP Fingerprints:**
```python
DHCP_FINGERPRINTS = {
    "1,3,6,15,119,252,95,44,46": "iOS",  # Apple iPhone/iPad
    "1,3,6,15,119,252,95,44,46,47": "macOS",
    "1,3,6,15,31,33,43,44,46,47,119,121,249,252": "Android",
    "1,15,3,6,44,46,47,31,33,121,249,43,252": "Windows",
}
```

**Detection Enhancement:**
```python
def _extract_dhcp_fingerprint(record: dict) -> str | None:
    """Extract DHCP fingerprint from Suricata DHCP event."""
    if record.get("event_type") == "dhcp":
        dhcp_data = record.get("dhcp", {})
        options = dhcp_data.get("options", [])
        # Sort and join option codes
        fingerprint = ",".join(str(opt.get("code")) for opt in options if opt.get("code"))
        return fingerprint
    return None
```

---

### 3. **Passive OS Fingerprinting (p0f)** (Priority: High)

**Purpose:** Identify OS from TCP/IP stack behavior without payload inspection.

**Implementation Options:**

**Option A: Suricata Built-in**
- Suricata has built-in p0f-style fingerprinting in `decoder` events
- Look for `event_type: "pcre"` or use Lua scripts

**Option B: Standalone p0f**
```python
import subprocess

def get_p0f_fingerprint(ip: str) -> dict | None:
    """Query p0f socket for OS fingerprint."""
    try:
        result = subprocess.run(
            ["p0f", "-s", "/var/run/p0f.sock", "-q", ip],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return parse_p0f_output(result.stdout)
    except Exception:
        return None
```

**Fingerprints to Store:**
```python
class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    
    device_id = Column(Integer, ForeignKey("devices.id"))
    os_guess = Column(String(64))  # "iOS 16.x", "Android 13"
    os_score = Column(Integer)  # p0f confidence (0-100)
    distance = Column(Integer)  # Network hops
    link_type = Column(String(32))  # "Ethernet", "WiFi", "LTE"
    raw_fp = Column(Text)  # Full fingerprint string
```

---

### 4. **mDNS/Bonjour Hostname Discovery** (Priority: Medium-High)

**Purpose:** Catch device hostnames advertised via multicast DNS.

**Why:** Phones often broadcast `.local` hostnames (e.g., "Eriks-iPhone.local")

**Implementation:**
```python
import socket
import struct

MDNS_PORT = 5353
MDNS_GROUP = "224.0.0.251"

def start_mdns_listener():
    """Listen for mDNS PTR and A records."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MDNS_PORT))
    
    mreq = struct.pack("4sl", socket.inet_aton(MDNS_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    while True:
        data, addr = sock.recvfrom(1024)
        parse_mdns_packet(data, addr)

def parse_mdns_packet(data: bytes, addr: tuple):
    """Parse mDNS packet for hostnames and services."""
    # Use dnslib or simple parsing
    # Look for A records and PTR records
    hostname = extract_hostname_from_mdns(data)
    if hostname:
        device_ip = addr[0]
        # Update or create device with this hostname
        update_device_hostname(device_ip, hostname, source="mDNS")
```

**Suricata Integration:**
- Suricata can log mDNS queries via Lua scripts
- Add custom rule: `alert udp any any -> 224.0.0.251 5353 (msg:"mDNS query"; sid:1000001;)`

---

### 5. **TLS/JA3 Fingerprinting** (Priority: Medium)

**Purpose:** Identify device/client type from TLS handshake characteristics.

**Already Partially in Vigil:**
```python
# detection.py lines 153-163 - TLS handling
tls_data = record.get("tls", {})
details = {
    "fingerprint": tls_data.get("fingerprint"),  # ❌ This is cert fingerprint, not JA3
    # ...
}
```

**JA3 Enhancement:**
```python
def calculate_ja3(record: dict) -> str | None:
    """Calculate JA3 fingerprint from TLS Client Hello."""
    tls = record.get("tls", {})
    # JA3 components:
    # 1. SSLVersion
    # 2. CipherSuites
    # 3. Extensions
    # 4. EllipticCurves
    # 5. EllipticCurvePointFormats
    
    # Suricata 6.0+ supports JA3 natively
    ja3_hash = tls.get("ja3", {}).get("hash")
    ja3_string = tls.get("ja3", {}).get("string")
    return ja3_hash

# Known JA3 signatures
JA3_DEVICE_SIGNATURES = {
    "769,47-53-5-10-49161-49162-49171-49172-49191-49192-49199-49200-158-162-106-47-7-10-5-53-49161-49162-49171-49172-50-56-19-4": "iOS Safari",
    "771,49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10": "Chrome/Android",
}
```

---

### 6. **Router API Integration** (Priority: Medium)

**Purpose:** Use router's authoritative DHCP table as ground truth.

**Implementation by Router:**

**UniFi Controller:**
```python
import requests

def get_unifi_clients() -> list[dict]:
    """Fetch connected clients from UniFi Controller."""
    session = requests.Session()
    # Login
    session.post(
        f"{UNIFI_URL}/api/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    # Get clients
    resp = session.get(f"{UNIFI_URL}/api/s/default/stat/sta")
    return [
        {
            "mac": c["mac"],
            "ip": c["ip"],
            "hostname": c.get("hostname", c.get("name", "")),
            "ap_mac": c.get("ap_mac"),  # For WiFi location tracking
            "radio": c.get("radio"),  # "ng" = 2.4GHz, "na" = 5GHz
            "signal": c.get("signal"),  # RSSI
        }
        for c in resp.json()["data"]
    ]
```

**OpenWrt:**
```python
def get_openwrt_dhcp_leases() -> list[dict]:
    """Fetch DHCP leases from OpenWrt."""
    # Via SSH or ubus
    result = subprocess.run(
        ["ssh", "root@openwrt", "cat /tmp/dhcp.leases"],
        capture_output=True, text=True
    )
    # Parse: timestamp mac ip hostname *duid
    leases = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 4:
            leases.append({
                "mac": parts[1],
                "ip": parts[2],
                "hostname": parts[3] if parts[3] != "*" else None,
            })
    return leases
```

**pfSense/OPNsense:**
```python
def get_pfsense_dhcp_leases() -> list[dict]:
    """Fetch DHCP leases via API."""
    resp = requests.get(
        f"{PFSENSE_URL}/api/v1/status/dhcp_leases",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return resp.json()["data"]
```

---

### 7. **HTTP User-Agent Analysis** (Priority: Low-Medium)

**Already Captured:**
```python
# detection.py lines 117-125
elif event_type == "http":
    http_data = record.get("http", {})
    details = {
        "user_agent": http_data.get("http_user_agent"),  # ✅ Available
    }
```

**Enhancement:**
```python
import re
from ua_parser import user_agent_parser

def analyze_user_agent(ua_string: str) -> dict:
    """Parse User-Agent for device identification."""
    if not ua_string:
        return {}
    
    parsed = user_agent_parser.Parse(ua_string)
    return {
        "device_type": parsed["device"]["family"],  # "iPhone", "SM-G991B"
        "os_family": parsed["os"]["family"],  # "iOS", "Android"
        "os_version": f"{parsed['os']['major']}.{parsed['os']['minor']}",
        "browser": parsed["user_agent"]["family"],
    }
```

---

## Implementation Priority

| Priority | Technique | Complexity | Impact |
|----------|-----------|------------|--------|
| P0 | **MAC-first lookup** + IP history | Low | Critical - Fixes core bug |
| P1 | DHCP fingerprinting | Medium | High - Identifies device type |
| P1 | mDNS listener | Low | High - Catches hostnames |
| P2 | Router API integration | Medium | High - Ground truth source |
| P2 | p0f OS fingerprinting | Medium | Medium - OS detection |
| P3 | JA3 TLS fingerprinting | Low | Medium - Client identification |
| P3 | User-Agent parsing | Low | Low - Supplementary info |

---

## Code Sketch: Device Correlation Engine

```python
# app/device_correlation.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from datetime import datetime, timezone
from typing import Optional

class DeviceAlias(Base):
    """Track aliases for a device (multiple IPs, hostnames)."""
    __tablename__ = "device_aliases"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    alias_type = Column(String(32))  # 'ip', 'hostname', 'mac_variant'
    alias_value = Column(String(255), index=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confidence = Column(Float, default=1.0)  # 0.0-1.0
    source = Column(String(64))  # 'dhcp', 'suricata', 'mdns', 'router_api'


class DeviceCorrelationEngine:
    """Correlate multiple identifiers to a single device."""
    
    def resolve_device(self, db, 
                      ip: str,
                      mac: Optional[str] = None,
                      hostname: Optional[str] = None,
                      dhcp_fingerprint: Optional[str] = None,
                      ja3_hash: Optional[str] = None,
                      user_agent: Optional[str] = None) -> Device:
        """
        Find or create a device using all available identifiers.
        
        Algorithm:
        1. Try MAC match (highest confidence)
        2. Try composite match (multiple weaker signals)
        3. Try IP match with recent activity
        4. Create new device if no match
        """
        
        # 1. MAC-based lookup (avoid gateway MACs)
        if mac and not self._is_gateway_mac(mac):
            device = db.query(Device).filter(Device.mac == mac).first()
            if device:
                self._update_device_aliases(device, ip, hostname)
                return device
        
        # 2. Composite fingerprint matching
        device = self._find_by_composite_fingerprint(
            db, dhcp_fingerprint, ja3_hash, hostname
        )
        if device:
            if mac:
                device.mac = mac  # Now we know the MAC
            self._update_device_aliases(device, ip, hostname)
            return device
        
        # 3. IP match with temporal window (last 24h)
        recent = datetime.now(timezone.utc) - timedelta(hours=24)
        device = (db.query(Device)
                  .filter(Device.ip == ip)
                  .filter(Device.last_seen >= recent)
                  .first())
        if device:
            self._update_device_aliases(device, ip, hostname, mac)
            return device
        
        # 4. Create new device
        return self._create_new_device(db, ip, mac, hostname, dhcp_fingerprint)
    
    def _find_by_composite_fingerprint(self, db, dhcp_fp, ja3, hostname):
        """Match device by multiple weak signals combined."""
        # Query aliases for matching signals
        matches = {}
        
        if dhcp_fp:
            alias = db.query(DeviceAlias).filter(
                DeviceAlias.alias_type == 'dhcp_fingerprint',
                DeviceAlias.alias_value == dhcp_fp
            ).first()
            if alias:
                matches[alias.device_id] = matches.get(alias.device_id, 0) + 0.4
        
        if ja3:
            alias = db.query(DeviceAlias).filter(
                DeviceAlias.alias_type == 'ja3_hash',
                DeviceAlias.alias_value == ja3
            ).first()
            if alias:
                matches[alias.device_id] = matches.get(alias.device_id, 0) + 0.3
        
        if hostname and len(hostname) > 3:
            alias = db.query(DeviceAlias).filter(
                DeviceAlias.alias_type == 'hostname',
                DeviceAlias.alias_value == hostname
            ).first()
            if alias:
                matches[alias.device_id] = matches.get(alias.device_id, 0) + 0.3
        
        # Return device with highest confidence > 0.7
        if matches:
            best_match = max(matches.items(), key=lambda x: x[1])
            if best_match[1] >= 0.7:
                return db.query(Device).filter(Device.id == best_match[0]).first()
        return None
    
    def _is_gateway_mac(self, mac: str) -> bool:
        """Check if MAC is likely a gateway/router."""
        # Common OUI prefixes for routers
        router_ouis = [
            "00:00:5e",  # IANA
            "00:50:56",  # VMware
            "52:54:00",  # QEMU/KVM
        ]
        mac_prefix = mac.lower()[:8]
        return mac_prefix in router_ouis
```

---

## Database Migration

```sql
-- Add IP history tracking
CREATE TABLE device_ip_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(32),
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
CREATE INDEX idx_ip_history_device ON device_ip_history(device_id);
CREATE INDEX idx_ip_history_ip ON device_ip_history(ip_address);

-- Add alias tracking
CREATE TABLE device_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    alias_type VARCHAR(32) NOT NULL,  -- 'ip', 'hostname', 'dhcp_fp', 'ja3'
    alias_value VARCHAR(255) NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(64),
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
CREATE INDEX idx_alias_lookup ON device_aliases(alias_type, alias_value);
CREATE INDEX idx_alias_device ON device_aliases(device_id);

-- Add fingerprinting columns to devices
ALTER TABLE devices ADD COLUMN dhcp_fingerprint VARCHAR(128);
ALTER TABLE devices ADD COLUMN ja3_hash VARCHAR(32);
ALTER TABLE devices ADD COLUMN p0f_os_guess VARCHAR(64);
ALTER TABLE devices ADD COLUMN mdns_hostname VARCHAR(255);
```

---

## Summary

**Immediate Fix Required:**
1. Change `_get_or_create_device()` to lookup by MAC first
2. Add `device_ip_history` table to track IP changes
3. Add `device_aliases` table for multi-identifier correlation

**Quick Wins:**
- Enable mDNS listening (low effort, catches phone hostnames)
- Integrate router API for authoritative DHCP tables

**Medium-term:**
- Add DHCP fingerprinting via Suricata Lua scripts
- Deploy p0f for OS fingerprinting
- Implement JA3 extraction from TLS events

**Result:** Phones will appear as single devices with IP history showing WiFi ↔ 5G transitions, rather than as duplicate/conflicting entries.
