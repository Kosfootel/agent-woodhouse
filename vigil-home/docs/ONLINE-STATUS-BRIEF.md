# Online Status Field Brief
**For:** Liz (GX-10 Backend)  
**From:** Woodhouse  
**Date:** 2026-05-08  
**Priority:** High (blocking dashboard display)

---

## Issue
Dashboard shows all devices as "Offline" because the API is **missing the `online` field**.

## Current API Response
```json
{
  "devices": [
    {
      "id": 1,
      "mac": "...",
      "last_seen": "2026-05-08T14:34:59",
      // MISSING: "online": true/false
    }
  ]
}
```

## Required Fix

Add `online` field computation to `/api/devices` endpoint:

```python
from datetime import datetime, timedelta

THRESHOLD_MINUTES = 5  # Device offline if not seen in 5 minutes

def is_online(last_seen: datetime | str) -> bool:
    """Compute online status from last_seen timestamp."""
    if isinstance(last_seen, str):
        last_seen = datetime.fromisoformat(last_seen)
    
    cutoff = datetime.now() - timedelta(minutes=THRESHOLD_MINUTES)
    return last_seen > cutoff

# In your API response:
return {
    "count": len(devices),
    "devices": [
        {
            **device,
            "online": is_online(device["last_seen"])
        }
        for device in devices
    ]
}
```

## Alternative (If Computing Server-Side)
Store `online` in database and update via heartbeat:

```python
# When device reports in:
async def update_device_heartbeat(device_id: int, ip: str):
    await db.execute(
        """
        UPDATE devices 
        SET ip = :ip,
            last_seen = NOW(),
            online = TRUE
        WHERE id = :id
        """,
        {"id": device_id, "ip": ip}
    )

# Background task: mark stale devices offline
async def mark_offline_devices():
    await db.execute(
        """
        UPDATE devices 
        SET online = FALSE 
        WHERE last_seen < NOW() - INTERVAL '5 minutes'
          AND online = TRUE
        """
    )
```

## Expected API Output
```json
{
  "count": 50,
  "devices": [
    {
      "id": 1,
      "mac": "00:00:00:00:00:00",
      "ip": "192.168.50.24",
      "last_seen": "2026-05-08T14:34:59",
      "online": true  // ← REQUIRED FIELD
    }
  ]
}
```

## Testing
1. Query `/api/devices`
2. Verify all devices have `online: true/false`
3. Dashboard should show correct status

---
**Estimated effort:** 15-30 minutes
