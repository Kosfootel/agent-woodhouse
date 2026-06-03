# Device Enrichment Update - Vendor & Manufacturer Info

**Date:** 2026-05-14  
**Status:** ✅ Complete

## Summary

Enhanced the Vigil dashboard device display with human-readable vendor/manufacturer information derived from MAC OUI lookup. Devices now show both device type and manufacturer, improving identification and contextual understanding.

## Changes Made

### Backend (`poc-backend/`)

#### 1. Database Model (`app/models.py`)
- Added `vendor` column to `Device` model (String(128), nullable)
- Updated `to_dict()` to include vendor in API responses

#### 2. Device Creation (`app/main.py`)
- Modified `/devices` POST endpoint to extract vendor from classifier results
- Vendor is now automatically populated during device registration

#### 3. Migrations (`migrations/`)
- **002_add_vendor_column.py**: Adds vendor column to existing databases
- **003_enrich_vendors.py**: Backfills vendor info for existing devices using OUI lookup
- **run_migrations.py**: Migration runner utility

**Usage:**
```bash
# Run all migrations
VIGIL_DB_PATH=/data/vigil.db python3 migrations/run_migrations.py

# Or run individually
VIGIL_DB_PATH=/data/vigil.db python3 migrations/002_add_vendor_column.py
VIGIL_DB_PATH=/data/vigil.db python3 migrations/003_enrich_vendors.py
```

### Frontend (`dashboard/`)

#### 1. Type Definitions (`src/lib/types.ts`)
- Added `vendor?: string` to `Device` interface
- Added `vendor: string | null` to `BackendDevice` interface

#### 2. API Layer (`src/lib/api.ts`)
- Updated `fetchDevices()` to map vendor from backend response
- Updated `fetchDevice()` to include vendor in device details

#### 3. Device List (`src/app/devices/page.tsx`)
- Enhanced `DeviceCard` component to display vendor badge
- Shows: Device Type • Manufacturer (when available)

#### 4. Device Detail (`src/app/devices/[id]/page.tsx`)
- Added Manufacturer field to Classification card
- Displays between Device Type and Confidence

## OUI Database Coverage

The built-in OUI database (`app/ai/classifier.py`) includes:

| Vendor | Device Types |
|--------|-------------|
| Amazon | Smart speakers, cameras, Eero |
| Google/Nest | Smart speakers, cameras, displays |
| Apple | HomePod, Apple TV, iOS devices |
| Samsung | Smart TVs, appliances |
| Philips (Hue) | Smart lights, hubs |
| TP-Link/Kasa | Smart plugs, switches |
| Ring | Cameras, doorbells, locks |
| Wyze | Cameras, sensors |
| Sonos | Speakers |
| Lutron | Smart lighting |
| Tuya | Generic IoT devices |
| Espressif | ESP32/ESP8266 custom devices |
| Raspberry Pi | Pi-based devices |
| Ubiquiti | Network equipment |
| Xiaomi | Smart home devices |
| Realtek | TVs, cameras |
| Intel | Smart displays, PCs |

## Behavioral Signatures

The classifier also uses behavioral patterns to identify devices:
- Protocol usage (RTSP, MQTT, HTTPS, etc.)
- Port ranges
- Traffic volume (kbps)
- Connection rate (connections/hour)
- Active hours
- Hub/bridge relationships

## Next Steps (Optional Enhancements)

1. **External OUI Database**: Load full Wireshark OUI database for broader coverage
2. **Vendor Logo**: Display vendor logos in device cards
3. **Vendor Filtering**: Add vendor filter to device list
4. **Vendor Search**: Search devices by manufacturer
5. **Custom Vendor Mappings**: Allow users to add custom OUI→vendor mappings

## Testing

To verify the changes:

1. **Backend**: Start the backend and check `/devices` endpoint returns vendor field
2. **Frontend**: Run dashboard and verify device cards show manufacturer info
3. **New Devices**: Register a new device and confirm vendor is auto-populated
4. **Existing Devices**: Run enrichment migration to backfill vendor info

## Files Modified

**Backend:**
- `poc-backend/app/models.py`
- `poc-backend/app/main.py`
- `poc-backend/migrations/002_add_vendor_column.py` (new)
- `poc-backend/migrations/003_enrich_vendors.py` (new)
- `poc-backend/migrations/run_migrations.py` (new)

**Frontend:**
- `dashboard/src/lib/types.ts`
- `dashboard/src/lib/api.ts`
- `dashboard/src/app/devices/page.tsx`
- `dashboard/src/app/devices/[id]/page.tsx`
