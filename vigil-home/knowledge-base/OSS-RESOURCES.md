# OSS-RESOURCES.md — Open-Source Libraries, Rules, and Tools

**Last Updated:** 2026-05-06  
**Version:** 1.0  

---

## Overview

This document catalogs open-source resources relevant to Vigil Home's detection pipeline. Resources are organized by type and tagged with their applicability.

---

## Table of Contents

1. [Suricata Rules & Configs](#1-suricata-rules--configs)
2. [Snort Rules & Configs](#2-snort-rules--configs)
3. [YARA Rules](#3-yara-rules)
4. [Sigma Rules](#4-sigma-rules)
5. [MITRE ATT&CK for ICS](#5-mitre-attck-for-ics)
6. [MISP Threat Intelligence Platform](#6-misp-threat-intelligence-platform)
7. [Shodan Tools & Utilities](#7-shodan-tools--utilities)
8. [IoT Device Identification](#8-iot-device-identification)
9. [Botnet Analysis Tools](#9-botnet-analysis-tools)
10. [Network Analysis Tools](#10-network-analysis-tools)
11. [Protocol Fuzzing & Security Testing](#11-protocol-fuzzing--security-testing)
12. [IoT-Specific Security Frameworks](#12-iot-specific-security-frameworks)
13. [Default Credential Databases](#13-default-credential-databases)
14. [Reference & Research Repos](#14-reference--research-repos)

---

## 1. Suricata Rules & Configs

### Emerging Threats (Proofpoint)

| Resource | URL | Description | License |
|----------|-----|-------------|---------|
| ET Open Rules | https://rules.emergingthreats.net/open/ | Free rule set for Suricata/Snort | Open |
| ET Pro Rules | https://rules.emergingthreats.net/ | Subscription rule set with IoT rules | Commercial |
| ET IoT Hunter | https://github.com/EmergingThreats/iot-hunter | IoT-specific traffic analysis rules (Python) | Apache 2.0 |

**Installation:**
```bash
# ET Open rules download
wget https://rules.emergingthreats.net/open/suricata-6.0.8/emerging.rules.tar.gz

# ET IoT Hunter (Python-based)
git clone https://github.com/EmergingThreats/iot-hunter.git
```

**IoT Coverage in ET Rules:**
- Known botnet C2 traffic
- Protocol anomalies (MQTT, CoAP, UPnP)
- Malware staging connections
- DNS tunneling detection

### SSLBL Suricata Rules (abuse.ch)

| Resource | URL |
|----------|-----|
| C2 IP blocklist (rules) | https://sslbl.abuse.ch/blacklist/sslipblacklist.rules |
| SSL certificate rules | https://sslbl.abuse.ch/blacklist/sslblacklist.rules |

**Integration:**
```bash
# Download and load daily
wget https://sslbl.abuse.ch/blacklist/sslipblacklist.rules -O /etc/suricata/rules/sslbl.rules
```

### Snort Community Rules

| Resource | URL | Description |
|----------|-----|-------------|
| Snort Community | https://www.snort.org/downloads/#rule-downloads | Free community rules |
| Snort Registered | https://www.snort.org/products | Free registered user rules (better coverage) |

---

## 2. Snort Rules & Configs

*Legacy but still widely deployed. Vigil Home should prefer Suricata for modern features (HTTP2, file extraction, Lua scripting).*

| Resource | URL | Notes |
|----------|-----|-------|
| Talos Intelligence | https://talosintelligence.com/ | Cisco Talos rules (Snort + ClamAV) |
| Snort Community | https://github.com/snort3/snort3-community-rules | Community-maintained |
| VRT Rules | Via Snort subscription | Commercial — extensive coverage |

---

## 3. YARA Rules

### Essential Repositories

| Repository | URL | Stars | Notes |
|-----------|-----|-------|-------|
| Neo23x0/signature-base | https://github.com/Neo23x0/signature-base | ⭐ 3K+ | Comprehensive rule collection including IoT/mirai |
| YARA Forge | https://github.com/YARAHQ/yara-forge | ⭐ 800+ | Aggregated YARA rules from multiple sources |
| InQuest/awesome-yara | https://github.com/InQuest/awesome-yara | ⭐ 3K+ | Curated list of YARA resources |
| Florian Roth (Nextron) | https://github.com/Neo23x0/signature-base | ⭐ 3K+ | Author of many high-quality rules |

### IoT-Specific YARA Rules

| Rule Set | URL | Description |
|----------|-----|-------------|
| Mirai YARA | `signature-base/yara/crime_mirai.yar` | Detection of Mirai malware binaries |
| Gafgyt/Bashlite | `signature-base/yara/crime_gafgyt.yar` | Gafgyt variant detection |
| IoT Botnet Analysis | https://github.com/Hariru0x00/IoT-Botnet-Analysis | Multi-family IoT botnet YARA rules |
| Mirai Toushi | https://github.com/iij/mirai-toushi | Cross-architecture Mirai config extractor (Ghidra) |
| MalwareBazaar YARA | https://bazaar.abuse.ch/browse/yara/ | Browser/searchable YARA rules per malware family |

### Sample YARA Rule (Mirai)
```yara
/*
   Author: Florian Roth (Neo23x0)
   Detects: Mirai malware binaries
*/
rule Crime_Mirai {
   meta:
      description = "Detects Mirai Malware"
      author = "Florian Roth"
      reference = "https://blog.malwaremustdie.org/"
      date = "2016-10-04"
   strings:
      $s0 = "Mirai" fullword ascii
      $s1 = "resolv.c" fullword ascii
      $s2 = "table.c" fullword ascii
      $s3 = "scanner.c" fullword ascii
      $s4 = "killer.c" fullword ascii
   condition:
      2 of ($s*)
}
```

### Integration for Vigil Home
- **Use case:** Scan firmware download payloads for known malware signatures
- **Use case:** Scan device filesystem artifacts (if accessible) for malicious binaries
- **Deployment:** Integrate YARA into Vigil Home's HTTP proxy for firmware inspection

---

## 4. Sigma Rules

**Format:** Generic, SIEM-agnostic detection rules in YAML  
**Repository:** https://github.com/SigmaHQ/sigma  
**Latest Release:** r2025-12-01  

### Why Sigma for Vigil Home
- Vendor-agnostic detection rule format
- Can be converted to Suricata/Snort rules
- Portable between Vigil Home detection backends
- Community-maintained with growing IoT coverage

### IoT-Relevant Sigma Rules (from SigmaHQ)

| Rule Category | Example | Relevance |
|--------------|---------|-----------|
| Network: DNS | DNS queries to dynamic DNS providers | High — C2 indicators |
| Network: Connection | Outbound to known malicious IPs | High — C2 blocklist |
| Network: HTTP | Suspicious User-Agent strings | Medium — IoT device profiling |
| Process creation | Wget/curl/tftp from unusual processes | Medium — malware download |
| Firewall | Port scan detection | High — lateral movement |

### Conversion Tool
```bash
# Sigma to Suricata
sigma convert -t suricata -r rule.yml

# Sigma to plaintext (for custom engines)
sigma convert -t plaintext -r rule.yml
```

---

## 5. MITRE ATT&CK for ICS

**Website:** https://attack.mitre.org/versions/v18/tactics/ics/  
**Version:** v18.1 (current)  
**Format:** STIX JSON, PDF, web  

### ICS Tactics Relevant to IoT/Home

| Tactic ID | Name | Relevance to Home IoT |
|-----------|------|----------------------|
| TA0107 | Initial Access | Default creds, exploit, supply chain |
| TA0108 | Execution | Malware download, script execution |
| TA0109 | Persistence | Firmware backdoor, cron jobs |
| TA0110 | Privilege Escalation | Root access via vuln |
| TA0111 | Evasion | Process hiding, traffic obfuscation |
| TA0112 | Discovery | Network scanning, device enumeration |
| TA0113 | Lateral Movement | Device-to-device pivot |
| TA0114 | Collection | Data harvesting, traffic capture |
| TA0115 | Command and Control | C2 beaconing, DNS tunneling |
| TA0116 | Inhibit Response Function | Block alerts, disable monitoring |
| TA0117 | Impact | DDoS, data theft, ransomware |

### STIX Mappings for Vigil Home
MITRE provides ATT&CK in STIX 2.1 format. Vigil Home can map detection events to ATT&CK techniques:
```bash
# Download ATT&CK for ICS STIX
wget https://attack.mitre.org/stix/ics-attack/ics-attack.json
```

---

## 6. MISP Threat Intelligence Platform

**Website:** https://www.misp-project.org/  
**License:** AGPL v3 (open source)  
**GitHub:** https://github.com/MISP/MISP  

### Key Features
- Threat sharing platform (peer-to-peer)
- Automatic IOC correlation
- Built-in feed integration (CISA KEV, abuse.ch, etc.)
- Galaxy clusters for IoT devices, malware families
- Export to Suricata rules, YARA, STIX

### Quick Start
```bash
# Docker Compose (evaluation)
git clone https://github.com/MISP/MISP-docker.git
cd MISP-docker
docker-compose up -d

# Production deployment
# See: https://misp-project.org/INSTALL.txt
```

### IoT Configuration
- **MISP Galaxy:** `misp-galaxy/cluster/iot.json` - IoT device types
- **Default Feeds:** Enable abuse.ch, CISA KEV, Botvrij feeds
- **Correlation:** Enable CVE correlation for device vulnerability mapping

---

## 7. Shodan Tools & Utilities

### Official Tools

| Tool | Description | URL |
|------|-------------|-----|
| Shodan CLI | Command-line interface for Shodan API | `pip install shodan` |
| Shodan Python | Python library for Shodan API | `pip install shodan` |
| Shodan Monitor | Tracking personal device exposures | https://monitor.shodan.io/ |

### Shodan Search Examples (IoT Discovery)

```python
# Python: Find vulnerable devices
import shodan

api = shodan.Shodan('YOUR_API_KEY')

# Search for exposed IoT devices
results = api.search('port:554 product:RTSP "200 OK"')

# Search by CVE
results = api.search('vuln:CVE-2024-xxxx')

# Country-specific vulnerable routers
results = api.search('country:US port:23 product:Linux router')
```

---

## 8. IoT Device Identification

### MAC OUI Lookup

| Resource | URL | License |
|----------|-----|---------|
| Wireshark OUI DB | https://gitlab.com/wireshark/wireshark/-/raw/master/manuf | Open (GPL) |
| IEEE OUI Registry | https://standards-oui.ieee.org/oui/oui.txt | Open |
| MAC Vendors API | https://macvendors.co/ | Free API (limited) |

### Device Fingerprinting Libraries

| Library | URL | Description |
|---------|-----|-------------|
| p0f | https://github.com/p0f/p0f | Passive OS fingerprinting |
| Nmap | https://nmap.org/ | Active scanning + OS detection |
| masscan | https://github.com/robertdavidgraham/masscan | High-speed scanning |
| Zeek (Bro) | https://zeek.org/ | Network analysis framework with device profiling |
| NetBox | https://docs.netbox.dev/ | Device inventory management |

### IoT Search Engines (Alternative to Shodan)

| Engine | URL | Notes |
|--------|-----|-------|
| Censys | https://search.censys.io/ | Free tier available, good API |
| ZoomEye | https://www.zoomeye.org/ | Free tier, Chinese origin |
| FOFA | https://en.fofa.info/ | Free tier, Chinese origin |
| BinaryEdge | https://www.binaryedge.io/ | Subscription |

---

## 9. Botnet Analysis Tools

| Tool | URL | Description |
|------|-----|-------------|
| Mirai Source | https://github.com/jgamblin/Mirai-Source-Code | Reference implementation (study only) |
| Mirai Configuration Extractor | https://github.com/iij/mirai-toushi | Ghidra-based Mirai config extraction |
| Mozi Detector | Network analysis (signature-based) | P2P botnet detection |
| IoT Botnet Analysis | https://github.com/Hariru0x00/IoT-Botnet-Analysis | YARA rules + analysis tools |
| VirusTotal | https://www.virustotal.com/ | Malware hash lookup API |

---

## 10. Network Analysis Tools

### Traffic Analysis

| Tool | URL | Description | Relevance |
|------|-----|-------------|-----------|
| Zeek (Bro) | https://zeek.org/ | Network security monitoring framework | High — HTTP/DNS/SSL logging |
| tcpdump | Pre-installed on most systems | Packet capture | Essential |
| tshark | Wireshark CLI | Packet analysis | Essential |
| ntopng | https://www.ntop.org/ | Network traffic monitoring | Medium — GUI |
| Packetbeat | https://www.elastic.co/beats/packetbeat | Network data to Elasticsearch | Medium |

### Flow Analysis

| Tool | URL | Description |
|------|-----|-------------|
| nfdump | https://github.com/phaag/nfdump | NetFlow processing |
| SiLK | https://github.com/cert-tools/silk | Network flow analysis (CERT) |
| YAF | https://tools.netsa.cert.org/yaf/ | Yet Another Flowmeter |

### DNS Analysis

| Tool | URL | Description |
|------|-----|-------------|
| dnscap | https://github.com/DNS-OARC/dnscap | DNS traffic capture |
| dnstap | https://dnstap.info/ | DNS logging protocol |
| dnsdist | https://dnsdist.org/ | DNS load balancer + analysis |
| PassiveDNS | https://github.com/gamelinux/passivedns | Passive DNS recording |

---

## 11. Protocol Fuzzing & Security Testing

*For test/dev environments, not production monitoring.*

| Tool | URL | Protocols |
|------|-----|-----------|
| AFL++ | https://github.com/AFLplusplus/AFLplusplus | General fuzzer |
| Boofuzz | https://github.com/jtpereyda/boofuzz | Network protocol fuzzer |
| MQTT Fuzz | https://github.com/F-Secure/mqtt_fuzz | MQTT-specific |
| CoAP Fuzzer | Various | CoAP protocol |
| Z-Fuzz | https://github.com/amengel/Z-Fuzz | Zigbee fuzzer |

---

## 12. IoT-Specific Security Frameworks

| Framework | URL | Description |
|-----------|-----|-------------|
| OWASP IoT Top 10 | https://owasp.org/www-project-internet-of-things-top-10/ | Risk categorization |
| OWASP IoT Testing Guide | https://owasp.org/www-project-internet-of-things/ | Methodology |
| NIST IR 8228 | https://doi.org/10.6028/NIST.IR.8228 | IoT security guidance |
| ENISA: IoT Security | https://www.enisa.europa.eu/ | EU IoT security recommendations |
| IoT Security Foundation | https://www.iotsecurityfoundation.org/ | Best practices + compliance |

---

## 13. Default Credential Databases

| Database | URL | Format | Coverage |
|----------|-----|--------|----------|
| DefaultCreds Cheat Sheet | https://github.com/ihebski/DefaultCreds-cheat-sheet | CSV | 6K+ stars, comprehensive |
| CIRT.net Passwords | https://cirt.net/passwords | Web search | 1000+ devices |
| RouterPasswords.com | https://routerpasswords.com/ | Web search | Common router brands |
| AccessChecker | https://accesschecker.net/en | Web search | 1123 brands, 49391 creds |
| Defaultinator | https://defaultinator.com/ | API + web | 300+ devices |

---

## 14. Reference & Research Repos

| Repository | URL | Description |
|-----------|-----|-------------|
| IoT Scanners and Exploit Tools | https://github.com/villau/iot-exploits | IoT security research |
| IoT Security 101 | https://github.com/V33RU/IoTSecurity101 | Curated IoT security resources |
| Awesome IoT Security | https://github.com/fkie-cad/awesome-embedded-and-iot-security | Comprehensive list |
| Awesome Hacking IoT | https://github.com/nebgnahz/awesome-iot-hacks | IoT vulnerability repository |
| OWASP IoTGoat | https://github.com/OWASP/IoTGoat | Deliberately vulnerable IoT firmware |

---

## Recommendations for Vigil Home

### Must-Have (Production)
1. **Suricata** with Emerging Threats rules + IoT Hunter
2. **YARA** with signature-base IoT rules
3. **CISA KEV + abuse.ch** feeds (automated daily pull)
4. **MITRE ATT&CK for ICS** mapping for detection taxonomy
5. **MISP** for threat intelligence correlation

### Should-Have (Beta)
6. **Zeek** for HTTP/DNS/SSL analysis
7. **Sigma rules** for cross-platform detection portability
8. **MAC OUI database** for device identification
9. **Default credential database** for trust scoring

### Nice-to-Have (Future)
10. **MISP full instance** for TIP operations
11. **Shodan API integration** for external exposure assessment
12. **Custom fuzzing** for protocol anomaly detection
13. **Zeek-based device fingerprinting** for passive identification
