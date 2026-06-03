# Vigil Home — Threat Intelligence Knowledge Base

**Version:** 1.0  
**Date:** 2026-05-06  
**Maintainer:** Woodhouse (Threat Intelligence Research Agent)  
**Status:** Foundational — Active

---

## Overview

This knowledge base provides the foundational threat intelligence library for the Vigil Home hardware security appliance. It is organized to support threat detection, behavioral analysis, trust scoring, and containment decision-making.

The knowledge base is designed for an **IoT-first, home-network context** — not enterprise or ICS/OT. Vigil Home operates at the residential router/gateway level, monitoring traffic between 10-50+ consumer IoT devices.

---

## Repository Structure

```
knowledge-base/
├── README.md                   # This file — overview and maintenance
├── THREAT-CATALOG.md           # IoT threats organized by device type
├── ATTACK-PATTERNS.md          # Behavioral attack patterns with detection signatures
├── VULNERABILITY-FEEDS.md      # Curated data sources, APIs, and feeds
├── OSS-RESOURCES.md            # Open-source libraries, rules, and tools
└── DETECTION-RULES.md          # Draft detection rules (Sigma-style)
```

---

## File Quick Reference

| File | What It Covers | Primary Audience |
|------|----------------|-----------------|
| `THREAT-CATALOG.md` | Device-specific vulnerabilities, known exploits, default credentials, firmware issues | Detection engineering, trust scoring |
| `ATTACK-PATTERNS.md` | Behavioral signatures, C2 patterns, lateral movement, IoC catalog | Anomaly detection, ML baselines |
| `VULNERABILITY-FEEDS.md` | NVD, CISA KEV, abuse.ch, MISP, vendor advisories — with API details | Threat intel pipeline engineering |
| `OSS-RESOURCES.md` | YARA rules, Sigma rules, Suricata/Snort configs, MISP, Shodan | Tool integration, rule authoring |
| `DETECTION-RULES.md` | Draft Sigma-format rules for Vigil Home detection engine | Detection implementation |

---

## Key Findings (Bitdefender/NETGEAR 2025 IoT Security Landscape Report)

- **29 daily attack attempts** per home (nearly 3× increase over 2024)
- **13.6 billion** security events detected across 6.1 million homes
- **22 connected devices** per household — each a potential target
- **Streaming devices (26%)**, **Smart TVs (21%)**, and **IP cameras (9%)** account for >50% of vulnerabilities
- **22.2 Tbps DDoS attack** traced to compromised home routers
- **BadBox botnet** continues targeting Android-based IoT devices
- Solar inverters, EV chargers, and home energy systems are emerging attack surfaces

Source: [Bitdefender/NETGEAR 2025 IoT Security Landscape Report](https://www.bitdefender.com/en-us/blog/hotforsecurity/bitdefender-and-netgear-2025-iot-security-landscape-report-shows-alarming-rise-in-smart-home-threats)

---

## Maintenance Guidelines

### Weekly Updates
- Check CISA KEV for new IoT-related CVEs
- Review abuse.ch SSLBL/Feodo for new C2 indicators
- Check Emerging Threats rules for new IoT signatures

### Monthly Updates
- Review MISP feeds for IoT-specific threat events
- Check NVD for high/critical IoT CVEs
- Update Shodan search queries for new device types
- Review vendor advisories (Ring, Nest, Wyze, TP-Link, Netgear)

### Quarterly Updates
- Full review and revision of detection rules
- Re-calibrate behavioral baselines based on new research
- Audit false-positive rates from in-production rules
- Refresh threat catalog with new device types and attack vectors

### Triggered Updates
- New major IoT botnet variant discovered (e.g., new Mirai fork)
- Critical CVE in a major consumer IoT vendor
- Significant change in threat landscape (e.g., new C2 protocol)
- Product requirement changes that affect threat coverage

---

## Threat Intelligence Maturity Model

| Level | State | Knowledge Base Readiness |
|-------|-------|------------------------|
| **1 — Initial** | Foundational research compiled | ✅ Current |
| **2 — Reactive** | Alert-triggered rule updates | 🔄 In progress |
| **3 — Proactive** | Predictive threat modeling | ⬜ Planned |
| **4 — Adaptive** | Automated threat feed ingestion | ⬜ Future |
| **5 — Autonomous** | Self-tuning detection rules | ⬜ Future |

---

## Data Freshness

| Data Source | Update Frequency | Last Updated |
|------------|-----------------|-------------|
| THREAT-CATALOG.md | Quarterly | 2026-05-06 |
| ATTACK-PATTERNS.md | Quarterly | 2026-05-06 |
| VULNERABILITY-FEEDS.md | Monthly | 2026-05-06 |
| OSS-RESOURCES.md | Monthly | 2026-05-06 |
| DETECTION-RULES.md | Monthly | 2026-05-06 |

---

## Related Documents

- [PRODUCT-REQUIREMENTS.md](../docs/PRODUCT-REQUIREMENTS.md)
- [CONTAINMENT-ACTUATION.md](../docs/CONTAINMENT-ACTUATION.md)

---

## Contact

For threat intelligence contributions, corrections, or additions:
- File an issue in the Vigil Home repo
- Tag with `threat-intel` and `knowledge-base` labels
- Include references/links to source material
