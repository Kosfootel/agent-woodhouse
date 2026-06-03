"""Events API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import os
from datetime import datetime, timedelta

router = APIRouter(tags=["events"])

# Database path - use environment variable or default
DB_PATH = os.getenv("DATABASE_PATH", "/app/data/vigil.db")


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


@router.get("/events", response_model=EventsListResponse)
async def get_events(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[int] = None,
    event_type: Optional[str] = None,
    hours: Optional[int] = None
):
    """Get recent events from the events table with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Use the actual events table schema from models.py
        query = """
            SELECT 
                e.id,
                e.device_id,
                e.type as event_type,
                e.description,
                e.created_at as timestamp
            FROM events e
            WHERE 1=1
        """
        params = []

        if device_id:
            query += " AND e.device_id = ?"
            params.append(device_id)

        if event_type:
            query += " AND e.type = ?"
            params.append(event_type)

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            query += " AND e.created_at > ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY e.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append(EventResponse(
                id=row["id"],
                device_id=row["device_id"] or 0,
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                details={"description": row["description"]}
            ))

        return EventsListResponse(count=len(events), events=events)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """Get a specific event by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                e.id,
                e.device_id,
                e.type as event_type,
                e.description,
                e.created_at as timestamp
            FROM events e
            WHERE e.id = ?
        """, (event_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Event not found")

        return EventResponse(
            id=row["id"],
            device_id=row["device_id"] or 0,
            event_type=row["event_type"],
            timestamp=row["timestamp"],
            details={"description": row["description"]}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
