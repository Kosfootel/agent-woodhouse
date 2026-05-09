# Vigil Home — Product Requirements Document

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft

---

## Overview

Vigil Home is a consumer hardware appliance that provides autonomous security monitoring for residential smart homes. It operates as an always-on guardian, establishing trust baselines for devices and communicating contextually about security and privacy concerns.

---

## Target Market

### Primary Persona: **Tech-Concerned Homeowner**

- **Demographics:** 30-55 years old, household income $75K+
- **Technology:** 10-50 connected devices, smart home enthusiast
- **Pain Points:** 
  - Don't know what's happening on their network
  - Worried about IoT security but don't have time to manage it
  - Want privacy without complexity
- **Quote:** *"I want to know my home is secure without becoming a security expert."*

### Secondary Persona: **Real Estate Professional**

- **Demographics:** Real estate agents, property managers
- **Pain Points:**
  - Device transfer is manual and error-prone
  - Clients ask for tech help during moves
  - Want value-add service for listings

---

## Core Features

### 1. Device Discovery & Inventory

**FR-1.1:** Automatically discover all devices on home network within 30 seconds of plug-in.

**FR-1.2:** Maintain persistent inventory with device fingerprinting (MAC, hostname, open ports, behavior patterns).

**FR-1.3:** Support manual device naming and room assignment via mobile app.

### 2. Trust Scoring

**FR-2.1:** Assign initial trust score (0.0-1.0) based on device type, manufacturer, and behavior baseline.

**FR-2.2:** Continuously adjust trust score based on:
- Communication patterns (new destinations, unusual frequency)
- Firmware update status
- Behavioral anomalies vs. baseline
- External threat intelligence

**FR-2.3:** Trust decay: Device not seen for 30 days → score degrades.

**FR-2.4:** Trust recovery: Device behaves normally for 7 days → score improves.

### 3. Narrative Communication

**FR-3.1:** Four-tier communication:
- **Whisper:** Subtle indicator, no action required (trust 0.6-0.8)
- **Mention:** Notable event, review if interested (trust 0.4-0.6)
- **Alert:** Attention required, potential issue (trust 0.2-0.4)
- **Alarm:** Immediate action recommended (trust <0.2)

**FR-3.2:** Natural language explanations: "Your thermostat is talking to a new server in Germany. It never has before."

**FR-3.3:** Quiet hours: No non-urgent notifications 22:00-07:00.

### 4. Privacy Protection

**FR-4.1:** Local processing: All ML inference runs on device.

**FR-4.2:** Encrypted cloud sync: Only metadata and threat signatures (not raw traffic).

**FR-4.3:** Privacy audit: Monthly report showing which devices accessed what data.

### 6. Containment & Actuation

**FR-6.1:** Vigil Home must be capable of non-destructive containment:
- Network-level isolation (VLAN quarantine)
- Traffic throttling and blocking
- Device-level restrictions (no permanent damage)

**FR-6.2:** Automatic containment triggers:
- Trust score <0.2 (ALARM tier)
- Suspicious behavior patterns
- Unknown devices with aggressive scanning
- Anomalous outbound connections

**FR-6.3:** Containment is not destruction:
- Devices remain powered
- Local functionality preserved where possible
- No data deletion
- Reversible by homeowner approval

**FR-6.4:** Homeowner approval workflow:
- Real-time notification of containment
- Clear explanation of why
- One-tap release options (24h, 7d, 30d, permanent)
- Explicit confirmation for permanent releases

**FR-6.5:** Trust decay for exceptions:
- All approvals are temporary by default
- Trust decays over time (0.95^n per day)
- Re-evaluation prompts at 7, 30, 90 days
- Automatic re-containment if trust falls below threshold

**FR-6.6:** CleanSL8/Shibboleth authorized agents:
- Pre-authenticated agents bypass containment
- Authorized behavior patterns whitelisted
- Deviation from authorized behavior triggers immediate containment
- Authorization expires automatically

**FR-6.7:** Security device monitoring:
- Even "approved" security devices are continuously monitored
- Behavioral deviation detection
- Trust score fluctuates based on ongoing activity
- No "permanent trusted" status

See `CONTAINMENT-ACTUATION.md` for full protocol specification.

---

## Non-Functional Requirements

### Performance

**NFR-1:** Device discovery: <30 seconds for 50 devices
**NFR-2:** Trust score update: <100ms per event
**NFR-3:** Notification latency: <5 seconds from detection

### Reliability

**NFR-4:** Uptime: 99.9% (8.7 hours downtime/year max)
**NFR-5:** Auto-recovery: Reboot after fault <60 seconds
**NFR-6:** OTA updates: Automatic, atomic rollback on failure

### Security

**NFR-7:** Secure boot: Hardware attestation required
**NFR-8:** Encrypted storage: AES-256 for logs and data
**NFR-9:** Zero-trust cloud: Device authenticates with hardware identity

---

## Subscription Tiers

### Vigil Essential — $9.99/month

- Device inventory and discovery
- Basic trust scoring
- Critical alerts only (Alert/Alarm tier)
- Monthly security report
- Email support

### Vigil Guardian — $19.99/month

- Everything in Essential
- Full trust scoring with behavior history
- All communication tiers (Whisper/Mention/Alert/Alarm)
- Privacy audit dashboard
- Family safety features
- CleanSL8 integration (1 transfer/year)
- Priority chat support

### Vigil Estate — $29.99/month

- Everything in Guardian
- Multi-property support
- Unlimited CleanSL8 transfers
- Premium support (phone)
- Beta access to new features

---

## Hardware Refresh Program

**Policy:** Active subscribers receive free hardware refresh every 3-4 years.

**Rationale:**
- Predictable revenue smoothing
- Ensures customers have capable hardware
- Reduces support burden from legacy devices
- Environmental responsibility (trade-in/recycling)

---

## Success Metrics

| Metric | Target (Year 1) |
|--------|----------------|
| Customer acquisition cost (CAC) | <$50 (via CleanSL8 channel) |
| Monthly churn | <5% |
| Net Promoter Score (NPS) | >50 |
| Average revenue per user (ARPU) | $18/month |
| Lifetime value (LTV) | $540 (30-month avg) |
| LTV:CAC ratio | >10:1 |

---

## Roadmap

### Phase 1: POC (Weeks 1-8)
- Hardware prototype (CM5)
- Core trust scoring
- Basic mobile app
- Alpha testing (10 homes)

### Phase 2: Beta (Months 3-6)
- Enclosure design
- CleanSL8 integration
- Beta program (100 homes)
- Regulatory certification

### Phase 3: Launch (Months 7-12)
- Production hardware
- Public launch
- Retail partnerships
- Series A fundraising

---

## Open Questions

1. **WiFi requirement:** Must customer use Vigil as router, or can it monitor existing network?
2. **Offline behavior:** What happens when internet is down?
3. **Multi-user:** How does family sharing work?
4. **Professional installation:** Offer setup service for non-technical users?

---

*Next: User journey mapping and CleanSL8 integration specification*
