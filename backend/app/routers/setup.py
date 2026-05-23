"""
Vigil Setup Router

Handles initial setup wizard:
- Router discovery on local network
- Router connection with credentials
- Device import and initial population
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, Device, Event
from app.utils.crypto import encrypt_password, decrypt_password

from app.router_monitor import RouterAuthError, RouterConnectionError, get_connected_devices

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"])


# ============ Pydantic Models ============

class DiscoveredRouter(BaseModel):
    ip: str
    type: str
    model: Optional[str] = None


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
    Scan the local network for routers.
    For now, this checks common router IPs and attempts detection.
    """
    discovered = []
    
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
            # Try to detect router by checking for common endpoints
            # ASUS routers have /login.cgi or /Main_Login.asp
            response = requests.get(f"http://{ip}/", timeout=2, allow_redirects=True)
            
            if response.status_code == 200:
                text = response.text.lower()
                
                # Detect router type from response
                if 'asus' in text or 'asuswrt' in text:
                    discovered.append(DiscoveredRouter(ip=ip, type="ASUS", model="ZenWiFi"))
                elif 'netgear' in text:
                    discovered.append(DiscoveredRouter(ip=ip, type="Netgear", model="Unknown"))
                elif 'tp-link' in text or 'tplink' in text:
                    discovered.append(DiscoveredRouter(ip=ip, type="TP-Link", model="Unknown"))
                elif 'linksys' in text:
                    discovered.append(DiscoveredRouter(ip=ip, type="Linksys", model="Unknown"))
                else:
                    # Generic router detected
                    discovered.append(DiscoveredRouter(ip=ip, type="Unknown", model="Router"))
                    
        except RequestException:
            continue
    
    return discovered


def save_router_credentials(ip: str, username: str, password: str, db: Session):
    """
    Save encrypted router credentials to the database.
    Uses a simple Device record with special status to store router info.
    """
    encrypted_password = encrypt_password(password)
    
    # Check if we already have router config
    existing = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    
    if existing:
        existing.name = f"router:{ip}:{username}:{encrypted_password}"
    else:
        router_config = Device(
            mac="ROUTER_CONFIG",
            ip=ip,
            name=f"router:{ip}:{username}:{encrypted_password}",
            type="router",
            status="configured"
        )
        db.add(router_config)
    
    db.commit()


def get_router_credentials(db: Session) -> Optional[tuple]:
    """
    Retrieve stored router credentials.
    Returns (ip, username, password) tuple or None.
    """
    config = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    if not config:
        return None
    
    try:
        # Parse stored format: router:ip:username:encrypted_password
        parts = config.name.split(":")
        if len(parts) >= 4:
            ip = parts[1]
            username = parts[2]
            encrypted_password = ":".join(parts[3:])  # Handle colons in password
            password = decrypt_password(encrypted_password)
            return (ip, username, password)
    except Exception as e:
        logger.error(f"Failed to parse router credentials: {e}")
    
    return None


def import_devices_from_router(devices_data: list, db: Session) -> int:
    """
    Import discovered devices into the database.
    Returns count of devices imported.
    """
    count = 0
    
    for device_data in devices_data:
        mac = device_data.get('mac', '').upper()
        if not mac:
            continue
        
        # Check if device already exists
        existing = db.query(Device).filter(Device.mac == mac).first()
        
        if existing:
            # Update existing device
            existing.ip = device_data.get('ip', existing.ip)
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
                ip=device_data.get('ip', '0.0.0.0'),
                hostname=device_data.get('hostname', 'Unknown Device'),
                device_type=device_type,
                containment_status='observing',
                trust_score=50.0
            )
            db.add(new_device)
            
            # Create event log
            event = Event(
                type='device_joined',
                description=f"New device discovered: {new_device.name} ({new_device.ip})"
            )
            db.add(event)
        
        count += 1
    
    db.commit()
    return count


# ============ API Endpoints ============

from datetime import datetime


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
    Connect to router with provided credentials and import devices.
    """
    try:
        # Attempt to connect to router
        logger.info(f"Attempting to connect to router at {credentials.ip}")
        
        devices_data = get_connected_devices(
            router_ip=credentials.ip,
            username=credentials.username,
            password=credentials.password
        )
        
        if not devices_data:
            return ConnectResponse(
                success=False,
                devices_found=0,
                message="Connected successfully but no devices found"
            )
        
        # Save encrypted credentials
        save_router_credentials(
            credentials.ip,
            credentials.username,
            credentials.password,
            db
        )
        
        # Import devices into database
        imported_count = import_devices_from_router(devices_data, db)
        
        logger.info(f"Successfully imported {imported_count} devices from router")
        
        return ConnectResponse(
            success=True,
            devices_found=imported_count,
            message=f"Connected and imported {imported_count} devices"
        )
        
    except RouterAuthError as e:
        logger.error(f"Authentication failed: {e}")
        return ConnectResponse(
            success=False,
            devices_found=0,
            message=f"Authentication failed: {str(e)}"
        )
    except RouterConnectionError as e:
        logger.error(f"Connection failed: {e}")
        return ConnectResponse(
            success=False,
            devices_found=0,
            message=f"Connection failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during connection: {e}")
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
    # Check if router is configured
    router_config = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    router_connected = router_config is not None
    
    # Count devices
    device_count = db.query(Device).filter(Device.mac != "ROUTER_CONFIG").count()
    
    return SetupStatus(
        is_setup_complete=router_connected and device_count > 0,
        router_connected=router_connected,
        device_count=device_count
    )
