"""
Vigil - Device Management Router
Endpoints for managing network devices.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import ipaddress

from app.models import get_db, Device, Event

router = APIRouter(prefix="/devices", tags=["devices"])


def is_docker_or_internal_ip(ip: str) -> bool:
    """Check if IP is a Docker/internal network IP that should be excluded from display."""
    try:
        addr = ipaddress.ip_address(ip)
        # Exclude Docker networks
        docker_networks = [
            ipaddress.ip_network('172.17.0.0/16'),   # Docker default bridge
            ipaddress.ip_network('172.18.0.0/16'),   # Docker custom bridge
            ipaddress.ip_network('172.19.0.0/16'),   # Docker custom bridge
            ipaddress.ip_network('172.20.0.0/14'),   # Docker large range
            ipaddress.ip_network('172.24.0.0/14'),   # Docker large range
            ipaddress.ip_network('172.28.0.0/14'),   # Docker large range
            ipaddress.ip_network('10.0.0.0/8'),      # Large private range (often container)
            ipaddress.ip_network('127.0.0.0/8'),     # Loopback
        ]
        for network in docker_networks:
            if addr in network:
                return True
        return False
    except ValueError:
        return True  # Invalid IP, filter it out


# ============ Pydantic Models ============

class DeviceResponse(BaseModel):
    id: int
    mac: str
    ip: str
    hostname: Optional[str]
    nickname: Optional[str]
    vendor: Optional[str]
    device_type: Optional[str]
    trust_score: float
    containment_status: str
    online: bool
    last_seen: datetime
    first_seen: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total_count: int


class BlockResponse(BaseModel):
    success: bool
    message: str


class DeviceUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    hostname: Optional[str] = None
    device_type: Optional[str] = None


class DeviceUpdateResponse(BaseModel):
    success: bool
    message: str
    device: Optional[DeviceResponse] = None


# ============ Endpoints ============

@router.get("", response_model=DeviceListResponse)
def list_devices(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all devices with optional filtering."""
    query = db.query(Device)
    
    if status:
        query = query.filter(Device.containment_status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Device.mac.ilike(search_filter)) |
            (Device.ip.ilike(search_filter)) |
            (Device.hostname.ilike(search_filter)) |
            (Device.nickname.ilike(search_filter))
        )
    
    devices = query.order_by(Device.last_seen.desc()).limit(limit).all()
    
    # Filter out Docker/internal IPs
    devices = [d for d in devices if not is_docker_or_internal_ip(d.ip)]
    
    total_count = len(devices)
    
    return DeviceListResponse(
        devices=devices,
        total_count=total_count
    )


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific device by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/{device_id}")
def update_device(
    device_id: int,
    request: DeviceUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update device nickname, hostname, or device type."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if request.nickname is not None:
        device.nickname = request.nickname
        # Create event for nickname change
        event = Event(
            device_id=device_id,
            type="device_updated",
            description=f"Device updated: nickname changed to '{request.nickname}'",
            severity="low",
            acknowledged=True
        )
        db.add(event)
    
    if request.hostname is not None:
        device.hostname = request.hostname
    
    if request.device_type is not None:
        device.device_type = request.device_type
    
    db.commit()
    db.refresh(device)
    
    return DeviceUpdateResponse(
        success=True,
        message="Device updated successfully",
        device=device
    )


@router.post("/{device_id}/block")
def block_device(device_id: int, db: Session = Depends(get_db)):
    """Block a device from accessing the network."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Cannot block trusted devices
    if device.containment_status == "trusted":
        return BlockResponse(
            success=False,
            message="Cannot block trusted devices. Please mark as untrusted first."
        )
    
    device.containment_status = "blocked"
    db.commit()
    
    # Create alert for blocking
    event = Event(
        device_id=device_id,
        type="device_blocked",
        description=f"Device {device.hostname or device.mac} has been blocked",
        severity="medium",
        acknowledged=False
    )
    db.add(event)
    db.commit()
    
    return BlockResponse(
        success=True,
        message=f"Device {device.hostname or device.mac} has been blocked"
    )


@router.post("/{device_id}/unblock")
def unblock_device(device_id: int, db: Session = Depends(get_db)):
    """Unblock a previously blocked device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.containment_status = "allowed"
    db.commit()
    
    return BlockResponse(
        success=True,
        message=f"Device {device.hostname or device.mac} has been unblocked"
    )


@router.post("/{device_id}/trust")
def trust_device(device_id: int, db: Session = Depends(get_db)):
    """Mark a device as trusted (baseline)."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.containment_status = "trusted"
    device.is_known = True
    device.trust_score = 1.0
    db.commit()
    
    # Create event for trust
    event = Event(
        device_id=device_id,
        type="device_trusted",
        description=f"Device {device.hostname or device.nickname or device.mac} marked as trusted",
        severity="low",
        acknowledged=True
    )
    db.add(event)
    db.commit()
    
    return {
        "success": True,
        "message": f"Device {device.hostname or device.nickname or device.mac} marked as trusted",
        "device_id": device_id
    }


@router.post("/{device_id}/untrust")
def untrust_device(device_id: int, db: Session = Depends(get_db)):
    """Remove trust status from a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.containment_status = "allowed"
    device.is_known = False
    device.trust_score = 0.5
    db.commit()
    
    return {
        "success": True,
        "message": f"Device {device.hostname or device.nickname or device.mac} trust status removed",
        "device_id": device_id
    }
