# RFC-0001: Layperson-Friendly Security Features for Vigil Home

**Status:** Draft  
**Author:** Woodhouse  
**Date:** 2026-05-15  
**Reviewers:** Erik Ross (Product Owner), Ray, Liz

---

## Summary

Enhance Vigil Home's API and dashboard to make network security monitoring accessible to non-technical users ("laypeople"). This involves enriching device data, adding behavioral baselines, creating network health metrics, and providing plain-English explanations of security events with one-click responses.

---

## Problem Statement

Vigil Home currently provides excellent technical security monitoring (Suricata-based detection, trust scoring, AI narratives) but presents it in ways that require security expertise to interpret. The vision is to make this accessible to homeowners who want to understand and protect their network without becoming security experts.

Current pain points:
- Device lists show MAC addresses and technical types, not friendly identities
- Trust scores exist but lack context ("0.7" vs "This device is behaving normally")
- Alerts are technical ("TCP SYN flood detected") vs actionable ("Your TV is acting strangely")
- No "at a glance" view of overall network health
- Containment exists but requires manual playbook configuration

---

## Goals

1. **Device Recognition** - Users can easily identify "what is this thing on my network?"
2. **Trust Clarity** - Users understand why a device is trusted or suspicious
3. **Actionable Alerts** - Every alert includes plain explanation + one-click response
4. **Network Confidence** - Single "health score" for overall security posture
5. **Proactive Reporting** - Weekly digest of what happened + what was done

---

## Non-Goals

- Building a new UI framework (enhance existing dashboard)
- Replacing Suricata (enhance data interpretation)
- Creating new detection methods (improve presentation of existing detection)
- Mobile app (focus on web dashboard)

---

## Proposed Changes

### Phase 1: Device Identity & Trust (Foundation)

#### API Changes

**1. Device Model Enhancement**
```python
# New fields in Device model
nickname: str           # User-defined friendly name ("Dad's iPhone")
icon_type: str         # Auto-detected: "phone", "laptop", "tv", "camera", etc.
baseline_bandwidth: float   # MB/hour typical usage
connection_pattern: str  # "daytime", "evening", "always_on", "intermittent"
containment_status: str # "trusted", "blocked", "observing", "pending_review"
```

**2. New Endpoints**
- `PATCH /devices/{id}/nickname` - Set friendly name
- `POST /devices/{id}/trust` - Mark device as trusted
- `POST /devices/{id}/block` - Block device at network level
- `GET /devices/{id}/behavior` - Get behavioral baseline data
- `GET /network/health` - Overall health score 0-100 with factor breakdown

**3. Enhanced Device Response**
```json
{
  "id": 42,
  "mac": "aa:bb:cc:dd:ee:ff",
  "vendor": "Apple",
  "device_type": "phone",
  "icon_type": "smartphone",
  "nickname": "Mom's iPhone",
  "trust_score": 0.92,
  "trust_status": "trusted",  // computed from score + user override
  "containment_status": "trusted",
  "baseline": {
    "typical_bandwidth_mbps": 2.5,
    "active_hours": ["08:00", "12:00", "18:00"],
    "pattern": "intermittent"
  },
  "first_seen": "2026-05-01T10:00:00Z",
  "last_seen": "2026-05-15T20:30:00Z",
  "online": true
}
```

#### Dashboard Changes
- Device list with icons + nicknames (not just MACs)
- Device detail modal with nickname editor
- Trust score sparkline over time
- "Mark as Trusted" / "Block Device" buttons

---

### Phase 2: Plain-English Alerts & Actions

#### API Changes

**1. Alert Model Enhancement**
```python
# Enhanced alert with actionable metadata
title: str              // "New Device: Unknown Phone"
narrative: str          // "A phone we haven't seen before joined your network..."
severity: str           // "info", "warning", "critical"
recommended_action: str  // "review", "trust", "block", "monitor"
affected_device_id: int
auto_resolved: bool     // Did Vigil take automated action?
```

**2. New Alert Endpoints**
- `POST /alerts/{id}/trust-device` - Trust device that triggered alert
- `POST /alerts/{id}/block-device` - Block device that triggered alert
- `POST /alerts/{id}/acknowledge` - User acknowledges and dismisses

**3. Alert Webhook/Digest**
- `GET /digest/weekly` - Generate weekly summary
- Background job to email weekly digest (already exists, enhance content)

#### Dashboard Changes
- Alert cards with: icon + title + narrative + severity badge + action buttons
- Alert timeline (chronological feed)
- "What's New" section for new/updated alerts
- Toast notifications for new alerts

---

### Phase 3: Network Health Score

#### API Changes

**1. Health Score Algorithm**
Factors weighted into 0-100 score:
- Device trust distribution (30%): avg(trust_score * device_age_weight)
- Alert volume (25%): normalize recent_alert_count vs baseline
- Unknown devices (20%): penalty for unclassified/untrusted devices
- Network stability (15%): device churn rate, offline anomalies
- Security posture (10%): containment coverage, playbook execution

**2. Health Endpoint**
```json
// GET /network/health
{
  "score": 87,
  "status": "healthy",  // "excellent" | "healthy" | "attention" | "critical"
  "factors": [
    {"name": "Device Trust", "score": 92, "weight": 0.30},
    {"name": "Alert Volume", "score": 85, "weight": 0.25},
    {"name": "Unknown Devices", "score": 78, "weight": 0.20},
    {"name": "Network Stability", "score": 90, "weight": 0.15},
    {"name": "Security Posture", "score": 95, "weight": 0.10}
  ],
  "top_concerns": [
    {"type": "untrusted_device", "device_id": 15, "message": "Unknown laptop hasn't been classified"}
  ],
  "last_updated": "2026-05-15T20:45:00Z"
}
```

#### Dashboard Changes
- Network health gauge (0-100) with color coding
- Factor breakdown with explanations
- "Top Concerns" callout box
- Historical trend (score over time)

---

## Migration Plan

### Database Migrations
1. `004_add_device_nickname.py` - Add nickname, icon_type, containment_status
2. `005_add_device_baseline.py` - Add baseline_bandwidth, connection_pattern
3. `006_add_alert_enhancements.py` - Add title, recommended_action, auto_resolved

### Backward Compatibility
- All new fields are nullable with sensible defaults
- Existing API responses remain unchanged (additive only)
- Dashboard gracefully handles missing new fields

---

## Security Considerations

- Containment actions require authentication (already enforced)
- Blocking should be reversible (soft block, not firewall hard block)
- Alert narratives are AI-generated—sanitize to prevent prompt injection in logs
- Health score algorithm shouldn't leak internal topology details

---

## Testing Strategy

- Unit tests for health score calculation
- Integration tests for new API endpoints
- Manual testing: create alert, verify narrative clarity, test one-click actions
- User validation: show dashboard to non-technical user, verify comprehension

---

## Alternatives Considered

1. **Build mobile app instead of web dashboard** - Rejected: web reaches all users, app adds friction
2. **Integrate with existing router UI** - Rejected: Vigil is appliance-based, keeps data local
3. **Simplify to binary secure/unsecure** - Rejected: loses valuable nuance, false confidence
4. **Pre-built playbook templates only** - Rejected: still requires user to understand and select

Selected approach balances depth of information with accessibility through progressive disclosure (summary → detail → technical).

---

## Open Questions

1. Should device blocking be immediate or require confirmation? (Confirmation recommended)
2. Should health score factor in time-of-day patterns? (Phase 2)
3. How to handle "shared" devices (housemate's phone vs guest)? (User-defined trust levels)
4. Integration with email alerts—send weekly digest automatically or on-demand? (Auto-send, opt-out)

---

## Timeline Estimate

- **Phase 1 (Device Identity):** 2-3 days (API + dashboard integration)
- **Phase 2 (Alerts & Actions):** 2-3 days (API + dashboard integration)
- **Phase 3 (Health Score):** 2-3 days (API + dashboard integration)
- **Testing & Polish:** 2-3 days
- **Total:** ~10 days of focused work

---

## Success Criteria

- [ ] Non-technical user can identify all 10 devices on their network by name
- [ ] Alert narrative understood without security knowledge
- [ ] Network health score actionable (user knows what to do if < 70)
- [ ] One-click containment actions work reliably
- [ ] Weekly digest email opened and understood

---

*Reviewers: Please comment with approval, concerns, or requested changes. Once approved, this RFC will guide implementation.*
