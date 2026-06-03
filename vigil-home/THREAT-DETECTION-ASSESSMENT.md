# Vigil Home — Threat Detection Assessment

**Date:** 2026-05-09  
**Author:** Security Engineering Review  
**Version:** 1.0  
**Scope:** Detection pipeline — Suricata IDS consumer, statistical anomaly detection (z-score), Bayesian trust scoring, device classification, narrative generation.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Detection Architecture](#2-current-detection-architecture)
3. [Capability-by-Capability Assessment](#3-capability-by-capability-assessment)
4. [Attack Vector Coverage](#4-attack-vector-coverage)
5. [Gap Analysis](#5-gap-analysis)
6. [Recommended Detection Rules & Configurations](#6-recommended-detection-rules--configurations)
7. [Implementation Priorities (P0/P1/P2)](#7-implementation-priorities-p0p1p2)
8. [Sample Detection Scenarios](#8-sample-detection-scenarios)
9. [False Positive Reduction Strategy](#9-false-positive-reduction-strategy)
10. [Recommended Tooling & Methodology Upgrades](#10-recommended-tooling--methodology-upgrades)
11. [Appendix: Suricata Ruleset Reference](#11-appendix-suricata-ruleset-reference)

---

## 1. Executive Summary

Vigil Home's detection pipeline consists of three layers:

| Layer | Technology | Strength | Weakness |
|-------|-----------|----------|----------|
| **Signature-based** | Suricata IDS (eve.json consumer) | Well-established, community rulesets exist | No custom IoT-targeted rules configured; default Suricata tuning absent |
| **Statistical anomaly** | Z-score on a single numeric feature (bytes per flow) with sliding window | Simple, adaptive baseline, well-tested | Univariate only; 1-feature proxy metric misses protocol, timing, and behavioural shifts |
| **Trust scoring** | Bayesian Beta(α, ω) with exponential decay | Principled calibration, handles evidence accumulation and time decay | Neutral initial trust (0.5) is aggressive for unknown IoT devices; no integration with external threat intelligence |

**Overall maturity: Early POC / Alpha.** The foundations are sound but detection coverage is narrow. The system currently detects:

- ✅ Suricata signature matches (whatever default ruleset is active)
- ✅ Unusual per-flow byte volumes (single univariate z-score)
- ✅ Trust score changes driven by Suricata alert severity (no independent trust logic)

**Critical gaps** include: no botnet/C2 detection, no behavioural baselines per device type, no protocol-aware anomaly detection, no multi-vector correlation, no external threat intel feeds, and no custom IoT-targeted Suricata rules.

---

## 2. Current Detection Architecture

### 2.1 Data Flow

```
Suricata (eve.json)
    │
    ▼
tail_eve_json()              ← polls /var/log/suricata/eve.json every 2s
    │
    ▼
process_eve_line()
    │
    ├──▶ _get_or_create_device()   → Device model, MAC OUI + hostname classification
    │
    ├──▶ _extract_anomaly_value()  → bytes_toserver + bytes_toclient (or netflow.bytes)
    │       │
    │       ▼
    │   AnomalyDetector.record()   → z-score check (window=100, z_threshold=3.0)
    │
    ├──▶ event_type dispatch:
    │       alert → creates Alert + generates narrative + emails if critical/high
    │       dns   → creates Event, flags non-NOERROR as low severity
    │       http  → creates Event, flags 4xx as low severity
    │       flow  → creates Event (info)
    │       tls   → creates Event (info)
    │       netflow → creates Event (info)
    │       *     → creates Event (info)
    │
    └──▶ _update_trust_score()     → Bayesian TrustModel update
         based on severity: high/critical → negative, info/low → positive
```

### 2.2 Key Configuration Constants

| Parameter | File | Value | Assessment |
|-----------|------|-------|------------|
| `window_size` | `anomaly.py` → `detection.py` | 100 observations | Moderate — OK for high-traffic devices, too slow to adapt for low-traffic ones |
| `z_threshold` | `anomaly.py` → `detection.py` | 3.0 | Conservative (3σ = ~0.3% false positive rate under Gaussian); reasonable starting point |
| `min_samples` | `anomaly.py` | max(10, window//10) = 10 | Too low for meaningful baseline; 30 would be minimum |
| `half_life` | `trust.py` / `detection.py` | 86,400s (1 day) | Reasonable for consumer IoT; may be too slow for active attack scenarios |
| `poll_interval` | `detection.py` | 2.0s | Acceptable; real-time enough for post-compromise detection |
| Initial trust score | `models.py` / `trust.py` | 0.5 | **Problematic**: new unknown devices start at neutral trust |

---

## 3. Capability-by-Capability Assessment

### 3.1 AnomalyDetector — `app/ai/anomaly.py`

**What it does well:**
- Clean sliding-window implementation with `collections.deque`
- Proper minimum-sample guard (`min_samples`)
- Adaptive baseline — old observations slide out naturally
- Returns structured `AnomalyResult` with all diagnostics
- Well-tested (17 unit tests covering edge cases)

**Critical weaknesses:**
1. **Univariate only** — operates on a single float. The `_extract_anomaly_value()` in `detection.py` reduces a complex Suricata record to `total_bytes` per flow. This misses:
   - Protocol changes (e.g., MQTT → unknown TCP)
   - Connection rate anomalies (connections/hour spikes)
   - Packet size distribution changes
   - Timing anomalies (off-hours activity)
   - DNS query patterns (NXDOMAIN bursts, random subdomain queries)

2. **One model per device, one feature per model** — there's no multivariate detector. A smart bulb that starts beaconing to a C2 server on an unusual port at a slightly higher but sub-3σ byte volume would be missed.

3. **Gaussian assumption** — z-scores assume normal distribution. IoT traffic is often multimodal (e.g., a camera at idle vs. streaming). A single mean/std captures neither state well.

4. **No concept of device-type baselines** — a Wyze cam and a smart plug share the same z-score logic. Their baseline traffic differs by 3+ orders of magnitude.

5. **Window sizing problem** — fixed at 100 for all devices. A sensor that generates one flow every 5 minutes would take ~8 hours to build a baseline. A camera generating 500 flows/minute would adapt too fast.

### 3.2 TrustModel — `app/ai/trust.py`

**What it does well:**
- Mathematically principled (Beta distribution / Bayesian updating)
- Built-in time decay via exponential half-life
- Evidence-weight tracking via `certainty` property
- Well-tested (15 unit tests)

**Critical weaknesses:**
1. **Initial neutral trust (0.5) is too permissive** — a brand-new, unknown device starts with 50% trust. For IoT environments, unknown devices should start at 0.2–0.3 until positively observed for a learning period.

2. **No integration with external threat intelligence** — trust score cannot be influenced by known-bad IPs, domains, or hash feeds. If `device.trust_score` drops, no action is taken beyond logging.

3. **Trust update is driven entirely by Suricata alert severity** — not by independent behavioural signals. A device performing slow, stealthy reconnaissance that never triggers a Suricata alert will maintain a high trust score indefinitely.

4. **No threshold-based enforcement** — there's no code that isolates or alerts when `trust_score` falls below a threshold (e.g., 0.2). The narrative generator references `threshold=0.3` in its template context, but nothing acts on it.

5. **Half-life of 1 day is fixed** — different IoT device classes need different decay rates. A temperature sensor that speaks once per hour needs a much longer half-life than a streaming stick that's constantly active.

### 3.3 DeviceClassifier — `app/ai/classifier.py`

**What it does well:**
- MAC OUI lookup for 50+ common IoT vendors
- Behavioural signature matching with weighted scoring
- Clean `Classification` dataclass

**Weaknesses:**
- OUI database is hardcoded and static — needs periodic updates
- Behavioural signatures assume single-device-per-type; many IoT devices share the same chipset (ESP32)
- No learning from observed behaviour — signatures are static rules, not ML models

### 3.4 Event/Alerts — `app/models.py`

**Strengths:**
- Clean schema, JSON-backed `details` field for extensibility
- `Event` and `Alert` separation is appropriate (event log vs. actionable alert)

**Weaknesses:**
- No `mitre_attack_id` or other threat-intel enrichment fields on Alert
- No `resolved_at` or `acknowledged_by` fields on Alert (operational gap)
- No `baseline_model_snapshot` on Device to compare current vs. historical behaviour

### 3.5 Suricata Consumer — `app/detection.py`

**Strengths:**
- Correct async tailing of eve.json
- Graceful handling of missing file, JSON parse errors, and device creation
- Email alerts for critical/high severity events
- Narrative generation adds context

**Weaknesses:**
1. **No Suricata configuration or ruleset management** — the code assumes Suricata is already running with some ruleset. There's no reference to which rules are loaded, no custom IoT rules, and no ruleset update mechanism.

2. **Single-feature anomaly metric** — `_extract_anomaly_value()` only uses total bytes, missing protocol, connection rate, timing, DNS, TLS, and HTTP-level anomalies.

3. **No rate limiting or alert deduplication** — if Suricata fires the same alert 1,000 times, Vigil creates 1,000 Alerts and sends 1,000 emails.

4. **Thread safety** — `_anomaly_detectors` and `_trust_models` dicts are not thread-safe (though the thread is single, so this is dormant).

5. **Passive-only** — no IPS mode, no active blocking or quarantine capability.

6. **No event correlation across devices** — each device is assessed independently. A coordinated attack across multiple IoT devices (e.g., Mirai scanning) would generate independent alerts with no cross-device linkage.

---

## 4. Attack Vector Coverage

### 4.1 Covered (Green)

| Attack Vector | How Detected | Confidence |
|---------------|-------------|------------|
| Known exploit attempts | Suricata signature match | ✅ High (if up-to-date ruleset) |
| High-volume DDoS participation | AnomalyDetector (byte volume spike) | 🟡 Medium (univariate) |
| Large-scale data exfiltration | AnomalyDetector (byte volume spike) | 🟡 Medium |
| Known C2 domain requests | Suricata DNS signature | 🟡 Medium (depends on ruleset) |
| Widespread port scanning | Suricata detection | 🟡 Medium (depends on ruleset) |

### 4.2 Partially Covered (Yellow)

| Attack Vector | Gap | Impact |
|---------------|-----|--------|
| Mirai-style telnet/ssh brute forcing | Suricata can detect individual attempts, but correlation of distributed brute force across many IPs is missing | 🟡 High — Mirai is the #1 IoT threat |
| Covert C2 beaconing (low-and-slow) | Won't trigger 3σ byte-volume anomaly; no independent connection-rate or timing baseline | 🟡 High |
| Firmware downgrade / malicious OTA | Detected only if Suricata has a specific rule for the CVE | 🟡 Medium |
| DNS tunneling / data exfiltration over DNS | Suricata can detect known-bad domains; Vigil's DNS handler only checks rcode | 🟡 Medium |

### 4.3 Not Covered (Red)

| Attack Vector | Why Missed | Priority |
|---------------|-----------|----------|
| **Device impersonation / MAC spoofing** | No MAC-to-physical-port binding; no DHCP fingerprinting | P0 |
| **Off-hours device activation** | No time-based baseline per device | P0 |
| **New protocol / port usage** | No "first-seen protocol" tracking per device | P0 |
| **Slow DDoS (Mirai variant)** | Per-device anomaly may not see aggregate effect; cross-device correlation needed | P0 |
| **Random subdomain DGA detection** | No entropy analysis on DNS queries | P1 |
| **CoAP/DTLS amplification attack** | No protocol-specific traffic shape detection | P1 |
| **BLE/Zigbee proxy attacks** | Not on wired network path (requires dedicated capture) | P1 |
| **Router/DNS hijack** | No validation of DNS responses vs. known good resolvers | P1 |
| **mDNS/SSDP reflection** | No multicast traffic analysis | P2 |
| **Physical tampering / device removal** | No keepalive or heartbeat baseline | P2 |

---

## 5. Gap Analysis

### 5.1 Detection Engineering Gaps

| # | Gap | Severity | Root Cause |
|---|-----|----------|------------|
| G1 | No custom IoT Suricata ruleset | **Critical** | No rules/ directory, no suricata.yaml configuration shipped with Vigil |
| G2 | No multi-feature anomaly detection | **High** | `_extract_anomaly_value` extracts only total bytes |
| G3 | No behavioural baselines per device type | **High** | All devices share same window=100, z=3.0 |
| G4 | No device-type-specific trust half-life | **Medium** | All TrustModels use fixed half_life=86400 |
| G5 | No time-of-day baseline | **Medium** | No per-device activity window tracking |
| G6 | No cross-device correlation | **Medium** | Each device assessed independently |
| G7 | No threat intel feeds | **High** | No AlienVault OTX, MISP, or STIX integration |
| G8 | No alert deduplication / suppression | **Medium** | Every Suricata alert creates a DB record + potential email |
| G9 | No active response (block/quarantine) | **Medium** | Detection only, no IPS or SDN integration |
| G10 | No ruleset update mechanism | **High** | Suricata rules are static at deployment |

### 5.2 Architectural Gaps

| # | Gap | Severity | Recommendation |
|---|-----|----------|----------------|
| A1 | Single consumer process (no HA) | Medium | Multi-worker with file locking or message queue |
| A2 | eve.json filesystem polling | Low | Switch to Unix socket or dedicated log forwarder (Filebeat) |
| A3 | No event retention policy | Medium | Add TTL-based event pruning to DB |
| A4 | No metrics / observability | Medium | Add Prometheus counters for alerts, anomalies, trust changes |

---

## 6. Recommended Detection Rules & Configurations

### 6.1 Suricata Ruleset Strategy

**Tier 1 — Essential (P0, deploy immediately):**

| Ruleset | Source | Purpose |
|---------|--------|---------|
| `emerging-malware.rules` | ET Open | General C2, botnet, malware |
| `emerging-dos.rules` | ET Open | DDoS detection |
| `emerging-trojan.rules` | ET Open | Trojan/backdoor C2 |
| `emerging-scan.rules` | ET Open | Port scanning, service discovery |
| `emerging-telnet.rules` | ET Open | Telnet brute force (Mirai vector) |
| `emerging-dns.rules` | ET Open | DNS abuse, tunneling, DGA |

**Tier 2 — IoT-specific (P1, add next):**

| Ruleset | Source | Purpose |
|---------|--------|---------|
| `emerging-scada.rules` | ET Open | SCADA/industrial — overlaps with IoT |
| `emerging-policy.rules` | ET Open | Policy violations (IoT devices using non-standard ports) |
| IoT-Hunter generated rules | ET `iot-hunter` tool | CVE-specific IoT device exploits |
| Custom vigil-iot.rules | Self-authored | See Section 6.2 |

**Tier 3 — Supplemental (P2):**

| Ruleset | Source | Purpose |
|---------|--------|---------|
| `emerging-web_server.rules` | ET Open | Web attacks on IoT management interfaces |
| `emerging-smtp.rules` | ET Open | Spam from compromised devices |
| `emerging-voip.rules` | ET Open | VoIP attacks (if SIP devices present) |

### 6.2 Custom Vigil Suricata Rules (vigil-iot.rules)

```suricata
# ── Vigil Home - Custom IoT Detection Rules ─────────────────────
#
# Purpose: Detect IoT-specific threats not covered by default rulesets
# Target: Consumer/SMB IoT environments
#

# 1. MIRAI-STYLE TELNET BRUTE FORCE
# Detects rapid telnet login attempts from an internal device
# (compromised IoT device scanning for more victims)
alert tcp $HOME_NET any -> $EXTERNAL_NET 23 (
    msg:"VIGIL IoT - Potential Mirai telnet brute force from internal device";
    flow:to_server,established;
    content:"|0d 0a|Login|3a|"; nocase;
    threshold:type both, track by_src, count 30, seconds 60;
    classtype:attempted-recon;
    sid:5000001; rev:1;
    metadata:severity high, device_type any;
)

# 2. RAPID SUCCESSIVE CONNECTIONS TO KNOWN C2 PORTS
# IoT device connecting to many unique IPs on common C2 ports
alert tcp $HOME_NET any -> $EXTERNAL_NET [80,443,8080,8443,4444,6667,31337] (
    msg:"VIGIL IoT - Rapid outbound connections (potential C2 beacon)";
    flow:to_server;
    detection_filter:track by_src, count 20, seconds 10;
    classtype:trojan-activity;
    sid:5000002; rev:1;
    metadata:severity high, device_type any;
)

# 3. DNS QUERY BURST (DGA / domain generation algorithm)
# Device making many DNS queries to unique domains in short window
alert dns $HOME_NET any -> any any (
    msg:"VIGIL IoT - DNS query burst (potential DGA or fast-flux)";
    dns.query; content:!"."; within:1;  # TLD-only queries
    detection_filter:track by_src, count 50, seconds 10;
    classtype:unknown;
    sid:5000003; rev:1;
    metadata:severity medium, device_type any;
)

# 4. IOT DEVICE TALKING TO KNOWN MALICIOUS IP
alert ip $HOME_NET any -> [185.220.101.0/24, 5.188.62.0/24, 23.129.64.0/24] any (
    msg:"VIGIL IoT - Connection to known malicious IP range";
    classtype:trojan-activity;
    sid:5000004; rev:1;
    metadata:severity critical;
)

# 5. UNUSUAL PROTOCOL USAGE FROM SMART HOME DEVICES
# E.g., a smart bulb using SSH or RDP
alert tcp $HOME_NET [22,23,3389,5900,445,135] -> $EXTERNAL_NET any (
    msg:"VIGIL IoT - Unusual outbound protocol from IoT device";
    flow:to_server;
    classtype:policy-violation;
    sid:5000005; rev:1;
    metadata:severity medium, device_type "smart_plug|smart_light|sensor";
)

# 6. NON-STANDARD DNS (encrypted DNS detection)
alert tcp $HOME_NET any -> $EXTERNAL_NET 853 (
    msg:"VIGIL IoT - DNS over TLS from IoT device (unusual)";
    flow:to_server;
    classtype:policy-violation;
    sid:5000006; rev:1;
    metadata:severity low;
)

# 7. SSDP / UPnP REFLECTION AMPLIFICATION
# Device being used as amplifier in DDoS
alert udp any 1900 -> $HOME_NET any (
    msg:"VIGIL IoT - SSDP response to non-local address (amplification)";
    content:"200 OK"; nocase;
    classtype:bad-unknown;
    sid:5000007; rev:1;
    metadata:severity high;
)

# 8. HTTP BRUTE FORCE / CREDENTIAL STUFFING
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"VIGIL IoT - Multiple auth failures on IoT web interface";
    http.response_body; content:"Login failed"; nocase;
    detection_filter:track by_src, count 10, seconds 30;
    classtype:attempted-user;
    sid:5000008; rev:1;
    metadata:severity high;
)
```

### 6.3 Suricata Configuration Recommendations

Place in `suricata.yaml`:

```yaml
# ── Vigil Home Suricata Configuration ──────────────────────────────

# Rulesets
default-rule-path: /etc/suricata/rules
rule-files:
  - emerging-malware.rules
  - emerging-dos.rules
  - emerging-telnet.rules
  - emerging-trojan.rules
  - emerging-scan.rules
  - emerging-dns.rules
  - emerging-scada.rules
  - emerging-policy.rules
  - vigil-iot.rules              # Custom rules above

# Performance tuning for consumer hardware
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes

# Reduce false positives in consumer environments
vars:
  address-groups:
    HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    SMTP_SERVERS: "$HOME_NET"
    DNS_SERVERS: "$HOME_NET"

# Stream engine
stream:
  memcap: 32MB
  checksum-validation: yes
  inline: no                 # IDS mode (passive) for consumer safety

# Thresholding to reduce noise
threshold-file: /etc/suricata/threshold.config

# Eve JSON output
eve-log:
  enabled: yes
  filetype: regular
  filename: /var/log/suricata/eve.json
  types:
    - alert
    - http
    - dns
    - tls
    - flow
    - netflow
```

### 6.4 Threshold Configuration (threshold.config)

```ini
# Suppress "ET SCAN Potential SSH Scan" after 10 alerts per source per hour
suppress gen_id 1, sig_id 2001219, track_by_src, count 10, seconds 3600

# Suppress repeated DNS NXDOMAIN alerts from the same device
suppress gen_id 1, sig_id 2008000, track_by_src, count 20, seconds 60

# Rate-limit all alerts per device to max 100/hour
threshold gen_id 1, sig_id 5000001, type threshold, track by_src, count 30, seconds 60
threshold gen_id 1, sig_id 5000002, type threshold, track by_src, count 20, seconds 10
```

---

## 7. Implementation Priorities (P0/P1/P2)

### P0 — Critical (Ship-blocking gaps)

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| P0-1 | **Multi-feature anomaly detection** — add connection rate, protocol entropy, off-hours activity, DNS query volume as parallel anomaly metrics | 3-4 days | Single-byte-volume z-score misses most IoT attacks |
| P0-2 | **Custom IoT Suricata ruleset** — create `vigil-iot.rules` (Section 6.2) and integrate into deployment | 1 day | Zero IoT-specific detection currently |
| P0-3 | **Alert deduplication** — implement threshold-based alert suppression (track by device + signature over time window) | 1 day | Prevents alert storms and email spam |
| P0-4 | **Device-type-specific baseline parameters** — window size, z-threshold, and trust half-life per device class | 2 days | A camera and a sensor need radically different baselines |
| P0-5 | **Initial trust score for unknown devices = 0.2** instead of 0.5 | 0.5 day | Current neutral trust is too permissive |

### P1 — High (Major capability gaps)

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| P1-1 | **Time-of-day baseline** — per-device activity window tracking; alert on activity outside expected hours | 2 days | Off-hours activation is a key IoT compromise indicator |
| P1-2 | **First-seen protocol/port tracking** — flag when a device uses a protocol it's never used before | 1 day | Protocol change is a strong behavioural anomaly signal |
| P1-3 | **Threat intelligence feed integration** — pull from AlienVault OTX or MISP; enrich alerts with IP/domain reputation | 3-4 days | Transforms "connection to 1.2.3.4" into "connection to known C2" |
| P1-4 | **Cross-device correlation** — detect coordinated behaviour (e.g., 5 devices simultaneously scanning) | 3 days | Needed for DDoS precursor detection |
| P1-5 | **Suricata ruleset auto-update** — daily fetch of latest ET Open rules | 1 day | Stale rules = missed detections |
| P1-6 | **Alert lifecycle management** — acknowledge, resolve, snooze; add `mitre_attack_id` field | 2 days | Operational best practice |
| P1-7 | **Trust-score-based isolation trigger** — when score < 0.2, auto-create quarantine rule or notification | 2 days | Turns trust scoring into an actionable control |

### P2 — Enhancement (Long-term improvements)

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| P2-1 | **DNS entropy analysis** — detect DGA/random subdomain queries | 3 days | Detects modern IoT malware C2 |
| P2-2 | **MAC spoofing detection** — track MAC-to-IP mapping changes; flag rapid changes | 1 day | Device impersonation vector |
| P2-3 | **Machine learning classifier** — replace static behavioural signatures with learned models (e.g., Isolation Forest per device) | 5-7 days | Adaptive, multi-dimensional baselines |
| P2-4 | **Prometheus metrics exporter** — alert count, anomaly rate, trust distribution | 1 day | Observability and health monitoring |
| P2-5 | **Passive DNS integration** — log DNS answers and correlate with known-threat domains | 2 days | Retrospective detection of past compromise |
| P2-6 | **Event retention and data lifecycle** — auto-purge events older than 90 days | 0.5 day | Database growth management |
| P2-7 | **BLE/Zigbee capture integration** — sniff side channel for non-IP IoT devices | TBD | Extends coverage beyond IP-based devices |

---

## 8. Sample Detection Scenarios

### Scenario 1: "Smart bulb begins beaconing to C2"

**Device:** Philips Hue bulb (192.168.1.42)  
**Normal behaviour:** MQTT to hue bridge (192.168.1.10), occasional HTTPS to meethue.com, ~0.5 kbps average, 2–5 connections/hour, active hours 06:00–23:00 UTC  
**Attack:** Bulb is compromised via CVE-2024-XXXX; it begins beaconing to a remote C2 on TCP 8443 every 60 seconds

**What current Vigil detects:**
```
❌ Slight byte volume increase (~1 kbps) — below 3σ threshold
❌ TLS to unknown IP — logged, severity=info, no alert
✅ No Suricata signature match (no rule for this C2 IP/domain)
❌ Trust score remains near 0.5 (no high-severity alerts generated)
```

**What Vigil *should* detect (after P0/P1 implementation):**
```
✅ "First-seen" protocol: device never used TLS before (was MQTT-only)
✅ Off-hours activity: beaconing at 03:00 (outside 06:00–23:00 window)
✅ New destination: IP 185.220.101.50 is in known malicious range (vigil-iot.rules sid:5000004)
✅ Trust score drops below 0.3 → auto-notification
✅ Cross-device: no other devices contacting this IP (suspicious)
```

**Alert narrative:** *"Living Room Bulb is active at 03:14 — unusual for this device. It's using TLS for the first time, connecting to an IP in a known malicious range. Trust score: 0.28. Recommendation: Isolate the device from the network."*

---

### Scenario 2: "Wyze cam participating in DDoS"

**Device:** Wyze Cam v3 (192.168.1.50)  
**Normal behaviour:** RTSP to local NVR, HTTPS to wyze.com, ~1 Mbps inbound/300 kbps outbound  
**Attack:** Cam is recruited into Mirai botnet; begins sending SYN floods to external target on port 80

**What current Vigil detects:**
```
✅ Byte volume anomaly: outbound traffic surges from 300 kbps to 4 Mbps
   → z-score ≈ 8.0 → AnomalyResult(is_anomaly=True)
✅ Connection rate anomaly (if multi-feature added in P0-1): 
   20 connections/min → 2,000 connections/min
```

**What's currently missing (P0 gaps):**
```
❌ No alert deduplication: 2,000 anomalous flows → 2,000 Alert DB records
❌ No cross-device correlation: can't tell if other devices are also surging
❌ No active response: device continues participating until manual intervention
```

---

### Scenario 3: "Credential stuffing on router admin panel"

**Device:** Unknown external IP → Vigil-protected router (192.168.1.1:443)  
**Normal behaviour:** Occasional admin logins from LAN  
**Attack:** External attacker brute-forces router admin password via WAN

**What current Vigil detects:**
```
✅ Suricata alert from HTTP 401 detection → severity=high
✅ Email notification sent
✅ Trust score drops on affected device
```

**What's missing:**
```
❌ No geolocation enrichment: "Login attempt from 5 known hostile IPs in Russia"
❌ No cross-device: "Same IPs also scanned your Nest camera"
❌ No progressive response: "3 attempts → log, 10 → alert, 50 → auto-block"
```

---

### Scenario 4: "Silent reconnaissance via DNS"

**Device:** ESP32-based sensor (192.168.1.77)  
**Normal behaviour:** Reports temperature via MQTT every 5 minutes to local broker; two DNS queries/hour  
**Attack:** Attacker enumerates internal network by forcing device to resolve random domains (DNS tunneling / reconnaissance)

**What current Vigil detects:**
```
❌ Byte volume unchanged (~200 bps) — no anomaly
❌ DNS queries logged but at severity=info
❌ Trust score unchanged (no high-severity events)
```

**What Vigil *should* detect (after P1 implementation):**
```
✅ DNS query rate: 2/hour → 300/hour → behavioural anomaly (connection rate feature)
✅ DNS entropy: "asdf1234.malicious.com" has high entropy → DGA suspicion
✅ NXDOMAIN rate: 90% of queries return NXDOMAIN → DNS tunneling indicator
```

---

## 9. False Positive Reduction Strategy

False positives are the #1 reason consumer security products get uninstalled. Vigil must be conservative.

### 9.1 Tiered Threshold Configuration

| Tier | Z-Score Threshold | Alert Action | Use Case |
|------|-------------------|-------------|----------|
| Green | < 2.0 | Log only, no alert | Normal variation |
| Yellow | 2.0–3.5 | Alert with severity=low | Suspicious; log in dashboard |
| Orange | 3.5–5.0 | Alert with severity=medium | Likely incident; email notification |
| Red | > 5.0 | Alert with severity=high/critical | Confirm incident; immediate action |

*Current single threshold (3.0) lumps yellow and orange together. Three-zone approach reduces noise.*

### 9.2 Device-Type-Specific Baselines

Each device class gets tuned parameters:

| Device Type | Window | z-Threshold | Min Samples | Trust half-life | Notes |
|------------|--------|-------------|-------------|-----------------|-------|
| Camera | 500 | 3.5 | 50 | 12h | High variable traffic; need higher threshold |
| Smart Plug | 50 | 3.0 | 20 | 48h | Low traffic; longer baseline window |
| Smart Speaker | 200 | 3.0 | 30 | 24h | Bursty traffic (voice commands) |
| Sensor | 30 | 2.5 | 15 | 72h | Very low traffic; faster reaction needed |
| Streaming | 300 | 4.0 | 40 | 6h | Highly variable bandwidth |
| Unknown | 100 | 3.0 | 30 | 24h | Conservative defaults |

### 9.3 Cooldown / Suppression Rules

- **Per-Device Alert Cooldown:** Maximum 1 alert per device per 5 minutes for the same `alert_type`.
- **Per-Signature Global Cooldown:** Maximum 1 email per signature ID per 10 minutes.
- **Dedup Window:** If a device generates 50 identical events in 60 seconds, coalesce into one alert with `count=50`.
- **Learning Mode:** First 24 hours of a new device generate info-only events (no alerts, no emails).

### 9.4 User Feedback Loop

- Allow users to mark alerts as "false positive" in dashboard
- Track FP rate per rule signature
- Auto-disable rules with >90% FP rate after 30 days
- Whitelist: allow users to whitelist specific IPs, domains, or device signatures

---

## 10. Recommended Tooling & Methodology Upgrades

### 10.1 Short-term (P0/P1)

| Tool/Method | Purpose | Effort |
|-------------|---------|--------|
| **Multi-feature anomaly detector** | Replace single z-score with parallel detectors: bytes, connections, protocols, DNS rate, timing | 3 days |
| **Adaptive z-threshold** | Compute threshold dynamically from observed percentiles (e.g., 99.7th percentile) instead of fixed 3.0 | 1 day |
| **Seasonal baseline** | Track per-hour-of-day mean/std (e.g., 24 separate baselines) for time-of-day awareness | 2 days |
| **ET Open auto-update cron** | Daily `curl` of emerging.rules.tar.gz → extract → reload Suricata | 0.5 day |

### 10.2 Medium-term (P1/P2)

| Tool/Method | Purpose | Effort |
|-------------|---------|--------|
| **Isolation Forest per device** | Multi-dimensional anomaly detection (bytes, connections, protocols, timing, DNS) | 5 days |
| **AlienVault OTX integration** | IP/domain/hash reputation lookup on alert creation | 2 days |
| **Alert aggregation engine** | Similar-event grouping + severity escalation | 3 days |
| **Prometheus + Grafana** | Real-time dashboard of detection stats, trust scores, device health | 2 days |

### 10.3 Long-term (Post-P2)

| Tool/Method | Purpose |
|-------------|---------|
| **Federated learning** | Anomaly models that learn from aggregate behaviour across Vigil instances without sharing raw data |
| **Honeytoken injection** | Deploy fake IoT devices / credentials to detect lateral movement |
| **Packet-level ML inference** | On-device ML model (e.g., Edge TPU) for real-time classification of every flow |

---

## 11. Appendix: Suricata Ruleset Reference

### Recommended ET Open Rulesets

| Ruleset File | URL | Coverage |
|-------------|-----|----------|
| `emerging-telnet.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-telnet.rules` | Telnet brute force, Mirai scanning |
| `emerging-dos.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-dos.rules` | DDoS attack signatures |
| `emerging-malware.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-malware.rules` | General malware C2 |
| `emerging-trojan.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-trojan.rules` | Trojan/backdoor C2 |
| `emerging-scan.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-scan.rules` | Network reconnaissance |
| `emerging-dns.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-dns.rules` | DNS abuse |
| `emerging-policy.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-policy.rules` | Policy violations |
| `emerging-scada.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-scada.rules` | SCADA/IoT device exploits |
| `emerging-web_server.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-web_server.rules` | Web server attacks |
| `emerging-exploit.rules` | `https://rules.emergingthreats.net/open/suricata/rules/emerging-exploit.rules` | Known exploit attempts |

### ET Open Download

```bash
# Download and extract the full ET Open ruleset
VERSION="7.0.6"  # Update to latest Suricata version
curl -LO "https://rules.emergingthreats.net/open/suricata-${VERSION}/emerging.rules.tar.gz"
tar -xzf emerging.rules.tar.gz -C /etc/suricata/rules/
```

### IoT-Hunter Tool

The [Emerging Threats IoT-Hunter](https://github.com/EmergingThreats/iot-hunter) tool generates Suricata rules for specific IoT CVEs. Integrate into the release pipeline:

```bash
git clone https://github.com/EmergingThreats/iot-hunter.git
# Generate rules from CSV of known IoT vulnerabilities
python IoT_hunter.py -i known_iot_vulns.csv -o vigil-iot-supplement.rules
```

---

## Summary

Vigil Home has a solid architectural foundation — clean separation of concerns, well-tested AI modules, and a correct Suricata integration pattern. The core gaps are **not architectural but capability-driven**: the anomaly detector is dangerously narrow (univariate byte-volume only), there are no custom IoT Suricata rules, trust scoring has no enforcement mechanism, and the system lacks correlation, threat intel, and deduplication.

The P0 recommendations (multi-feature anomaly detection, custom ruleset, deduplication, device-type-aware baselines, trust score recalibration) close the most critical gaps and can be implemented in approximately 7-10 engineering days.

The system is not yet ready for a consumer-facing beta due to the high false-positive risk from univariate anomaly detection and the near-total inability to detect stealthy C2 beaconing, DGA, off-hours compromise, and credential stuffing — the four most common IoT attack patterns.
