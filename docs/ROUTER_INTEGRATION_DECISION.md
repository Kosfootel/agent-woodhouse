# Router Integration Architectural Decision

**Date:** 2026-05-23
**Decision:** Defer router API integration to future release
**Status:** Commented out in codebase, ARP-only for MVP

## Context

The ASUS GT6 router API authentication is blocked due to:
1. Router lockout protection after failed attempts (`error_num: 2`)
2. Client-side JavaScript encryption not reverse-engineered
3. All authentication methods (base64, hex, MD5, SHA256) redirect to login

## Decision

**Router API integration is deferred** until Vigil is either:
- Embedded in a router (Vigil becomes router firmware)
- A router is embedded in Vigil (Vigil hardware includes router)

## Rationale

1. **Authentication barrier is non-trivial** - ASUS uses client-side encryption that changes between firmware versions
2. **Lockout protection prevents testing** - Router temporarily blocks after failed attempts
3. **ARP + MAC OUI provides sufficient device discovery** for MVP
4. **Router integration is more valuable when Vigil IS the router**

## Current Implementation (Working)

- ARP table scanning for device discovery
- MAC OUI lookup for vendor identification  
- Auto-generated device names: `{Vendor}-{MAC_suffix}`
- No router credentials required

## Future Enhancement

When Vigil is embedded in a router:
1. Direct access to router's internal APIs
2. No authentication required (same process space)
3. Rich device metadata (hostnames, connection type, bandwidth, etc.)
4. Real-time device tracking

## Files Modified

- `backend/app/routers/setup.py` - Router imports commented out, ARP-only mode
- `docs/ASUS_RESEARCH.md` - Research on why authentication failed

## Commit

`76f5d90` - refactor(setup): comment out router integration, use ARP only
