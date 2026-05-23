"""Devices API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/devices", tags=["devices"])

# Database path
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"


class DeviceResponse(BaseModel):
    id: int
    mac: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    trust_score: float = 50.0
    status: str = "active"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    nickname: Optional[str] = None
    online: bool = True


class DevicesListResponse(BaseModel):
    count: int
    devices: List[DeviceResponse]


class DeviceUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    device_type: Optional[str] = None


class BlockRequest(BaseModel):
    pass


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/", response_model=DevicesListResponse)
async def get_devices(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    device_type: Optional[str] = None
):
    """Get all devices with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                id,
                mac,
                ip,
                hostname,
                device_type,
                vendor,
                trust_score,
                status,
                first_seen,
                last_seen,
                nickname
            FROM devices
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if device_type:
            query += " AND device_type = ?"
            params.append(device_type)

        query += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Calculate online status based on last_seen
        now = datetime.now()
        devices = []
        for row in rows:
            last_seen = None
            if row["last_seen"]:
                try:
                    last_seen = datetime.fromisoformat(row["last_seen"].replace('Z', '+00:00'))
                except:
                    pass
            
            # Device is online if seen in last 5 minutes
            online = False
            if last_seen:
                diff = (now - last_seen.replace(tzinfo=None)).total_seconds()
                online = diff < 300  # 5 minutes

            devices.append(DeviceResponse(
                id=row["id"],
                mac=row["mac"],
                ip=row["ip"],
                hostname=row["hostname"],
                device_type=row["device_type"] or "unknown",
                vendor=row["vendor"],
                trust_score=row["trust_score"] or 50.0,
                status=row["status"] or "active",
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
                nickname=row["nickname"],
                online=online
            ))

        conn.close()

        return DevicesListResponse(count=len(devices), devices=devices)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int):
    """Get a specific device by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                id,
                mac,
                ip,
                hostname,
                device_type,
                vendor,
                trust_score,
                status,
                first_seen,
                last_seen,
                nickname
            FROM devices
            WHERE id = ?
        """, (device_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Device not found")

        # Calculate online status
        now = datetime.now()
        online = False
        if row["last_seen"]:
            try:
                last_seen = datetime.fromisoformat(row["last_seen"].replace('Z', '+00:00'))
                diff = (now - last_seen.replace(tzinfo=None)).total_seconds()
                online = diff < 300
            except:
                pass

        return DeviceResponse(
            id=row["id"],
            mac=row["mac"],
            ip=row["ip"],
            hostname=row["hostname"],
            device_type=row["device_type"] or "unknown",
            vendor=row["vendor"],
            trust_score=row["trust_score"] or 50.0,
            status=row["status"] or "active",
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            nickname=row["nickname"],
            online=online
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{device_id}/block")
async def block_device(device_id: int):
    """Block a device."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET status = 'blocked'
            WHERE id = ?
        """, (device_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Device not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Device blocked"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{device_id}/unblock")
async def unblock_device(device_id: int):
    """Unblock a device."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET status = 'active'
            WHERE id = ?
        """, (device_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Device not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Device unblocked"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
