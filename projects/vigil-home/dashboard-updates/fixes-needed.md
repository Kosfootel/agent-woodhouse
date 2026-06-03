# Dashboard Fixes Needed

The build is failing because the dashboard code references `device.name` but the API returns `device.hostname`.

## Changes Required:

### 1. src/app/devices/[id]/page.tsx
- Line 52: Change `device.name` to `device.hostname`
- Line 81: Change `device.name` to `device.hostname`

### 2. src/app/devices/page.tsx  
Need to check if it also uses device.name

### 3. src/lib/api.ts
The fetchDevices function maps `name` from API but should use `hostname`

### 4. src/lib/types.ts
Already updated with new fields

## Quick Fix:
Update all references from `device.name` to `device.hostname` in the dashboard code.
