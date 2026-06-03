# Vigil Home — Containment & Actuation Protocol

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft — Non-Destructive Defense

---

## Core Principle

> **"Contain first. Question second. Trust is earned, not granted."**

Vigil Home is not merely an alarm system. It is an active defender with the capability to contain suspicious activity in real-time, seek homeowner approval for release, and maintain perpetual monitoring even of "approved" exceptions.

---

## The Containment Model

### Philosophy: Non-Destructive Defense

| Approach | Vigil Method | Rationale |
|----------|--------------|-----------|
| **Block** | Network-level containment (VLAN isolation, traffic drop) | Immediate protection |
| **Quarantine** | Restricted network segment with limited egress | Suspected but not condemned |
| **Throttle** | Rate-limit suspicious traffic | Reduce blast radius |
| **Log & Alert** | Monitor without intervention | Low trust but not yet threatening |

**Never:** Delete data, brick devices, or cause permanent damage.

---

## Response Tiers with Containment

| Tier | Condition | Vigil Action | User Experience |
|------|-----------|--------------|-----------------|
| **Whisper** | Trust 0.6-0.8 | Monitor, log | "I noticed something. Worth watching." |
| **Mention** | Trust 0.4-0.6 | Log, slight throttle | "Unusual activity on [device]. Keeping an eye on it." |
| **Alert** | Trust 0.2-0.4 | **Contain + Notify** | "[Device] is behaving suspiciously. I've restricted its network access. Review?" |
| **Alarm** | Trust <0.2 | **Quarantine + Notify** | "[Device] triggered a security concern. Isolated pending your review." |

---

## The Approval Workflow

### Step 1: Automatic Containment

```
Threat Detected → Immediate Containment → Homeowner Notification

Example:
"Your Smart TV attempted to connect to 185.220.101.42 (Russia) — 
 first time ever. I've blocked the connection. Trust score: 0.15."
```

### Step 2: Homeowner Decision

**Option A: Release (Temporary)**
- **Duration:** 24 hours default
- **Monitoring:** Enhanced scrutiny
- **Expiry:** Returns to contained state unless trust improves

**Option B: Release + Whitelist (Conditional)**
- **Condition:** Device type + destination pattern
- **Monitoring:** Ongoing behavioral analysis
- **Expiry:** Re-evaluate weekly

**Option C: Maintain Containment**
- **Action:** Device remains restricted
- **Escalation:** Manual investigation recommended

**Option D: Remove Device**
- **Action:** Disconnect from network
- **Note:** User-initiated, not automated

### Step 3: Dynamic Trust Adjustment

```
Release Granted → Trust Score: 0.15 → 0.35 (temporary)

Day 1-7: Heightened monitoring
Day 8-14: If behavior normal → Trust 0.50
Day 15-30: If behavior normal → Trust 0.65
Day 30+: If behavior normal → Trust 0.75 (new baseline)

Any deviation → Immediate re-containment, trust reset
```

---

## The "CleanSL8 Exception" Pattern

### Scenario: Real Estate Agent Scans Network

**Without Shibboleth + Containment:**
```
ALARM → Port scan detected → Block all traffic → Homeowner wakes up at 2 AM
```

**With Shibboleth + Containment:**
```
1. CleanSL8 Agent authenticates via Shibboleth
2. Vigil: "CleanSL8-AGENT-42 verified for transfer TX-12345"
3. CleanSL8 begins scan
4. Vigil: "Scanning authorized. Containment: MONITOR ONLY."
5. Vigil observes but does not restrict
6. Scan complete → Authorization expires
7. CleanSL8 agent loses all privileges
```

### Scenario: New Security Device Installed

**User installs "SuperSecure Home Scanner"**

```
Vigil Detection:
"New device 'SuperSecure-Hub' detected. Behavior: aggressive port scanning.
Trust: 0.12. CONTAINED."

User Notification:
"I found a new device scanning your network. This may be your security 
system, but I need your approval before allowing it full access."

User Response: "Yes, this is my security device. Allow it."

Vigil Action:
- Release from containment (24 hours)
- Trust: 0.12 → 0.35 (temporary)
- Monitoring: AGGRESSIVE
- Weekly re-evaluation

Week 1 Follow-up:
"Your security device continues normal scanning patterns. 
Trust improved to 0.48. Monitoring continues."

Week 4 Follow-up:
"Security device behaving within expected parameters. 
Trust: 0.65. Reduced monitoring frequency."

Month 3 Anomaly:
"Your security device just attempted to upload 2GB to unknown server 
in China. Never done this before. CONTAINED. Trust reset to 0.15."
```

---

## Containment Implementation

### Network-Level Controls

**Option 1: VLAN Isolation (Recommended)**
```
Default VLAN: 10 (Trusted devices)
Quarantine VLAN: 99 (Contained devices)

Contained devices:
- Can reach Vigil Home (for status/updates)
- Cannot reach Internet
- Cannot reach other LAN devices
- Can be released to VLAN 10 on approval
```

**Option 2: eBPF/XDP Packet Drop**
```
Kernel-level filtering:
- Drop packets from contained MAC addresses
- Log all attempted connections
- Zero performance overhead
```

**Option 3: DHCP Lease Manipulation**
```
- Issue contained devices to quarantine subnet
- Limit lease time (force re-auth)
- Works with any router
```

### Hardware Requirements

| Feature | Requirement | Purpose |
|---------|-------------|---------|
| **802.1Q VLAN** | Required | Network isolation |
| **Managed Switch** | Preferred | Port-level control |
| **eBPF Support** | Required (kernel 5.0+) | High-performance filtering |
| **Multiple NICs** | Optional | Physical isolation |

---

## Trust Decay for Exceptions

**The Rule:** Every exception expires.

| Exception Type | Default Duration | Re-evaluation |
|----------------|------------------|---------------|
| One-time release | 24 hours | Manual review |
| Temporary whitelist | 7 days | Automated trust assessment |
| Permanent whitelist | 30 days | Quarterly review + user prompt |
| Security device exception | 14 days | Weekly behavior analysis |

**Trust Decay Function:**
```
Trust(t) = Trust_approved × (0.95)^(days_since_approval)

After 30 days: Trust = 0.21 × original
After 60 days: Trust = 0.046 × original
After 90 days: Automatic re-containment for review
```

---

## User Interface Patterns

### Containment Dashboard

```
┌─────────────────────────────────────────┐
│  CONTAINED DEVICES (2)                  │
├─────────────────────────────────────────┤
│                                         │
│  📵 Smart TV (Living Room)              │
│     Status: CONTAINED                   │
│     Reason: Suspicious outbound traffic │
│     Trust: 0.15 → 0.42 (improving)      │
│     [Review] [Release 24h] [Remove]     │
│                                         │
│  📵 Unknown Device (MAC: a1:b2:...)     │
│     Status: CONTAINED                   │
│     Reason: Port scanning detected      │
│     Trust: 0.08                         │
│     [Identify] [Remove]                 │
│                                         │
└─────────────────────────────────────────┘
```

### Release Confirmation

```
Release 'Smart TV' from containment?

⚠️  This device was contained for:
    • Connection to unknown server (185.220.101.42)
    • First-time behavior
    • Trust score: 0.15

Duration:
○ 24 hours    ● 7 days    ○ 30 days    ○ Permanent

[Release with Monitoring] [Cancel]
```

---

## CleanSL8 Integration with Containment

### Authorized Agent Workflow

```
1. Shibboleth Authentication
   └─ CleanSL8 proves identity
   
2. Capability Grant
   └─ Vigil: "CleanSL8 authorized for: 
        - Port scanning (expected)
        - Device inventory (expected)
        - Baseline extraction (expected)
        - Duration: 72 hours"

3. Monitor Mode
   └─ Vigil observes but does not contain
   └─ Trust: 0.92 (verified identity)
   
4. Deviation Detection
   └─ If CleanSL8 attempts unexpected action:
       - Immediately contain
       - Alert: "CleanSL8-AGENT-42 attempted unauthorized action"
       - Trust: 0.92 → 0.20
       
5. Expiration
   └─ Authorization expires
   └─ Any continued CleanSL8 activity → Treated as unknown threat
```

---

## Edge Cases

### What if Vigil itself is compromised?

**Design:** Vigil hardware has hardware write-protect on containment rules.
- Malware on Vigil cannot disable containment
- Physical access required to override
- Tamper detection alerts homeowner

### What if homeowner is socially engineered?

**Design:** Multiple release options require explicit confirmation.
- "Permanent" release requires typing confirmation phrase
- Unusual release patterns (3+ in 24h) trigger additional verification
- Secondary notification to emergency contact (optional)

### What if contained device is critical?

**Design:** Graceful degradation, not hard failure.
- Security camera contained → Still records locally
- Thermostat contained → Maintains last settings
- Smart lock contained → Physical key still works

---

## Success Metrics

| Metric | Target |
|--------|--------|
| False positive containment | <5% of total containments |
| Average time to release approval | <2 minutes (user-initiated) |
| Re-containment rate | <10% (most approved devices stay approved) |
| User satisfaction with containment | >85% ("I felt protected, not annoyed") |
| Security incident prevented by containment | >90% of detected threats |

---

## Open Questions

1. **Emergency override:** Should homeowner have "panic release" that bypasses all checks?
2. **Family members:** Can spouse/child approve releases, or only primary account?
3. **Smart home integration:** Should containment notify Alexa/Google Home? ("Vigil has isolated a device")
4. **Professional mode:** Offer "security professional" mode with more permissive defaults?

---

*Next: Technical implementation details for VLAN/eBPF containment*
