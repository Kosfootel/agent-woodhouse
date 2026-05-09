# ATTACK-PATTERNS.md — Behavioral Attack Patterns for Home Networks

**Last Updated:** 2026-05-06  
**Version:** 1.0  

---

## Table of Contents

1. [Attack Lifecycle for Home Networks](#1-attack-lifecycle-for-home-networks)
2. [Reconnaissance](#2-reconnaissance)
3. [Initial Access](#3-initial-access)
4. [Lateral Movement](#4-lateral-movement)
5. [Command & Control (C2)](#5-command--control-c2)
6. [Botnet Enrollment](#6-botnet-enrollment)
7. [Data Exfiltration](#7-data-exfiltration)
8. [Ransomware on Home Networks](#8-ransomware-on-home-networks)
9. [Cryptojacking on IoT](#9-cryptojacking-on-iot)
10. [Denial of Service](#10-denial-of-service)
11. [Physical & Proximity Attacks](#11-physical--proximity-attacks)
12. [Behavioral IoC Catalog](#12-behavioral-ioc-catalog)

---

## 1. Attack Lifecycle for Home Networks

Adapted from MITRE ATT&CK® for ICS and Enterprise, mapped to residential IoT context:

```
RECON → INITIAL ACCESS → LATERAL MOVEMENT → PERSISTENCE → C2 → IMPACT

Phase 1: Reconnaissance (passive/active)
Phase 2: Initial Access (default creds, CVE exploit, phishing)
Phase 3: Lateral Movement (device-to-device scanning)
Phase 4: Persistence (firmware backdoor, cron job, hardcoded account)
Phase 5: C2 (beaconing, DNS tunneling, MQTT overlay)
Phase 6: Impact (DDoS, data theft, ransomware, surveillance)
```

**Vigil Home Mapping:**
- **RECON →** Early trust decay signal (Whisper/Mention tier)
- **LATERAL →** Alert tier (containment)
- **C2 established →** Alarm tier (quarantine)
- **Impact occurring →** Alarm tier (automatic containment, homeowner notification)

---

## 2. Reconnaissance

### 2.1 External Port Scanning
**ATT&CK ID:** T0822 (External Remote Services — ICS), T1046 (Network Service Scanning — Enterprise)

**Pattern:** External IP conducts sequential or random port scans against the home's public IP.

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Sequential port probing from same source IP | High number of SYNs to closed ports | 🟡 Mention |
| Mass scans (Shodan, Censys) | Known scanner IP ranges | 🟢 Whisper |
| Targeted scanning (specific ports 22, 23, 80, 443, 3389) | Known attack probes | 🟠 Alert |
| UPnP/SSDP mapping queries | Unexpected WAN-side SSDP responses | 🟠 Alert |

**Normal Baseline:** Most home routers will see occasional scanner traffic. Vigil Home should baseline typical scan volume and alert on statistically significant increases.

### 2.2 Device Fingerprinting
**Pattern:** Attacker identifies IoT devices by their network signatures.

| Technique | Observable | Detection |
|-----------|-----------|-----------|
| MAC OUI lookup | Not directly observable | Monitor for unusual ICMP/ARP sweep patterns |
| mDNS/LLMNR queries | Device responds with name, model, services | 🟢 Whisper: First-seen mDNS responder |
| UPnP device description | `GET /description.xml` queries | 🟡 Mention: UPnP queries from new hosts |
| DHCP fingerprint analysis | Not directly observable (passive) | Hard to detect; focus on scanning behavior |
| HTTP User-Agent analysis | Requests with IoT-specific user agents | 🟠 Alert: Known scanner user agents |

### 2.3 Local Network Reconnaissance
**Pattern:** Compromised device scans the LAN for other targets.

| Indicator | Detection | Confidence |
|-----------|-----------|------------|
| ARP sweep from IoT device | High rate of ARP requests to sequential IPs | High - anomalous for most IoT devices |
| TCP SYN scan from IoT device | IoT device connecting to many ports on many hosts | High - IoT devices rarely port scan |
| ICMP sweep from IoT device | Pings to many hosts in quick succession | Medium |
| DNS reverse lookup bursts | PTR queries for many local IPs | Medium |
| SSDP/UPnP discovery from IoT | `M-SEARCH` broadcasts from non-hub device | High - UPnP hubs are known; other devices shouldn't |

**Vigil Home Rule:** Any IoT device conducting network scans is suspicious. Baseline: routers/hubs may scan. Exceptions: CleanSL8 authenticated agents, network management tools.

---

## 3. Initial Access

### 3.1 Default Credential Exploitation
**Pattern:** Attackers use credential dictionaries (commonly Mirai's built-in list of ~60 username/password pairs).

| Step | Observable |
|------|-----------|
| TCP connect to port 23/22/80/443 | SYN to management port |
| Authentication attempt | Telnet/SSH/HTTP auth traffic |
| Failed login bursts | Multiple auth failures in short period |
| Successful login | Session establishment on management port |

**Detection:** Monitor auth failure patterns. High rate of failures followed by success = credential brute-force succeeded.

**Mirai's credential list** (subset used globally):
```
root:root, root:admin, root:12345, root:password
admin:admin, admin:password, admin:1234, admin:(blank)
support:support, user:user, guest:guest
```

### 3.2 CVE Exploitation
**Pattern:** Automated exploit attempt targeting known vulnerabilities.

| Phase | Observable |
|-------|-----------|
| Probe | HTTP POST/GET with exploit payload in URI or body |
| Payload delivery | Outbound connection to download payload from attacker host |
| Execution | Anomalous process execution on IoT device |
| Callback | Connection to C2 server |

**Common IoT CVE exploitation vectors:**
- Router: UPnP SOAP buffer overflows
- Camera: RTSP/RTP protocol exploits
- NAS: SMB/WebDAV remote code execution
- Hub: Zigbee/Z-Wave protocol stack exploits

**Detection:** Monitor for known exploit payload signatures, anomalous outbound connections following inbound connection attempts.

### 3.3 Firmware Update Hijacking
**Pattern:** Man-in-the-middle of firmware update process.

| Step | Observable |
|------|-----------|
| Update check | DNS query to vendor update server |
| Redirection | DNS response pointing to different IP (DNS hijack) OR connection to non-vendor update server IP |
| Binary download | Unencrypted HTTP download from unexpected source |
| Flash write | Traffic indicating firmware blob transfer |

**Detection:** Alert on firmware downloads from non-vendor IPs. Monitor for unsigned or downgraded firmware versions.

---

## 4. Lateral Movement

### 4.1 Device-to-Device Pivot
**Pattern:** Compromised device A attacks device B on the same LAN.

**Common pivot paths:**
```
Camera → Router (SSH/telnet credential attack)
Smart TV → NAS (SMB vulnerability)
Thermostat → Smart Lock (Zigbee bridge abuse)
Smart Speaker → Smart Hub (local API abuse)
IoT Bridge → All connected IoT devices
```

**Detection for Vigil Home:**
- Baseline: Most IoT devices only talk to their cloud service(s) and hub
- Suspicious: Device A making more than X connections to Device B in Y minutes
- Suspicious: Device connecting to management ports of other devices
- High alert: Failed auth on any device originating from another IoT device

### 4.2 Router Compromise = Full Network Control
**Pattern:** Router is the crown jewel. Compromise grants attacker visibility into all traffic.

**Indicator chain:**
1. Router telnet/SSH login attempt (from WAN or compromised LAN device)
2. Router firmware change or config modification
3. DNS settings changed on router
4. Port forwarding rules modified
5. New VPN or remote access configured

**Detection for Vigil Home (critical):** Monitor router for:
- Configuration changes not initiated by homeowner
- DNS server IP changes
- Port forwarding creations/deletions
- New remote management users

### 4.3 Zigbee/Z-Wave Network Pivot
**Pattern:** Attacker compromises a Zigbee coordinator (hub/bridge) and uses the mesh protocol to attack other devices.

**Attack vectors:**
- Network key extraction (physical access to hub)
- Replay attacks against smart locks
- Pairing window hijacking
- Touchlink commissioning abuse (Zigbee)

**Detection:** Limited visibility on Zigbee/Z-Wave traffic for network-level monitors. Focus on hub behavior — anomalous pairing activity or unexpected hub firmware changes.

---

## 5. Command & Control (C2)

### 5.1 HTTP/HTTPS Beaconing
**Most common C2 pattern for IoT malware.**

| Indicator | Behavior | Detection |
|-----------|----------|-----------|
| Periodic HTTPS to same IP | Regular intervals (±variance) | Beaconing detection algorithm |
| User-Agent anomalies | Non-browser UA from IoT device | Suspicious — IoT device connecting to web server |
| Known-bad IP/Domain | C2 blocklist match | Immediate alarm |
| Dynamic DNS domain | Connection to DDNS hostname | Suspicious (legitimate usage exists) |
| Long URI with encoded data | HTTP GET `/?id=xxxx&cmd=yyyy` | Suspicious — potential C2 polling |

**Beaconing detection formula:**
```
Normalize connection intervals → calculate standard deviation
If σ < 0.3 × mean interval → potential beacon
If mean interval > 60 seconds → slow beacon
If mean interval < 60 seconds → fast beacon
```

### 5.2 DNS Tunneling
**Pattern:** C2 data encoded in DNS queries/responses.

| Indicator | Detection |
|-----------|-----------|
| High volume of DNS queries to same domain | DNS TXT/AAAA queries to single domain |
| Long subdomain strings | `base64encodedpayload.evil.com` |
| Unusual DNS record types | TXT, NULL, MX queries from IoT device |
| Non-existent domain queries (NXDOMAIN rate) | Attacker exfiltrating over NXDOMAIN responses |

**Vigil Home Detection:** Monitor DNS query entropy. Legitimate IoT DNS queries are short and predictable. High-entropy subdomains with regular intervals = potential DNS tunneling.

### 5.3 MQTT C2
**Pattern:** IoT malware uses existing MQTT infrastructure for C2.

| Indicator | Detection |
|-----------|-----------|
| IoT device subscribing to wildcard MQTT topic | MQTT SUBSCRIBE with `#` or `+/...` |
| Device publishing to unusual topics | MQTT PUBLISH to topics non-standard for that device |
| MQTT traffic to unknown broker | Connection to non-vendor broker |
| Encrypted payload in MQTT messages | Payload entropy analysis |

### 5.4 P2P C2 (Mozi-style)
**Pattern:** Mozi botnet uses distributed hash table (DHT)-based P2P network — no central C2 server.

| Indicator | Detection |
|-----------|-----------|
| DHT traffic from IoT device | Unusual UDP traffic to many peers on port 19652 |
| P2P keepalive messages | Regular small UDP packets to distributed IPs |
| Encrypted P2P payloads | High-entropy UDP payloads |

**Detection complexity:** Hard to distinguish from legitimate P2P traffic (torrents, gaming). Mozi typically targets specific ports (19652).

### 5.5 WebSocket C2
**Pattern:** Malware uses WebSockets over HTTP(S) for persistent bidirectional communication.

| Indicator | Detection |
|-----------|-----------|
| Upgrade: websocket header from IoT device | HTTP Upgrade header to specific endpoints |
| Persistent TCP connection from IoT | Long-lived TCP, unusual for most IoT devices |
| WebSocket to non-vendor endpoint | Unexpected WebSocket destination |

---

## 6. Botnet Enrollment

### 6.1 Mirai-Style Enrollment
**Standard pattern for most IoT botnets:**

```
Phase 1: Scanner finds vulnerable device (port 23/22 open)
Phase 2: Brute-force default credentials
Phase 3: wget/tftp download of malware binary
Phase 4: Execution (architecture-aware payload)
Phase 5: Kill competing botnet processes
Phase 6: Hide process (process name spoofing)
Phase 7: Connect to C2 / begin scanning
```

**Detection per phase:**

| Phase | Observable | Detection Timing |
|-------|-----------|-----------------|
| Scanning | ARP sweep + TCP SYNs from device | ✅ Real-time |
| Brute-force | Telnet/SSH auth failures from internal device | ✅ Real-time |
| Binary download | HTTP/TFTP connection to IP in suspicious range | ✅ Real-time |
| Execution | Anomalous process creation (limited visibility) | ❌ OS-level |
| Process killing | Connection termination patterns | ⚠️ Log-based |
| C2 connect | Beaconing detection | ✅ Real-time |

### 6.2 Murdoc Botnet Enrollment (2025 Variant)
**Source:** Qualys TRU, Jan 2025

**Exploited targets:** AVTECH Cameras, Huawei HG532 routers

**Detection indicators:**
- Exploit pattern: HTTP POST to specific vulnerable endpoints
- Payload: shell script downloading Mirai binary via wget/curl/tftp
- C2: Hardcoded C2 IP in malware binary
- Scanning: Port 23/2323 telnet scanning from infected device

### 6.3 BadBox Botnet Enrollment
**Target:** Android-based IoT devices (TV boxes, Android Things devices)

**Mechanism:** Malicious firmware pre-installed at manufacturing stage — no exploit needed.

**Detection:** Pre-installed malware is difficult to detect at network level. Focus on:
- Anomalous outbound connections from Android IoT devices
- Ad fraud patterns (invisible ad clicks in traffic)
- Credential theft traffic

---

## 7. Data Exfiltration

### 7.1 DNS Exfiltration
**Pattern:** Data encoded in DNS queries.

**Detection:**
- High variance in DNS query lengths from a single device
- Regular NXDOMAIN responses followed by TXT queries
- Unusual TTL values in DNS responses

### 7.2 HTTP/HTTPS Exfiltration
**Pattern:** Data sent as HTTP POST body or encoded in GET parameters.

**Detection:**
- Large POST requests from devices that don't normally send large data
- Periodic uploads from IoT device to unknown endpoint
- Image/video upload from camera to non-vendor destination (high alert)

### 7.3 MQTT Data Exfiltration
**Pattern:** Device publishes sensitive data via MQTT topic.

**Detection:**
- Unusual MQTT publish frequency from device
- MQTT payload size inconsistent with normal heartbeat
- MQTT connection to non-vendor broker

---

## 8. Ransomware on Home Networks

### 8.1 NAS/Storage Ransomware
**Pattern:** Ransomware encrypts NAS files via SMB/NFS or direct attack.

| Attack Vector | Detection |
|--------------|-----------|
| SMB brute-force from LAN device | Multiple SMB auth failures |
| Direct NAS web admin exploitation | HTTP POST to admin endpoint |
| Router compromise → redirect to malicious NAS firmware | Router DNS change |
| USB drive infection → connected to NAS | Physical — requires OS-level detection |

**Vigil Home Detection:**
- High rate of file operations on NAS (volume monitoring)
- Changed SMB/NFS traffic patterns (encrypted vs. plain)
- NAS making connections to external C2 servers

### 8.2 IoT Device Ransomware (Emerging)
**Pattern:** Smart lock disabled, thermostat set to extreme temps, camera stream blocked.

**Detection:** Behavioral change notification — "Your smart lock has received an unexpected firmware update command."

---

## 9. Cryptojacking on IoT

**Pattern:** Malware uses IoT device CPU for cryptocurrency mining.

| Indicator | Detection | Confidence |
|-----------|-----------|------------|
| Sustained CPU-bound network activity | Device continuously receiving/transmitting | Medium - could be legitimate update |
| Connection to mining pool IPs | Stratum protocol on known pool ports | High - known pool IP databases |
| Power consumption increase | Not observable at network level | N/A |
| Device becoming unresponsive | Missing expected heartbeats | Medium |

**Detection for Vigil Home:** Maintain known mining pool IP list. Alert on any IoT device connecting to known pools. Stratum protocol (port 3333, 4444, 5555, etc.) from IoT devices is highly suspicious.

---

## 10. Denial of Service

### 10.1 Home Network as Attack Source
**Pattern:** Compromised IoT devices participate in DDoS attacks.

| DDoS Type | Observable Traffic | Detection |
|-----------|-------------------|-----------|
| SYN flood | High volume of SYN packets to single external host | 🔴 Anomalous outbound volume |
| UDP flood | High volume of UDP to random ports | 🔴 Unusual protocol pattern |
| DNS amplification | Small DNS queries resulting in large responses (spoofed src) | 🟠 SSDP/DNS response traffic |
| HTTP flood | Coordinated HTTP GETs to single target from multiple devices | 🟠 Coordinated traffic pattern |

**Vigil Home Detection:** Monitor outbound traffic volume per device. Alert on any device exceeding baseline by >5σ. High-volume outbound traffic is extremely anomalous for most IoT devices.

### 10.2 Home Network as Attack Target
**Pattern:** Attacker DDoS the home router to disrupt connectivity.

| Indicator | Detection |
|-----------|-----------|
| Saturation of inbound bandwidth | Interface utilization spike |
| Connection exhaustion | Router state table overflow |
| UPnP/SSDP reflection | Inbound SSDP responses from WAN |

---

## 11. Physical & Proximity Attacks

### 11.1 Evil Twin / Rogue AP
**Pattern:** Attacker sets up malicious Wi-Fi access point with same SSID.

| Indicator | Detection |
|-----------|-----------|
| New AP with same SSID | Duplicate BSSID for same SSID |
| Signal strength variance | Rogue AP typically has different signal pattern |
| DHCP server change | Different gateway IP from rogue AP |

**Vigil Home Detection:** Monitor for duplicate SSID announcements, unusual DHCP gateway changes.

### 11.2 Bluetooth Proximity Attacks
| Attack | Vector | Range |
|--------|--------|-------|
| BlueBorne | BT protocol stack vulnerability | ~10m |
| BLE Replay | Capture and replay BLE commands | ~10m |
| BLE Spoofing | Clone BLE MAC address of legitimate device | ~10m |

### 11.3 Zigbee Proximity Attacks
| Attack | Vector | Range |
|--------|--------|-------|
| Network key extraction | Physical access to coordinator | 0m (physical) |
| Replay attack | Capture Zigbee frames | ~100m |
| Touchlink attack | Force unauthenticated pairing | ~30m |

---

## 12. Behavioral IoC Catalog

### 12.1 Device Communication Baselines
*These baselines are starting points. In production, Vigil Home should learn device-specific baselines.*

| Device Type | Expected Cloud Comms | Expected Local Comms | Update Comms |
|------------|---------------------|---------------------|--------------|
| IP Camera | Vendor cloud, RTSP streams | Hub/bridge, NVR | Vendor update server |
| Smart TV | Content providers (Netflix, Hulu, etc.), vendor telemetry | DLNA/UPnP, remote app | Update server (monthly) |
| Smart Speaker | Voice cloud (AWS/GCP), music streaming | App control, mDNS | Update server (bi-weekly) |
| Smart Lock | Minimal cloud polling | Hub/bridge, BT | Update server (quarterly) |
| Thermostat | Vendor cloud (5-15 min intervals) | Hub/bridge | Update server (monthly) |
| Smart Bulb | Vendor cloud (polling) | Hub/bridge, BT | Update server (rare) |
| Smart Hub | Constant vendor cloud connection | All IoT device comms | Update server (monthly) |
| Solar Inverter | Energy monitoring cloud | Modbus to sensors | Update server (quarterly) |
| EV Charger | Charging platform cloud | N/A | Update server (quarterly) |

### 12.2 Suspicious Behavioral Indicators

| Indicator ID | Behavior | Severity | Device Types |
|-------------|----------|----------|-------------|
| B-001 | Device port scanning other LAN hosts | 🔴 High | Any IoT |
| B-002 | Device connecting to known C2 IP | 🔴 Critical | Any |
| B-003 | Device connecting to new cloud endpoint (never seen) | 🟠 Medium | Any |
| B-004 | Device active during configured quiet hours | 🟡 Medium | Non-critical IoT |
| B-005 | Device beaconing at regular intervals | 🟠 High | Any (post-compromise) |
| B-006 | Device downloading large binary | 🟠 High | Any IoT (potential malware) |
| B-007 | Device DNS querying for dynamic DNS domains | 🟡 Medium | Any |
| B-008 | Device communicating with multiple countries | 🟠 Medium | Non-cloud IoT |
| B-009 | Device MQTT subscribe to wildcard topic | 🔴 Critical | MQTT-capable |
| B-010 | Device firmware version changed/regressed | 🟠 High | Any |
| B-011 | Device sending large POST requests to unknown endpoint | 🟠 High | Cameras, speakers |
| B-012 | Device attempting SSH/telnet to router or other devices | 🔴 Critical | Any |
| B-013 | Device traffic volume >5σ from baseline | 🟠 High | All |
| B-014 | Multiple IoT devices exhibiting same anomaly simultaneously | 🔴 Critical | Widespread infection |
| B-015 | Device DNS queries to known malware domains | 🔴 Critical | Any |

### 12.3 Normal Behavioral Patterns (for anomaly comparison)

| Device Type | Normal Outbound Connections/Day | Normal Total Traffic/Day | Normal Protocols |
|------------|-------------------------------|------------------------|-----------------|
| Light bulb | 50-200 (short polling) | <10 MB | HTTPS, MQTT |
| Smart plug | 50-200 | <10 MB | HTTPS |
| Thermostat | 100-500 | 1-5 MB | HTTPS |
| Camera (cloud) | 500-2000 | 100 MB - 5 GB | RTSP, HTTPS, P2P |
| Camera (local NVR) | 50-100 | <5 MB (only control) | HTTP, local RTSP |
| Smart TV | 1000-5000 | 100 MB - 10 GB | HTTPS, DNS, HLS |
| Speaker | 200-1000 | 20-200 MB | HTTPS, gRPC, WebSocket |
| Router/AP | 1000-10000 | Variable | DNS, NTP, HTTPS |

---

## References

1. MITRE ATT&CK for ICS — https://attack.mitre.org/versions/v18/tactics/ics/
2. Mirai Botnet Source Code — Available on GitHub (for reference only)
3. Qualys TRU: Murdoc Botnet — Jan 2025
4. arXiv: Analyzing Mirai Variants — https://arxiv.org/abs/2508.01909
5. OWASP IoT Attack Surface Areas — https://owasp.org/www-project-internet-of-things/
6. Fortinet: Hide 'N Seek — router-to-smart-home attacks
7. Claroty Team82: Pwn2Own WAN-to-LAN exploits
