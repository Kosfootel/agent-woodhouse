# Router Integration Module

This module provides router discovery, API communication, and device synchronization for the vigil-home project.

## Features

- **Router Discovery**: Automatically finds routers via gateway detection, MAC OUI lookup, and SSDP/UPnP
- **Secure Credential Storage**: AES-256 encrypted credentials using Fernet
- **ASUSWRT Support**: Full API client for ASUS routers (including GT6)
- **Device Sync**: Polls router and syncs connected devices to SQLite
- **FastAPI Integration**: Ready-to-use endpoint stubs

## Installation

### Requirements

```bash
pip install aiohttp cryptography
```

### Files

- `router_integration.py` - Main module with all classes
- `test_router_integration.py` - pytest test suite
- `__init__.py` - Module exports

## Usage

### Quick Start

```python
import asyncio
from router_integration import RouterDiscovery, SecureCredentialManager, ASUSWRTClient

async def main():
    # 1. Discover routers
    discovery = RouterDiscovery()
    routers = await discovery.discover()
    print(f"Found {len(routers)} router(s)")
    
    for router in routers:
        print(f"  - {router.brand} at {router.ip_address}")
    
    # 2. Store credentials securely
    cred_manager = SecureCredentialManager()
    cred_manager.store_credentials(
        router_id="my_router",
        username="admin",
        password="your_password"
    )
    
    # 3. Connect and get devices
    credentials = cred_manager.get_credentials("my_router")
    async with ASUSWRTClient(routers[0].ip_address, credentials) as client:
        devices = await client.get_connected_devices()
        print(f"Found {len(devices)} connected devices")

asyncio.run(main())
```

### Router Discovery

```python
from router_integration import RouterDiscovery

discovery = RouterDiscovery()
routers = await discovery.discover()

# Discovery methods used:
# - Gateway IP detection
# - MAC OUI lookup (ASUS, Netgear, TP-Link, Linksys, Ubiquiti)
# - SSDP/UPnP multicast discovery
```

### Secure Credentials

```python
from router_integration import SecureCredentialManager

# Initialize (creates router_credentials.db)
cred_manager = SecureCredentialManager(db_path="router_credentials.db")

# Store credentials (encrypted with AES-256)
cred_manager.store_credentials(
    router_id="router_192_168_1_1",
    username="admin",
    password="secret",
    api_key="optional_api_key"
)

# Retrieve credentials (automatically decrypted)
creds = cred_manager.get_credentials("router_192_168_1_1")
print(creds["username"])  # "admin"

# Delete credentials
cred_manager.delete_credentials("router_192_168_1_1")
```

### ASUS Router API

```python
from router_integration import ASUSWRTClient

credentials = {"username": "admin", "password": "your_pass"}

async with ASUSWRTClient("192.168.1.1", credentials) as client:
    # Authenticate
    success = await client.authenticate()
    
    # Get all connected devices
    devices = await client.get_connected_devices()
    for device in devices:
        print(f"{device.name}: {device.mac_address} ({device.ip_address})")
    
    # Get router info
    info = await client.get_router_info()
    print(f"Model: {info['model']}, Firmware: {info['firmware']}")
    
    # Get specific device details
    details = await client.get_device_details("AA:BB:CC:DD:EE:FF")
```

### Device Synchronization

```python
from router_integration import DeviceSyncService, RouterDiscovery, ASUSWRTClient

async def sync_router_devices(router_ip, credentials):
    sync_service = DeviceSyncService(db_path="vigil_devices.db")
    
    async with ASUSWRTClient(router_ip, credentials) as client:
        devices = await client.get_connected_devices()
        sync_service.sync_devices(devices, router_ip)
    
    # Query synced devices
    all_devices = sync_service.get_devices(connected_only=False)
    online_devices = sync_service.get_devices(connected_only=True)
    
    # Get specific device
    device = sync_service.get_device_by_mac("AA:BB:CC:DD:EE:FF")
```

## FastAPI Integration

Add to your FastAPI app:

```python
from fastapi import FastAPI
from router_integration import router as router_api

app = FastAPI()
app.include_router(router_api)
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/router/discover` | GET | Discover routers on network |
| `/router/configure` | POST | Configure router credentials |
| `/router/sync` | POST | Sync devices from router |
| `/router/devices` | GET | List synced devices |

### Example API Calls

```bash
# Discover routers
curl http://localhost:8000/router/discover

# Configure router
curl -X POST http://localhost:8000/router/configure \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.1.1", "username": "admin", "password": "pass"}'

# Sync devices
curl -X POST "http://localhost:8000/router/sync?router_id=router_192_168_1_1"

# List devices
curl "http://localhost:8000/router/devices?connected_only=true"
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_router_integration.py -v

# Run specific test class
pytest test_router_integration.py::TestSecureCredentialManager -v

# Run with coverage
pytest test_router_integration.py --cov=router_integration
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Router Integration                        │
├─────────────────────────────────────────────────────────────┤
│  RouterDiscovery        SecureCredentialManager              │
│  ├── Gateway Detection  ├── AES-256 Encryption (Fernet)      │
│  ├── MAC OUI Lookup     └── SQLite Storage                   │
│  └── SSDP/UPnP                                              │
├─────────────────────────────────────────────────────────────┤
│  RouterAPIClient (ABC)        DeviceSyncService              │
│  └── ASUSWRTClient            ├── SQLite Database            │
│      ├── Authentication       └── Device Polling           │
│      ├── Get Devices                                        │
│      └── Router Info                                        │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Endpoints                         │
│  /discover  /configure  /sync  /devices                     │
└─────────────────────────────────────────────────────────────┘
```

## Router Support

### Currently Supported

| Brand | Models | Method | Status |
|-------|--------|--------|--------|
| ASUS | GT6, RT series | ASUSWRT API | ✅ Implemented |

### Planned Support

| Brand | Detection | Status |
|-------|-----------|--------|
| Netgear | OUI + SSDP | 🔜 Planned |
| TP-Link | OUI + SSDP | 🔜 Planned |
| Linksys | OUI + SSDP | 🔜 Planned |
| Ubiquiti | OUI + SSDP | 🔜 Planned |

## Security Notes

- Credentials are encrypted with AES-256 (Fernet)
- Encryption key is stored in the same database (consider moving to environment variable for production)
- HTTPS support available for ASUSWRT (disabled by default for local networks)
- Session tokens are managed automatically

## Troubleshooting

### Router not discovered

1. Check router is on same network
2. Verify SSDP/UPnP is enabled in router settings
3. Check gateway detection with `ip route` command

### Authentication fails

1. Verify username/password
2. Check if router web interface uses non-standard login
3. Try enabling HTTPS if router requires it

### No devices returned

1. Verify authentication succeeded
2. Check router admin UI shows connected clients
3. Some routers require specific API endpoints - check logs

## License

Part of vigil-home project.
