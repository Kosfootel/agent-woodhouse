# MyHomeID + CleanSL8 + Vigil Home — Integrated Property Security Architecture

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Conceptual Design

---

## Executive Summary

**The Integration:** MyHomeID provides the persistent identity layer, CleanSL8 manages device inventory and transfer, and Vigil Home maintains continuous security monitoring. Together, they form the **first complete property security stack** — where security context travels with the property, not the owner.

**Key Innovation:** Security baselines and device trust scores persist across home sales, enabling seamless protection for new homeowners from day one.

---

## The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: VIGIL HOME — Security Guardian                   │
│  • Continuous monitoring                                  │
│  • Trust baselines per device                             │
│  • Containment and actuation                              │
│  • Narrative communication                                │
└────────────────────────┬────────────────────────────────────┘
                         │
         Security Baselines & Behavioral Patterns
                         │
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 2: CLEANSL8 — Device Transfer Service               │
│  • Device inventory management                             │
│  • Settings & credentials capture                          │
│  • Transfer facilitation                                   │
│  • Buyer/seller coordination                               │
└────────────────────────┬────────────────────────────────────┘
                         │
         Device Inventory, Settings, Credentials
                         │
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 1: MYHOMEID — Property Identity Infrastructure      │
│  • Persistent property identifier                          │
│  • Verified property identity                              │
│  • Cross-transaction persistence                           │
│  • Ownership history (not personal data)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## MyHomeID: The Foundation Layer

### Core Concept

**Every home receives a persistent, verified digital identity.**

**Key Properties:**
- **Immutable:** MyHomeID is assigned at construction and persists forever
- **Verified:** Linked to county assessor records, not self-claimed
- **Transferable:** Survives every sale, refinance, rental
- **Property-scoped:** Contains property characteristics, not personal data

### Data Model

```json
{
  "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
  "property": {
    "address": "123 Main St, Pittsburgh, PA 15201",
    "parcel_id": "0012-F-001234",
    "sqft": 2400,
    "year_built": 2018,
    "property_type": "single_family"
  },
  "services": {
    "cleansl8": {
      "device_count": 23,
      "last_inventory": "2026-05-01T14:30:00Z",
      "transfer_count": 1
    },
    "vigil_home": {
      "baseline_established": "2025-06-15T09:00:00Z",
      "security_score": 0.87,
      "incidents": 0,
      "containment_events": 2
    }
  },
  "created": "2018-06-01T00:00:00Z",
  "updated": "2026-05-06T08:25:00Z"
}
```

### Privacy Design

**MyHomeID contains NO personal data:**
- ❌ No owner names
- ❌ No contact information  
- ❌ No financial records
- ✅ Property characteristics only
- ✅ Service metadata (device counts, scores)
- ✅ Anonymous behavioral patterns

---

## CleanSL8: The Device Layer

### Device Passport System

**Each device receives a "passport" that travels with MyHomeID:**

```json
{
  "device_passport": {
    "passport_id": "DP-2026-a1b2c3d4",
    "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
    "device": {
      "category": "smart_camera",
      "manufacturer": "Ring",
      "model": "Video Doorbell Pro 2",
      "mac_address": "AA:BB:CC:11:22:33",
      "serial": "RING-ABC-123456"
    },
    "configuration": {
      "wifi_network": "MyHomeIoT_5G",
      "static_ip": null,
      "ports": [443, 8883],
      "cloud_services": ["ring.com", "aws.device.ring.com"]
    },
    "vigil_baseline": {
      "trust_score": 0.91,
      "typical_upload": "50MB/day",
      "typical_destinations": ["ring.com", "aws.device.ring.com"],
      "active_hours": "06:00-23:00",
      "baseline_established": "2025-06-15"
    },
    "transfer_history": [
      {
        "date": "2025-06-15",
        "event": "installed",
        "from": null,
        "to": "original_owner"
      },
      {
        "date": "2026-05-01",
        "event": "transferred",
        "from": "original_owner",
        "to": "new_owner",
        "via": "cleansl8"
      }
    ]
  }
}
```

### Transfer Workflow with MyHomeID

```
┌─────────────────────────────────────────────────────────────┐
│  SALE INITIATED                                             │
│  MyHomeID: MHID-2026-US-PA-ALLEGHENY-12345678              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CLEANSL8 AGENT ARRIVES                                     │
│  • Authenticates via Shibboleth                             │
│  • Scans network (authorized activity)                      │
│  • Captures all device passports                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  VIGIL HOME RESPONDS                                        │
│  • "CleanSL8-AGENT-42 verified for transfer TX-12345"     │
│  • Exports security baselines for all devices               │
│  • Attaches baseline data to device passports               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  MYHOMEID UPDATED                                           │
│  • Device inventory refreshed                             │
│  • Vigil baselines attached                                 │
│  • "Transfer pending" flag set                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  NEW HOMEOWNER ARRIVES                                      │
│  • Receives MyHomeID-linked Vigil Home Hub                  │
│  • Vigil: "Welcome to MyHomeID-12345678. 23 devices found.  │
│           21 baselines transferred. 2 new devices detected.│
│           Establishing trust..."                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Vigil Home: The Security Layer

### Baseline Persistence Model

**Vigil Home maintains two types of security data:**

#### 1. Device Baselines (Transferable)

```json
{
  "device_baseline": {
    "passport_id": "DP-2026-a1b2c3d4",
    "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
    "profile": {
      "trust_score": 0.91,
      "behavioral_fingerprint": "sha256:abc123...",
      "communication_patterns": {
        "destinations": ["ring.com", "aws.device.ring.com"],
        "protocols": ["HTTPS", "MQTT"],
        "typical_ports": [443, 8883],
        "data_volume": "30-80MB/day",
        "active_hours": ["06:00", "23:00"]
      },
      "anomaly_history": [
        {
          "date": "2025-08-12",
          "type": "unusual_destination",
          "ip": "185.220.101.42",
          "action": "contained",
          "resolution": "user_approved_update"
        }
      ]
    }
  }
}
```

#### 2. Network Context (Non-Transferable)

```json
{
  "network_context": {
    "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
    "local_network": "192.168.1.0/24",
    "gateway": "192.168.1.1",
    "dns_servers": ["1.1.1.1", "8.8.8.8"],
    "isp": "Comcast Xfinity",
    "typical_latency_ms": 12,
    "geolocation": "Pittsburgh, PA"
  }
}
```

### Transfer Scenarios

#### Scenario A: Ideal Transfer

**Conditions:** Same devices, new owner

```
Seller's Vigil ──────► MyHomeID ──────► Buyer's Vigil
     │                      │                  │
     ├─ 23 device baselines ├─ attaches data  ├─ imports baselines
     ├─ trust scores (0.91)   ├─ marks devices  ├─ "21 devices known,
     └─ behavioral patterns   └─ "transferred"   │  2 new, learning..."
```

**Vigil Narrative:**
> "Welcome home. I've received the security profile for this property. 21 of your devices have established baselines from the previous owner. 2 devices are new — I'm observing them to establish trust. Everything looks normal so far."

#### Scenario B: Device Change During Transfer

**Conditions:** Seller removes some devices, buyer adds new ones

```
Seller's Devices (23):
├─ Ring Doorbell ──────► Stays with property (baseline transfers)
├─ Nest Thermostat ────► Seller takes (removal event logged)
└─ Smart Lock ─────────► Seller takes (removal event logged)

Buyer's Devices (25):
├─ 21 transferred with baselines
├─ 2 removed (noted in transfer record)
├─ 3 new devices (new baselines being established)
└─ 1 unknown device (contained pending identification)
```

**Vigil Narrative:**
> "Transfer complete. 21 devices with security history. The previous owner removed their Nest thermostat and smart lock — I've noted this in the transfer record. 3 new devices are being evaluated. I found 1 unknown device — I've isolated it until you can identify it."

#### Scenario C: New Construction

**Conditions:** No previous owner, fresh MyHomeID

```
MyHomeID created ──────► CleanSL8 empty inventory ──────► Vigil learning

Vigil: "New property detected. MyHomeID-12345678 created today. 
        No transfer history. Beginning fresh trust establishment 
        for all devices..."
```

**Vigil Narrative:**
> "Welcome to your new home. I'm establishing security baselines for all your devices. This takes about 14 days of normal activity. I'll let you know if anything seems unusual during this learning period."

---

## The Shibboleth Protocol: Trust Bridge

### Cross-Service Authentication

**MyHomeID acts as the trust anchor:**

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  CleanSL8    │◄───────►│   MyHomeID   │◄───────►│  Vigil Home  │
│    Agent     │  verify │   Registry   │  verify │     Hub      │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       │    "I am authorized    │                        │
       │     for MHID-12345"    │                        │
       └────────────────────────►│                        │
       │                        │                        │
       │                        │ "CleanSL8-AGENT-42      │
       │                        │  verified for           │
       │                        │  MyHomeID-12345"        │
       │                        └────────────────────────►│
       │                                                 │
       │    "Requesting device                            │
       │     baselines"                                    │
       └──────────────────────────────────────────────────►│
                                                            │
       │    "Baselines attached                            │
       │     to MyHomeID-12345"                            │
       │◄───────────────────────────────────────────────────┘
```

### Trust Verification Flow

1. **CleanSL8 agent arrives at property**
2. **Presents credentials signed by Agency.services**
3. **MyHomeID verifies:** "Is this agent authorized for this property?"
4. **Vigil Home receives:** "CleanSL8-AGENT-42 verified via MyHomeID"
5. **Vigil exports baselines** and attaches to MyHomeID
6. **MyHomeID updates** device inventory with security baselines

---

## API Integration Points

### MyHomeID API (Hypothetical — To Confirm with Christian)

```http
# Get property security profile
GET /v1/properties/{myhome_id}/security
Authorization: Bearer {vigil_token}

Response:
{
  "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
  "vigil_enabled": true,
  "device_count": 23,
  "security_score": 0.87,
  "baselines_available": true,
  "last_vigil_sync": "2026-05-01T14:30:00Z"
}
```

```http
# Export security baselines
POST /v1/properties/{myhome_id}/security/baselines/export
Authorization: Bearer {vigil_token}

Request:
{
  "transfer_id": "TX-12345",
  "export_format": "vigil_v1"
}

Response:
{
  "export_id": "EXP-67890",
  "baseline_count": 23,
  "download_url": "https://api.myhomeid.com/v1/exports/EXP-67890",
  "expires_at": "2026-05-07T14:30:00Z"
}
```

```http
# Import security baselines (new owner)
POST /v1/properties/{myhome_id}/security/baselines/import
Authorization: Bearer {vigil_token}

Request:
{
  "transfer_id": "TX-12345",
  "baseline_data": { /* encrypted baseline package */ }
}

Response:
{
  "imported": 21,
  "new_devices": 2,
  "removed_devices": 0,
  "security_score": 0.87
}
```

### CleanSL8 API Integration

```http
# Notify CleanSL8 of Vigil baseline availability
POST /v1/transfers/{transfer_id}/vigil-baselines
Authorization: Bearer {cleansl8_token}

Request:
{
  "myhome_id": "MHID-2026-US-PA-ALLEGHENY-12345678",
  "baseline_summary": {
    "device_count": 23,
    "security_score": 0.87,
    "containment_events": 2,
    "anomaly_count": 1
  },
  "download_url": "https://vigil.agency.services/baselines/..."
}
```

---

## Security Considerations

### Data Sensitivity

| Data Type | Sensitivity | Handling |
|-----------|-------------|----------|
| Device MAC addresses | Medium | Hashed in transit |
| Trust scores | Low | Openly transferable |
| Behavioral patterns | Low | Anonymized |
| Anomaly history | Low | Pattern only, no PII |
| Network topology | Medium | Non-transferable |
| User credentials | **High** | **Never stored** |

### Privacy Guarantees

1. **No personal data in baselines** — Only behavioral patterns, not user activity
2. **No credential storage** — Vigil never stores WiFi passwords or device credentials
3. **Opt-in transfers** — Seller must explicitly approve baseline export
4. **Buyer control** — New owner can reset all baselines if desired
5. **Encrypted in transit** — All baseline data encrypted with property-specific keys

### Threat Model: Baseline Poisoning

**Attack:** Malicious seller establishes "normal" baselines that include backdoor behavior

**Mitigations:**
- Vigil flags deviations from **known-good** patterns (industry baselines)
- New owner 14-day "fresh eyes" period with heightened monitoring
- CleanSL8 verification of device authenticity
- Optional: Professional security audit for high-value transfers

---

## Business Model Integration

### Revenue Flow

```
┌─────────────────────────────────────────────────────────────┐
│  SALE TRANSACTION                                           │
│  $300,000 home sale                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│  MyHomeID  │   │  CleanSL8  │   │ Vigil Home │
│  ($5/mo)   │   │  ($149)    │   │  ($199)    │
│            │   │  Transfer  │   │  Transfer  │
│  Property  │   │  Service   │   │  Baselines │
│  identity  │   │            │   │            │
└────────────┘   └────────────┘   └────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│ Seller Package   │           │ Buyer Package    │
│ $199 (Vigil)     │           │ $199 (Vigil)     │
│ $149 (CleanSL8)  │           │ $149 (CleanSL8)  │
│ $60 (MyHomeID)   │           │ $60 (MyHomeID)   │
│ ─────────────────│           │ ─────────────────│
│ $408 total       │           │ $408 total       │
│ Security export  │           │ Security import  │
└──────────────────┘           └──────────────────┘
```

### Bundle: "Secure Home Transfer"

**Price:** $599 (vs. $816 à la carte)

**Includes:**
- MyHomeID property verification
- CleanSL8 device inventory + transfer
- Vigil Home security baseline transfer
- 90-day Vigil Home subscription
- Security guarantee (up to $1,000 if breach during transfer)

---

## Implementation Roadmap

### Phase 1: POC (Months 1-4)
- [ ] Confirm MyHomeID API specifications with Christian
- [ ] Build baseline export/import prototype
- [ ] Test transfer with 3-5 properties
- [ ] Validate Shibboleth integration

### Phase 2: Beta (Months 5-8)
- [ ] Production MyHomeID integration
- [ ] CleanSL8 workflow integration
- [ ] 100 transfer pilot
- [ ] Security audit

### Phase 3: Launch (Months 9-12)
- [ ] Public availability
- [ ] Real estate partnership program
- [ ] Insurance integration (security guarantees)
- [ ] Regulatory compliance (if needed)

---

## Open Questions

### For Christian (CleanSL8/MyHomeID):

1. **MyHomeID API availability:** Is there a REST API for property security data?
2. **Data ownership:** Who owns the baseline data — seller, buyer, or property?
3. **Privacy model:** Can baselines be exported without PII?
4. **Shibboleth integration:** Does MyHomeID support agent-to-agent trust verification?
5. **Revenue share:** How should Vigil revenue be split in bundled transfers?

### For Vigil Home Development:

1. **Baseline versioning:** How to handle evolving device firmware?
2. **False positive risk:** What if transferred baseline causes false alarms?
3. **Opt-out mechanism:** How does new owner reject imported baselines?
4. **Multi-Vigil support:** What if seller and buyer both have Vigil?

---

## Conclusion

**MyHomeID + CleanSL8 + Vigil Home creates the first truly persistent property security system.**

Instead of every homeowner starting from zero security knowledge, Vigil Home enables **continuous security context** that improves over time and travels with the property. A home that has been protected for years can transfer that protection to new owners instantly.

**The promise:** *"This home comes with security built-in — not just devices, but years of trust and protection."*

---

*Next: Confirm MyHomeID API specifications with Christian*
