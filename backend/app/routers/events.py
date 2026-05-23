"""Events API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/events", tags=["events"])

# Database path
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"


class EventResponse(BaseModel):
    id: int
    device_id: int
    event_type: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class EventsListResponse(BaseModel):
    count: int
    events: List[EventResponse]


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/", response_model=EventsListResponse)
async def get_events(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[int] = None,
    event_type: Optional[str] = None,
    hours: Optional[int] = None
):
    """Get recent events with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                do.id,
                do.device_id,
                do.observation_type as event_type,
                do.timestamp,
                do.raw_data as details,
                d.hostname as device_name
            FROM device_observations do
            LEFT JOIN devices d ON do.device_id = d.id
            WHERE 1=1
        """
        params = []

        if device_id:
            query += " AND do.device_id = ?"
            params.append(device_id)

        if event_type:
            query += " AND do.observation_type = ?"
            params.append(event_type)

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            query += " AND do.timestamp > ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY do.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            import json
            details = {}
            if row["details"]:
                try:
                    details = json.loads(row["details"])
                except:
                    details = {"raw": row["details"]}
            
            events.append(EventResponse(
                id=row["id"],
                device_id=row["device_id"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                details={
                    **details,
                    "device_name": row["device_name"] or f"Device {row['device_id']}"
                }
            ))

        return EventsListResponse(count=len(events), events=events)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """Get a specific event by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                do.id,
                do.device_id,
                do.observation_type as event_type,
                do.timestamp,
                do.raw_data as details,
                d.hostname as device_name
            FROM device_observations do
            LEFT JOIN devices d ON do.device_id = d.id
            WHERE do.id = ?
        """, (event_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Event not found")

        import json
        details = {}
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except:
                details = {"raw": row["details"]}

        return EventResponse(
            id=row["id"],
            device_id=row["device_id"],
            event_type=row["event_type"],
            timestamp=row["timestamp"],
            details={
                **details,
                "device_name": row["device_name"] or f"Device {row['device_id']}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
