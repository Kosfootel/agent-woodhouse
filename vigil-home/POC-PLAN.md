# Vigil Home — Proof of Concept Plan

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** In Progress

---

## Objective
Build a working Vigil Home prototype that demonstrates:
1. Network traffic monitoring
2. Device discovery and fingerprinting
3. Trust baseline establishment
4. Containment (VLAN isolation)
5. Narrative alerts

---

## Hardware Selection: Raspberry Pi CM5

**Decision Rationale:**
- Fastest path to working prototype (days, not weeks)
- Sufficient for POC (quad-core, 4GB RAM, eMMC)
- Established ecosystem (cases, PoE hats, documentation)
- Easy to iterate: swap Compute Module for upgrades

**Security limitations for POC:**
- Broadcom VideoCore blob (acceptable for POC, not production)
- No hardware root of trust (acceptable for POC)
- Will add external TPM module for security demonstration

**Production path:** N100 + Coreboot (Phase 2)

---

## BOM for POC

| Component | Model | Cost | Source |
|-----------|-------|------|--------|
| Compute Module | CM5 (4GB RAM, 32GB eMMC) | $45 | Digi-Key |
| IO Board | CM5 IO Board | $35 | PiShop |
| Case | Passive cooling case | $25 | Amazon |
| TPM Module | Infineon SLB9672 | $8 | Mouser |
| PoE Hat | Official CM5 PoE+ Hat | $25 | PiShop |
| Ethernet | Integrated (1GbE) | - | IO Board |
| WiFi | Optional USB dongle | $15 | Amazon |

**Total:** ~$153

---

## POC Architecture

```
┌─────────────────────────────────────────────┐
│  CM5 IO Board                               │
│  ┌───────────────────────────────────────┐ │
│  │  CM5 Module (4GB/32GB)               │ │
│  │  • Debian 12 (Bookworm)              │ │
│  │  • Suricata (IDS)                    │ │
│  │  • Python detection engine           │ │
│  │  • SQLite database                   │ │
│  └───────────────────────────────────────┘ │
│  ┌───────────────────────────────────────┐ │
│  │  TPM2 Module (SLB9672)               │ │
│  │  • Secure key storage                │ │
│  │  • Device attestation                │ │
│  └───────────────────────────────────────┘ │
│  ┌───────────────────────────────────────┐ │
│  │  Network Interfaces                    │ │
│  │  • eth0: WAN (uplink to router)      │ │
│  │  • eth1: LAN (to managed switch)     │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Managed Switch (TP-Link TL-SG108E)        │
│  • VLAN 10: Trusted devices               │
│  • VLAN 99: Quarantine                      │
│  • Port mirroring for monitoring            │
└─────────────────────────────────────────────┘
```

---

## Software Stack

### Base System
- **OS:** Debian 12 (Bookworm) — stable, minimal, well-supported
- **Kernel:** 6.6 LTS with eBPF support
- **Network:** systemd-networkd + nftables

### Detection Engine
- **Suricata:** Network traffic analysis (IDS mode for POC)
- **Rules:** Emerging Threats Open + Vigil custom rules
- **Output:** JSON to SQLite for processing

### Device Discovery
- **arp-scan:** Layer 2 device discovery
- **nmap:** Fingerprinting (controlled, non-intrusive)
- **p0f:** Passive OS fingerprinting

### Containment
- **nftables:** Packet filtering
- **bridge-utils:** VLAN management
- **dnsmasq:** DHCP with VLAN assignment

### Application Layer
- **Python 3.11:** Main application
- **FastAPI:** REST API
- **SQLite:** Local database
- **Rich:** Console output (narrative mode)

---

## POC Scope: Week-by-Week

### Week 1: Foundation (May 6-12)
- [x] Finalize BOM and order components
- [ ] Flash CM5 with Debian 12
- [ ] Basic network bridge (WAN → LAN)
- [ ] Install Suricata with ET Open rules
- [ ] Verify traffic capture

### Week 2: Detection (May 13-19)
- [ ] Device discovery service
- [ ] Fingerprint first 5 device types
- [ ] Implement 5 detection rules (VHR-001 to VHR-005)
- [ ] SQLite schema for devices and baselines
- [ ] Basic trust scoring

### Week 3: Containment (May 20-26)
- [ ] VLAN configuration (10/99)
- [ ] DHCP quarantine assignment
- [ ] nftables rules for containment
- [ ] Trust decay implementation
- [ ] Approval workflow (CLI for POC)

### Week 4: Narrative (May 27-June 2)
- [ ] Narrative generation engine
- [ ] Console output (Rich)
- [ ] Web UI (minimal, read-only for POC)
- [ ] Demo script and documentation
- [ ] Record demo video

---

## Detection Rules for POC

| Rule | Detection | Action |
|------|-----------|--------|
| VHR-001 | Port scanning | Alert |
| VHR-002 | New device discovered | Mention |
| VHR-003 | C2 beaconing pattern | Alarm |
| VHR-004 | Default credential attempt | Alarm |
| VHR-005 | Unusual hours activity | Mention |

---

## Success Criteria

### Week 1
- [ ] CM5 passes traffic end-to-end
- [ ] Suricata captures and logs traffic
- [ ] No stability issues (24h uptime)

### Week 2
- [ ] Auto-discovers 5+ devices on test network
- [ ] Correctly identifies device types (camera, speaker, etc.)
- [ ] Trust scores calculate without errors
- [ ] Detection rules trigger appropriately

### Week 3
- [ ] VLAN isolation functional
- [ ] Suspicious device automatically quarantined
- [ ] Release workflow operational
- [ ] Trust decay visible in data

### Week 4
- [ ] Narrative output understandable to non-technical user
- [ ] Demo runs 10 minutes without intervention
- [ ] Clean handoff to Christian for CleanSL8 integration planning

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CM5 supply shortage | Medium | Delay | Order from multiple vendors; N100 fallback |
| Suricata performance | Low | Poor detection | Tune rules; IDS mode only (no IPS) |
| VLAN complexity | Medium | Network issues | Document configs; use managed switch |
| Time constraints | High | Incomplete POC | Prioritize core features; defer polish |

---

## Deliverables

1. **Working Prototype:** CM5-based Vigil Home device
2. **Demo Video:** 5-10 minute walkthrough
3. **Technical Documentation:** Setup guide, architecture decisions
4. **CleanSL8 Integration Plan:** API contracts for Christian
5. **Phase 2 Proposal:** N100 + Coreboot production path

---

## Immediate Next Actions

1. **Order components** (Digi-Key, Mouser, PiShop)
2. **Set up build environment** (Debian VM for cross-compilation)
3. **Download CM5 OS image** (Raspberry Pi OS Lite or Debian)
4. **Survey test network** (document current devices for baseline)

---

**Started:** 2026-05-06 15:52 EDT  
**Target Demo:** June 2, 2026
