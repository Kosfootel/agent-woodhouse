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
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import get_db, Device, Event
from app.utils.crypto import encrypt_password, decrypt_password

# Router integration commented out - future enhancement when Vigil is embedded in router
# See docs/ASUS_RESEARCH.md for details
# from app.routers.factory import RouterFactory, get_connected_devices
# from app.routers.discovery import RouterDiscovery
# from app.routers.base import RouterException, RouterAuthError, RouterConnectionError
from app.routers.implementations.generic import GenericRouter

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


class RouterCredentials(BaseModel):
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
        mac = device_data.get('mac_address', '').upper()
        if not mac:
            continue
        
        # Check if device already exists
        existing = db.query(Device).filter(Device.mac == mac).first()
        
        if existing:
            # Update existing device
            existing.ip = device_data.get('ip_address', existing.ip)
            existing.hostname = device_data.get('hostname') or existing.hostname
            existing.last_seen = datetime.utcnow()
            existing.containment_status = 'observing'
        else:
            # Determine device type from hostname/connection
            hostname = device_data.get('hostname', '').lower()
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
                ip=device_data.get('ip_address', '0.0.0.0'),
                hostname=device_data.get('hostname', 'Unknown Device'),
                device_type=device_type,
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


# ============ API Endpoints ============


@router.post("/setup/discover", response_model=DiscoverResponse)
def discover_routers():
    """
    Scan the network for available routers.
    """
    routers = discover_routers_on_network()
    return DiscoverResponse(routers=routers)


@router.post("/setup/connect", response_model=ConnectResponse)
def connect_router(credentials: RouterCredentials, db: Session = Depends(get_db)):
    """
    Connect to network and discover devices via ARP scanning.
    
    Router API integration is a future enhancement - see docs/ASUS_RESEARCH.md
    For now, uses ARP table scanning which doesn't require router credentials.
    """
    try:
        logger.info(f"Starting device discovery via ARP scanning")
        
        # Use ARP-based discovery (no router credentials needed)
        from app.routers.implementations.generic import GenericRouter
        router_impl = GenericRouter(credentials.ip, credentials.username, credentials.password)
        devices_data = router_impl.get_devices()
        
        if not devices_data:
            return ConnectResponse(
                success=False,
                devices_found=0,
                message="No devices found on network"
            )
        
        # Import devices into database
        imported_count = import_devices_from_router(devices_data, db)
        
        logger.info(f"Successfully imported {imported_count} devices via ARP")
        
        return ConnectResponse(
            success=True,
            devices_found=imported_count,
            message=f"Discovered and imported {imported_count} devices"
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
