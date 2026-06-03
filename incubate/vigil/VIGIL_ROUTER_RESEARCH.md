# Existing Router Administration Solutions

## Executive Summary

After surveying the landscape of open-source router administration tools, several mature projects exist that Vigil can leverage. The strongest immediate integration candidate is **asusrouter** (Python library with 300+ GitHub stars, actively maintained), which provides comprehensive ASUS router API access. For broader network management, **OpenWISP** and **LibreNMS** offer established frameworks, though they focus on enterprise/multi-device scenarios rather than single-router home defense.

**Key Finding:** No existing open-source project specifically addresses AI-assisted home network defense with automated threat response. This is Vigil's opportunity — build on top of proven router libraries rather than reinventing them.

---

## ASUS-Specific Libraries

### 1. asusrouter (Python Library)
- **Repository:** https://github.com/Vaskivskyi/asusrouter
- **Language:** Python
- **Stars/Forks:** ~300 stars, ~30 forks (as of 2025-05-24)
- **Last Updated:** Active development, last commit within weeks
- **License:** Apache-2.0
- **Features:**
  - Full ASUSWRT API wrapper (HTTP/HTTPS)
  - Supports stock ASUS firmware and ASUSMerlin
  - Device monitoring and tracking
  - Traffic statistics per device
  - VPN status monitoring
  - Port forwarding management
  - System info retrieval (CPU, RAM, temperatures)
  - LED control
  - Firmware update checking
  - Async support (aioasusrouter)

- **Vigil Relevance:** **HIGHEST PRIORITY INTEGRATION**
  - Provides foundation for device blocking via MAC address
  - Traffic monitoring capabilities for anomaly detection
  - Already handles authentication and session management
  - Can be extended for Vigil's AI-driven decisions
  - Home Assistant integration exists, proving stability

### 2. Home Assistant ASUS Router Integration
- **Repository:** https://github.com/home-assistant/core/tree/dev/homeassistant/components/asuswrt
- **Language:** Python
- **Integration:** Native Home Assistant component
- **Features:**
  - Device presence detection
  - Upload/download sensors
  - CPU/memory sensors
  - Load average tracking

- **Vigil Relevance:**
  - Reference implementation for device tracking
  - Shows how to consume asusrouter library effectively
  - Can be adapted for standalone use

### 3. pyasuswrt (Fork/Alternative)
- **Repository:** Various community forks
- **Status:** Less active than asusrouter
- **Recommendation:** Use asusrouter instead

### 4. RouterOS API (MikroTik) - Reference Only
- **Repository:** https://github.com/socialwifi/RouterOS-api
- **Note:** Not ASUS-specific, but similar API pattern
- **Vigil Relevance:** Reference for router API abstraction design

---

## General Router Management Platforms

### 1. OpenWISP
- **Website:** https://openwisp.org/
- **Repository:** https://github.com/openwisp/
- **Language:** Python/Django
- **Stars:** 1000+ across organization
- **Last Updated:** Very active (enterprise-backed)
- **License:** GPL-3.0
- **Features:**
  - Multi-device network management
  - Configuration management across routers
  - Monitoring and alerts
  - VPN orchestration
  - Firmware management
  - Multi-tenant architecture

- **Vigil Relevance:**
  - **Architecture reference** for multi-node mesh (future consideration)
  - Overkill for single-home router use case
  - Good pattern for configuration-as-code
  - Could inspire Vigil's "network policy" layer

### 2. LibreNMS
- **Website:** https://www.librenms.org/
- **Repository:** https://github.com/librenms/librenms
- **Language:** PHP
- **Stars:** 4,000+
- **Last Updated:** Extremely active
- **License:** GPL-3.0
- **Features:**
  - Network device discovery
  - SNMP-based monitoring
  - Alerting engine
  - Traffic graphs and visualization
  - Plugin ecosystem

- **Vigil Relevance:**
  - Reference for SNMP-based device discovery
  - Alerting patterns for network anomalies
  - Visualization approach for traffic analysis
  - PHP stack less relevant for Vigil (Python preferred)

### 3. OPNsense/pfSense
- **Website:** https://opnsense.org/ / https://www.pfsense.org/
- **Repository:** https://github.com/opnsense/core
- **Language:** PHP/FreeBSD
- **Features:**
  - Full firewall/router OS
  - REST API available
  - Intrusion detection (Suricata)
  - Traffic shaping
  - VPN support

- **Vigil Relevance:**
  - Reference for security-focused router OS
  - API patterns for firewall rule management
  - IDS/IPS integration patterns
  - Heavyweight — Vigil aims for lighter deployment

### 4. OpenWrt UBus/JSON-RPC
- **Documentation:** https://openwrt.org/docs/techref/ubus
- **Features:**
  - Built-in API for OpenWrt-based routers
  - JSON-RPC interface
  - UBus message bus

- **Vigil Relevance:**
  - If supporting OpenWrt routers in future
  - Simpler than ASUS API in some ways

---

## Network Defense & Security Platforms

### 1. Pi-hole
- **Website:** https://pi-hole.net/
- **Repository:** https://github.com/pi-hole/pi-hole
- **Language:** Shell/Bash, Python
- **Stars:** 50,000+
- **Last Updated:** Very active
- **License:** EUPL-1.2
- **Features:**
  - DNS-level ad and tracker blocking
  - Network-wide blocking
  - Query logging and analytics
  - Web admin interface
  - DHCP server optional
  - API for automation

- **Vigil Relevance:**
  - **Integration candidate:** Vigil could feed threat intelligence to Pi-hole
  - API exists for adding blocklists
  - Pattern for "DNS sinkhole" defense
  - Less granular than device-level blocking

### 2. AdGuard Home
- **Website:** https://adguard.com/adguard-home/overview.html
- **Repository:** https://github.com/AdguardTeam/AdGuardHome
- **Language:** Go
- **Stars:** 25,000+
- **Last Updated:** Very active
- **Features:**
  - DNS-based blocking
  - Parental controls
  - Safe search enforcement
  - Per-client statistics
  - REST API

- **Vigil Relevance:**
  - Alternative to Pi-hole with richer API
  - Per-device controls more granular
  - Could be integrated for threat domain blocking

### 3. Suricata
- **Website:** https://suricata.io/
- **Repository:** https://github.com/OISIC/Suricata
- **Language:** C
- **Features:**
  - IDS/IPS engine
  - Deep packet inspection
  - Rule-based detection
  - NetFlow support

- **Vigil Relevance:**
  - Reference for intrusion detection patterns
  - Rule format inspiration for Vigil threat signatures
  - Too heavy for router deployment; Vigil should be lighter

### 4. Zeek (formerly Bro)
- **Website:** https://zeek.org/
- **Repository:** https://github.com/zeek/zeek
- **Language:** C++
- **Features:**
  - Network analysis framework
  - Traffic scripting
  - Protocol analysis

- **Vigil Relevance:**
  - Pattern for traffic analysis and scripting
  - Reference for protocol detection

### 5. CrowdSec
- **Website:** https://www.crowdsec.net/
- **Repository:** https://github.com/crowdsecurity/crowdsec
- **Language:** Go
- **Stars:** 10,000+
- **Last Updated:** Very active
- **Features:**
  - Collaborative IPS
  - Threat intelligence sharing
  - Bouncer agents for enforcement
  - Multi-source log analysis

- **Vigil Relevance:**
  - **Strong integration candidate**
  - Could contribute ASUS router data to CrowdSec network
  - Could consume CrowdSec blocklists
  - "Bouncer" pattern for enforcement

---

## Parental Controls & Device Management

### 1. Circle (by Disney) - Proprietary Reference
- **Product:** https://www.meetcircle.com/
- **Note:** Commercial product, not open source
- **Features:**
  - Device-level internet pausing
  - Time limits per device
  - Content filtering
  - Usage tracking

- **Vigil Relevance:**
  - UX reference for device management
  - Feature benchmark

### 2. FamilyShield / CleanBrowsing
- **Type:** DNS-based filtering services
- **Vigil Relevance:** Reference for threat categorization

---

## Analysis: What Each Project Does/Doesn't Do

### Device Blocking Capabilities

| Project | MAC Block | IP Block | VLAN | Time-based | API Quality |
|---------|-----------|----------|------|------------|-------------|
| asusrouter | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ⭐⭐⭐⭐ REST |
| OpenWISP | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐ Django REST |
| Pi-hole | ✅ Per-client | ✅ Yes | ❌ No | ❌ No | ⭐⭐⭐ REST |
| AdGuard Home | ✅ Per-client | ✅ Yes | ❌ No | ❌ No | ⭐⭐⭐⭐ REST |
| OPNsense | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐ REST |

### Traffic Monitoring

| Project | NetFlow | Packet Capture | Per-Device Stats | Protocol Analysis |
|---------|---------|---------------|------------------|-------------------|
| asusrouter | ❌ No | ❌ No | ✅ Yes (limited) | ❌ No |
| LibreNMS | ✅ Yes | ❌ No | ✅ Yes | ❌ Basic |
| Suricata | ❌ No | ✅ Yes | ❌ No | ✅ Deep |
| Zeek | ❌ No | ✅ Yes | ✅ Yes | ✅ Advanced |

### Firmware Management

| Project | Auto-Update | Firmware Download | ASUS Specific |
|---------|-------------|-------------------|---------------|
| asusrouter | ❌ Check only | ❌ No | ✅ Yes |
| OpenWISP | ✅ Yes | ✅ Yes | ❌ Generic |
| ASUS Merlin | ✅ Yes | ✅ Yes | ✅ ASUSMerlin only |

---

## Recommendations for Vigil

### Immediate Integration Candidates (Use, Don't Build)

1. **asusrouter (Python)**
   - **Purpose:** ASUS router API foundation
   - **Action:** Add as dependency, wrap for Vigil's needs
   - **Extend:** Add missing methods if needed (contribute upstream)

2. **AdGuard Home** (Optional)
   - **Purpose:** DNS-level threat blocking
   - **Action:** Integrate via API to add Vigil-managed blocklists
   - **Benefit:** Layered defense (DNS + device block)

3. **CrowdSec**
   - **Purpose:** Threat intelligence feed
   - **Action:** Consume CrowdSec blocklists, contribute ASUS detections
   - **Benefit:** Community-powered threat detection

### Reference Architecture Patterns

1. **OpenWISP's Configuration Management**
   - Pattern: "Policy as code" for network rules
   - Adapt for Vigil's threat response policies

2. **Pi-hole's Query Logging**
   - Pattern: Time-series DNS query storage
   - Adapt for Vigil's network event log

3. **CrowdSec's Bouncer Model**
   - Pattern: Separate detection from enforcement
   - Vigil detection engine → Bouncer agents on routers

### Gaps Vigil Can Fill (Build These)

1. **AI-Powered Anomaly Detection**
   - None of the surveyed tools use ML/AI for threat detection
   - Vigil's core differentiator: behavioral analysis, not rule-based

2. **Automated Device Quarantine**
   - Existing tools require manual blocking
   - Vigil's value: autonomous response to detected threats

3. **Natural Language Query Interface**
   - "What's the suspicious device on my network?"
   - No existing project offers conversational network admin

4. **Cross-Router Threat Intelligence**
   - Per-home learning, optional anonymized sharing
   - "Device with MAC pattern X is acting suspiciously"

5. **Smart Device Fingerprinting**
   - Identify IoT devices by behavior, not just MAC OUI
   - Detect firmware version vulnerabilities

6. **Zero-Trust for Home Networks**
   - Treat all devices as potentially hostile
   - Dynamic trust scoring based on behavior

---

## Build vs. Integrate Decision Matrix

| Component | Build | Integrate | Notes |
|-----------|-------|-----------|-------|
| ASUS Router API | ❌ | ✅ asusrouter | Mature, well-maintained |
| Traffic Monitoring | ✅ | ❌ | Need AI-friendly data collection |
| Device Blocking | ❌ | ✅ asusrouter | Extend existing |
| DNS Blocking | ❌ | ✅ AdGuard/Pi-hole | Layered defense |
| Threat Intelligence | 🔄 Hybrid | 🔄 CrowdSec | Consume + contribute |
| Anomaly Detection | ✅ ML | ❌ | Vigil's core value |
| Policy Engine | ✅ | ❌ | AI-driven rules unique |
| Web Dashboard | ✅ | ❌ | AI-powered insights |

**Verdict:** Vigil should be an **intelligence layer** on top of existing router libraries, not a replacement for them.

---

## Open Source Contribution Opportunities

### Projects Vigil Should Contribute To

1. **asusrouter**
   - Add missing endpoints if discovered
   - Contribute tests
   - Document edge cases for ASUS firmware variants

2. **CrowdSec**
   - Create "bouncer" for ASUS routers
   - Submit detection scenarios for consumer router threats

3. **Home Assistant**
   - If building Vigil integration, share useful sensors

### Projects Vigil Should Not Duplicate

- ❌ Router API wrappers (asusrouter exists)
- ❌ DNS sinkholes (Pi-hole/AdGuard exist)
- ❌ Enterprise NMS (OpenWISP/LibreNMS exist)
- ❌ Full router OS (OpenWrt/OPNsense exist)

---

## Research Sources

- GitHub search: "asus router python api"
- GitHub search: "ASUSWRT python library"
- GitHub search: "home assistant asus router"
- OpenWISP documentation: https://openwisp.org/docs/
- asusrouter PyPI: https://pypi.org/project/asusrouter/
- CrowdSec documentation: https://docs.crowdsec.net/
- Pi-hole API documentation: https://docs.pi-hole.net/api/

---

## Next Steps

1. **Prototype:** Build Vigil prototype using `asusrouter` library
2. **Test:** Validate against ASUS RT-AX86U (Erik's router)
3. **Extend:** Identify missing API endpoints for blocking/containment
4. **Evaluate:** Test AdGuard Home integration for DNS layer
5. **Design:** Create Vigil-specific threat detection data models

---

*Research completed: 2025-05-24*
*Researcher: Woodhouse (AI Agent)*
*For: Vigil Project (Phase 0: Research)*
