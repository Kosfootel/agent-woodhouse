# ASUS GT6 Router Integration Research

**Date:** 2026-05-23
**Router Model:** ASUS GT6 (ZenWiFi Pro ET12)
**Firmware:** ASUSWRT

## Authentication Attempts

### Standard Methods Tested (All Failed)

1. **Base64 encoded credentials** - `login_authorization: base64(username:password)`
   - Result: Redirects to login page
   - Status: Failed

2. **URL-safe base64 variant**
   - Result: Redirects to login page
   - Status: Failed

3. **Hex encoded credentials**
   - Result: Redirects to login page
   - Status: Failed

4. **Password-only encoding**
   - Result: Redirects to login page
   - Status: Failed

5. **MD5/SHA256 password hash**
   - Result: Redirects to login page
   - Status: Failed

6. **Direct form fields (login_username, login_passwd)**
   - Result: Redirects to login page
   - Status: Failed

### Login Page Analysis

From `/Main_Login.asp`:

```javascript
var login_info = tryParseJSON('{ 
    "lock_time": 205, 
    "error_status": 10, 
    "error_num": 2, 
    "page": "GameDashboard.asp" 
}');
```

**Observations:**
- `error_num: 2` - Multiple failed login attempts detected
- `lock_time: 205` - Some form of lockout/timing mechanism
- `error_status: 10` - Unknown error code (likely "temporarily locked")
- `is_logined()` returns `0` (not logged in)

### Router State

- **Authentication Required:** All API endpoints redirect to `/Main_Login.asp`
- **Lockout Status:** Router may be temporarily locking out after failed attempts
- **HTTPS:** Not available (connection refused on port 443)

## Working Solution: ARP Fallback with MAC OUI

Since ASUS API authentication is not working, the implemented solution uses:

### Device Discovery via ARP

**Location:** `backend/app/routers/implementations/generic.py`

**Method:**
1. Ping sweep network range to populate ARP table
2. Parse `ip neigh show` output for MAC→IP mappings
3. Filter by router's network prefix
4. Skip router itself and duplicates

### MAC OUI Lookup for Vendor Identification

**Database includes:**
- Apple: `40:6C:8F`, `DA:EC:34`, `0E:0A:55`
- ASUS: `08:BF:B8`, `AC:22:0B`
- Realtek: `00:E0:4C`
- Intel: `38:05:25`
- Samsung: `4C:BA:D7`, `C8:A3:62`
- LG: `A8:6E:84`
- Sony: `10:B1:DF`

### Device Naming Convention

Generated as: `{Vendor}-{MAC_suffix4}`

Examples:
- `Apple-127F` (40:6c:8f:0e:12:7f)
- `Realtek-FACC` (00:e0:4c:be:fa:cc)
- `Samsung-2158` (c8:a3:62:14:21:58)

## Limitations of ARP Method

| Feature | ASUS API | ARP Fallback |
|---------|----------|--------------|
| Device Hostnames | ✓ (from router) | ✗ (MAC-based) |
| Vendor Info | ✓ (from router DB) | ✓ (from OUI) |
| Connection Type | ✓ (2.4G/5G/Ethernet) | ✗ (unknown) |
| Signal Strength | ✓ (RSSI) | ✗ |
| Bandwidth Stats | ✓ | ✗ |
| Online Status | ✓ | Partial (ARP state) |

## Recommendations

### Immediate (ARP Fallback)
- Use MAC OUI lookup for device identification
- Accept that some device info will be limited
- Allow users to manually edit device names in UI

### Future (ASUS API)
- Wait for router lockout to expire, then retry authentication
- Research exact ASUS GT6 authentication mechanism
- Consider using Selenium to automate browser login if API fails
- Check for alternative protocols (SNMP, UPnP)

### Alternative Approaches
1. **SNMP Discovery** - Many routers support SNMP for device discovery
2. **UPnP Discovery** - UPnP IGD can provide device info
3. **Promiscuous Mode** - Monitor network traffic to identify devices
4. **mDNS/Bonjour** - Discover Apple and other mDNS-enabled devices

## Files Modified

- `backend/app/routers/implementations/generic.py` - ARP discovery with MAC OUI

## Git Commit

`78e1b50` - fix(router): improve ARP device discovery with MAC OUI lookup
