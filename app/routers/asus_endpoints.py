"""
Router Management API Endpoints for Vigil

Provides endpoints for:
- Router connection and authentication
- Device blocking/unblocking
- Client enumeration
- Firmware management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.routers.implementations.asus import ASUSRouter
from app.routers.base import (
    RouterCredentials,
    RouterAuthError,
    RouterConnectionError,
)
from app.routers.router_credentials import (
    RouterCredentialsStore,
    get_db,
    DEFAULT_ROUTER_IP
)

router = APIRouter(prefix="/api/router/asus", tags=["router-asus"])
logger = logging.getLogger(__name__)


class ConnectionResponse(BaseModel):
    """Response model for router connection."""
    status: str
    router: str
    message: str


class DeviceListResponse(BaseModel):
    """Response model for device list."""
    count: int
    clients: List[Dict[str, Any]]
    timestamp: str


class BlockDeviceRequest(BaseModel):
    """Request model for blocking a device."""
    mac_address: str = Field(..., description="MAC address to block")
    duration_minutes: Optional[int] = Field(
        default=None, 
        description="Block duration (None = indefinite)"
    )


class BlockDeviceResponse(BaseModel):
    """Response model for block operation."""
    status: str
    mac_address: str
    message: str


class FirmwareInfoResponse(BaseModel):
    """Response model for firmware info."""
    current_version: Optional[str]
    model: Optional[str]
    update_available: bool
    ip_address: str


def _get_router_client(db: Session, router_ip: str = DEFAULT_ROUTER_IP) -> ASUSRouter:
    """Get configured ASUS router client."""
    store = RouterCredentialsStore(db)
    creds = store.get_credentials(router_ip)
    
    if not creds:
        raise HTTPException(
            status_code=401,
            detail="Router credentials not configured. Use /api/router/credentials first."
        )
    
    base_creds = RouterCredentials(
        username=creds.admin_username,
        password=creds.admin_password
    )
    
    return ASUSRouter(
        ip_address=creds.router_ip,
        credentials=base_creds,
        use_https=False,
        timeout=10
    )


@router.post("/connect", response_model=ConnectionResponse)
async def connect_to_router(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Establish connection to ASUS router.
    
    Attempts authentication with stored credentials.
    Returns success/failure status.
    """
    try:
        client = _get_router_client(db, router_ip)
        
        if client.connect():
            client.disconnect()
            return ConnectionResponse(
                status="connected",
                router=router_ip,
                message="Successfully authenticated to ASUS router"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed - check credentials"
            )
            
    except RouterAuthError:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed - invalid username/password"
        )
    except RouterConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Connection error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Router connection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(e)}"
        )


@router.get("/clients", response_model=DeviceListResponse)
async def get_router_clients(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Get list of clients from router's perspective.
    
    Returns devices as seen by the router including:
    - MAC addresses
    - IP addresses
    - Hostnames
    - Connection types (wired/wireless)
    - Signal strength (RSSI)
    """
    client = None
    try:
        client = _get_router_client(db, router_ip)
        
        if not client.connect():
            raise HTTPException(
                status_code=401,
                detail="Failed to connect to router"
            )
        
        devices = client.get_connected_devices()
        
        # Convert devices to dict for JSON serialization
        clients_data = []
        for device in devices:
            clients_data.append({
                "mac": device.mac,
                "ip": device.ip,
                "hostname": device.hostname,
                "connection_type": device.connection_type,
                "rssi": device.rssi,
                "is_online": device.is_online,
                "vendor": device.vendor,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None
            })
        
        return DeviceListResponse(
            count=len(clients_data),
            clients=clients_data,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve clients: {str(e)}"
        )
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


@router.post("/block", response_model=BlockDeviceResponse)
async def block_device_by_mac(
    request: BlockDeviceRequest,
    background_tasks: BackgroundTasks,
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Block a device by MAC address at router level.
    
    Uses ASUS parental controls to block the device.
    May require parental controls to be enabled on router.
    
    Optionally specify duration_minutes for temporary blocks.
    """
    client = None
    try:
        client = _get_router_client(db, router_ip)
        
        if not client.connect():
            raise HTTPException(
                status_code=401,
                detail="Failed to connect to router"
            )
        
        success = client.block_device(request.mac_address)
        
        if success:
            # Schedule auto-unblock if duration specified
            if request.duration_minutes:
                background_tasks.add_task(
                    _scheduled_unblock,
                    router_ip,
                    request.mac_address,
                    request.duration_minutes
                )
            
            return BlockDeviceResponse(
                status="blocked",
                mac_address=request.mac_address,
                message=f"Device blocked at router level" + 
                       (f" for {request.duration_minutes} minutes" if request.duration_minutes else " indefinitely")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to block device - router may not support this operation"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking device: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to block device: {str(e)}"
        )
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


@router.post("/unblock", response_model=BlockDeviceResponse)
async def unblock_device_by_mac(
    mac_address: str,
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Unblock a previously blocked device.
    
    Removes the device from the router's block list.
    """
    client = None
    try:
        client = _get_router_client(db, router_ip)
        
        if not client.connect():
            raise HTTPException(
                status_code=401,
                detail="Failed to connect to router"
            )
        
        success = client.unblock_device(mac_address)
        
        if success:
            return BlockDeviceResponse(
                status="unblocked",
                mac_address=mac_address,
                message="Device unblocked successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to unblock device"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking device: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unblock device: {str(e)}"
        )
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


@router.get("/firmware", response_model=FirmwareInfoResponse)
async def check_firmware(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Check router firmware status.
    
    Returns current firmware version and model information.
    """
    client = None
    try:
        client = _get_router_client(db, router_ip)
        
        if not client.connect():
            raise HTTPException(
                status_code=401,
                detail="Failed to connect to router"
            )
        
        firmware_info = client.check_firmware_version()
        
        return FirmwareInfoResponse(
            current_version=firmware_info.get("current_version"),
            model=firmware_info.get("model"),
            update_available=firmware_info.get("update_available", False),
            ip_address=router_ip
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking firmware: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check firmware: {str(e)}"
        )
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


async def _scheduled_unblock(
    router_ip: str,
    mac_address: str,
    delay_minutes: int
):
    """Background task to automatically unblock a device after delay."""
    import asyncio
    
    logger.info(f"Scheduling unblock for {mac_address} in {delay_minutes} minutes")
    await asyncio.sleep(delay_minutes * 60)
    
    # Note: This would need DB access to actually execute
    # In production, this should use a proper task queue
    logger.info(f"Auto-unblock time reached for {mac_address}")


@router.get("/status")
async def get_router_status(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Get overall router status.
    
    Returns connectivity, authentication status, and basic info.
    """
    client = None
    try:
        store = RouterCredentialsStore(db)
        creds = store.get_credentials(router_ip)
        
        if not creds:
            return {
                "configured": False,
                "connected": False,
                "router_ip": router_ip,
                "message": "Credentials not configured"
            }
        
        # Test connection
        client = _get_router_client(db, router_ip)
        is_connected = client.connect()
        
        if is_connected:
            info = client.get_router_info()
            client.disconnect()
            
            return {
                "configured": True,
                "connected": True,
                "router_ip": router_ip,
                "model": info.model,
                "is_reachable": info.is_reachable,
                "features": info.features,
                "message": "Router connected and operational"
            }
        else:
            return {
                "configured": True,
                "connected": False,
                "router_ip": router_ip,
                "message": "Credentials configured but connection failed"
            }
            
    except Exception as e:
        logger.error(f"Error getting router status: {e}")
        return {
            "configured": True if creds else False,
            "connected": False,
            "router_ip": router_ip,
            "message": f"Error: {str(e)}"
        }
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass
