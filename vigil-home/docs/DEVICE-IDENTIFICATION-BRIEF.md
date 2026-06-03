# Device Identification Implementation Brief
**For:** Liz (GX-10 Backend)  
**From:** Woodhouse  
**Date:** 2026-05-08  
**Priority:** Medium  
**Est. Effort:** 4-6 hours

---

## Current State
All 50 network devices show `device_type: null` and `hostname: null`. Users cannot identify what's on their network.

## Objective
Implement automatic device identification via:
1. **MAC OUI lookup** → Manufacturer identification
2. **mDNS discovery** → Hostname capture

---

## Task 1: MAC OUI Database Lookup

### Goal
Parse MAC address prefix to identify device manufacturer.

### Data Source
IEEE OUI Registry (public, free):  
https://standards-ieee.org/products-services/registries/oui/

Or use Wireshark's `manuf` file (maintained, ~16K entries):  
https://gitlab.com/wireshark/wireshark/-/raw/master/manuf

### Implementation

```python
# 1. Download/parse OUI database
# Format: "00:00:00\tXerox\tXerox Corporation"

import csv
from pathlib import Path

class OUILookup:
    def __init__(self, manuf_file: str = "manuf.txt"):
        self.oui_map = {}
        self._load_oui(manuf_file)
    
    def _load_oui(self, filepath: str):
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    mac_prefix = parts[0].replace(':', '').upper()
                    self.oui_map[mac_prefix] = parts[1]
    
    def lookup(self, mac: str) -> str | None:
        """Extract OUI from MAC and return manufacturer."""
        # Normalize MAC: "00:00:00:192:168:50:24" -> "000000"
        clean_mac = mac.replace(':', '').replace('-', '').upper()
        oui = clean_mac[:6]  # First 3 octets
        return self.oui_map.get(oui)

# 2. Integrate into device discovery
# In your device ingestion pipeline:

async def enrich_device(device: dict) -> dict:
    oui_lookup = OUILookup()
    
    # Parse MAC and get manufacturer
    if mac := device.get('mac'):
        device['manufacturer'] = oui_lookup.lookup(mac)
        
        # Infer device_type from manufacturer hints
        device['device_type'] = infer_type_from_manufacturer(
            device['manufacturer']
        )
    
    return device

def infer_type_from_manufacturer(mfr: str | None) -> str | None:
    """Heuristic mapping of manufacturer to device type."""
    if not mfr:
        return None
    
    mfr_lower = mfr.lower()
    type_hints = {
        'raspberry': 'computer',
        'apple': 'phone/computer',
        'espressif': 'iot',
        'arduino': 'iot',
        'samsung': 'phone/tv',
        'lg': 'tv/appliance',
        'sony': 'tv/gaming',
        'philips': 'lighting/appliance',
        'tp-link': 'networking',
        'ubiquiti': 'networking',
        'amazon': 'smart speaker',
        'google': 'smart speaker',
    }
    
    for hint, dtype in type_hints.items():
        if hint in mfr_lower:
            return dtype
    
    return None
```

### Database Schema Update
```sql
-- Add new fields to devices table
ALTER TABLE devices ADD COLUMN manufacturer TEXT;
ALTER TABLE devices ADD COLUMN oui TEXT;  -- First 3 octets for quick lookup

-- Index for fast OUI lookups
CREATE INDEX idx_devices_oui ON devices(oui);
```

---

## Task 2: mDNS/Bonjour Discovery

### Goal
Capture device hostnames broadcast via multicast DNS (port 5353).

### How mDNS Works
- Devices broadcast `hostname.local` (e.g., `iPhone-Erik.local`)
- No central server — pure multicast
- Most modern IoT, phones, computers support this

### Implementation

```python
# Option A: Use avahi-utils (system dependency)
import subprocess
import asyncio

async def discover_mdns_hosts(timeout: int = 30) -> dict[str, str]:
    """Use avahi-browse to discover mDNS hostnames."""
    try:
        proc = await asyncio.create_subprocess_exec(
            'avahi-browse', '-a', '-t',  # All services, terminate after cache
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(
            proc.communicate(), 
            timeout=timeout
        )
        
        # Parse output: "+ eth0 IPv4 iPhone-Erik _ssh._tcp local"
        hostnames = {}
        for line in stdout.decode().split('\n'):
            if 'IPv4' in line and '_tcp' in line:
                parts = line.split()
                if len(parts) >= 4:
                    hostname = parts[3]
                    hostnames[hostname] = parts[0]  # interface
        
        return hostnames
    except Exception as e:
        logger.error(f"mDNS discovery failed: {e}")
        return {}

# Option B: Pure Python with zeroconf (preferred)
# pip install zeroconf

from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import time

class MDNSListener(ServiceListener):
    def __init__(self):
        self.hostnames = {}
    
    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info and info.addresses:
            ip = str(ipaddress.ip_address(info.addresses[0]))
            hostname = name.split('.')[0]  # Strip ._tcp.local
            self.hostnames[ip] = hostname
            logger.info(f"mDNS: {ip} -> {hostname}")
    
    def remove_service(self, zc, type_, name):
        pass
    
    def update_service(self, zc, type_, name):
        pass

async def start_mdns_discovery(duration: int = 60):
    """Run mDNS discovery for specified duration."""
    zc = Zeroconf()
    listener = MDNSListener()
    
    # Browse common service types
    service_types = [
        "_http._tcp.local.",
        "_ssh._tcp.local.",
        "_smb._tcp.local.",
        "_airplay._tcp.local.",
        "_googlecast._tcp.local.",
    ]
    
    browsers = [
        ServiceBrowser(zc, st, listener) 
        for st in service_types
    ]
    
    await asyncio.sleep(duration)
    
    zc.close()
    return listener.hostnames

# Integration: Update devices with discovered hostnames
async def update_device_hostnames(db_session, discovered: dict[str, str]):
    """Match discovered mDNS hostnames to devices by IP."""
    for ip, hostname in discovered.items():
        await db_session.execute(
            """
            UPDATE devices 
            SET hostname = :hostname,
                name = COALESCE(name, :hostname)  -- Use hostname as display name if no name set
            WHERE ip = :ip
            """,
            {"hostname": hostname, "ip": ip}
        )
    await db_session.commit()
```

### System Dependencies

```bash
# On Debian/Ubuntu (GX-10)
sudo apt-get update
sudo apt-get install -y avahi-daemon avahi-utils

# For Python zeroconf (no system deps)
pip install zeroconf
```

### Service Integration

```python
# Add to your background task scheduler
# runs every 5 minutes

async def device_identification_task():
    """Periodic task to identify unknown devices."""
    # 1. Run mDNS discovery
    discovered = await start_mdns_discovery(duration=30)
    await update_device_hostnames(db, discovered)
    
    # 2. Enrich unclassified devices with OUI lookup
    unknown_devices = await db.fetchall(
        "SELECT * FROM devices WHERE device_type IS NULL"
    )
    
    for device in unknown_devices:
        enriched = await enrich_device(dict(device))
        await db.execute(
            """
            UPDATE devices 
            SET manufacturer = :manufacturer,
                device_type = :device_type,
                oui = :oui
            WHERE id = :id
            """,
            enriched
        )
```

---

## Expected Outcomes

| Before | After |
|--------|-------|
| `device_type: null` | `device_type: "computer"` |
| `hostname: null` | `hostname: "RaspberryPi.local"` |
| `manufacturer: null` | `manufacturer: "Raspberry Pi Foundation"` |
| Unknown devices | Named, categorized devices |

---

## Testing Checklist

- [ ] OUI lookup returns correct manufacturer for known MACs
- [ ] mDNS discovery captures `.local` hostnames on network
- [ ] Device API returns enriched data
- [ ] Dashboard shows manufacturer + hostname
- [ ] Fallback to "Unknown" if no match

---

## Questions?
Ping Woodhouse or Mr. Ross for clarification.
