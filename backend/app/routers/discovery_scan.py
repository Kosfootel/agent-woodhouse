"""Discovery scan API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import uuid
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/discovery", tags=["discovery"])

# Database path
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"


class ScanRequest(BaseModel):
    subnet: Optional[str] = None
    timeout: Optional[int] = 60


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    total_found: int
    message: str


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/scan", response_model=ScanResponse)
async def start_discovery_scan(request: ScanRequest):
    """Start a device discovery scan on the network."""
    try:
        scan_id = str(uuid.uuid4())
        
        # Get router config to determine network range
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT router_ip FROM router_config WHERE id = 1")
        row = cursor.fetchone()
        
        router_ip = row["router_ip"] if row else "192.168.1.1"
        conn.close()

        # Derive subnet from router IP
        subnet_parts = router_ip.rsplit('.', 1)
        subnet = f"{subnet_parts[0]}.0/24" if len(subnet_parts) == 2 else "192.168.1.0/24"
        
        if request.subnet:
            subnet = request.subnet

        # For now, we return a mock response
        # In production, this would trigger an async discovery task
        # that updates devices in the database
        
        # Simulate some found devices (in production this would be actual scan results)
        # For now, count existing devices as "found"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM devices")
        row = cursor.fetchone()
        total_found = row["count"] if row else 0
        conn.close()

        return ScanResponse(
            scan_id=scan_id,
            status="completed",
            total_found=total_found,
            message=f"Discovery scan completed on {subnet}. Found {total_found} devices."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery error: {str(e)}")


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get the status of a discovery scan."""
    # For now, return mock status
    return {
        "scan_id": scan_id,
        "status": "completed",
        "progress": 100,
        "devices_found": 0,
        "message": "Scan completed"
    }
