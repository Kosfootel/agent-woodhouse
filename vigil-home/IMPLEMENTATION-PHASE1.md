# Phase 1 Implementation: Device Identity Enhancement

**Goal:** Make devices identifiable and manageable for laypeople

## Changes Required

### 1. Database Migration

**File:** `migrations/004_add_device_identity.py`

Adds fields to `devices` table:
- `nickname` (TEXT) - User-defined friendly name
- `icon_type` (TEXT) - Auto-detected icon category
- `containment_status` (TEXT) - trusted|blocked|observing|pending_review
- `user_trust_override` (BOOLEAN) - Whether user manually set trust

### 2. API Enhancements

**New Endpoints:**
- `PATCH /devices/{id}/nickname` - Set device nickname
- `POST /devices/{id}/trust` - Mark as trusted (user override)
- `POST /devices/{id}/block` - Block device (set containment_status)
- `GET /devices/{id}/behavior` - Get behavioral data

**Enhanced Endpoints:**
- `GET /devices` - Include new fields in response
- `GET /devices/{id}` - Include new fields + behavior

### 3. Backend Logic

**Device Classification Enhancement:**
- Map device types to icon types (phone→smartphone, laptop→laptop, etc.)
- Auto-set containment_status based on trust_score on first detection

**Behavioral Analysis:**
- Calculate typical connection hours from event history
- Determine bandwidth patterns from flow data
- Store baselines for anomaly detection

### 4. Dashboard Updates

**Device List Page:**
- Show icon + nickname (or hostname fallback) instead of MAC
- Visual trust indicator (color coded)
- Quick action buttons (trust/block)

**Device Detail Page:**
- Nickname editor
- Device info card with icon
- Trust history sparkline
- Containment actions
- Behavior summary

## Implementation Order

1. Database migration
2. Backend model updates
3. New API endpoints
4. Update existing endpoints
5. Test API
6. Update dashboard components
7. Deploy to GX-10
8. Verify on dashboard (.32)

## API Response Examples

### GET /devices (enhanced)
```json
{
  "devices": [
    {
      "id": 42,
      "mac": "aa:bb:cc:dd:ee:ff",
      "ip": "192.168.50.105",
      "hostname": "iPhone-Erik",
      "vendor": "Apple",
      "device_type": "phone",
      "icon_type": "smartphone",
      "nickname": "Dad's iPhone",
      "trust_score": 0.92,
      "containment_status": "trusted",
      "user_trust_override": true,
      "first_seen": "2026-05-01T10:00:00Z",
      "last_seen": "2026-05-15T20:30:00Z",
      "online": true
    }
  ]
}
```

### GET /devices/{id}/behavior
```json
{
  "device_id": 42,
  "typical_hours": ["08:00-09:00", "12:00-13:00", "18:00-23:00"],
  "connection_pattern": "intermittent",
  "avg_bandwidth_mbps": 2.5,
  "peak_bandwidth_mbps": 45.2,
  "common_destinations": ["apple.com", "icloud.com"],
  "behavior_summary": "Normal smartphone usage pattern"
}
```

## Testing Checklist

- [ ] Migration runs successfully on GX-10
- [ ] Devices endpoint returns new fields
- [ ] Nickname can be set and persists
- [ ] Trust/block actions update containment_status
- [ ] Dashboard displays nicknames and icons
- [ ] Dashboard shows trust indicators
- [ ] Dashboard actions work (trust/block)
