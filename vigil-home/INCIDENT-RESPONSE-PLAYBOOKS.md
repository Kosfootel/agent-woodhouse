# Vigil Home — Incident Response Playbooks
*Structured security response for consumer/SMB IoT networks*

**Version:** 1.0  
**Date:** 2026-05-09  
**Status:** Draft — awaiting implementation

---

## Table of Contents

1. [Philosophy & Approach](#1-philosophy--approach)
2. [Alert Severity Classification Matrix](#2-alert-severity-classification-matrix)
3. [Alert Lifecycle](#3-alert-lifecycle)
4. [Containment Capabilities & Decision Tree](#4-containment-capabilities--decision-tree)
5. [Escalation Flow](#5-escalation-flow)
6. [Incident Type Playbooks (5)](#6-incident-type-playbooks)
7. [Communication Templates](#7-communication-templates)
8. [Dashboard & Notification Integration](#8-dashboard--notification-integration)
9. [Post-Incident Review Template](#9-post-incident-review-template)
10. [Future Capabilities Roadmap](#10-future-capabilities-roadmap)

---

## 1. Philosophy & Approach

### Design Principles

| Principle | Description |
|-----------|-------------|
| **No false alarm is free** | Every unnecessary alert erodes trust. Prioritize signal-to-noise over coverage. |
| **Default: inform, don't block** | Vigil is a guardian, not a warden. Auto-block only when certainty is extremely high. |
| **Explainable actions** | Every recommendation comes with a plain-English "why" and "what happens next." |
| **Respect the owner's choice** | Technical users get controls; family members get safety confirmation. |
| **Graceful escalation** | Start with notification, escalate to actionable, reserve isolation for worst case. |

### Response Tiers

Vigil supports three tiers of response, determined by severity and certainty:

| Tier | Name | Description | Who Acts |
|------|------|-------------|----------|
| 1 | **Inform & Monitor** | Notify user, log event, track for patterns. No active intervention. | Vigil (auto) |
| 2 | **Recommend Action** | Escalate with specific recommendation. User must approve network-level actions. | User |
| 3 | **Auto-Contain** | Isolate or block when certainty is extremely high and risk warrants immediate action. | Vigil (auto, with undo) |

---

## 2. Alert Severity Classification Matrix

### Severity Levels

```
CRITICAL  ┃ 🚨 ┃ Active compromise — isolate immediately
HIGH      ┃ 🔴 ┃ Likely malicious — investigate now  
MEDIUM    ┃ 🔶 ┃ Suspicious — investigate soon
LOW       ┃ ⚠️  ┃ Mildly unusual — monitor
INFO      ┃ ℹ️  ┃ Informational — no action needed
```

### Classification Criteria

| Factor | INFO | LOW | MEDIUM | HIGH | CRITICAL |
|--------|------|-----|--------|------|----------|
| **Z-score (anomaly)** | < 2.0 | 2.0–3.0 | 3.0–5.0 | 5.0–8.0 | > 8.0 |
| **Trust score** | > 0.7 | 0.5–0.7 | 0.3–0.5 | 0.15–0.3 | < 0.15 |
| **Trust delta (24h)** | ±0.05 | -0.1 | -0.2 | -0.3 | -0.4 |
| **Known C2 indicator** | — | — | — | DNS hit | Direct connect |
| **Auth failures (in 5m)** | 0 | 1 | 2–3 | 4–10 | >10 |
| **New protocol on device** | — | Incidental | Service discovery | Data channel | C2 protocol |
| **Multi-device correlation** | Isolated | 1 device | 2 devices | 3–5 devices | >5 devices |
| **Lateral movement** | None | 1 conn | 2–5 conn | ARP scan | Port sweep |
| **Known malware pattern** | — | Weak score | Partial match | Strong match | Confirmed |

### Severity → Response Mapping

| Severity | Notification | Dashboard | Auto-Action | User Action Required |
|----------|-------------|-----------|-------------|---------------------|
| **INFO** | None (logged) | Count in summary | None | None |
| **LOW** | Optional silent push | Alert list entry | None | Review within 24h |
| **MEDIUM** | Email + dashboard toast | Alert list + device highlight | None | Review within 1h |
| **HIGH** | Immediate email + SMS/push | Alert popup + device blink | Recommend isolation | Acknowledge within 15m |
| **CRITICAL** | Immediate email + SMS + phone alert | Full-screen alert + siren | Auto-isolate device + rate-limit | Acknowledge within 5m or escalate |

### Severity Determination Rules

```
severity = max(
    anomaly_severity(device),
    trust_severity(device),
    threat_intel_severity(ip, domain, pattern),
    multi_device_severity()
)

Where each sub-function maps input ranges to {INFO, LOW, MEDIUM, HIGH, CRITICAL}
as defined in the matrix above.
```

---

## 3. Alert Lifecycle

```
                 ┌──────────┐
                 │  Event   │
                 └────┬─────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ Anomaly Detection   │
            │ & Severity Scoring  │
            └──────────┬──────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
       ┌────────────┐   ┌──────────────┐
       │ Below      │   │ Above        │
       │ threshold  │   │ threshold    │
       └────────────┘   └──────┬───────┘
              │                 │
              ▼                 ▼
       ┌────────────┐   ┌──────────────────┐
       │ Logged     │   │ Alert Created     │
       │ (no alert) │   │ Severity Assigned │
       └────────────┘   └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌────────────────┐       ┌──────────────────┐
            │ Auto-Response  │       │ Auto-Response    │
            │ (Inform &      │       │ (Containment)    │
            │  Recommend)    │       │ if CRITICAL/HIGH │
            └────────┬───────┘       └────────┬─────────┘
                     │                        │
                     ▼                        ▼
              ┌──────────────┐        ┌────────────────┐
              │ User Acknowledges │        │ Device Isolated  │
              │ (or timeout)      │        │ (auto + undo)    │
              └────────┬──────────┘        └────────┬─────────┘
                       │                            │
                       ▼                            ▼
              ┌────────────────────┐      ┌─────────────────┐
              │ Investigation      │      │ Investigation   │
              │ Phase              │      │ Phase (post-    │
              │                    │      │  isolation)     │
              └────────┬───────────┘      └────────┬────────┘
                       │                            │
                       ▼                            ▼
              ┌────────────────────┐      ┌─────────────────┐
              │ Resolution:        │      │ Resolution:     │
              │ - False positive   │      │ - Re-image      │
              │ - Accept risk      │      │ - Block IP      │
              │ - Restrict device  │      │ - Replace device│
              └────────┬───────────┘      └────────┬────────┘
                       │                            │
                       ▼                            ▼
              ┌─────────────────────────────────────────┐
              │ Alert Closed / Resolved                  │
              │ (with classification tag: FP / Benign /  │
              │  Malicious / Mitigated)                  │
              └─────────────────────────────────────────┘
```

### Lifecycle States

| State | Description | Transitions |
|-------|-------------|-------------|
| **NEW** | Alert created, user not notified yet | → NOTIFIED |
| **NOTIFIED** | User has been alerted via configured channels | → ACKNOWLEDGED, → ESCALATED (timeout) |
| **ACKNOWLEDGED** | User seen the alert | → INVESTIGATING, → DISMISSED |
| **INVESTIGATING** | User is looking into it | → RESOLVED, → MITIGATED |
| **CONTAINED** | Auto or manual isolation active | → INVESTIGATING, → RESOLVED |
| **DISMISSED** | False positive or accepted risk | → (closed) |
| **MITIGATED** | Action taken, device restored or restricted | → (closed) |
| **RESOLVED** | Root cause addressed, all clear | → (closed) |

---

## 4. Containment Capabilities & Decision Tree

### Current Capabilities (V1)

Vigil operates at the network observation layer. Containment options in V1 are:

| Capability | Level | How | Auto? | Undo? | Notes |
|------------|-------|-----|-------|-------|-------|
| **Alert only** | Notification | Email + dashboard | Yes | N/A | Default for MEDIUM and below |
| **Dashboard isolation request** | Recommend | Button in device detail | No | — | User clicks "Isolate" |
| **Rate-limit device** | Network | iptables `hashlimit` module | Auto (CRITICAL) | Yes (auto-expire 1h) | Limits connections/min |
| **Full device isolation** | Network | iptables DROP rule (MAC) | Auto (CRITICAL), Manual (HIGH) | Yes (1-click restore) | Blocks all L3+ traffic |
| **Block destination IP** | Network | iptables REJECT rule | Manual | Yes | Only for confirmed C2 / malicious egress |
| **DNS sinkhole** | Network | Local DNS override → 0.0.0.0 | Manual | Yes | For known-bad domains |

### Future Capabilities (V2+)

| Capability | Level | Auto? | Requires |
|------------|-------|-------|----------|
| **VLAN quarantine** | Network | Manual | OpenFlow/Managed switch API |
| **Device certificate revocation** | Device | Auto | PKI + device support |
| **Wireless de-auth** | Network | Auto | Managed AP API (Ubiquiti, etc.) |
| **SmartThings/HomeKit integration** | Device | Auto | Vendor API tokens |
| **Quarantine SSID** | Network | Manual | Dual-SSID capable AP |
| **ARP spoofing block** | Network | Auto | Vigil on gateway only |

### Containment Decision Tree

```
┌─────────────────────────────────────────────────────┐
│                 ALERT FIRED                         │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
           Do any of these apply?
           ┌──────────────────────┐
           │ • Known C2 beacon    │
           │ • Active data        │
           │   exfiltration       │
           │ • >10 auth failures  │
           │   in 5 min           │
           │ • Trust < 0.15       │
           │   AND z-score > 8    │
           └───────┬──────┬───────┘
                   │      │
          YES      │      │ NO
                   │      │
                   ▼      ▼
       ┌──────────────────┐  ┌────────────────────────┐
       │ CRITICAL         │  │ Severity < CRITICAL    │
       │ Path: Auto-      │  │ Path: User Decision    │
       │ Contain          │  │                         │
       └────────┬─────────┘  └───────────┬─────────────┘
                │                        │
                ▼                        ▼
       ┌──────────────────┐  ┌────────────────────────┐
       │ 1. Rate-limit     │  │ Is the device type     │
       │    device (1h)   │  │ high-risk?              │
       │ 2. Isolate if    │  │ (camera, lock, unknown) │
       │    data xfer     │  └──────┬──────────┬───────┘
       │    > 50MB/min    │        YES        NO
       │ 3. Notify user   │         │          │
       │    immediately   │         ▼          ▼
       └──────────────────┘  ┌──────────┐  ┌──────────────┐
                │            │ MEDIUM/  │  │ LOW/INFO     │
                ▼            │ HIGH     │  │ Alert only   │
       ┌──────────────────┐  │ Recommend│  │ Log & monitor│
       │ User must:       │  │ isolate  │  └──────────────┘
       │ - Acknowledge    │  └──────────┘
       │   within 5 min   │        │
       │ - Or auto-undo   │        ▼
       │   isolation if   │  ┌─────────────────────┐
       │   no response    │  │ User action:        │
       │ - Can re-enable  │  │ - Accept risk       │
       │   device from    │  │ - Isolate           │
       │   dashboard      │  │ - Rate-limit        │
       └──────────────────┘  └─────────────────────┘
```

### Containment Action Details

#### Rate-Limit
```yaml
action: rate_limit
target: device
method: iptables hashlimit
parameters:
  limit: "10/sec"
  burst: 20
  expire_after: 3600  # seconds (1 hour)
effect: Drops packets exceeding rate. Device stays online but slow.
undo: Auto-expires after 1 hour, or user clicks "Remove Limit" in dashboard.
risks: May cause legitimate device to malfunction if rate limit is too low.
```

#### Full Isolation
```yaml
action: isolate
target: device
method: iptables DROP (by MAC)
parameters:
  direction: both  # ingress and egress
  persist: false   # not across reboot (for now)
effect: Device can't communicate with anything on network or internet.
undo: 1-click "Reconnect" on dashboard. Removes iptables rule.
risks: Device will show as offline. May miss legitimate security updates.
```

#### Block Destination
```yaml
action: block_ip
target: ip_address
method: iptables REJECT
parameters:
  protocol: any
  chain: FORWARD
effect: All traffic to/from that IP is blocked for all devices.
undo: 1-click "Unblock" on dashboard.
risks: May be a shared hosting IP — could block legitimate services.
```

#### DNS Sinkhole
```yaml
action: dns_sinkhole
target: domain
method: Local DNS override → 0.0.0.0
effect: DNS queries for that domain resolve to nothing. Blocks at DNS layer.
undo: Remove override via dashboard.
risks: Device may retry aggressively. Not effective against direct IP connections.
```

---

## 5. Escalation Flow

### User-Facing Escalation

```
         ┌──────────────────────┐
         │ Alert Created        │
         │ Severity: MEDIUM+    │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
  ┌──────────────┐    ┌──────────────────┐
  │ User online  │    │ User offline /   │
  │ in dashboard │    │ not responding   │
  └──────┬───────┘    └────────┬─────────┘
         │                     │
         ▼                     ▼
  ┌──────────────┐    ┌──────────────────┐
  │ Dashboard    │    │ Email escalation │
  │ notification │    │ chain:           │
  │ sent         │    │ 1. Email (0m)    │
  └──────┬───────┘    │ 2. SMS/Push      │
         │            │    (3m no ack)   │
         ▼            │ 3. Phone call    │
  ┌──────────────┐    │    (10m no ack)  │
  │ User         │    │ 4. Auto-isolate  │
  │ acknowledges │    │    (15m no ack)  │
  │ within       │    └──────────────────┘
  │ configured   │             │
  │ window       │             ▼
  └──────┬───────┘    ┌──────────────────┐
         │            │ Auto-isolation   │
         ▼            │ triggered        │
  ┌──────────────┐    │ (for CRITICAL    │
  │ Investigation │    │  only)           │
  │ phase begins │    └──────────────────┘
  └──────────────┘             │
                               ▼
                      ┌──────────────────┐
                      │ Wait for user    │
                      │ + undo is        │
                      │ available        │
                      └──────────────────┘
```

### Escalation Timeouts by Severity

| Severity | Notification Channel | Acknowledge Deadline | Auto-Escalation Action |
|----------|---------------------|---------------------|------------------------|
| **INFO** | None (logged) | — | — |
| **LOW** | Dashboard badge | 24h | Alert moves to "Stale" state |
| **MEDIUM** | Dashboard toast + email | 1h | Re-notify + increase severity display |
| **HIGH** | Email + push/SMS | 15m | Re-notify every 5m; recommend isolate |
| **CRITICAL** | Email + SMS + phone alert | 5m | Auto-isolate device; notify again |

### Escalation Matrix (What to Do When)

| Situation | Action |
|-----------|--------|
| User acknowledges but takes no action in 1h | Dashboard nudge: "You have unresolved HIGH+ alerts" |
| User dismisses CRITICAL alert as false positive | Log the dismissal. Track pattern — if same device fires again within 24h, auto-escalate |
| Device reconnects after auto-isolation | Re-isolate immediately + escalate notification (someone may have power-cycled the device) |
| Multiple devices affected simultaneously | Escalate to "multi-device incident" — suggest network-wide scan |
| User offline > 24h with active HIGH+ alerts | Auto-isolate all CRITICAL/HIGH alert devices; log for review when user returns |

---

## 6. Incident Type Playbooks

---

### Playbook 01: Suspicious External Connection from Smart Camera

**Severity:** MEDIUM–HIGH

#### Description
An IP camera or video doorbell is making connections to an external IP that does not match its normal cloud service endpoints. This could indicate a compromised device sending video to an attacker, or a misconfigured camera firmware update.

#### Detection
```
Triggers:
  - Camera connects to IP not in its known provider range (AWS, Azure, GCP regions)
  - Connection to a newly-registered domain (< 30 days old)
  - Data egress volume > 2× baseline for > 5 minutes
  - Destination port is non-standard (not 443, 554)
```

#### Initial Triage

| Step | Action | Details |
|------|--------|---------|
| 1 | Identify destination | Capture destination IP, port, protocol. Check threat intel. |
| 2 | Check if known provider | Compare against known camera cloud IP ranges |
| 3 | Measure data volume | Is traffic bidirectional or one-way outbound? |
| 4 | Check trust score | If < 0.3, escalate to HIGH |
| 5 | Check other cameras | Same destination across multiple cameras? |

#### Response Steps

```
┌──────────────────────────────────────────────────────────┐
│  MEDIUM severity                                         │
│  User action: Investigate                                │
├──────────────────────────────────────────────────────────┤
│ 1. Dashboard shows: "Camera X connecting to unusual IP" │
│ 2. User taps "View Details" → IP, geo, reverse DNS      │
│ 3. User decides:                                         │
│    a) "It's valid" → Dismiss + "Mark as known"          │
│    b) "I'm not sure" → Rate-limit camera                │
│    c) "This is suspicious" → Isolate camera             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  HIGH severity                                           │
│  User action: Respond immediately                        │
├──────────────────────────────────────────────────────────┤
│ 1. Auto: Rate-limit camera (10/sec)                      │
│ 2. Email: "Camera X may be compromised" + link to         │
│    dashboard                                             │
│ 3. User decides:                                         │
│    a) Isolate → Block all camera traffic                 │
│    b) Block IP → Add destination IP to blocklist         │
│    c) Report FP → Submit to Vigil model feedback         │
└──────────────────────────────────────────────────────────┘
```

#### Recovery

| Scenario | Recovery Action |
|----------|----------------|
| **False positive** | Mark as "Known IP." Trust score recovers after 24h of normal behavior. |
| **Compromised firmware** | Factory reset camera, apply latest firmware, reconnect. Monitor trust score for 48h. |
| **Attacker redirect** | Change cloud account password. Re-authenticate camera. Monitor for 72h. |
| **Unknown** | Keep isolated. Investigate threat intel for destination IP. Replace if no resolution in 7 days. |

---

### Playbook 02: Device Exhibiting Mirai-Like Behavior

**Severity:** HIGH–CRITICAL

#### Description
A device is performing reconnaissance or scanning behavior consistent with IoT botnet malware (Mirai, Hajime, Bashlite, etc.). This includes brute-force SSH/telnet attempts, scanning random IP ranges, or exploiting known IoT CVEs.

#### Detection
```
Triggers:
  - Outbound TCP connections to random IPs on ports 22, 23, 2323, 80, 8080
  - SYN flood pattern from a normally low-traffic device
  - ARP scanning of entire subnet (/24 sweep in < 60 seconds)
  - Telnet/SSH connection attempts to other local devices
  - Traffic volume spike to unregistered domains
```

#### Initial Triage

| Step | Action | Details |
|------|--------|---------|
| 1 | Confirm scanning behavior | Check connection logs — is it sequential IPs? Common ports? |
| 2 | Check source port consistency | Mirai-variant often uses ephemeral ports |
| 3 | Identify target scope | Local subnet scanning (lateral) vs. internet scanning (C2) |
| 4 | Check other devices for same pattern | Botnets often infect multiple devices |
| 5 | Block immediately if CRITICAL | Auto-isolate regardless of user response |

#### Response Steps

```
┌──────────────────────────────────────────────────────────┐
│  CRITICAL severity — AUTO-CONTAIN                       │
├──────────────────────────────────────────────────────────┤
│ 1. AUTO: Isolate device immediately (iptables DROP)     │
│ 2. AUTO: Rate-limit the entire subnet temporarily       │
│ 3. Notify: "🚨 Device X isolated — botnet behavior      │
│    detected" + full narrative                           │
│ 4. Log: Full packet capture trigger (last 60s buffer)   │
│ 5. Check: Any other devices showing pre-cursor signs    │
│    (DNS queries to known C2, unusual Telnet outbound)   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Post-isolation user actions                             │
├──────────────────────────────────────────────────────────┤
│ 1. Run scan on other devices for similar signs          │
│ 2. Change default passwords on ALL IoT devices          │
│ 3. Disable telnet/SSH on devices if possible            │
│ 4. Check if device has known CVE → patch or replace     │
│ 5. After clean: Factory reset + latest firmware         │
│ 6. Reconnect isolated device → monitor for 72h          │
└──────────────────────────────────────────────────────────┘
```

#### Recovery

| Scenario | Recovery Action |
|----------|----------------|
| **Confirmed infection** | Factory reset + firmware update + password change. Trust score resets to 0.3. 72h monitoring. |
| **False positive** | Review detection thresholds. Add device model to exception list if it uses legitimate scanning-based discovery. |
| **Partial infection** | (e.g., device scanning but not part of botnet) — investigate cause, restrict to VLAN, upgrade firmware. |
| **Multiple infected** | Isolate all. Full network audit. Consider network-wide password reset. |

#### Indicators (for post-incident analysis)

```
Network IOCs:
- Outbound to ports 22, 23, 2323, 80, 8080 in rapid succession  
- Sequential IP targeting (/24 range scanning)
- Repeated SYN packets without completion
- DDoS traffic patterns (large UDP floods)
- DNS queries to known bad domains (if threat intel available)

Host IOCs:
- Modified /bin/busybox (common on embedded Linux)
- Telnet/SSH credentials changed
- Unknown processes running
- Unusual outbound connections at startup
```

---

### Playbook 03: New Unknown Device on Network

**Severity:** LOW–MEDIUM

#### Description
An unrecognized device has appeared on the network. This could be a guest's phone, a new IoT device the owner forgot they added, or an unauthorized device (rogue AP, Evil Twin, physical intruder).

#### Detection
```
Triggers:
  - DHCP lease assigned to unknown MAC
  - ARP table entry for IP not in device database
  - New OUI not matching any previously seen vendor
  - Rogue DHCP server detected
```

#### Initial Triage

| Step | Action | Details |
|------|--------|---------|
| 1 | MAC OUI lookup | Manufacturer — is it a known IoT vendor or generic chipset? |
| 2 | Check DHCP hostname | Does it broadcast a device name? |
| 3 | Observe behavior | What protocols does it use? Does it scan? |
| 4 | Classify device | Run classifier on behavioral features |

#### Response Steps

```
┌──────────────────────────────────────────────────────────┐
│  LOW severity — Inform only                             │
├──────────────────────────────────────────────────────────┤
│ 1. Dashboard notification: "New device: XX:XX:XX        │
│    (Vendor?) connected to the network"                  │
│ 2. Auto-classify: Show best guess + confidence          │
│ 3. No auto-action — this is normal network churn        │
│ 4. User options:                                        │
│    a) "This is mine" → Name it + mark as known          │
│    b) "I don't recognize it" → Run quick behavioral     │
│       analysis                                          │
│    c) "Block it" → Isolate immediately                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  MEDIUM severity — Escalate if suspicious               │
├──────────────────────────────────────────────────────────┤
│ Triggers for escalation:                                │
│ - Device has no DHCP hostname (suspicious)              │
│ - Device is scanning subnet within 5 min of joining     │
│ - Device OUI is "Espressif" or generic Realtek          │
│   (common in cheap exploit hardware)                    │
│ - Device connected via Ethernet (physical access)       │
│   during unusual hours                                  │
├──────────────────────────────────────────────────────────┤
│ 1. Notify: "Unknown device is scanning the network"     │
│ 2. Suggest: "Consider isolating until identified"       │
│ 3. Auto: If ARP scanning detected, bump to HIGH         │
└──────────────────────────────────────────────────────────┘
```

#### Recovery

| Scenario | Recovery Action |
|----------|----------------|
| **Known device** | Add to device database. Trust score starts at 0.5 (neutral). |
| **Guest device** | No action needed. Optionally add to "guest" group (future VLAN feature). |
| **Unauthorized device** | Isolate, notify user. Log MAC for blacklist. |
| **Rogue AP** | Isolate. Report MAC to manufacturer? Physically locate with signal strength (future). |

---

### Playbook 04: Trust Score Rapid Decline

**Severity:** MEDIUM–HIGH

#### Description
A device's Bayesian trust score is dropping rapidly — multiple negative evidence events in quick succession. This is a "meta-alert" that aggregates individual anomalies into a broader pattern.

#### Detection
```
Triggers:
  - Trust score drops by > 0.2 in 1 hour
  - Trust score drops by > 0.3 in 24 hours
  - Trust score crosses below 0.3 threshold
  - Multiple anomaly types in a single device (traffic spike + new protocol + off-hours)
```

#### Initial Triage

| Step | Action | Details |
|------|--------|---------|
| 1 | Review all events | What caused each negative evidence point? |
| 2 | Check pattern | Single type of negative vs. diverse anomalies? |
| 3 | Compare to similar devices | Is this affecting multiple devices of same type? |
| 4 | Check recent changes | Firmware update? New network equipment? |

#### Response Steps

```
┌──────────────────────────────────────────────────────────┐
│  MEDIUM severity — Investigation mode                   │
├──────────────────────────────────────────────────────────┤
│ 1. Dashboard shows: "Camera X trust dropping —          │
│    review details"                                      │
│ 2. User sees timeline of negative events:                │
│    - 14:32 Traffic spike (z=3.5)                        │
│    - 14:45 New protocol (CoAP, first time)               │
│    - 15:01 Connection burst (12x normal)                 │
│ 3. User options:                                        │
│    a) Accept pattern → Dismiss (adds positive evidence) │
│    b) Investigate → View each event detail              │
│    c) Precaution → Rate-limit device                    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  HIGH severity — Trust < 0.3                            │
├──────────────────────────────────────────────────────────┤
│ 1. Alert: "Device X trust is critically low"            │
│ 2. Auto: Rate-limit device                              │
│ 3. Recommend: "Consider isolating this device"          │
│ 4. User options:                                        │
│    a) Isolate → Full block                              │
│    b) Monitor → Keep rate-limited, review in 1h         │
│    c) Mark false positive → Reset trust, add exception  │
└──────────────────────────────────────────────────────────┘
```

#### Trust Score Recovery

| Action | Effect on Trust |
|--------|----------------|
| User marks "This is fine" | +0.5 alpha (strong positive evidence) |
| Device behaves normally for 24h | ~0.05 recovery (slow rebuild) |
| Device behaves normally for 7d | ~0.2 recovery |
| User resets trust | Score → 0.5 (neutral) |
| Device replaced | Score reset to 0.5 |

---

### Playbook 05: C2 Beaconing Detected

**Severity:** HIGH–CRITICAL

#### Description
A device is making regular, periodic connections to an IP or domain that matches known C2 (command and control) patterns. This is the strongest indicator of active compromise.

#### Detection
```
Triggers:
  - Regular connections to same IP every N minutes (±10%)
  - DNS query to algorithmically-generated domain (DGA pattern)
  - Connection to IP on C2 threat intel list (if available)
  - Connection to domain that shares infrastructure with known C2
  - Regular heartbeat pattern with very small data payloads
  - Connection that occurs at consistent intervals regardless of device activity
```

#### Initial Triage

| Step | Action | Details |
|------|--------|---------|
| 1 | Confirm pattern | Is it truly periodic? Check interval consistency |
| 2 | Check destination | Is it a known cloud service? (AWS/Azure/GCP LB = lower concern) |
| 3 | Check payload size | C2 beacons are typically very small (100–500 bytes) |
| 4 | Check direction | Is traffic bidirectional? C2 is often two-way |
| 5 | Check other devices | Same destination across multiple devices? |

#### Response Steps

```
┌──────────────────────────────────────────────────────────┐
│  CRITICAL severity — AUTO-CONTAIN                       │
├──────────────────────────────────────────────────────────┤
│ 1. AUTO: Full device isolation (iptables DROP)          │
│ 2. AUTO: Block destination IP at gateway level          │
│    (so no other device can reach it)                    │
│ 3. AUTO: DNS sinkhole the domain (if applicable)        │
│ 4. Notify: "🚨 C2 beacon detected on Device X —         │
│    device isolated, C2 IP blocked"                     │
│ 5. Log: Full connection history to that IP              │
│ 6. Scan: Check all other devices for connections        │
│    to the same IP                                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Post-isolation user actions                             │
├──────────────────────────────────────────────────────────┤
│ These actions require user intervention:                  │
│                                                         │
│ 1. Confirm destination threat intelligence               │
│    - Who owns the IP? (RDAP lookup)                     │
│    - Is it on public blocklists?                        │
│    - Does the domain match known malware families?      │
│                                                         │
│ 2. Determine infection vector                           │
│    - Check device for default credentials               │
│    - Check for known CVEs for this device model         │
│    - Review recent device changes (firmware, config)    │
│                                                         │
│ 3. Remediate device                                     │
│    - Factory reset + firmware update                    │
│    - Change credentials                                 │
│    - Reconnect and monitor for 72h                      │
│    - If re-infected, replace device                     │
│                                                         │
│ 4. Report (optional)                                    │
│    - Submit C2 IP to abuseipdb.com or similar           │
│    - File report with CISA or local CERT                │
└──────────────────────────────────────────────────────────┘
```

#### C2 Pattern Reference

```
Classic Beacon Patterns:
  └─ Fixed interval: Connect every 300s ±5s
  └─ Jittered: Connect every 300s ±60s (evades simple detection)
  └─ HTTP beacon: GET /index.html, returns 404, 150-byte payload
  └─ DNS beacon: TXT query to subdomain of C2 domain
  └─ MQTT beacon: PUBLISH to topic with device ID as payload

Non-C2 Lookalikes (possible false positives):
  └─ Heartbeat keepalive (cloud IoT SDKs: AWS IoT, Azure IoT Hub)
  └─ NTP sync (but this is UDP, short, no payload)
  └─ DNS refresh (periodic but to known resolver)
  └─ MQTT keepalive (PINGREQ every 60s — normal for MQTT)
```

#### Recovery

| Scenario | Recovery Action |
|----------|----------------|
| **Confirmed C2** | Factory reset or replace device. Update all credentials. Monitor for 7 days. |
| **Legitimate cloud service** | (false positive) — add destination to "known good" list. Adjust C2 detection thresholds for this device type. |
| **Misconfigured MQTT** | Device connects to wrong broker. Fix MQTT config. Add broker to known list. |
| **Multi-device compromise** | Full network incident. Isolate all affected. Network-wide credential rotation. |

---

## 7. Communication Templates

### Email Notification Templates

#### CRITICAL Alert — Immediate Action Required

```
Subject: 🚨 VIGIL CRITICAL — [DEVICE_NAME] — [BRIEF_SUMMARY]
Priority: HIGH

Vigil Home Security — Critical Alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL: [SUMMARY_LINE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Device: [DEVICE_NAME] ([DEVICE_TYPE])
Time:   [TIMESTAMP]
Trust:  [TRUST_SCORE]

[NARRATIVE_DESCRIPTION — 2-3 sentences]

What Vigil did automatically:
  • Device [DEVICE_NAME] has been isolated from the network
  • Destination IP [IP_ADDRESS] has been blocked
  • [Any other auto-actions]

What you should do now:
  1. Open Vigil Dashboard: http://vigil.local or http://[IP]:3000
  2. Review the event details and confirm if this is legitimate
  3. If malicious: Factory reset [DEVICE_NAME] and change its credentials
  4. If false positive: Click "Mark as False Positive" in the dashboard

One-click actions (from dashboard):
  • 🔗 Reconnect device (undo isolation)
  • 📋 View connection history to [IP]
  • ✅ Mark as false positive

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vigil Home Security
Your network guardian
```

#### HIGH Alert — Investigate Soon

```
Subject: 🔴 VIGIL HIGH — [DEVICE_NAME] — [BRIEF_SUMMARY]

Vigil Home Security — High Severity Alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 HIGH: [SUMMARY_LINE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Device: [DEVICE_NAME] ([DEVICE_TYPE])
Time:   [TIMESTAMP]
Trust:  [TRUST_SCORE]

[NARRATIVE_DESCRIPTION]

Recommended action: [RECOMMENDATION]

View details: http://vigil.local/alerts/[ALERT_ID]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vigil Home Security
```

#### MEDIUM Alert — Review When Convenient

```
Subject: 🔶 Vigil: [DEVICE_NAME] — [BRIEF_SUMMARY]

🔶 MEDIUM: [SUMMARY_LINE]

Device: [DEVICE_NAME] ([DEVICE_TYPE])
Time:   [TIMESTAMP]

[NARRATIVE_DESCRIPTION]

No automatic action was taken. Review when convenient.

View: http://vigil.local/alerts/[ALERT_ID]
```

#### LOW Alert — Digest-Style

```
Subject: ⚠️ Vigil: [COUNT] new low-severity alerts

⚠️ Vigil has logged [COUNT] low-severity events since your last check:

  • [DEVICE1]: [SUMMARY]
  • [DEVICE2]: [SUMMARY]
  • ...

No action needed. View all: http://vigil.local/alerts
```

### SMS / Push Notification Templates

```
🚨 CRITICAL: [DEVICE] isolated — C2 beacon detected.
Open http://vigil.local/alerts

🔴 HIGH: [DEVICE] — traffic spike/scan detected.
Open http://vigil.local/alerts

🔶 MEDIUM: New unknown device on network.
[http://vigil.local/alerts]
```

### Dashboard Toast Notifications

```
┌────────────────────────────────────────────────────┐
│ 🚨 CRITICAL                                        │
│ Kitchen Cam isolated — botnet behavior detected    │
│ [View] [Reconnect] [Mark as FP]                    │
│                                        2m ago      │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│ 🔴 HIGH                                             │
│ Nest Hub — unusual external connection             │
│ [View] [Isolate] [Dismiss]                         │
│                                         30s ago     │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│ 🔶 MEDIUM                                           │
│ New device: "ESP-BEDROOM" (Espressif ESP32)        │
│ [View] [Trust] [Isolate]                           │
│                                         1m ago      │
└────────────────────────────────────────────────────┘
```

---

## 8. Dashboard & Notification Integration

### Alert Center API (Proposed Endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts` | List alerts (filter: severity, device, status, time) |
| `GET` | `/alerts/{id}` | Alert detail + connection timeline |
| `PATCH` | `/alerts/{id}` | Update alert status (acknowledge, dismiss, resolve) |
| `POST` | `/alerts/{id}/action` | Take containment action (isolate, rate-limit, block-ip) |
| `POST` | `/alerts/{id}/undo` | Undo containment action |
| `GET` | `/alerts/stats` | Alert statistics (counts by severity, trend) |

### Notification Channels

| Channel | V1 Support | Notes |
|---------|------------|-------|
| Dashboard | ✅ Real-time (SSE) | Primary interface |
| Email | ✅ SMTP | Configurable per severity |
| Push notification | ❌ | Future (PWA or mobile app) |
| SMS | ❌ | Future (Twilio API) |
| Phone call | ❌ | Future (only for CRITICAL, no-response) |

### Notification Configuration (User Preferences)

```yaml
notifications:
  email:
    enabled: true
    address: user@example.com
    min_severity: MEDIUM  # Only MEDIUM+ sends email
  
  # Future
  push:
    enabled: false
    min_severity: HIGH
  
  sms:
    enabled: false
    phone: "+15551234567"
    min_severity: CRITICAL

auto_contain:
  enabled: true
  critical_auto_isolate: true
  rate_limit_on_high: true

escalation:
  acknowledge_timeout:
    critical: 5  # minutes
    high: 15
    medium: 60
  auto_isolate_if_unacknowledged: true
```

---

## 9. Post-Incident Review Template

After every CRITICAL incident (or HIGH if user chooses), Vigil generates a Post-Incident Review (PIR) entry.

```yaml
# PIR entry structure
incident_id: "VIGIL-2026-0513-001"
timestamp: "2026-05-13T14:32:00Z"
severity: CRITICAL
playbook: "02_Device_Mirai_Behavior"

device:
  name: "Kitchen Cam"
  mac: "8c:f5:a3:12:34:56"
  type: camera
  vendor: "Wyze"
  firmware: "4.36.0.215"
  trust_before: 0.62
  trust_after: 0.18
  classification: "Confirmed infection"

timeline:
  - time: "14:27:00" - "First anomaly: connection burst (z=4.2)"
  - time: "14:29:00" - "ARP scan detected (/24 sweep)"
  - time: "14:30:00" - "Trust score crossed 0.3"
  - time: "14:31:00" - "C2 beacon pattern confirmed"
  - time: "14:31:05" - "Auto-isolation triggered"
  - time: "14:32:00" - "User notified via email + dashboard"

actions_taken:
  - type: auto_isolate
    effective: true
    revert_allowed: true
  - type: auto_rate_limit_subnet
    effective: false (no other devices affected)

containment:
  device_isolated: 12h
  ip_blocked: true
  dns_sinkhole: false (domain not used)

remediation:
  - Factory reset performed
  - Firmware updated from 4.36.0.215 to 4.36.1.100
  - Password changed from default
  - Reconnected: "2026-05-14T02:00:00Z"
  - Monitoring: "72h — no re-infection detected"

root_cause: "Default credentials — device discovered via Shodan-like scanning"

lessons:
  - "Add firmware version tracking to device baseline"
  - "Consider auto-isolating any device with trust < 0.2"
  - "False positive risk was low — pattern was unambiguous"

user_feedback: "Alert was clear. Auto-isolation was appropriate."
```

---

## 10. Future Capabilities Roadmap

| Capability | Priority | Target | Depends On |
|-----------|----------|--------|------------|
| **Push notifications** (PWA) | High | V1.1 | Service Worker registration |
| **SMS alerts** | Medium | V1.2 | Twilio API integration |
| **Managed switch API** (VLAN isolation) | Medium | V2.0 | Switch model support (Ubiquiti, TP-Link Omada) |
| **Rogue AP detection** | Medium | V2.0 | Signal strength monitoring |
| **Threat intel feeds** | Low | V2.0 | API keys, rate limits |
| **Phone call escalation** | Low | V2.0 | Twilio voice API |
| **Multi-user notifications** | Low | V2.0 | User profiles |
| **Packet capture on trigger** | Medium | V1.1 | tcpdump integration |
| **Scheduled network scan** | Low | V1.1 | nmap or custom scanner |
| **Weekly security digest** | Low | V1.1 | Email template + aggregation |
| **HomeKit/SmartThings integration** | Low | V3.0 | Vendor API access |
| **ML-based C2 detection** (vs. static thresholds) | Medium | V2.0 | Training data pipeline |

---

## Appendix A: Quick Reference Cards

### Severity Quick Reference

| Color | Level | Auto-Action | User Window |
|-------|-------|-------------|-------------|
| 🚨 Critical | Confirm compromise | Isolate + rate-limit | 5m |
| 🔴 High | Likely malicious | Rate-limit | 15m |
| 🔶 Medium | Suspicious | None | 1h |
| ⚠️ Low | Mildly unusual | None | 24h |
| ℹ️ Info | Normal churn | Log only | — |

### Device Risk Rating

| Risk | Types | Default Containment |
|------|-------|---------------------|
| 🔴 High | Camera, smart lock, unknown | Rate-limit on MEDIUM+; isolate on HIGH+ |
| 🟠 Medium | Smart speaker, hub, streaming | Alert only on MEDIUM; isolate on CRITICAL |
| 🟢 Low | Smart plug, light, sensor | Alert only on HIGH+ |

### Containment Actions by Risk

| Action | Response Time | Reversible | User Skill |
|--------|--------------|------------|------------|
| Alert only | Instant | N/A | None |
| Rate-limit | <1s | Yes (auto-expire) | Low |
| Isolate device | <1s | Yes (1-click) | Low |
| Block IP | <1s | Yes (1-click) | Low |
| DNS sinkhole | <1s | Yes (1-click) | Low |
| VLAN quarantine | 1-5s | Yes (1-click) | Medium (switch config) |

---

## Appendix B: Test Scenarios

### Scenario 1: Benign Camera Firmware Update
```
Context: Wyze Cam downloads 50MB firmware update from update.wyzecdn.com
Expected: MEDIUM alert (traffic spike) → user checks and marks "firmware update"
→ Dismissed. Trust drops slightly, recovers in 24h.
Verdict: Correct behavior. No over-reaction.
```

### Scenario 2: Real C2 Beacon on Smart Plug
```
Context: TP-Link Kasa plug starts beaconing to 185.220.101.x every 300s
Expected: CRITICAL alert → auto-isolate → user notified → investigation
→ Device compromised → factory reset.
Verdict: Correct behavior. Auto-isolation saves user time.
```

### Scenario 3: Guest Phone Joins Network
```
Context: Friend's iPhone connects to WiFi for the first time
Expected: LOW alert → user identifies as guest → device added to known list
→ No further action.
Verdict: Correct behavior. Low noise, quick resolution.
```

### Scenario 4: Multiple Devices Simultaneously Anomalous
```
Context: Power outage → all devices reconnect at once → traffic spike across network
Expected: Alerts suppressed / coalesced → "Network-wide anomaly: likely power event"
→ User dismisses once. No individual device alerts.
Verdict: Coalescence prevents alert storm.
```

### Scenario 5: Smart Lock Brute Force
```
Context: 15 failed auth attempts on Schlage lock in 2 minutes from local IP
Expected: MEDIUM → HIGH escalation as count increases → isolate attacking device
→ Notify user. Lock retains trust (external attack, not compromised).
Verdict: Correct. Trust model distinguishes victim from attacker.
```
