# Vigil Router Agent Specification

## Agent Identity
- **Name:** Vigil Router Specialist
- **Role:** Router administration, firmware management, network defense
- **Capabilities:**
  - ASUSWRT API integration
  - Credential management
  - Firmware updates
  - Device blocking/quarantine
  - Network segmentation
  - Traffic monitoring

## Responsibilities

### 1. Router Discovery
- Identify router model and firmware
- Determine available APIs and capabilities
- Map admin interfaces

### 2. Credential Management
- Secure credential storage in Vigil vault
- Credential rotation schedule
- Access logging

### 3. Network Defense
- Block devices at MAC level
- VLAN isolation for threats
- DHCP manipulation for containment
- DNS redirection for honeypots

### 4. Firmware Maintenance
- Check for updates weekly
- Validate firmware signatures
- Schedule maintenance windows
- Rollback capability

### 5. Monitoring
- Router health checks
- Connected device tracking
- Bandwidth monitoring
- Intrusion detection

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/router/credentials | POST | Store admin credentials |
| /api/router/credentials/status | GET | Check if configured |
| /api/router/credentials/verify | GET | Test credentials work |
| /api/router/credentials | DELETE | Remove stored credentials |
| /api/router/asus/connect | POST | Authenticate to router |
| /api/router/asus/clients | GET | Get connected devices |
| /api/router/asus/block | POST | Block MAC address |
| /api/router/asus/unblock | POST | Unblock MAC address |
| /api/router/asus/firmware | GET | Check firmware version |
| /api/router/asus/status | GET | Get router status |

## Security Considerations

1. **Credential Encryption:** AES-256 via Vigil vault
2. **Access Control:** Only Vigil core can request router actions
3. **Audit Logging:** All router changes logged
4. **Fail-Safe:** Timeout on block commands, auto-unblock after period
5. **Rate Limiting:** Prevent accidental DoS via blocking

## Integration with Vigil Core

```python
# Vigil core requests device containment
async def contain_device(device_id: str, level: str):
    device = await get_device(device_id)
    
    if level == "quarantine":
        # Request router agent to isolate
        await router_agent.isolate_device(
            mac=device.mac_address,
            vlan="quarantine"
        )
    elif level == "block":
        # Block completely
        await router_agent.block_mac(device.mac_address)
```

## Deployment

1. Router agent runs on Vigil server (GX-10)
2. Maintains persistent connection to router
3. WebSocket for real-time router events
4. REST API for Vigil core integration

## Router Capabilities Matrix

| Feature | ASUS GT6 | RT-AX86U | RT-AX88U |
|---------|----------|----------|----------|
| Device List | ✓ | ✓ | ✓ |
| Device Block | ✓ | ✓ | ✓ |
| VLAN Config | ✓ | ✓ | ✓ |
| Firmware Check | ✓ | ✓ | ✓ |
| Traffic Stats | ✓ | ✓ | ✓ |
| Parental Controls | ✓ | ✓ | ✓ |

## Configuration

Environment variables:
- `VIGIL_ROUTER_IP`: Router IP (default: 192.168.50.1)
- `VIGIL_ROUTER_TIMEOUT`: Connection timeout (default: 10s)
- `VIGIL_ROUTER_RETRIES`: Retry attempts (default: 3)

## Testing

```bash
# Test router connectivity
curl -X POST http://localhost:8000/api/router/asus/connect

# Get connected devices
curl http://localhost:8000/api/router/asus/clients

# Block a device
curl -X POST http://localhost:8000/api/router/asus/block \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff", "duration_minutes": 60}'

# Unblock a device  
curl -X POST http://localhost:8000/api/router/asus/unblock \
  -d "mac_address=aa:bb:cc:dd:ee:ff"
```
