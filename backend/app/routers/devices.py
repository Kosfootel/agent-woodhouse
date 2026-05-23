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

from app.models import get_db, Device, Event

router = APIRouter(prefix="/devices", tags=["devices"])


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
    total_count = db.query(Device).count()
    
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


@router.post("/{device_id}/block", response_model=BlockResponse)
def block_device(device_id: int, db: Session = Depends(get_db)):
    """Block a device from network access."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.containment_status == "blocked":
        return BlockResponse(success=True, message="Device already blocked")
    
    device.containment_status = "blocked"
    device.trust_score = 0.0
    
    # Create event log
    event = Event(
        device_id=device_id,
        type="device_blocked",
        description=f"Device {device.mac} ({device.ip}) was blocked"
    )
    db.add(event)
    db.commit()
    
    return BlockResponse(
        success=True,
        message=f"Device {device.mac} has been blocked"
    )


@router.post("/{device_id}/unblock", response_model=BlockResponse)
def unblock_device(device_id: int, db: Session = Depends(get_db)):
    """Unblock a device and restore network access."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.containment_status != "blocked":
        return BlockResponse(success=True, message="Device is not blocked")
    
    device.containment_status = "observing"
    device.trust_score = 50.0  # Reset to neutral
    
    # Create event log
    event = Event(
        device_id=device_id,
        type="device_unblocked",
        description=f"Device {device.mac} ({device.ip}) was unblocked"
    )
    db.add(event)
    db.commit()
    
    return BlockResponse(
        success=True,
        message=f"Device {device.mac} has been unblocked"
    )


class DeviceUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    hostname: Optional[str] = None
    device_type: Optional[str] = None


class DeviceUpdateResponse(BaseModel):
    success: bool
    message: str
    device: DeviceResponse


@router.patch("/{device_id}", response_model=DeviceUpdateResponse)
def update_device(
    device_id: int,
    request: DeviceUpdateRequest,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if request.nickname is not None:
        old_nickname = device.nickname
        device.nickname = request.nickname
        event = Event(
            device_id=device_id,
            type="device_updated",
            description=f"Device nickname changed from '{old_nickname}' to '{request.nickname}'"
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
