# ASUS GT6 Router Integration Research

**Date:** 2026-05-23  
**Router Model:** ASUS GT6 (ZenWiFi Pro ET12)  
**Status:** ARP fallback working, API authentication blocked  

## Summary

The ASUS GT6 router API authentication is currently failing with all standard methods tested. The router appears to have a lockout mechanism after failed login attempts.

## Authentication Attempts

Multiple authentication methods were tested and all failed:
- Base64 encoded credentials
- URL-safe base64
- Hex encoding
- MD5/SHA256 password hashes
- Direct form fields

All resulted in redirect to login page.

## Current Solution

Using ARP fallback with MAC OUI lookup for device discovery:
- 12+ devices discovered
- Vendor identification working (Apple, Realtek, Samsung, LG)
- Device names auto-generated from vendor + MAC suffix

## Limitations

ARP method cannot provide:
- True device hostnames from router
- Connection type (2.4G/5G/Ethernet)
- Signal strength/RSSI
- Bandwidth statistics

## Recommendations

1. **Immediate:** Use ARP fallback with manual device naming in UI
2. **Future:** Research exact ASUS GT6 auth mechanism once lockout expires
3. **Alternative:** Consider SNMP or UPnP for device discovery

## Files

- backend/app/routers/implementations/generic.py
