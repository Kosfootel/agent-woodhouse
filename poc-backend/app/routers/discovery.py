from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime

from ..device_discovery import DeviceDiscoveryService

router = APIRouter(prefix="/api/devices", tags=["device-discovery"])

# Database setup
DB_PATH = "devices.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for device discovery sources
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_discovery_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            source TEXT NOT NULL,
            data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for IP address history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_ip_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for device metadata (nickname, type)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_metadata (
            device_id TEXT PRIMARY KEY,
            nickname TEXT,
            device_type TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

class DiscoveryRequest(BaseModel):
    ip_address: str
    mac_address: Optional[str] = None

class NicknameRequest(BaseModel):
    nickname: str

class TypeRequest(BaseModel):
    device_type: str

@router.post("/{device_id}/discover")
async def discover_device(device_id: str, request: DiscoveryRequest):
    """Run discovery on specific device using device_discovery module."""
    try:
        # Initialize discovery service
        discovery_service = DeviceDiscoveryService()
        
        # Run discovery on the device
        enriched_device = await discovery_service.discover_device(
            ip=request.ip_address, 
            mac=request.mac_address
        )
        
        # Store discovery results in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Store each discovery result
        for result in enriched_device.discovery_results:
            cursor.execute('''
                INSERT INTO device_discovery_sources 
                (device_id, source, data) VALUES (?, ?, ?)
            ''', (
                device_id, 
                result.source.value, 
                json.dumps(result.__dict__)
            ))
        
        conn.commit()
        conn.close()
        
        return {
            "device_id": device_id,
            "discovered": True,
            "results": [result.__dict__ for result in enriched_device.discovery_results],
            "enriched_device": enriched_device.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@router.get("/{device_id}/discovery-history")
async def get_discovery_history(device_id: str):
    """Get discovery sources for device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT source, data, timestamp FROM device_discovery_sources 
        WHERE device_id = ? ORDER BY timestamp DESC
    ''', (device_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "source": row[0],
            "data": json.loads(row[1]) if row[1] else {},
            "timestamp": row[2]
        })
    
    return {
        "device_id": device_id,
        "discovery_history": history
    }

@router.get("/{device_id}/ip-history")
async def get_ip_history(device_id: str):
    """Get IP address history for device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ip_address, timestamp FROM device_ip_history 
        WHERE device_id = ? ORDER BY timestamp DESC
    ''', (device_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = [{"ip_address": row[0], "timestamp": row[1]} for row in rows]
    
    return {
        "device_id": device_id,
        "ip_history": history
    }

@router.post("/{device_id}/nickname")
async def set_nickname(device_id: str, request: NicknameRequest):
    """Set user nickname for device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert or update nickname
    cursor.execute('''
        INSERT OR REPLACE INTO device_metadata 
        (device_id, nickname, device_type, updated_at) 
        VALUES (?, ?, COALESCE((SELECT device_type FROM device_metadata WHERE device_id = ?), ''), CURRENT_TIMESTAMP)
    ''', (device_id, request.nickname, device_id))
    
    conn.commit()
    conn.close()
    
    return {
        "device_id": device_id,
        "nickname": request.nickname,
        "updated": True
    }

@router.post("/{device_id}/type")
async def set_device_type(device_id: str, request: TypeRequest):
    """Set/override device type for device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert or update device type
    cursor.execute('''
        INSERT OR REPLACE INTO device_metadata 
        (device_id, nickname, device_type, updated_at) 
        VALUES (?, COALESCE((SELECT nickname FROM device_metadata WHERE device_id = ?), ''), ?, CURRENT_TIMESTAMP)
    ''', (device_id, device_id, request.device_type))
    
    conn.commit()
    conn.close()
    
    return {
        "device_id": device_id,
        "device_type": request.device_type,
        "updated": True
    }

# Helper function to log IP address changes
def log_ip_change(device_id: str, ip_address: str):
    """Log IP address changes for a device."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO device_ip_history (device_id, ip_address) 
        VALUES (?, ?)
    ''', (device_id, ip_address))
    
    conn.commit()
    conn.close()