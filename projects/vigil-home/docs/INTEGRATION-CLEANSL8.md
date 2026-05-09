# CleanSL8 + Vigil Home Integration Specification

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft

---

## Overview

This document defines the technical integration between **CleanSL8** (smart home device transfer service) and **Vigil Home** (security guardian appliance).

The integration enables:
1. **Seamless device transfer:** Security baseline travels with devices
2. **Trust continuity:** New homeowner inherits established trust scores
3. **Zero-friction onboarding:** Vigil Home pre-configured for transferred devices

---

## User Journeys

### Journey A: Seller (Move-Out)

**Actor:** Homeowner selling property  
**Goal:** Export device inventory and security baseline for transfer

```
1. CleanSL8 App → Initiate "Home Sale" workflow
2. Scan QR codes on all smart devices (or auto-discover via Vigil Home)
3. Vigil Home → Generate "Territory Snapshot":
   - Device inventory (MAC, type, manufacturer, firmware)
   - Trust scores per device
   - Behavioral baselines (communication patterns)
   - Historical alerts/notable events
4. CleanSL8 → Upload to secure transfer vault (encrypted)
5. Listing → "Smart home devices included, pre-secured with Vigil"
```

### Journey B: Buyer (Move-In)

**Actor:** Homeowner purchasing property  
**Goal:** Inherit devices with security context

```
1. Closing → CleanSL8 transfer initiated by agent/title company
2. Vigil Home Hub shipped to buyer's new address
3. Buyer plugs in Vigil Home → Auto-detects transferred devices
4. Vigil Home → Import "Territory Snapshot":
   - "These devices came from 123 Oak St. Previous trust: 0.87"
5. Vigil Home → Begin "acclimation period":
   - Week 1: Monitor only, learn new patterns
   - Week 2+: Full protection active
```

### Journey C: Agent (Facilitator)

**Actor:** Real estate agent  
**Goal:** Provide value-add service, ensure smooth transfer

```
1. Listing → Agent offers "Smart Home Security Package"
2. CleanSL8 Dashboard → Device compatibility check
3. Transfer → Agent tracks status, resolves issues
4. Post-close → Agent receives "transfer complete" notification
5. Relationship → Agent becomes Vigil referral source
```

---

## Technical Integration

### API Contract

#### 1. Export Baseline (CleanSL8 → Vigil)

```http
POST /v1/transfer/export
Authorization: Bearer {clean_sl8_token}
Content-Type: application/json

{
  "property_id": "PROP-12345",
  "transfer_id": "TRANS-67890",
  "vigil_snapshot": {
    "version": "1.0",
    "generated_at": "2026-05-06T10:30:00Z",
    "device_count": 23,
    "devices": [
      {
        "device_id": "dev_a1b2c3",
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "device_type": "smart_thermostat",
        "manufacturer": "Nest",
        "model": "Learning Thermostat",
        "firmware_version": "5.9.1",
        "trust_score": 0.92,
        "trust_history": [
          {"date": "2026-04-01", "score": 0.89, "reason": "baseline_established"},
          {"date": "2026-05-01", "score": 0.92, "reason": "consistent_behavior"}
        ],
        "behavior_baseline": {
          "typical_destinations": ["172.217.0.0/16", "99.84.0.0/16"],
          "avg_daily_connections": 45,
          "connection_pattern": "regular", // regular, intermittent, bursty
          "firmware_update_status": "current"
        },
        "notable_events": [
          {
            "date": "2026-03-15",
            "type": "mention",
            "description": "Firmware updated from 5.8.2 to 5.9.1"
          }
        ]
      }
    ],
    "network_fingerprint": {
      "typical_dns_queries": ["dns.google", "cloudflare-dns.com"],
      "typical_ntp_servers": ["time.google.com"],
      "typical_cloud_endpoints": ["aws.amazon.com", "googleapis.com"]
    },
    "vigil_metadata": {
      "total_monitoring_days": 245,
      "alerts_generated": 3,
      "alarms_generated": 0,
      "average_trust_score": 0.84
    }
  }
}
```

#### 2. Import Baseline (Vigil → CleanSL8)

```http
POST /v1/transfer/import
Authorization: Bearer {vigil_home_token}
Content-Type: application/json

{
  "transfer_id": "TRANS-67890",
  "vigil_device_id": "VH-ABC123",
  "snapshot": { /* Baseline data from above */ },
  "import_settings": {
    "acclimation_period_days": 7,
    "trust_carryover_percentage": 0.8, // 80% of previous trust retained
    "alert_on_deviation": true
  }
}

Response:
{
  "status": "imported",
  "devices_recognized": 21, // 2 may not be detected yet
  "devices_pending": 2,
  "acclimation_end_date": "2026-05-13T00:00:00Z",
  "initial_trust_scores_assigned": true
}
```

#### 3. Transfer Status

```http
GET /v1/transfer/{transfer_id}/status

Response:
{
  "transfer_id": "TRANS-67890",
  "status": "in_progress", // pending, in_progress, completed, expired
  "seller_confirmed": true,
  "buyer_confirmed": true,
  "vigil_hub_shipped": true,
  "vigil_hub_delivered": true,
  "baseline_imported": true,
  "acclimation_active": true,
  "acclimation_days_remaining": 5,
  "completion_percentage": 75
}
```

---

## Data Model

### Territory Snapshot

A portable representation of a home's security state:

```json
{
  "snapshot_id": "uuid",
  "version": "1.0",
  "created_at": "ISO8601",
  "property": {
    "address_hash": "sha256_of_address", // privacy preserved
    "device_count": 23
  },
  "devices": [ /* Array of Device Profiles */ ],
  "network_profile": { /* Typical traffic patterns */ },
  "vigil_stats": { /* Monitoring metadata */ }
}
```

### Device Profile

```json
{
  "device_id": "uuid",
  "hardware": {
    "mac_address": "hashed", // one-way hash for privacy
    "manufacturer": "string",
    "model": "string",
    "category": "thermostat|camera|lock|speaker|hub|other"
  },
  "security": {
    "trust_score": 0.0-1.0,
    "trust_history": [],
    "last_firmware_update": "date",
    "vulnerabilities": []
  },
  "behavior": {
    "communication_pattern": "regular|intermittent|bursty",
    "typical_destinations": [],
    "typical_ports": [],
    "bandwidth_usage": "low|medium|high"
  }
}
```

---

## Security & Privacy

### Data Minimization

- **No raw traffic:** Only metadata and patterns exported
- **No PII:** Addresses hashed, no personal data in snapshot
- **Encrypted at rest:** AES-256 for all transfer data
- **Time-bounded:** Snapshots expire after 90 days if unclaimed

### Consent Model

- **Seller consent:** Explicit opt-in for baseline export
- **Buyer consent:** Explicit opt-in for baseline import
- **Revocation:** Seller can invalidate snapshot before transfer completes

---

## Business Logic

### Trust Carryover

When devices move to new network:

| Scenario | Trust Adjustment |
|----------|------------------|
| Device behaves similarly to baseline | 90% of previous trust retained |
| Device shows new but benign patterns | 70% retained, monitored closely |
| Device shows concerning patterns | 40% retained, alert generated |
| Device not detected within 7 days | Baseline expires, start fresh |

### Acclimation Period

**Days 1-7:** Vigil learns new network
- Trust scores frozen at import level
- Monitoring active, no automated actions
- User sees: "Learning your new home..."

**Day 8+:** Full protection active
- Trust scores begin adjusting
- Automated tiered responses enabled
- User sees: "Protection active. Trust baseline established."

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Device in snapshot not found | Mark "pending", alert if not found in 7 days |
| Device found but behaves differently | Reduced trust, notify user |
| Snapshot import fails | Offer manual onboarding or fresh start |
| Network completely different | Suggest fresh baseline (rarely used) |

---

## Open Questions

1. **Device ownership:** How do we handle devices seller takes with them?
2. **Rental properties:** Multi-tenant snapshots for apartment buildings?
3. **Commercial:** Integration with commercial real estate platforms?
4. **Insurance:** Can this data reduce home insurance premiums?

---

*Next: User journey wireframes and mobile app mockups*
