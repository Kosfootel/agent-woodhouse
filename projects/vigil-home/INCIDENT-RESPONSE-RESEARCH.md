# Incident Response Research: Enrichment Resources for Vigil Home

**Date:** 2026-05-09
**Author:** Research Subagent
**Status:** Draft for Review
**Related Docs:** [OSS-RESOURCES.md](./knowledge-base/OSS-RESOURCES.md), [THREAT-CATALOG.md](./knowledge-base/THREAT-CATALOG.md)

---

## Executive Summary

Vigil Home's current detection pipeline (Suricata IDS + behavioral anomaly detection + Bayesian trust scoring) generates rich signals but lacks **contextual enrichment** — the ability to answer "What does this IP belong to?", "Is this C2 traffic?", "Has this domain been flagged before?" — without which alerts remain raw data points rather than actionable narratives. This document surveys open-source and free-tier threat intelligence sources, incident response frameworks, IoT-specific threat feeds, and enrichment APIs that can plug into Vigil Home's alert pipeline to transform raw detections into intelligence-rich, actionable alerts.

**Key finding:** The highest-value integrations for Vigil Home are (1) **AbuseIPDB** + **abuse.ch (SSLBL/Feodo)** for instant IP/host reputation at near-zero cost, (2) **Shodan InternetDB** (free, no key) for device fingerprinting enrichment, (3) a **NIST SP 800-61-inspired lightweight IR playbook** structured for consumer/SMB response, and (4) **MITRE ATT&CK for ICS** technique mapping for standardized alert taxonomy. These four provide 80% of the enrichment value with minimal integration overhead.

---

## Table of Contents

1. [Incident Response Frameworks](#1-incident-response-frameworks)
2. [Open-Source Threat Intelligence Sources](#2-open-source-threat-intelligence-sources)
3. [IoT-Specific Threat Feeds & Data Sources](#3-iot-specific-threat-feeds--data-sources)
4. [Enrichment APIs & Services](#4-enrichment-apis--services)
5. [Comparison Matrix](#5-comparison-matrix)
6. [Recommended Implementation Roadmap](#6-recommended-implementation-roadmap)
7. [Sample Enrichment Flow Diagram](#7-sample-enrichment-flow-diagram)
8. [Top 5 Highest-Value Integrations](#8-top-5-highest-value-integrations-with-rationale)

---

## 1. Incident Response Frameworks

### 1.1 NIST SP 800-61 Rev. 3 — Computer Security Incident Handling Guide

| Attribute | Detail |
|-----------|--------|
| **URL** | https://csrc.nist.gov/publications/detail/sp/800-61/rev-3/final |
| **Status** | Rev. 3 finalized April 2025 (replaces Rev. 2 from 2012) |
| **License** | Public domain (US government) |
| **Format** | PDF, HTML |

**Key Phases (the "NIST 4"):**

```
1. Preparation     → Pre-deployment hardening, playbooks, training
2. Detection & Analysis → Confirm alert, scope, classify severity
3. Containment, Eradication & Recovery → Isolate device, remediate, restore
4. Post-Incident Activity → Lessons learned, update detection rules
```

**Relevance to Vigil Home:**
- Phase 2 maps directly to Vigil's **narrative generation** — the IR framework defines what context must be gathered before escalation
- Phase 3 can inform **containment actuation** (auto-isolate rogue IoT device via VLAN/ACL)
- Phase 4 feeds back into **trust score updates** and **rule tuning**
- Rev. 3 adds cloud, supply chain, and ransomware considerations — partially relevant to smart home ecosystems (cloud-dependent IoT)
- **Recommendation:** Use the NIST phases as the backbone of Vigil's built-in incident playbook, adapted for the consumer/SMB context (reduced jargon, fewer human analyst dependencies)

### 1.2 SANS Incident Handler's Handbook (PICERL)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://www.sans.org/reading-room/whitepapers/incident/incident-handlers-handbook-33901 |
| **License** | Free download (SANS Reading Room) |
| **Format** | PDF |

**PICERL Phases:**

```
Preparation → Identification → Containment → Eradication → Recovery → Lessons Learned
```

**Relevance to Vigil Home:**
- More granular than NIST; the Identification phase can incorporate Vigil's **multi-signal correlation** (Suricata + anomaly + trust score change = confirmed incident)
- Containment phase aligns with Vigil's planned **"Auto-Quarantine"** feature for high-severity device trust drops
- The handbook includes template playbooks that can be adapted for IoT scenarios (e.g., "Smart Lock Compromised" playbook)
- **Recommendation:** Use PICERL as the **playbook structure** for Vigil's incident response module; it maps well to the Guardian persona's "detect → explain → contain → recover" narrative arc

### 1.3 MITRE ATT&CK for ICS

| Attribute | Detail |
|-----------|--------|
| **URL** | https://attack.mitre.org/matrices/ics/ |
| **Version** | v18 (current), 150+ techniques across 12 tactics |
| **License** | Open (Creative Commons) |
| **Format** | STIX 2.1 JSON, web, PDF |

**Key Tactics Relevant to Home IoT:**

| Tactic | ID | Relevance |
|--------|----|-----------|
| Initial Access | TA0107 | Default credentials, internet-exposed devices |
| Execution | TA0108 | Malware download, script injection |
| Persistence | TA0109 | Firmware backdoor, scheduled tasks |
| Command and Control | TA0115 | C2 beaconing, DNS tunneling, MQTT exfiltration |
| Inhibit Response Function | TA0116 | Disable alerting, block firmware updates |
| Impact | TA0117 | DDoS, data theft, ransom |

**Relevance to Vigil Home:**
- Provides a **standardized taxonomy** for alert classification — instead of "suspicious connection," Vigil can say "MITRE ATT&CK Tactic: Command and Control (TA0115)"
- STIX 2.1 format enables machine-readable detection rules
- Can be used to **score alert severity** by technique (e.g., TA0116 Inhibit Response Function is always Critical)
- Existing ATT&CK coverage in Vigil's detection rules can be mapped for dashboard UI
- **Recommendation:** Integrate ATT&CK technique IDs into Vigil's alert output as a standard field; use the ICS matrix for IoT devices and the Enterprise matrix for non-IoT traffic (laptops, phones)

### 1.4 OWASP IoT Top 10 / IoT Security Verification Standard (ISVS)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://owasp.org/www-project-internet-of-things-top-10/ |
| **License** | Open (Creative Commons) |
| **Format** | Web, PDF |

**OWASP IoT Top 10 (2024):**
1. Weak, Guessable, or Hardcoded Passwords
2. Insecure Network Services
3. Insecure Ecosystem Interfaces
4. Lack of Secure Update Mechanism
5. Use of Insecure or Outdated Components
6. Insufficient Privacy Protection
7. Insecure Data Transfer and Storage
8. Lack of Device Management
9. Insecure Default Settings
10. Lack of Physical Hardening

**Relevance to Vigil Home:**
- Useful as a **device risk classification framework** — a device exhibiting multiple OWASP IoT Top 10 issues (weak password + unencrypted traffic + outdated firmware) gets a lower baseline trust score
- Can inform the **trust scoring algorithm**: each OWASP category maps to a trust score modifier
- **Recommendation:** Adopt OWASP IoT Top 10 categories as risk dimensions in Vigil's device profiling module

### 1.5 Lightweight Frameworks for Consumer/SMB

| Framework | Source | Why It Fits Vigil |
|-----------|--------|-------------------|
| **NISTIR 8425** — IoT Core Baseline for Consumer IoT | https://csrc.nist.gov/publications/detail/nistir/8425/final | NIST's IoT baseline; maps device capabilities to security requirements |
| **CISA's Cyber Essentials** | https://www.cisa.gov/cyber-essentials | Very lightweight: 6 basic controls; good for consumer-facing response content |
| **IoT Security Foundation (IoTSF)** Best Practices | https://www.iotsecurityfoundation.org/ | Mature industry body with vendor-neutral IoT guidelines |
| **NIST Cybersecurity Framework (CSF) 2.0** for Small Business | https://www.nist.gov/cyberframework | "Quick Start" guides for SMB; 6 functions (Govern, Identify, Protect, Detect, Respond, Recover) |

**Recommendation:** Use **NIST CSF 2.0** as the overarching framework for Vigil's security posture management (it's what consumers' insurance carriers may ask about), and **NIST SP 800-61 Phase 2** as the alert enrichment workflow.

---

## 2. Open-Source Threat Intelligence Sources

### 2.1 AbuseIPDB

| Attribute | Detail |
|-----------|--------|
| **URL** | https://www.abuseipdb.com/ |
| **API Docs** | https://docs.abuseipdb.com/ |
| **Data Types** | IP address reputation, abuse reports, ISP, domain, country, last reported, confidence score |
| **Free Tier** | 1,000 IP checks/day + 100 blocklist downloads/day |
| **API Limits** | Standard (free): 1,000 req/day; paid plans start at unlimited |
| **Integration Complexity** | **Low** — REST JSON API, single endpoint, SDKs for Python |
| **Priority** | **P0** |

**Key Features:**
- Confidence score (0-100) — directly usable in Vigil's trust score calculation
- Abuse report history (last 30 days visible on free tier)
- Category classification (e.g., "Port Scan," "Brute Force," "Web App Attack")
- Blocklist download in various formats (CIDR, IP list)
- Fail2Ban integration available (reuse proven integration patterns)

**Vigil Integration Use Case:**
```
Suricata detects connection to external IP
  → AbuseIPDB lookup
  → If confidence > 70: escalate alert severity, add "Known malicious IP" narrative
  → If confidence > 90: trigger containment action
```

### 2.2 abuse.ch (SSLBL / Feodo Tracker / URLhaus)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://abuse.ch/ (multiple platforms) |
| **Feeds** | SSLBL (SSL certs used by malware), Feodo Tracker (C2 indicators), URLhaus (malware URLs), Threatfox (IOC aggregator) |
| **License** | Open (CC0 / freely usable) |
| **Format** | TXT blocklists, Suricata rules, STIX, CSV, JSON |
| **Free Tier** | **Unlimited** — all feeds are free and open |
| **Integration Complexity** | **Low** — static file download or API polling; Suricata-ready rules available |
| **Priority** | **P0** |

**Key Features:**
- **SSLBL:** SSL certificate blacklist (malware C2 certs) — available as Suricata rules, ideal for Vigil's existing Suricata pipeline
- **Feodo Tracker:** Botnet C2 IPs for Dridex, Heodo, etc. — downloadable as Suricata rules
- **URLhaus:** Active malware distribution URLs (filtered by status=online)
- **ThreatFox:** Aggregated IOCs from multiple sources with tags, malware family, and reference links
- All feeds are timestamped and regularly updated (every few hours)

**Vigil Integration Use Case:**
```
Daily cron:
  wget https://sslbl.abuse.ch/blacklist/sslipblacklist.rules -O /etc/suricata/rules/abuse.rules
  wget https://feodotracker.abuse.ch/downloads/ipblocklist.csv -O /var/vigil/feeds/feodo.csv
  → Suricata auto-loads updated rules; Vigil enricher cross-references all alerts
```

### 2.3 AlienVault OTX (Open Threat Exchange)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://otx.alienvault.com/ |
| **API Docs** | https://otx.alienvault.com/api |
| **Data Types** | IPs, domains, URLs, hashes (MD5/SHA1/SHA256), CVE mappings, malware families, YARA rules |
| **Free Tier** | **Completely free** — no rate limits documented for basic API access |
| **API Limits** | Effectively unlimited for personal use; pulses per subscriber limit applies to custom pulses |
| **Integration Complexity** | **Medium** — richer API (multiple endpoints), requires API key, but well-documented Python SDK (`OTXv2`) |
| **Priority** | **P1** (complement to AbuseIPDB) |

**Key Features:**
- OTX Pulse subscriptions (choose pulses by sector, malware family, or geo)
- IoC enrichment with context (who reported it, when, related pulses)
- Community threat intelligence from 200K+ contributors
- Malware family classification with references
- Built-in CVE correlation

**Vigil Integration Use Case:**
```
Alert comes in for IP X.X.X.X
  → OTX query returns: part of "Mirai Variant Jan 2026" pulse (confidence: high)
  → Vigil narrative: "IP X.X.X.X is associated with a known Mirai variant C2 (OTX pulse #12345)"
  → Trust score: apply negative modifier to any device communicating with this IP
```

### 2.4 GreyNoise Community API

| Attribute | Detail |
|-----------|--------|
| **URL** | https://greynoise.io/ |
| **API Docs** | https://docs.greynoise.io/docs/using-the-greynoise-community-api |
| **Data Types** | IP classification (malicious vs. benign internet background noise), last seen, tags, actor, metadata |
| **Free Tier** | **Community API** — unauthenticated, limited daily lookups (undocumented limit, ~50-100/day) |
| **API Limits** | Free: ~50-100/day; Paid (subscription): unlimited |
| **Integration Complexity** | **Low** — simple GET request; Python SDK available |
| **Priority** | **P1** (high ROI for classifying external IPs) |

**Key Features:**
- Answers: "Is this IP scanning the whole internet, or is this targeted?"
- Classification: `noise` (internet background scanner), `riot` (benign service like CDN), `unknown` (no data)
- Tags: "Mirai," "IoT Scanner," "SSH Bruteforcer" — directly relevant to home IoT threat landscape
- RIoT dataset identifies known-safe IPs (CDNs, SaaS providers) to reduce false positives

**Vigil Integration Use Case:**
```
Anomaly detection flags device talking to new external IP
  → GreyNoise lookup
  → If "noise": likely false positive (internet background scan), don't alert
  → If "malicious" + tag "Mirai C2": escalate immediately
  → If "unknown": proceed with other enrichment, no discount applied
```

### 2.5 VirusTotal Public API

| Attribute | Detail |
|-----------|--------|
| **URL** | https://www.virustotal.com/ |
| **API Docs** | https://developers.virustotal.com/reference/public-vs-premium-api |
| **Data Types** | File hashes, URLs, domains, IPs — multi-engine scan results, community comments, detections |
| **Free Tier** | **4 requests/minute** — extremely limited; 500/day cap |
| **API Limits** | Public: 4 req/min, ~500 req/day (soft); Premium: custom |
| **Integration Complexity** | **Medium** — API key required, rate limiting logic needed, multiple endpoint types |
| **Priority** | **P2** (rate limits make it unreliable for real-time enrichment) |

**Key Features:**
- Multi-engine detection (60+ AV vendors)
- Detection ratio (how many engines flagged it)
- Community comments and analysis
- File behavior reports (sandbox execution)
- URL scan reports

**Vigil Integration Use Case:**
```
Batch/offline enrichment (not real-time due to rate limits):
  Collect external IPs/domains from past 24h of Suricata alerts
  → Queue VT lookups at 4 req/min
  → Update local IOC cache for next-day alert enrichment
  → Use for "known scanner" IP marking
```

**Important Limitation:** VT's free tier is too restrictive for real-time alert enrichment. However, it's valuable for **offline batch analysis** and **malware hash verification** (e.g., if Vigil downloads a firmware file, hash it and check VT).

### 2.6 MISP (Malware Information Sharing Platform)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://www.misp-project.org/ |
| **GitHub** | https://github.com/MISP/MISP |
| **License** | AGPL v3 (open source — self-hosted) |
| **Data Types** | Full STIX 2.1 IOCs (IPs, domains, hashes, YARA rules, CVE mappings), correlation groups |
| **Free Tier** | **Self-hosted** — completely free but requires infrastructure (~4GB RAM minimum) |
| **API Limits** | Self-managed (MISP administrator controls limits) |
| **Integration Complexity** | **High** — requires deploying and maintaining a MISP instance, or connecting to an existing community |
| **Priority** | **P2** (high value but significant operational overhead for consumer appliance) |

**Key Features:**
- Peered threat sharing with global MISP community
- Automatic IOC correlation (finds relationships between seemingly unrelated IOCs)
- Built-in feed integration (CISA KEV, abuse.ch, Botvrij, etc.)
- Galaxy clusters for IoT devices and malware families
- Export to Suricata rules, YARA, STIX, CSV
- Python SDK (PyMISP) for integration

**Vigil Integration Use Case:**
```
Vigil Cloud (backend service) runs a lightweight MISP instance
  → Subscribes to relevant feeds (CISA KEV, abuse.ch, IoT Galaxy clusters)
  → Syncs daily: new IOCs pushed to each Vigil Home appliance
  → Appliance caches IOCs locally for real-time lookup during alert enrichment
```

**Recommendation:** Do not deploy MISP on the Vigil Home appliance itself (resource constraints). Instead, deploy a central MISP instance in Vigil Cloud and push curated IOC feeds to appliances. This is a Phase 2+ capability.

### 2.7 Emerging Threats (Proofpoint)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://rules.emergingthreats.net/ |
| **Data Types** | Suricata/Snort rules (open + pro) covering malware, exploits, policy violations |
| **Free Tier** | **ET Open** — full Suricata ruleset, free, no registration |
| **API Limits** | N/A (file download only) |
| **Integration Complexity** | **Low** — already part of Vigil's Suricata pipeline per OSS-RESOURCES.md |
| **Priority** | **P0** (already planned/implemented) |

**Key Features:**
- **ET Open:** Free Suricata ruleset, updated regularly
- **ET Pro:** Commercial ruleset ($500/yr); includes IoT-specific rules, better coverage, lower false positive rate
- **ET IoT Hunter:** Open-source Python tool for IoT-specific traffic analysis (MQTT, CoAP, UPnP, mDNS)
- Rules are classified by category: malware C2, exploit kit, info steal, etc.

**Note:** Already documented in OSS-RESOURCES.md as a must-have integration. The key new recommendation is to evaluate **ET Pro** for its IoT rule coverage — at $500/yr for a commercial product, it may be worth including in the $19.99/mo subscription cost.

---

## 3. IoT-Specific Threat Feeds & Data Sources

### 3.1 C2 Tracker (montysecurity)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://github.com/montysecurity/C2-Tracker |
| **Data Types** | Live C2 server IPs for major C2 frameworks (Cobalt Strike, Metasploit, Empire, Sliver, etc.) |
| **License** | Open source (MIT) |
| **Update Frequency** | Daily |
| **Free Tier** | **Free** (public GitHub repo) |
| **Integration Complexity** | **Low** — CSV/JSON feed, simple download |
| **Priority** | **P1** |

**Key Features:**
- Uses Shodan to discover new C2 servers via SSL certificate fingerprints
- Covers: Cobalt Strike, Metasploit, Empire, PoshC2, Covenant, Sliver, Brute Ratel, etc.
- Updates daily — fresh indicators for C2 detection

### 3.2 C2IntelFeeds (drb-ra)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://github.com/drb-ra/C2IntelFeeds/ |
| **Data Types** | Automated C2 IOC feeds (IPs, domains) for multiple C2 frameworks |
| **License** | Open source |
| **Update Frequency** | Automated |
| **Free Tier** | **Free** |
| **Integration Complexity** | **Low** |
| **Priority** | **P2** |

### 3.3 Nokia Deepfield Public Research (Mirai/Botnet IOCs)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://github.com/deepfield/public-research |
| **Data Types** | DDoS botnet research IOCs including Mirai variants, YARA rules |
| **License** | Open source |
| **Free Tier** | **Free** |
| **Integration Complexity** | **Low** |
| **Priority** | **P2** |

### 3.4 CISA Known Exploited Vulnerabilities (KEV) Catalog

| Attribute | Detail |
|-----------|--------|
| **URL** | https://www.cisa.gov/known-exploited-vulnerabilities-catalog |
| **API** | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json |
| **Data Types** | CVEs with known exploits, CISA-added metadata (date added, due date, remediation) |
| **License** | Public domain (US government) |
| **Update Frequency** | Continuous (often daily) |
| **Free Tier** | **Free** and unlimited |
| **Integration Complexity** | **Low** — single JSON feed |
| **Priority** | **P0** |

**Key Features:**
- Curated list of CVEs with confirmed active exploitation
- Includes remediation actions and due dates
- Machine-readable JSON feed
- Directly relevant for trust scoring: device running software with a KEV CVE should have trust score reduced

### 3.5 Shodan InternetDB API (Free)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://internetdb.shodan.io/ |
| **API Format** | `GET https://internetdb.shodan.io/{ip}` — no key required |
| **Data Types** | Open ports, service banners, CVE information, hostnames |
| **Free Tier** | **Completely free** — no API key, no account needed |
| **API Limits** | Undocumented but generous; designed for non-commercial use |
| **Integration Complexity** | **Low** — single HTTP GET |
| **Priority** | **P1** |

**Key Features:**
- Fast IP lookups returning open ports and related CVEs
- Useful for fingerprinting an external IP (is it a web server? a camera? an IoT hub?)
- CVE information: if an external IP has a known vulnerable service, Vigil can flag connections as higher risk
- No registration required — simplest possible integration

### 3.6 Censys Free API

| Attribute | Detail |
|-----------|--------|
| **URL** | https://search.censys.io/ |
| **API Docs** | https://docs.censys.com/ |
| **Data Types** | Host information, open ports, services, SSL certificates, DNS records |
| **Free Tier** | Free account: 1 credit/lookup with limited monthly credits (~50-100 lookups/month) |
| **Integration Complexity** | **Medium** — API key required, credit-based consumption |
| **Priority** | **P2** (Shodan InternetDB is simpler and free for basic lookups) |

---

## 4. Enrichment APIs & Services

### 4.1 IP Geolocation — IPinfo.io (Free Tier)

| Attribute | Detail |
|-----------|--------|
| **URL** | https://ipinfo.io/ |
| **Data Types** | IP geolocation (country, region, city, coordinates), ASN, ISP, organization |
| **Free Tier** | **IPinfo Lite** — country-level geolocation + ASN, unlimited requests |
| **API Limits** | Authenticated free: 50,000 req/month for API details; public API (no key): unlimited but limited fields |
| **Integration Complexity** | **Low** — single GET with optional API key |
| **Priority** | **P1** |

**Key Features:**
- Country + ASN + ISP on free tier — sufficient for most alert enrichment needs
- IPinfo Lite download available as CSV database for offline use
- Paid tiers add city-level, coordinates, carrier, privacy detection (VPN/proxy)

**Vigil Integration Use Case:**
```
Suricata detects outbound connection to 185.xxx.xxx.xxx
  → ipinfo: AS "DDoS-Guard", ISP "Russian hosting", country "RU"
  → Vigil narrative: "Device connected to Russian hosting provider (DDoS-Guard), typically associated with malicious infrastructure"
```

### 4.2 SSL Certificate Transparency — crt.sh

| Attribute | Detail |
|-----------|--------|
| **URL** | https://crt.sh/ |
| **Data Types** | SSL certificate issuance history, subdomains for a domain, issuer details |
| **Free Tier** | **Free** — no API key, no rate limits |
| **API Limits** | Public endpoint, be reasonable (~1 req/sec) |
| **Integration Complexity** | **Low** — simple REST query; Python libraries available (`pycrtsh`) |
| **Priority** | **P2** (niche use case for Vigil) |

**Key Features:**
- Query by IP, domain, SHA-1, SHA-256 fingerprint
- Certificate transparency logs — can detect suspicious certificate issuance
- Useful for verifying whether a connection's SSL cert matches what crt.sh expects for a domain

**Vigil Integration Use Case:**
```
Rare case — deep investigation mode:
  Device connects to domain with suspicious SSL certificate
  → crt.sh lookup: does the domain's cert match historical TLs logs?
  → If mismatch: possible man-in-the-middle or phishing
```

### 4.3 URLScan.io

| Attribute | Detail |
|-----------|--------|
| **URL** | https://urlscan.io/ |
| **Data Types** | URL/domain analysis, screenshot, DOM content, redirect chain, HTTP headers, IP resolutions |
| **Free Tier** | 50 private scans/day, 2,500 public scans/day |
| **API Limits** | Free: 50 private/day, 2,500 public/day (public scans are visible on urlscan.io) |
| **Integration Complexity** | **Medium** — API key required, two-step (submit + poll result) |
| **Priority** | **P2** (overkill for real-time, useful for batch analysis) |

**Vigil Integration Use Case:**
```
Periodic batch analysis:
  Extract all external domains from past 24h of traffic
  → Submit to urlscan.io (public scan)
  → Review results: any flagged as malicious?
  → Update local domain reputation cache
```

### 4.4 National Vulnerability Database (NVD) API 2.0

| Attribute | Detail |
|-----------|--------|
| **URL** | https://nvd.nist.gov/developers/vulnerabilities |
| **Data Types** | CVE details, CVSS scores, CPE matches (affected products), references |
| **Free Tier** | **Free** — API key increases rate limit from 5 to 50 req/30 seconds |
| **API Limits** | No key: 5 req/30s; With key: 50 req/30s |
| **Integration Complexity** | **Low** — REST API, JSON responses |
| **Priority** | **P2** (for device vulnerability enrichment, can be batched) |

**Vigil Integration Use Case:**
```
Vigil identifies a device model via MAC OUI + mDNS/UPnP
  → Query NVD for CVEs matching device CPE
  → If CVSS > 7.0: reduce device trust score, add to narrative
  → "Your TP-Link Kasa HS103 has 3 known vulnerabilities (CVSS 8.1, 7.5, 6.8)"
```

### 4.5 MAC Address OUI Lookup

| Attribute | Detail |
|-----------|--------|
| **URL** | https://standards-oui.ieee.org/oui/oui.txt |
| **Data Types** | Manufacturer name from OUI prefix |
| **Free Tier** | **Free** and unlimited |
| **Integration Complexity** | **Low** — static text file download, parse locally |
| **Priority** | **P0** (already partially implemented per OSS-RESOURCES.md) |

**Note:** Already documented in OSS-RESOURCES.md. Recommendation: ensure the OUI database is included in the appliance base image and updated monthly via system update mechanism.

---

## 5. Comparison Matrix

| Resource | Category | Free Tier Limit | API Type | Complexity | Priority | Alert Pipeline Use |
|----------|----------|----------------|----------|------------|----------|-------------------|
| **AbuseIPDB** | IP Reputation | 1,000/day | REST JSON | Low | **P0** | Real-time IP check on outbound connections |
| **abuse.ch (SSLBL/Feodo)** | C2/Botnet IOCs | Unlimited | Download/Suricata | Low | **P0** | Pre-loaded signatures in Suricata |
| **ET Open Rules** | IDS Rules | Unlimited | File download | Low | **P0** | Core Suricata rule set (already integrated) |
| **CISA KEV** | Vulnerability | Unlimited | JSON feed | Low | **P0** | Trust score input for device risk |
| **GreyNoise Community** | Noise Classification | ~50-100/day | REST JSON | Low | **P1** | False-positive reduction for external IP alerts |
| **AlienVault OTX** | Multi-IOC | Unlimited | REST + SDK | Medium | **P1** | Context enrichment for suspicious IPs/domains |
| **Shodan InternetDB** | Service Fingerprint | Unlimited (no key) | REST JSON | Low | **P1** | Identify external IP device type |
| **IPinfo.io** | Geolocation | 50K/month | REST JSON | Low | **P1** | Alert narrative: "connection from country X" |
| **C2 Tracker (monty)** | C2 IPs | Unlimited | GitHub feed | Low | **P1** | C2 detection blocklist |
| **VirusTotal Public** | Multi-AV | 4 req/min | REST JSON | Medium | **P2** | Batch/offline hash analysis |
| **MISP (self-hosted)** | Full TIP | Self-managed | REST + PyMISP | High | **P2** | Central IOC management (Vigil Cloud) |
| **Censys Free** | Host Data | ~50/month | REST | Medium | **P2** | Deep-dive external IP enrichment |
| **crt.sh** | SSL Certs | Unlimited | REST | Low | **P2** | Suspicious cert investigation |
| **URLScan.io** | URL Analysis | 50 private/day | REST | Medium | **P2** | Batch domain analysis |
| **NVD API** | Vulnerability | 50 req/30s | REST | Low | **P2** | Device CVE lookup |
| **Nokia Deepfield** | DDoS/Botnet IOCs | Unlimited | GitHub | Low | **P2** | Botnet detection signatures |

---

## 6. Recommended Implementation Roadmap

### Phase 1: Core Enrichment (Weeks 1-2) — P0 Items
**Goal:** Immediate alert quality improvement with minimal development effort.

1. **AbuseIPDB lookup module**
   - Create `EnrichmentEngine.enhance_with_abuseipdb(ip)` in Vigil's alert pipeline
   - Cache results locally (TTL: 1 hour) to stay within 1,000/day limit
   - Add enrichment fields to alert output: `abuseipdb_confidence`, `abuseipdb_reports_count`
   - Integrate into narrative generation: "IP contacted has been reported X times for Y activity"

2. **abuse.ch feed sync**
   - Daily cron: download SSLBL blocklist + Feodo C2 IPs
   - Convert to Suricata rules and load into Vigil's rule set
   - Monitor rule match rates weekly

3. **CISA KEV sync**
   - Daily cron: download CISA KEV JSON
   - Index by CPE/product for device vulnerability matching
   - Use as trust score modifier

### Phase 2: Context & FP Reduction (Weeks 3-4) — P1 Items
**Goal:** Reduce false positives and add geographic/service context to alerts.

1. **GreyNoise integration** (critical for FP reduction)
   - Create `is_noise(ip)` — first enrichment call in pipeline
   - If `noise`: reduce alert severity, add "internet background noise" note to narrative
   - If `riot`: tag as known-safe service, skip enrichment
   - Cache aggressively (TTL: 24h) since free tier is limited

2. **IPinfo geolocation**
   - Add `ipinfo_country`, `ipinfo_asn`, `ipinfo_isp` to alert enrichment
   - If country differs from device's home country by >2,000 km and protocol is SSH/Telnet: add suspicion note

3. **Shodan InternetDB**
   - For external IPs flagged by Suricata: lookup open ports and services
   - Add to narrative: "IP is running [service] on port [port]"
   - Identify IoT devices: "IP appears to be an RTSP camera (port 554 open)"

4. **C2 Tracker sync**
   - Daily download of C2 IP blocklist
   - Cross-reference all outbound Suricata alerts against C2 IPs
   - Any match triggers immediate high-severity alert

### Phase 3: Deep Enrichment (Weeks 5-6) — P1/P2 Items
**Goal:** Malware hash analysis, threat context, and device vulnerability mapping.

1. **AlienVault OTX pulses**
   - Subscribe to relevant pulses (IoT botnet, Mirai, router malware)
   - Cross-reference IOCs from pulses against Vigil's cached IP/domain sightings
   - Add OTX pulse references to alert narratives

2. **NVD device vulnerability mapping**
   - Build device-to-CPE mapping table (TP-Link HS103 → cpe:2.3:h:tp-link:hs103:*)
   - On device onboarding and periodically: query NVD for device-relevant CVEs
   - Adjust trust score based on unpatched CVEs

3. **VirusTotal batch analysis** (offline)
   - Daily batch: hash any downloaded firmware/files → submit to VT
   - Queue lookups at 4 req/min
   - Log results for post-incident analysis

### Phase 4: Advanced (Phase 2+ of Vigil Product) — P2 Items
**Goal:** Centralized threat intelligence operations.

1. **MISP deployment (Vigil Cloud)**
   - Deploy MISP instance in Vigil Cloud backend
   - Subscribe to CISA KEV, abuse.ch, Botvrij, and OTX pulses
   - Push curated alert feed + IOC updates to all Vigil Home appliances
   - Enable two-way Intel sharing (if desired by community)

2. **URLScan.io batch domain analysis**
   - Weekly batch: submit unknown domains seen in device traffic
   - Review results for malicious classifications

---

## 7. Sample Enrichment Flow Diagram

```
                                    VIGIL HOME ENRICHMENT PIPELINE
                                    ==============================

    ┌─────────────────────────────────────────────────────────────────────┐
    │                       SURICATA IDS ALERT                           │
    │    src_ip: 192.168.1.105  →  dst_ip: 185.XX.XX.XX  port: 443      │
    │    rule: ET MALWARE [Mirai] Outbound Connection to C2              │
    └──────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. THREAT INTEL ENRICHMENT (Phase 1 + 2)                         │
    │                                                                     │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐        │
    │  │ GreyNoise   │───→│ AbuseIPDB   │───→│ Shodan InternetDB│        │
    │  │ (FP filter) │    │ (reputation)│    │ (service info)  │        │
    │  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘        │
    │         │                  │                    │                  │
    │         ▼                  ▼                    ▼                  │
    │  "Internet bg   "Confidence: 92%    "Open ports: 443, 8080       │
    │   noise"        Reports: 45          HTTP: nginx 1.24"            │
    │  → FP filter    Category: C2"                                     │
    │                                                                     │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐        │
    │  │ IPinfo Geo  │    │ C2 Tracker  │    │abuse.ch SSLBL   │        │
    │  │ (location)  │    │ (C2 match)  │    │(SSL cert check) │        │
    │  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘        │
    │         │                  │                    │                  │
    │         ▼                  ▼                    ▼                  │
    │  "Country: RU   "Matched: Cobalt    "SSL cert: malicious        │
    │   ISP: DDoS-    Strike server       serial ABC123"              │
    │   Guard"        (montysecurity)"                                 │
    └─────────────────┬──────────────────────────────────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  2. DEVICE CONTEXT                                                 │
    │                                                                     │
    │  ┌──────────────┐     ┌──────────────┐     ┌───────────────────┐   │
    │  │ MAC OUI      │     │ Device Trust  │     │ Vulnerability    │   │
    │  │ (manufacturer)│     │ (current score)│     │ (CVE lookup)    │   │
    │  └──────┬───────┘     └──────┬───────┘     └────────┬──────────┘   │
    │         │                    │                      │              │
    │         ▼                    ▼                      ▼              │
    │  "TP-Link Kasa  "Trust: ████████░░                  │              │
    │   HS103"         (82/100) - ↓5%"                   │              │
    │                                       "CVE-2025-1234             │
    │                                        unpatched"                 │
    └─────────────────┬──────────────────────────────────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  3. THREAT FRAMEWORK MAPPING                                       │
    │                                                                     │
    │  ┌──────────────────────┐  ┌──────────────────────────────────┐    │
    │  │ MITRE ATT&CK for ICS │  │      OWASP IoT Top 10           │    │
    │  │ Tactic: TA0115 (C2)  │  │ Risk: Insecure Network Services │    │
    │  │ Technique: T0846     │  │ (OWASP-IoT-2)                   │    │
    │  │ (Remote System Info  │  │                                  │    │
    │   │ Discovery)           │  │                                  │    │
    │  └──────────────────────┘  └──────────────────────────────────┘    │
    └─────────────────┬──────────────────────────────────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  4. NARRATIVE GENERATION (Final Alert Output)                      │
    │                                                                     │
    │  "**HIGH SEVERITY** — Your TP-Link Kasa HS103 smart plug           │
    │   (trust score: 77/100) connected to a known malicious server.     │
    │                                                                     │
    │   • IP: 185.XX.XX.XX (Russia, DDoS-Guard hosting)                  │
    │   • Reported 45 times for C2 activity (AbuseIPDB, confidence 92%)   │
    │   • Matches known Cobalt Strike C2 server (C2 Tracker)              │
    │   • Device has unpatched CVE-2025-1234 (CVSS 8.1)                  │
    │                                                                     │
    │   MITRE ATT&CK: Command & Control (TA0115) — C2 Beaconing (T0846)  │
    │   OWASP IoT Risk: Insecure Network Services                        │
    │                                                                     │
    │   **Recommended action:** Review device and consider isolating     │
    │   from your network until the issue is resolved."                  │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Top 5 Highest-Value Integrations With Rationale

### #1: AbuseIPDB + abuse.ch Feeds (P0)
**Combined rationale:** These two together provide **IP reputation + C2 blocklisting** at near-zero cost and with extremely low integration complexity. AbuseIPDB gives per-IP confidence scores and abuse history; abuse.ch gives pre-built Suricata rulesets for immediate C2 detection. Together they cover the two most common enrichment needs: "Is this IP bad?" and "Is this C2 traffic?" — which answer the majority of alert questions for a home IoT security appliance. Estimated impact: **40-50% of enrichment value** with <1 week of integration work.

### #2: GreyNoise Community API (P1)
**Rationale:** False-positive reduction is the single highest-leverage improvement for any home security product. Consumers have low tolerance for false alarms. GreyNoise answers "Is this just internet background noise?" — if yes, the alert can be silently handled or deferred. This directly improves user trust in the Guardian persona. Free tier (~50-100 lookups/day) is sufficient for most homes where the appliance sees a few hundred external IPs per day; implement aggressive caching to maximize coverage. Estimated impact: **30-40% FP reduction** with <2 days of integration work.

### #3: Shodan InternetDB (P1 — Free, No Key)
**Rationale:** The ability to identify *what kind of service* an external IP is running — "this is a web server," "this is another IoT camera," "this is a Tor exit node" — dramatically improves narrative quality. It's free, requires no API key, and is a single HTTP GET. For a home security product, being able to say "Device connected to a web hosting service" vs. "Device connected to an IoT device in Brazil" is the difference between a vague and a useful alert. Estimated impact: **Adds service-level context to 20-30% of alerts** with <1 day of integration.

### #4: CISA Known Exploited Vulnerabilities (KEV) Feed (P0)
**Rationale:** This feed directly feeds Vigil's unique value proposition: **device trust scoring based on known vulnerabilities**. When CISA publishes a KEV entry for a CVE affecting a TP-Link smart plug, Vigil can reduce that device's trust score and notify the user proactively — before any malicious traffic is detected. This is a proactive security capability, not just reactive alert enrichment. The feed is free, government-curated, and updated daily. Estimated impact: **Proactive vulnerability notification for 10-20% of smart home devices** with <1 day of integration.

### #5: IPinfo.io Geolocation + ASN Data (P1)
**Rationale:** Geographic context is one of the simplest yet most effective narrative enhancements. "Connection to Russia" carries immediate weight for a US-based home. IPinfo provides country + ASN + ISP on its free tier (50K/month), which is well within range for a home appliance. Combined with AbuseIPDB confidence scores, geographic context helps users and automated systems triage alerts. Estimated impact: **Adds geographic context to 100% of external IP alerts** with <1 hour of integration.

---

## Appendix A: Quick Reference — All Endpoints

```
# AbuseIPDB (requires API key)
GET https://api.abuseipdb.com/api/v2/check?ipAddress=X.X.X.X
Header: Key: <api_key>
Header: Accept: application/json

# GreyNoise Community (no key, limited)
GET https://api.greynoise.io/v3/community/X.X.X.X

# Shodan InternetDB (no key required)
GET https://internetdb.shodan.io/X.X.X.X

# IPinfo (no key, limited fields)
GET https://ipinfo.io/X.X.X.X/json
# IPinfo (with free key, more fields)
GET https://ipinfo.io/X.X.X.X?token=<token>

# AlienVault OTX (requires API key)
GET https://otx.alienvault.com/api/v1/indicators/IPv4/X.X.X.X/general
Header: X-OTX-API-KEY: <api_key>

# crt.sh (no key)
GET https://crt.sh/?q=X.X.X.X&output=json

# VirusTotal (requires API key, 4 req/min)
GET https://www.virustotal.com/api/v3/ip_addresses/X.X.X.X
Header: x-apikey: <api_key>

# CISA KEV (no key)
GET https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

# NVD API 2.0 (key optional, recommended)
GET https://services.nvd.nist.gov/rest/json/cves/2.0?cpeName=cpe:2.3:h:tp-link:hs103&key=<api_key>

# abuse.ch SSLBL Suricata rules (no key)
GET https://sslbl.abuse.ch/blacklist/sslipblacklist.rules
GET https://sslbl.abuse.ch/blacklist/sslblacklist.rules

# Feodo Tracker C2 blocklist (no key)
GET https://feodotracker.abuse.ch/downloads/ipblocklist.csv
```

## Appendix B: Data Privacy Considerations

All of the recommendations above involve sending IP addresses or domains to external services. For a home security product with a "privacy-first" positioning:

1. **AbuseIPDB/GreyNoise/IPinfo:** These accept single IP lookups with no historical context. The privacy exposure is minimal — you're asking "is this IP known bad?" — which reveals the IP but not any device or user information.

2. **CISA KEV / NVD / abuse.ch / C2 Tracker:** These are static/polled feeds — no lookup data is sent to them. Privacy risk: **none**. These are preferred from a privacy perspective.

3. **AlienVault OTX / VirusTotal:** These receive the indicator you're looking up. Privacy risk is moderate; the indicator itself (IP/domain/hash) might reveal what devices are in your network.

4. **Recommendation:** Make external enrichment **opt-in** in Vigil's settings with clear privacy disclosures. Default to cached/polled feeds (CISA KEV, abuse.ch, C2 Tracker) and require explicit consent for real-time cloud lookups (AbuseIPDB, OTX, VT).

---

*End of document. For related OSS resources, see [knowledge-base/OSS-RESOURCES.md](./knowledge-base/OSS-RESOURCES.md).*
