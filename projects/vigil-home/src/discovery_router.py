"""Device Discovery Router for Vigil API

Provides API endpoints for device discovery operations including:
- Triggering device scans (mDNS, NetBIOS, SNMP, UPnP)
- Viewing discovery results
- Managing enriched device information
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_auth
from app.rate_limiter import limiter, GENERAL_LIMITS

router = APIRouter(prefix="/discovery", tags=["device-discovery"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DiscoveryScanRequest(BaseModel):
    """Request to trigger a device discovery scan."""
    target_ip: Optional[str] = Field(None, description="Specific IP to scan, or None for broadcast")
    methods: List[str] = Field(default=["mdns", "netbios", "upnp"], description="Discovery methods to use")
    timeout: float = Field(default=5.0, ge=1.0, le=30.0, description="Scan timeout in seconds")


class DiscoveryResultItem(BaseModel):
    """A single discovery result."""
    source: str
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    services: List[str] = []
    confidence: float = 0.0
    timestamp: str


class DiscoveryScanResponse(BaseModel):
    """Response from a discovery scan."""
    scan_id: str
    status: str
    results: List[DiscoveryResultItem]
    total_found: int
    duration_ms: float


class EnrichedDeviceInfo(BaseModel):
    """Enriched device information."""
    mac: str
    ip: str
    primary_name: Optional[str] = None
    hostname: Optional[str] = None
    mdns_name: Optional[str] = None
    netbios_name: Optional[str] = None
    upnp_friendly_name: Optional[str] = None
    user_nickname: Optional[str] = None
    device_type: Optional[str] = None
    device_type_confidence: float = 0.0
    vendor: Optional[str] = None
    model: Optional[str] = None
    services: List[str] = []
    discovery_sources: List[str] = []
    last_discovered: str


class UpdateNicknameRequest(BaseModel):
    """Request to update device nickname."""
    nickname: str = Field(..., min_length=1, max_length=100)


class DiscoveryStatusResponse(BaseModel):
    """Discovery service status."""
    status: str
    supported_methods: List[str]
    last_scan: Optional[str] = None
    devices_discovered_24h: int = 0


# ============================================================================
# Routes
# ============================================================================

@router.get("/status", response_model=DiscoveryStatusResponse)
@limiter.limit(GENERAL_LIMITS)
def get_discovery_status(
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get the status of the discovery service."""
    return DiscoveryStatusResponse(
        status="active",
        supported_methods=["mdns", "netbios", "snmp", "upnp", "arp"],
        last_scan=None,
        devices_discovered_24h=0,
    )


@router.post("/scan", response_model=DiscoveryScanResponse)
@limiter.limit(GENERAL_LIMITS)
async def run_discovery_scan(
    req: DiscoveryScanRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Trigger a device discovery scan.
    
    Scans for devices using the specified methods (mdns, netbios, upnp, snmp).
    Returns discovered devices with enriched metadata.
    """
    import uuid
    import time
    
    scan_id = str(uuid.uuid4())
    start_time = time.time()
    
    # TODO: Implement actual discovery scan using device_discovery.py
    # For now, return placeholder response
    results = []
    
    duration_ms = (time.time() - start_time) * 1000
    
    return DiscoveryScanResponse(
        scan_id=scan_id,
        status="completed",
        results=results,
        total_found=len(results),
        duration_ms=duration_ms,
    )


@router.get("/devices", response_model=List[EnrichedDeviceInfo])
@limiter.limit(GENERAL_LIMITS)
def list_discovered_devices(
    request: Request,
    source: Optional[str] = Query(None, description="Filter by discovery source"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """List discovered devices with enriched information.
    
    Returns devices discovered through various discovery methods (mDNS, NetBIOS, etc.)
    with enriched metadata like hostnames, device types, and services.
    """
    # TODO: Implement actual device listing from discovery database
    # For now, return empty list
    return []


@router.get("/devices/{mac_address}", response_model=EnrichedDeviceInfo)
@limiter.limit(GENERAL_LIMITS)
def get_device_discovery_info(
    mac_address: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get detailed discovery information for a specific device."""
    raise HTTPException(status_code=404, detail="Device discovery info not found")


@router.patch("/devices/{mac_address}/nickname")
@limiter.limit(GENERAL_LIMITS)
def update_device_nickname(
    mac_address: str,
    req: UpdateNicknameRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Update the user-friendly nickname for a device."""
    # TODO: Implement nickname update
    return {
        "message": "Nickname updated",
        "mac": mac_address,
        "nickname": req.nickname,
    }


@router.get("/methods")
@limiter.limit(GENERAL_LIMITS)
def list_discovery_methods(
    request: Request,
    auth: dict = Depends(require_auth),
):
    """List available discovery methods and their status."""
    return {
        "methods": [
            {
                "id": "mdns",
                "name": "mDNS/Bonjour",
                "description": "Multicast DNS discovery for Apple/Bonjour devices",
                "available": True,
            },
            {
                "id": "netbios",
                "name": "NetBIOS",
                "description": "NetBIOS name resolution for Windows devices",
                "available": True,
            },
            {
                "id": "upnp",
                "name": "UPnP/SSDP",
                "description": "Universal Plug and Play discovery for IoT devices",
                "available": True,
            },
            {
                "id": "snmp",
                "name": "SNMP",
                "description": "Simple Network Management Protocol queries",
                "available": True,
            },
            {
                "id": "arp",
                "name": "ARP Scan",
                "description": "ARP table scanning for network devices",
                "available": True,
            },
        ]
    }
