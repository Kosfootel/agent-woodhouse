# Device API Enhancement Brief
**For:** Liz (GX-10 Backend)  
**From:** Woodhouse  
**Date:** 2026-05-08  
**Priority:** High  
**Est. Effort:** 4-6 hours

---

## Issue Summary
Dashboard displaying incomplete device information:
1. **All devices show "Offline"** — `online` field missing from API
2. **All devices show "Unknown" type** — `device_type` and `hostname` fields null

---

## Task 1: Add Online Status Field (HIGH PRIORITY)

### Problem
Dashboard expects `device.online: boolean` but API doesn't provide it.

### Current API Response
```json
{
  "devices": [{
    "id": 1,
    "mac": "...",
    "last_seen": "2026-05-08T14:34:59"
    // MISSING: "online": true
  }]
}
```

### Solution
Compute `online` from `last_seen` in API response:

```python
from datetime import datetime, timedelta

THRESHOLD_MINUTES = 5

def is_online(last_seen: datetime | str) -> bool:
    if isinstance(last_seen, str):
        last_seen = datetime.fromisoformat(last_seen)
    cutoff = datetime.now() - timedelta(minutes=THRESHOLD_MINUTES)
    return last_seen > cutoff

# In /api/devices endpoint:
return {
    "count": len(devices),
    "devices": [
        {**device, "online": is_online(device["last_seen"])}
        for device in devices
    ]
}
```

---

## Task 2: Device Identification (MAC OUI + mDNS)

### Problem
All devices show `device_type: null`, `hostname: null`, `manufacturer: null`.

### Solution A: MAC OUI Lookup
Parse first 3 octets of MAC → identify manufacturer.

```python
import csv

class OUILookup:
    def __init__(self, manuf_file: str = "manuf.txt"):
        self.oui_map = {}
        # Download from: https://gitlab.com/wireshark/wireshark/-/raw/master/manuf
        with open(manuf_file) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    mac_prefix = parts[0].replace(':', '').upper()
                    self.oui_map[mac_prefix] = parts[1]
    
    def lookup(self, mac: str) -> str | None:
        clean_mac = mac.replace(':', '').replace('-', '').upper()
        return self.oui_map.get(clean_mac[:6])  # First 3 octets

def infer_device_type(manufacturer: str | None) -> str | None:
    if not manufacturer:
        return None
    mfr = manufacturer.lower()
    hints = {
        'raspberry': 'computer',
        'apple': 'phone/computer',
        'espressif': 'iot',
        'samsung': 'phone/tv',
        'tp-link': 'networking',
        'ubiquiti': 'networking',
        'amazon': 'smart speaker',
        'google': 'smart speaker',
    }
    for hint, dtype in hints.items():
        if hint in mfr:
            return dtype
    return None
```

### Solution B: mDNS Discovery
Capture hostnames via multicast DNS.

```python
# pip install zeroconf
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener

class MDNSListener(ServiceListener):
    def __init__(self):
        self.hostnames = {}  # ip -> hostname
    
    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info and info.addresses:
            ip = str(ipaddress.ip_address(info.addresses[0]))
            hostname = name.split('.')[0]
            self.hostnames[ip] = hostname

async def discover_mdns(duration: int = 60) -> dict[str, str]:
    zc = Zeroconf()
    listener = MDNSListener()
    
    service_types = [
        "_http._tcp.local.",
        "_ssh._tcp.local.",
        "_smb._tcp.local.",
        "_airplay._tcp.local.",
    ]
    
    browsers = [ServiceBrowser(zc, st, listener) for st in service_types]
    await asyncio.sleep(duration)
    zc.close()
    return listener.hostnames

# Match to devices by IP
async def update_device_hostnames(db, discovered: dict[str, str]):
    for ip, hostname in discovered.items():
        await db.execute(
            """UPDATE devices 
               SET hostname = :hostname,
                   name = COALESCE(name, :hostname)
               WHERE ip = :ip""",
            {"hostname": hostname, "ip": ip}
        )
```

### Database Schema Changes
```sql
-- Add new columns
ALTER TABLE devices ADD COLUMN manufacturer TEXT;
ALTER TABLE devices ADD COLUMN oui TEXT;
ALTER TABLE devices ADD COLUMN hostname TEXT;

-- Index for OUI lookups
CREATE INDEX idx_devices_oui ON devices(oui);
```

### Background Task Integration
```python
# Run every 5 minutes
async def device_enrichment_task():
    # 1. Run mDNS discovery
    discovered = await discover_mdns(duration=30)
    await update_device_hostnames(db, discovered)
    
    # 2. Enrich unclassified devices with OUI
    unknown = await db.fetchall(
        "SELECT * FROM devices WHERE device_type IS NULL"
    )
    oui = OUILookup()
    
    for device in unknown:
        if mac := device.get('mac'):
            mfr = oui.lookup(mac)
            await db.execute(
                """UPDATE devices 
                   SET manufacturer = :mfr,
                       device_type = :dtype,
                       oui = :oui
                   WHERE id = :id""",
                {
                    "mfr": mfr,
                    "dtype": infer_device_type(mfr),
                    "oui": mac.replace(':', '').upper()[:6],
                    "id": device['id']
                }
            )
```

---

## Expected API Output

```json
{
  "count": 50,
  "devices": [{
    "id": 1,
    "mac": "dc:a6:32:aa:bb:cc",
    "ip": "192.168.50.24",
    "last_seen": "2026-05-08T14:34:59",
    "online": true,
    "manufacturer": "Raspberry Pi Foundation",
    "device_type": "computer",
    "hostname": "raspberrypi.local",
    "name": "raspberrypi.local",
    "trust_score": 85
  }]
}
```

---

## System Dependencies

```bash
# On GX-10 (Debian/Ubuntu)
sudo apt-get install -y avahi-daemon avahi-utils  # Optional, for avahi-browse
pip install zeroconf  # Pure Python, preferred
```

---

## Testing Checklist

- [ ] `/api/devices` returns `online: true/false` for all devices
- [ ] `manufacturer` populated from MAC OUI lookup
- [ ] `device_type` inferred from manufacturer hints
- [ ] `hostname` captured from mDNS discovery
- [ ] Background task runs every 5 minutes
- [ ] Dashboard shows correct online status
- [ ] Dashboard shows manufacturer/hostname where available

---

## Questions?
Ping Woodhouse or Mr. Ross for clarification.
