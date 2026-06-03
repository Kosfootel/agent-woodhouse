# Vigil Device Data Quality Fix - Summary

## What Was Done

### 1. Downloaded Full OUI Database (38,841 entries)
- Source: Nmap's maintained list from IEEE (https://raw.githubusercontent.com/nmap/nmap/master/nmap-mac-prefixes)
- Saved to: `/data/oui_database.json` on GX-10
- Combined with Vigil's built-in 52 OUI entries
- **Result: 38,841 OUI entries available for vendor lookup**

### 2. Database Statistics

**BEFORE:**
- Total devices: 95
- With nicknames: 0
- With vendor info: 0
- With classified_type: 0
- With icon_type: 0

**AFTER:**
- Total devices: 95
- With nicknames: **95 (100%)**
- With vendor info: 0* (see note below)
- With classified_type: **95 (100%)**
- With icon_type: **95 (100%)**

### 3. Nickname Generation Rules
Nicknames are generated based on priority:
1. **Hostname-based**: If device has a meaningful hostname (e.g., "connectivity-check.ubuntu.com" → "connectivity-check")
2. **IP-based fallback**: "Unknown Device [last octet of IP]" (e.g., "Unknown Device 91")

### 4. Device Classification
All 95 devices have been classified using the DeviceClassifier:
- classified_type: Set to device category (e.g., "generic_iot")
- classified_confidence: Set to confidence score
- icon_type: Mapped from classified type (e.g., "device" for generic_iot)

## Known Issue: Fake MAC Addresses

**Problem:** All 95 devices in the database have fake MAC addresses generated from IP addresses (format: `00:00:00:IP:OCTETS`). Examples:
- `00:00:00:192:168:50:30` (from IP 192.168.50.30)
- `00:00:00:178:156:152:91` (from IP 178.156.152.91)

**Impact:**
- OUI lookup is skipped for fake MACs (OUI `000000` would incorrectly match to Xerox)
- No vendor information can be determined without real MAC addresses
- Devices are still classified by behavioral signatures (hostname patterns)

**Root Cause:** The detection code creates fake MACs when real MAC addresses aren't captured:
```python
mac = src_mac or f"00:00:00:{src_ip.replace('.', ':')}"
```

**Recommendation:** To fix this properly, the Vigil detection system needs to capture actual MAC addresses from network traffic (ARP, DHCP, etc.). The OUI database is ready to identify vendors once real MACs are available.

## Files Created

1. **OUI Database**: `/data/oui_database.json` (38,822 entries from IEEE via Nmap)
2. **Fix Script**: `/app/fix_devices.py` (in vigil-api container, also saved at `/opt/vigil/fix_vigil_devices_v4.py`)

## How to Re-run

```bash
ssh gx-10
docker exec vigil-api python /app/fix_devices.py
```

## Next Steps for Full Data Quality

1. **Fix MAC Detection**: Modify the detection code to capture real MAC addresses from:
   - ARP requests/replies
   - DHCP packets
   - mDNS/Bonjour traffic
   - Any Layer 2 traffic

2. **Re-run Classification**: Once real MACs are available, run the fix script again to:
   - Look up vendors via OUI (38,841 entries ready)
   - Get better device classifications
   - Generate vendor-specific nicknames

3. **Verify Progress**: Check statistics with:
   ```bash
   docker exec vigil-api sqlite3 /data/vigil.db 'SELECT COUNT(*) as total, COUNT(CASE WHEN nickname IS NOT NULL THEN 1 END) as with_nickname, COUNT(CASE WHEN vendor IS NOT NULL THEN 1 END) as with_vendor, COUNT(CASE WHEN mac NOT LIKE "00:00:00:%" THEN 1 END) as real_macs FROM devices;'
   ```
