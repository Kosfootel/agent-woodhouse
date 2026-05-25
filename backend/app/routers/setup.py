"""
Vigil Setup Router

Handles initial setup wizard:
- Router discovery on local network
- Router connection with credentials
- Device import and initial population

Updated to use new router abstraction architecture (factory pattern).
"""

import os
import logging
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import get_db, Device, Event
from app.utils.crypto import encrypt_password, decrypt_password

# Router integration commented out - future enhancement when Vigil is embedded in router
# See docs/ASUS_RESEARCH.md for details
# from app.routers.factory import RouterFactory, get_connected_devices
from app.routers.discovery import RouterDiscovery
# from app.routers.base import RouterException, RouterAuthError, RouterConnectionError
from app.routers.implementations.generic import GenericRouter

# Import device discovery service for multi-protocol scanning
from app.device_discovery import DeviceDiscoveryService, DiscoverySource, DiscoveryResult
from app.active_discovery import run_active_scan, ActiveDiscovery

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"])


# ============ Pydantic Models ============

class DiscoveredRouter(BaseModel):
    ip: str
    type: str
    model: Optional[str] = None
    confidence: float = 0.0


class DiscoverResponse(BaseModel):
    routers: List[DiscoveredRouter]


class RouterCredentialsInput(BaseModel):
    ip: str
    username: str
    password: str


class ConnectResponse(BaseModel):
    success: bool
    devices_found: int
    message: str


class SetupStatus(BaseModel):
    is_setup_complete: bool
    router_connected: bool
    device_count: int


class AgentAnnouncementInput(BaseModel):
    name: str
    ip: str
    mac: Optional[str] = None
    agent_type: str = "mesh"
    capabilities: List[str] = []


# ============ Helper Functions ============

def discover_routers_on_network() -> List[DiscoveredRouter]:
    """
    Scan the local network for routers using the new router discovery.
    
    Uses MAC OUI lookup, HTTP fingerprinting, and other detection methods.
    """
    discovered = []
    discovery = RouterDiscovery()
    
    # Common router IP ranges to check
    common_ips = [
        "192.168.50.1",   # ASUS default
        "192.168.1.1",    # Generic
        "192.168.0.1",    # Netgear, D-Link
        "10.0.0.1",       # Some ISPs
        "10.0.1.1",       # Apple routers
    ]
    
    import requests
    from requests.exceptions import RequestException
    
    for ip in common_ips:
        try:
            # Check if router is reachable
            response = requests.get(f"http://{ip}/", timeout=2, allow_redirects=True)
            
            if response.status_code == 200:
                # Use new discovery to detect vendor
                result = discovery.discover(ip)
                
                discovered.append(DiscoveredRouter(
                    ip=ip,
                    type=result.vendor.value,
                    model=result.router_info.model if result.router_info else None,
                    confidence=result.confidence
                ))
                    
        except RequestException:
            continue
    
    # Sort by confidence (highest first)
    discovered.sort(key=lambda x: x.confidence, reverse=True)
    
    return discovered


def save_router_credentials(ip: str, username: str, password: str, db: Session):
    """Save encrypted router credentials to database."""
    from sqlalchemy import text
    
    encrypted = encrypt_password(password)
    
    # Store in a configuration table or special device entry
    # Using environment or config for now
    os.environ["VIGIL_ROUTER_IP"] = ip
    os.environ["VIGIL_ROUTER_USER"] = username
    # Password should be stored encrypted in database


def import_devices_from_router(devices_data: list, db: Session) -> int:
    """
    Import discovered devices into the database.
    Returns count of devices imported.
    """
    count = 0
    
    for device_data in devices_data:
        mac = get_attr(device_data, 'mac_address', '').upper()
        if not mac:
            continue
        
        # Check if device already exists
        existing = db.query(Device).filter(Device.mac == mac).first()
        
        if existing:
            # Update existing device
            existing.ip = get_attr(device_data, 'ip_address', existing.ip)
            existing.hostname = get_attr(device_data, 'hostname') or existing.hostname
            existing.vendor = get_attr(device_data, "vendor") or existing.vendor
            existing.last_seen = datetime.utcnow()
            existing.containment_status = 'observing'
        else:
            # Determine device type from hostname/connection
            hostname = get_attr(device_data, 'hostname', '').lower()
            device_type = 'unknown'
            
            if any(kw in hostname for kw in ['phone', 'iphone', 'pixel', 'samsung']):
                device_type = 'phone'
            elif any(kw in hostname for kw in ['macbook', 'laptop', 'desktop', 'pc']):
                device_type = 'laptop'
            elif any(kw in hostname for kw in ['tv', 'speaker', 'homepod', 'echo', 'nest']):
                device_type = 'iot'
            
            # Create new device
            new_device = Device(
                mac=mac,
                ip=get_attr(device_data, 'ip_address', '0.0.0.0'),
                hostname=get_attr(device_data, 'hostname', 'Unknown Device'),
                device_type=device_type,
                vendor=get_attr(device_data, "vendor"),
                containment_status='observing',
                trust_score=50.0
            )
            db.add(new_device)
            
            # Create event log
            event = Event(
                type='device_joined',
                description=f"New device discovered: {new_device.hostname} ({new_device.ip})"
            )
            db.add(event)
        
        count += 1
    
    db.commit()
    return count


def import_discovery_results(devices: List[DiscoveryResult], db: Session) -> int:
    """
    Import devices discovered via multi-protocol scanning.
    Returns count of new devices imported.
    """
    count = 0
    
    for result in devices:
        # Get the best identifier - prefer MAC, fall back to IP
        mac = result.mac
        ip = result.ip
        
        if not mac and not ip:
            continue
            
        # Try to find existing device by MAC or IP
        existing = None
        if mac:
            existing = db.query(Device).filter(Device.mac == mac.upper()).first()
        if not existing and ip:
            existing = db.query(Device).filter(Device.ip == ip).first()
        
        # Determine the best name to use
        name = (result.device_name or 
                result.hostname or 
                f"Device-{ip.split('.')[-1] if ip else 'unknown'}")
        
        # Get device type from result
        device_type = result.device_type or 'unknown'
        
        if existing:
            # Update existing device with enriched info
            existing.ip = ip or existing.ip
            existing.hostname = result.hostname or existing.hostname
            existing.vendor = result.vendor or existing.vendor
            existing.device_type = device_type if device_type != 'unknown' else existing.device_type
            
            # Update discovery_method to show multi-protocol was used
            if existing.discovery_method == 'manual':
                existing.discovery_method = result.source.value
            elif result.source.value not in existing.discovery_method:
                existing.discovery_method = f"{existing.discovery_method},{result.source.value}"
            
            existing.last_seen = datetime.utcnow()
        else:
            # Create new device from discovery result
            new_device = Device(
                mac=mac.upper() if mac else f"DISCOVERED_{ip.replace('.', '_')}",
                ip=ip or '0.0.0.0',
                hostname=result.hostname,
                nickname=result.device_name,
                device_type=device_type,
                vendor=result.vendor,
                
                containment_status='observing',
                trust_score=50.0,
                discovery_method=result.source.value
            )
            db.add(new_device)
            
            # Create event log
            event = Event(
                type='device_joined',
                description=f"New device via {result.source.value}: {name} ({ip})"
            )
            db.add(event)
            count += 1
    
    db.commit()
    return count


def import_active_scan_results(devices: List[Dict], db: Session) -> int:
    """
    Import devices discovered via active port scanning.
    Returns count of new devices imported.
    """
    count = 0
    scanner = ActiveDiscovery()
    
    for device_info in devices:
        ip = device_info['ip']
        open_ports = device_info.get('open_ports', [])
        
        if not ip:
            continue
        
        # Try to find existing device by IP
        existing = db.query(Device).filter(Device.ip == ip).first()
        
        # OS fingerprinting
        os_guess = scanner.fingerprint_os(open_ports)
        device_type = scanner.infer_device_type(open_ports, os_guess)
        
        # Build metadata
        import json
        metadata = {
            "open_ports": open_ports,
            "discovery_method": "active_scan",
            "confidence": device_info.get('confidence', 0.6),
            "os_guess": os_guess
        }
        
        if existing:
            # Update existing device with enriched info
            if hasattr(existing, 'os_info'):
                existing.os_info = os_guess
            existing.device_type = device_type if existing.device_type == 'unknown' else existing.device_type
            
            # Update discovery_method to show active scan was used
            if existing.discovery_method == 'manual':
                existing.discovery_method = "active_scan"
            elif "active_scan" not in existing.discovery_method:
                existing.discovery_method = f"{existing.discovery_method},active_scan"
            
            existing.last_seen = datetime.utcnow()
            
            # Update metadata
            if existing.metadata:
                try:
                    existing_meta = json.loads(existing.metadata) if isinstance(existing.metadata, str) else existing.metadata
                    existing_meta.update(metadata)
                    existing.metadata = json.dumps(existing_meta)
                except:
                    existing.metadata = json.dumps(metadata)
            else:
                existing.metadata = json.dumps(metadata)
        else:
            # Create new device from active scan
            new_device = Device(
                mac=f"ACTIVE_{ip.replace('.', '_')}",
                ip=ip,
                hostname=f"Active-Scan-{ip.split('.')[-1]}",
                device_type=device_type,
                vendor=os_guess,
                containment_status='observing',
                trust_score=40.0,  # Lower trust for active-only devices
                discovery_method="active_scan",
                metadata=json.dumps(metadata)
            )
            db.add(new_device)
            
            # Create event log
            ports_str = ", ".join([str(p['port']) for p in open_ports])
            event = Event(
                type='device_joined',
                description=f"New device via active scan: {ip} (ports: {ports_str})"
            )
            db.add(event)
            count += 1
            logger.info(f"Imported active-scan device: {ip} with ports {ports_str}")
    
    db.commit()
    return count


# ============ API Endpoints ============


@router.post("/setup/discover", response_model=DiscoverResponse)
def discover_routers():
    """
    Scan the network for available routers.
    """
    routers = discover_routers_on_network()
    return DiscoverResponse(routers=routers)


@router.post("/setup/connect", response_model=ConnectResponse)
async def connect_router(credentials: RouterCredentialsInput, db: Session = Depends(get_db)):
    """
    Connect to network and discover devices via ARP scanning + multi-protocol discovery.
    
    Router API integration is a future enhancement - see docs/ASUS_RESEARCH.md
    For now, uses ARP table scanning which doesn't require router credentials,
    plus mDNS/UPnP/NetBIOS/SNMP for enhanced device discovery.
    """
    try:
        logger.info(f"Starting device discovery via ARP scanning + multi-protocol discovery")
        
        # Use ARP-based discovery (no router credentials needed)
        from app.routers.implementations.generic import GenericRouter
        from app.routers.base import RouterCredentials as BaseRouterCreds
        creds = BaseRouterCreds(ip_address=credentials.ip, username=credentials.username, password=credentials.password)
        router_impl = GenericRouter(creds)
        devices_data = router_impl.get_connected_devices()
        
        arp_count = len(devices_data) if devices_data else 0
        logger.info(f"ARP discovery found {arp_count} devices")
        
        # Import ARP-discovered devices first
        if devices_data:
            arp_imported = import_devices_from_router(devices_data, db)
            logger.info(f"Imported {arp_imported} devices from ARP scan")
        
        # Run multi-protocol discovery
        discovery_service = DeviceDiscoveryService()
        discovered_devices = []
        
        try:
            logger.info("Starting multi-protocol discovery (UPnP/mDNS/NetBIOS/SNMP)...")
            discovered_devices = await discovery_service.scan_network()
            logger.info(f"Multi-protocol discovery found {len(discovered_devices)} devices")
            
            # Log each discovered device
            for device in discovered_devices:
                logger.info(f"  - {device.device_name or device.hostname or 'unknown'} @ {device.ip} via {device.source.value}")
            
            # Import discovered devices
            if discovered_devices:
                discovery_imported = import_discovery_results(discovered_devices, db)
                logger.info(f"Imported {discovery_imported} new devices from multi-protocol scan")
        except Exception as e:
            logger.error(f"Multi-protocol discovery failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Run active scanning for devices not found via passive discovery
        active_devices = []
        try:
            logger.info("Starting active network scanning (TCP port scanning)...")
            active_devices = await run_active_scan(network="192.168.50", timeout=2.0)
            logger.info(f"Active scanning found {len(active_devices)} additional devices")
            
            # Import discovered devices from active scanning
            if active_devices:
                active_imported = import_active_scan_results(active_devices, db)
                logger.info(f"Imported {active_imported} new devices from active scan")
        except Exception as e:
            logger.error(f"Active scanning failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Get total device count for response
        total_devices = db.query(Device).filter(Device.mac != "ROUTER_CONFIG").count()
        
        return ConnectResponse(
            success=True,
            devices_found=total_devices,
            message=f"Discovery complete. ARP: {arp_count}, Multi-protocol: {len(discovered_devices)}, Active: {len(active_devices)}, Total in DB: {total_devices}"
        )
        
    except Exception as e:
        logger.error(f"Error during device discovery: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ConnectResponse(
            success=False,
            devices_found=0,
            message=f"Error: {str(e)}"
        )


@router.post("/setup/agent/announce")
async def announce_agent(announcement: AgentAnnouncementInput, db: Session = Depends(get_db)):
    """
    Allow agents to self-announce to Vigil.
    
    This endpoint allows mesh agents to register themselves with the Vigil
    system, marking them as known agents in the device database.
    """
    logger.info(f"Agent announcement: {announcement.name} @ {announcement.ip}")
    
    # Check if device exists by IP
    device = db.query(Device).filter(Device.ip == announcement.ip).first()
    
    # Also check by MAC if provided
    if not device and announcement.mac:
        device = db.query(Device).filter(Device.mac == announcement.mac.upper()).first()
    
    # Build metadata JSON string
    metadata_str = f"agent_type:{announcement.agent_type};capabilities:{','.join(announcement.capabilities)};announced_at:{datetime.utcnow().isoformat()}"
    
    if device:
        # Update existing device
        device.nickname = announcement.name
        device.last_seen = datetime.utcnow()
        
        # Store agent info in hostname field or vendor field as markers
        device.hostname = f"AGENT:{announcement.name}"
        device.vendor = f"VIGIL_AGENT:{announcement.agent_type}"
        
        db.commit()
        logger.info(f"Updated existing device {device.id} as agent {announcement.name}")
        return {
            "status": "updated",
            "device_id": device.id,
            "message": f"Agent {announcement.name} updated on existing device"
        }
    else:
        # Create new device record for the agent
        mac_addr = announcement.mac.upper() if announcement.mac else f"AGENT_{announcement.ip.replace('.', '_')}"
        new_device = Device(
            mac=mac_addr,
            ip=announcement.ip,
            hostname=f"AGENT:{announcement.name}",
            nickname=announcement.name,
            vendor=f"VIGIL_AGENT:{announcement.agent_type}",
            device_type="agent",
            containment_status='trusted',
            trust_score=100.0,
            discovery_method="agent_announcement",
            is_known=True
        )
        db.add(new_device)
        db.commit()
        
        # Create event log
        event = Event(
            type='agent_registered',
            description=f"New agent registered: {announcement.name} ({announcement.ip}) type={announcement.agent_type}"
        )
        db.add(event)
        db.commit()
        
        logger.info(f"Created new agent device {new_device.id} for {announcement.name}")
        return {
            "status": "created",
            "device_id": new_device.id,
            "message": f"Agent {announcement.name} registered as new device"
        }


@router.get("/setup/agents")
async def list_agents(db: Session = Depends(get_db)):
    """
    List all registered agents.
    """
    # Find devices marked as agents
    agents = db.query(Device).filter(Device.hostname.like("AGENT:%")).all()
    
    return {
        "count": len(agents),
        "agents": [
            {
                "id": agent.id,
                "name": agent.nickname,
                "ip": agent.ip,
                "mac": agent.mac,
                "type": agent.vendor.replace("VIGIL_AGENT:", "") if agent.vendor and agent.vendor.startswith("VIGIL_AGENT:") else "unknown",
                "last_seen": agent.last_seen.isoformat() if agent.last_seen else None
            }
            for agent in agents
        ]
    }


@router.get("/setup/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Get the current setup status.
    """
    # Count real devices (exclude config markers)
    device_count = db.query(Device).filter(Device.mac != "ROUTER_CONFIG").count()
    
    # Setup is complete if we have devices imported
    return SetupStatus(
        is_setup_complete=device_count > 0,
        router_connected=device_count > 0,
        device_count=device_count
    )


# Helper to get attribute from dict or dataclass
def get_attr(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict):
        return obj.get(key, default)
    return default

# ============ Router Credential Setup (New) ============

from typing import Dict


# Include router credential endpoints from separate module
try:
    from . import setup_router_credentials
    router.include_router(setup_router_credentials.router)
except Exception as e:
    logger.warning(f"Could not include router credentials module: {e}")
