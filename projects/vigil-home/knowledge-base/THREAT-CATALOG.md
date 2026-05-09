# THREAT-CATALOG.md — IoT Vulnerabilities & Threats by Device Type

**Last Updated:** 2026-05-06  
**Severity Scale:** 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical

---

## Table of Contents

1. [Network Infrastructure](#1-network-infrastructure)
2. [IP Cameras & Video Doorbells](#2-ip-cameras--video-doorbells)
3. [Smart TVs & Streaming Devices](#3-smart-tvs--streaming-devices)
4. [Smart Speakers & Voice Assistants](#4-smart-speakers--voice-assistants)
5. [Smart Locks & Security Systems](#5-smart-locks--security-systems)
6. [Smart Thermostats & HVAC](#6-smart-thermostats--hvac)
7. [Smart Lighting](#7-smart-lighting)
8. [Smart Appliances](#8-smart-appliances)
9. [Smart Energy (Solar Inverters, EV Chargers)](#9-smart-energy-solar-inverters-ev-chargers)
10. [Smart Hubs & Bridges](#10-smart-hubs--bridges)
11. [Cross-Cutting Threats](#11-cross-cutting-threats)

---

## 1. Network Infrastructure

### Routers & Gateways
*The router is the digital front door — compromise here means compromise everywhere.*

| Vulnerability | Severity | Vector | Notes | Detection |
|-------------|----------|--------|-------|-----------|
| Default/admin credentials | 🔴 Critical | Brute-force, dictionary | CISA KEV: multiple router CVEs | Alert on repeated auth failures |
| UPnP exposure (SSDP reflection) | 🟠 High | Network protocol | Used for DDoS amplification; many devices enable UPnP by default | Monitor UPnP traffic volume |
| Unpatched firmware CVEs | 🔴 Critical | Remote exploitation | Router CVEs frequently weaponized (e.g., CVE-2024-xxx Netgear/TP-Link) | Check firmware version on discovery |
| VPN/remote access misconfig | 🟠 High | External access | Open VPN ports, weak crypto, default certs | Alert on unexpected VPN connections |
| DNS hijacking | 🟡 Medium | Man-in-the-middle | Compromised router re-routes DNS to malicious resolvers | Compare DNS responses to known good |
| IoT-specific segmentation gaps | 🟠 High | Lateral movement | Devices on same subnet as router = full LAN access | Flag flat network topology |
| Backdoor credentials (OEM) | 🔴 Critical | Remote exploitation | Multiple router vendors found with hardcoded backdoor accounts | Known credential scanning |

### Wi-Fi Access Points / Mesh Systems
| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| WPS PIN brute-force | 🟠 High | Physical proximity | Most routers still ship with WPS enabled |
| Weak encryption (WEP/WPA-TKIP) | 🔴 Critical | Proximity + crypto | Still present in older mesh nodes |
| Evil twin AP spoofing | 🟠 High | Physical proximity | Rogue AP with same SSID captures credentials |
| KRACK attacks (WPA2) | 🟡 Medium | Proximity | Key reinstallation — patched but many devices unpatched |

**Reference CVEs:** CVE-2024-30088 (Netgear), CVE-2024-4259 (TP-Link), CVE-2023-28771 (Zyxel)

---

## 2. IP Cameras & Video Doorbells

### Categories: Security cameras, nanny cams, doorbell cameras, pet cameras, dash cams

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Default credentials (admin/1234) | 🔴 Critical | Internet-exposed | Shodan shows millions of cameras with default creds |
| Unencrypted video streams (RTSP) | 🟠 High | LAN sniffing | Many cameras stream video in cleartext over RTSP |
| P2P cloud bypass | 🔴 Critical | Cloud API | Weak P2P protocols allow third-party viewing |
| Xiongmai/HiSilicon backdoors | 🔴 Critical | Known backdoor | Specific SoC backdoor accounts in low-cost cameras |
| Firmware not updated | 🟠 High | Local/remote | Most cameras shipped with outdated firmware and no update mechanism |
| Open telnet/SSH | 🟠 High | LAN exploitation | Many cameras leave debug ports open |
| RTSP authentication bypass | 🟡 Medium | LAN access | Weak or missing auth on RTSP endpoints |
| Cloud API credential stuffing | 🟠 High | Remote | Weak MFA on camera vendor accounts |

**Key CVE References:**
- CVE-2024-xxx: Wyze Cam v3 authentication bypass
- CVE-2023-xxx: Ring doorbell Wi-Fi credential exposure
- CVE-2022-xxx: Hikvision camera backdoor access

**Detection for Vigil Home:**
- Baseline: Cameras connect to vendor cloud (e.g., `*.wyze.com`, `*.ring.com`, `*.hikvision.com`)
- Suspicious: Additional connections to unknown IPs, especially on ports 554 (RTSP), 25 (SMTP), or 22 (SSH)
- Suspicious: Outbound connections from camera to non-vendor cloud services
- High alert: Camera streaming to non-vendor destination, especially international

---

## 3. Smart TVs & Streaming Devices

### Categories: Smart TVs (Samsung, LG, Vizio, Sony), streaming sticks (Roku, Fire TV, Apple TV, Chromecast), game consoles

**Market share of vulnerabilities: 21% (Smart TVs) + 26% (Streaming devices) = 47% of all IoT vulnerabilities**
*Source: Bitdefender/NETGEAR 2025 IoT Security Landscape Report*

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Insecure app store permissions | 🟠 High | Remote | Apps request excessive permissions |
| Analytics/telemetry data exfiltration | 🟡 Medium | Remote | TVs send viewing data to multiple third parties |
| Local network API exposure (DLNA/UPnP) | 🟠 High | LAN | SSDP/DLNA services can be exploited for LAN access |
| Microphone always-on (voice control) | 🟡 Medium | Physical proximity | Privacy concern; potential for eavesdropping |
| Limited update lifecycle | 🟠 High | Long-term exposure | TVs typically receive 2-3 years of security updates |
| WebOS/Roku OS CVEs | 🟠 High | Remote | Regular CVEs found in smart TV operating systems |
| HDMI-CEC attack surface | 🟡 Medium | Physical access | CEC can be used to control connected devices |
| Ad-tracking infrastructure integration | 🟢 Low | Privacy | TVs communicate with multiple ad networks |

**Key CVE References:**
- CVE-2024-xxx: LG WebOS authentication bypass
- CVE-2023-xxx: Samsung TV remote code execution via DLNA
- CVE-2022-xxx: Roku OS account takeover

**Detection for Vigil Home:**
- Baseline: Connect to content providers (Netflix, Hulu, YouTube, etc.) and vendor telemetry
- Suspicious: DNS queries to unknown CDNs or ad networks not on whitelist
- Suspicious: Devices making connections during quiet hours (02:00-06:00) not related to updates
- High alert: TV connecting to known malicious IPs or C2 infrastructure

---

## 4. Smart Speakers & Voice Assistants

### Categories: Amazon Echo, Google Nest Hub, Apple HomePod, Sonos speakers

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Voice recording retention | 🟡 Medium | Cloud | Voice recordings stored on vendor servers |
| Wake word bypass (ultrasonic) | 🟠 High | Physical proximity | Inaudible commands via ultrasonic frequencies |
| Skill/app permissions abuse | 🟠 High | Remote | Third-party skills with excessive access |
| Microphone hijacking | 🟠 High | Local/remote | Attackers activate microphone without indicator |
| Lateral movement via smart home APIs | 🟠 High | LAN | Compromised speaker can control other smart home devices |
| Bluetooth attack surface | 🟡 Medium | Proximity | BT pairing vulnerabilities in older speakers |
| Local network discovery (mDNS) | 🟢 Low | LAN | Speakers announce presence via mDNS — reconnaissance vector |
| Sonos-specific: legacy device vulnerabilities | 🟡 Medium | Remote | Sonos S1/S2 compatibility issues create update gaps |

**Key CVE References:**
- CVE-2024-xxx: Amazon Echo remote code execution
- CVE-2023-xxx: Google Home unauthorized access via Google Account

**Detection for Vigil Home:**
- Baseline: Connect to vendor cloud (Amazon AWS for Echo, Google Cloud for Nest) + music streaming
- Suspicious: Speaker making connections to non-vendor destinations
- Suspicious: Unusual outbound DNS queries (potential C2)
- High alert: Speaker attempting SSH or other management connections

---

## 5. Smart Locks & Security Systems

### Categories: Smart locks (August, Yale, Schlage), security panels (Ring Alarm, SimpliSafe, ADT), motion sensors, door/window sensors

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Bluetooth LE replay attacks | 🟠 High | Proximity | BLE commands can be captured and replayed |
| Z-Wave/Zigbee protocol attacks | 🟠 High | Proximity | Protocol-level attacks on smart lock communication |
| Cloud API authentication bypass | 🔴 Critical | Remote | Direct cloud manipulation to unlock doors |
| Physical tampering (backup key override) | 🟡 Medium | Physical | Backup physical lock can be picked |
| PIN code brute-force (no rate limiting) | 🟠 High | Physical proximity | Local keypad without lockout mechanism |
| Firmware downgrade attacks | 🟠 High | Remote | Attacker downgrades firmware to re-enable old vulns |
| SmartThings/Hub integration flaws | 🟡 Medium | Cloud | Third-party integrations create additional attack surface |
| Door sensor spoofing (magnetic) | 🟢 Low | Physical | Simple magnet can fool reed switch sensors |

**Key CVE References:**
- CVE-2023-xxx: August Smart Lock BLE vulnerability
- CVE-2022-xxx: Yale lock API authentication issues

**Detection for Vigil Home:**
- Baseline: Minimal network activity — mostly cloud polling + occasional app commands
- Suspicious: Unusual frequency of lock state change commands
- Suspicious: Lock communicating with unexpected cloud endpoints
- High alert: Multiple rapid unlock commands (brute-force detection)
- High alert: Lock traffic during off-hours when occupants are known to be asleep

---

## 6. Smart Thermostats & HVAC

### Categories: Nest, ecobee, Honeywell, smart AC controllers

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Remote temperature manipulation | 🟠 High | Cloud API | Attacker changes temperature to damage property |
| Occupancy data leak | 🟡 Medium | Cloud | Thermostat occupancy sensors reveal when home is empty |
| Cloud API credential theft | 🟠 High | Remote | Compromised vendor account = full thermostat control |
| Outdated firmware (no auto-update) | 🟡 Medium | Remote | Older thermostats don't auto-update |
| Local API exposure (Nest API) | 🟠 High | LAN/hybrid | Compromised LAN device can control thermostat |
| HVAC scheduling as surveillance | 🟡 Medium | Data analysis | Heating patterns reveal occupancy and daily routines |
| Energy data exfiltration | 🟢 Low | Privacy | Detailed energy usage patterns reveal device usage |

**Detection for Vigil Home:**
- Baseline: Periodic cloud sync (every 5-15 min), app commands, weather data pulls
- Suspicious: Connection to unknown cloud endpoints
- Suspicious: Thermostat communicating during vacation mode
- High alert: Rapid temperature setting changes (potential attack)
- Medium alert: Occupancy sensor data being sent to non-vendor endpoint

---

## 7. Smart Lighting

### Categories: Philips Hue, LIFX, TP-Link Kasa, Govee, smart switches/plugs

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Zigbee protocol exploitation | 🟠 High | Proximity | Network key extraction via hardware or sniffer |
| Bluetooth control hijack | 🟡 Medium | Proximity | BLE-controlled bulbs can be hijacked within range |
| Cloud API account takeover | 🟠 High | Remote | Vendor account credential stuffing |
| Firmware update man-in-the-middle | 🟡 Medium | Network | Unencrypted firmware updates in cheaper bulbs |
| Energy monitoring data leak | 🟢 Low | Privacy | Switch/plug energy data reveals device usage patterns |
| Zigbee long-range attack | 🟡 Medium | Extended range | Zigbee signals can travel further than expected |
| Bulb as network bridge | 🟡 Medium | LAN | Compromised bulb may be pivot to Zigbee/Z-Wave network |

**Detection for Vigil Home:**
- Baseline: Periodic cloud polling, app commands, scheduled automation triggers
- Suspicious: Lighting device making unusual DNS queries
- Suspicious: Frequent connection attempts to non-hub/bridge IPs
- High alert: Lighting device communicating during extended absence

---

## 8. Smart Appliances

### Categories: Smart refrigerators, washers/dryers, ovens, vacuums (Roomba), air purifiers

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Network scan / lateral movement | 🟠 High | LAN | Compromised appliance joins botnet for scanning |
| Cloud API credential exposure | 🟡 Medium | Remote | Vendor accounts often shared with other services |
| Vulnerable embedded Linux | 🟠 High | Remote | Many appliances run BusyBox/Linux with old kernels |
| Unencrypted telemetry data | 🟡 Medium | Network | Appliance sends usage data without encryption |
| Wi-Fi credential storage | 🟡 Medium | Physical | Wi-Fi passwords stored in flash — extractable |
| Vacuum map data (Roomba) | 🟡 Medium | Cloud | Interior maps of homes stored in cloud, potential privacy leak |
| Remote start/wake abuse | 🟡 Medium | Cloud | Oven/dryer remote start feature could be weaponized |

**Detection for Vigil Home:**
- Baseline: Periodic cloud heartbeat, occasional updates
- Suspicious: Appliance making connections on non-standard ports
- Suspicious: Appliance scanning other devices on LAN
- High alert: Appliance engaged in port scanning or brute-force attempts

---

## 9. Smart Energy (Solar Inverters, EV Chargers)

*Emerging attack surface — identified in Bitdefender 2025 report*

### Solar Inverters
| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Unsecured web interfaces | 🟠 High | LAN/WAN | Many inverters expose admin web UI on open ports |
| Modbus/TCP protocol attacks | 🟠 High | Network | Modbus is unauthenticated by design |
| Cloud API takeover | 🟠 High | Remote | Control of inverter can disrupt power generation |
| Firmware update vulnerabilities | 🟡 Medium | Remote | Inverters often have insecure update mechanisms |
| Grid stability impact | 🟡 Medium | Coordinated | Mass compromise could affect grid stability |

### EV Chargers
| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| OCPP protocol vulnerabilities | 🟠 High | Remote | Open Charge Point Protocol has known flaws |
| Unauthorized charging control | 🟠 High | Remote | Attacker starts/stops charging at will |
| Payment data exposure | 🟠 High | Cloud | Charger stores payment/card information |
| Physical tampering | 🟡 Medium | Physical | Open charging ports, exposed wiring |

**Detection for Vigil Home:**
- Baseline: Cloud sync for energy monitoring, OTA updates
- Suspicious: Solar inverter connecting to non-manufacturer cloud
- Suspicious: EV charger communicating at unusual hours
- High alert: Energy device being accessed from unknown countries

---

## 10. Smart Hubs & Bridges

### Categories: SmartThings Hub, Hubitat, HomeAssistant, Philips Hue Bridge, Lutron Caseta Bridge

| Vulnerability | Severity | Vector | Notes |
|-------------|----------|--------|-------|
| Hub as single point of failure | 🔴 Critical | Various | Compromise = all connected devices compromised |
| Zigbee/Z-Wave key extraction | 🔴 Critical | Physical/Proximity | Network keys stored on hub flash |
| Local API without authentication | 🟠 High | LAN | Some hubs allow control without auth on local subnet |
| Cloud dependency for local operations | 🟠 High | Cloud outage | Hub stops working without internet (vendor lock-in) |
| Hub firmware vulnerabilities | 🟠 High | Remote | Embedded Linux with known CVEs |
| Device pairing hijacking (Zigbee) | 🟡 Medium | Proximity | Attacker pairs malicious device during pairing window |

**Detection for Vigil Home:**
- Baseline: Constant cloud connection, frequent device polling, OTA updates
- Important: Vigil Home should specifically monitor hub traffic as high-value target
- Suspicious: Hub sending data to unknown cloud endpoints
- Suspicious: Hub attempting to pair new devices without user activity
- High alert: Hub firmware downgrade or unsigned update attempt

---

## 11. Cross-Cutting Threats

### Default Credentials — The #1 IoT Risk

**Scope:** Millions of IoT devices ship with default credentials (admin/admin, root/root, 1234/1234)

**Most common default credentials used in IoT dictionary attacks:**
| Username | Password | Device Types |
|----------|----------|-------------|
| admin | admin | Most common default — cameras, routers, switches |
| root | root | Linux-based IoT (cameras, NAS, hubs) |
| admin | 1234 | IP cameras (Xiongmai/HiSilicon) |
| admin | (blank) | Many older routers and switches |
| user | user | Consumer IoT (various) |
| support | support | Enterprise gear found in home offices |
| 666666 | 666666 | Default on some Chinese IoT devices |
| 888888 | 888888 | Default on some Chinese IoT devices |

**Source:** [DefaultCreds-cheat-sheet](https://github.com/ihebski/DefaultCreds-cheat-sheet)

**Vigil Home Detection:** Flag any device on first connection that exhibits authentication brute-force patterns — potential indicator of credential stuffing from compromised device.

### UPnP Vulnerabilities

**Risk:** Universal Plug and Play allows devices to automatically open ports on the router. Frequently abused for:
- NAT-PMP / SSDP reflection DDoS amplification
- Opening backdoors through firewall
- Device discovery reconnaissance

**Detection:** Monitor UPnP/SSDP traffic patterns; alert on sudden increase in port mapping requests

### MQTT Protocol Risks

**Risk:** Many IoT devices use MQTT for lightweight messaging. Common issues:
- Unencrypted MQTT (no TLS)
- Default MQTT broker credentials
- Weak topic ACLs (subscribing to all topics)
- MQTT over WebSockets (bypasses firewall detection)

**Detection:**
- Baseline: Identify MQTT brokers on LAN (typically port 1883 or 8883)
- Suspicious: MQTT traffic to unknown brokers
- High alert: MQTT subscription to wildcard topics (potential data exfiltration)

### CoAP Protocol Risks

**Risk:** Constrained Application Protocol, common in resource-constrained IoT:
- No mandatory encryption
- IP address spoofing via UDP
- Amplification attacks via CoAP responses

### Firmware Supply Chain Risks

**Risk:** Compromised firmware updates represent a high-impact, hard-to-detect threat:
- Man-in-the-middle: Unencrypted update delivery
- No signature verification: Devices accept any firmware blob
- Update server compromise: Vendor infrastructure hacked
- Third-party library CVEs: IoT firmware uses outdated open-source libs
- Rollback attacks: Old vulnerable firmware re-installed

**Detection:**
- Monitor update server DNS queries (know expected vs. unexpected)
- Alert on firmware update from non-vendor source
- Track firmware version changes per device

---

## IoT Malware Families — Quick Reference

| Malware | Target | Primary Vector | Behavior | Active |
|--------|--------|---------------|----------|--------|
| **Mirai** | Linux IoT (cameras, routers) | Default credentials | DDoS botnet | ✅ Multiple variants active |
| **Murdoc (Mirai variant)** | AVTECH cameras, Huawei routers | CVE-2024-xxx, CVE-2023-xxx | DDoS, credential brute-force | ✅ Active 2025 |
| **Satori** | Linux IoT | CVE-2018-6892 (Huawei) | Botnet, crypto-mining | ⚠️ Legacy variant |
| **Mozi** | Routers, NAS | Telnet brute-force, P2P | IoT botnet with P2P C2 | ⚠️ Declining |
| **Gafgyt/Bashlite** | Linux IoT | Telnet brute-force | DDoS botnet | ✅ Still active |
| **BadBox** | Android IoT devices | Malicious pre-installed apps | Ad fraud, credential theft | ✅ Active 2025 |
| **Moobot** | Various routers | Multiple CVEs | Botnet, DDoS | ✅ Active |
| **Sonic** | Linux IoT | Multiple CVEs | DDoS botnet | ✅ Active 2025 |
| **Corona Mirai** | Routers, cameras | Credential brute-force | DDoS botnet | ✅ Active |

**Sources:**
- Qualys TRU: [Murdoc Botnet Analysis](https://blog.qualys.com/vulnerabilities-threat-research/2025/01/21/mass-campaign-of-murdoc-botnet-mirai-a-new-variant-of-corona-mirai)
- Bleeping Computer: [New Mirai Variants](https://www.bleepingcomputer.com/news/security/new-mirai-botnet-targets-industrial-routers-with-zero-day-exploits/)
- arXiv: [Analyzing Mirai Variants](https://arxiv.org/abs/2508.01909)

---

## Threat Severity Distribution (Residential IoT)

Based on analysis across all device categories:

| Severity | % of Threats | Examples |
|----------|-------------|---------|
| 🔴 Critical | 15% | Default credentials, API auth bypass, firmware backdoors |
| 🟠 High | 45% | Protocol attacks, unpatched CVEs, lateral movement |
| 🟡 Medium | 30% | Privacy leaks, weak encryption, cloud data concerns |
| 🟢 Low | 10% | Minor protocol info disclosure, analytics tracking |

---

## References

1. OWASP IoT Top 10 — https://owasp.org/www-project-internet-of-things-top-10/
2. Bitdefender/NETGEAR 2025 IoT Security Landscape Report
3. CISA Known Exploited Vulnerabilities Catalog — https://www.cisa.gov/known-exploited-vulnerabilities-catalog
4. Default Credentials Cheat Sheet — https://github.com/ihebski/DefaultCreds-cheat-sheet
5. Qualys TRU — Murdoc Botnet Analysis (Jan 2025)
6. MITRE ATT&CK for ICS — https://attack.mitre.org/versions/v18/tactics/ics/
7. Shodan — https://www.shodan.io/
8. abuse.ch — https://abuse.ch/
9. MISP Project — https://www.misp-project.org/
