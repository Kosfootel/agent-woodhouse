"""Alerts API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime, timedelta

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Database path
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"


class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int]
    severity: str
    alert_type: str
    title: str
    narrative: Optional[str] = None
    acknowledged: bool
    timestamp: str


class AlertsListResponse(BaseModel):
    count: int
    alerts: List[AlertResponse]


class AcknowledgeRequest(BaseModel):
    pass


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/", response_model=AlertsListResponse)
async def get_alerts(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[int] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    hours: Optional[int] = None
):
    """Get alerts with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                id,
                device_id,
                severity,
                alert_type,
                title,
                description as narrative,
                acknowledged,
                created_at as timestamp
            FROM alerts
            WHERE 1=1
        """
        params = []

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(1 if acknowledged else 0)

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            query += " AND created_at > ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        alerts = []
        for row in rows:
            alerts.append(AlertResponse(
                id=row["id"],
                device_id=row["device_id"],
                severity=row["severity"],
                alert_type=row["alert_type"],
                title=row["title"],
                narrative=row["narrative"],
                acknowledged=bool(row["acknowledged"]),
                timestamp=row["timestamp"]
            ))

        return AlertsListResponse(count=len(alerts), alerts=alerts)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int):
    """Get a specific alert by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                id,
                device_id,
                severity,
                alert_type,
                title,
                description as narrative,
                acknowledged,
                created_at as timestamp
            FROM alerts
            WHERE id = ?
        """, (alert_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")

        return AlertResponse(
            id=row["id"],
            device_id=row["device_id"],
            severity=row["severity"],
            alert_type=row["alert_type"],
            title=row["title"],
            narrative=row["narrative"],
            acknowledged=bool(row["acknowledged"]),
            timestamp=row["timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 1,
                acknowledged_at = CURRENT_TIMESTAMP,
                acknowledged_by = 'api'
            WHERE id = ?
        """, (alert_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Alert not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Alert acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.patch("/{alert_id}/unacknowledge")
async def unacknowledge_alert(alert_id: int):
    """Unacknowledge an alert."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 0,
                acknowledged_at = NULL,
                acknowledged_by = NULL
            WHERE id = ?
        """, (alert_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Alert not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Alert unacknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
