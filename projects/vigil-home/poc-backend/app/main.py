"""Vigil Home - FastAPI Application"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.models import Device, Event, Alert
from app.detection import start_eve_consumer

app = FastAPI(
    title="Vigil Home API",
    description="IoT threat detection backend",
    version="0.1.0",
)


class BaselineRequest(BaseModel):
    """Request body for creating a device baseline."""
    mac: str
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None


# ── Startup ──────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    init_db()
    start_eve_consumer()


# ── Device endpoints ─────────────────────────────────────────────────────────


@app.get("/devices")
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all known devices with trust scores."""
    devices = db.query(Device).offset(skip).limit(limit).all()
    return {
        "count": len(devices),
        "devices": [d.to_dict() for d in devices],
    }


@app.get("/devices/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    recent_events = (
        db.query(Event)
        .filter(Event.device_id == device_id)
        .order_by(Event.timestamp.desc())
        .limit(20)
        .all()
    )
    open_alerts = (
        db.query(Alert)
        .filter(Alert.device_id == device_id, Alert.status == "open")
        .order_by(Alert.timestamp.desc())
        .limit(20)
        .all()
    )

    return {
        **device.to_dict(),
        "recent_events": [e.to_dict() for e in recent_events],
        "open_alerts": [a.to_dict() for a in open_alerts],
    }


# ── Alert endpoints ──────────────────────────────────────────────────────────


@app.get("/alerts")
def list_alerts(
    status: Optional[str] = Query(None, pattern="^(open|acknowledged|resolved)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List security alerts with optional filtering."""
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    alerts = query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()
    return {
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


# ── Event endpoints ──────────────────────────────────────────────────────────


@app.get("/events")
def list_events(
    device_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, pattern="^(info|low|medium|high|critical)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List security events with optional filtering."""
    query = db.query(Event)
    if device_id is not None:
        query = query.filter(Event.device_id == device_id)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)
    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()
    return {
        "count": len(events),
        "events": [e.to_dict() for e in events],
    }


# ── Baseline endpoint ────────────────────────────────────────────────────────


@app.post("/baseline")
def create_baseline(req: BaselineRequest, db: Session = Depends(get_db)):
    """Register or update a device behaviour baseline."""
    device = db.query(Device).filter(Device.mac == req.mac).first()
    if not device:
        device = Device(
            mac=req.mac,
            ip=req.ip,
            hostname=req.hostname,
            device_type=req.device_type,
            trust_score=0.5,
        )
        db.add(device)
    else:
        device.ip = req.ip
        if req.hostname:
            device.hostname = req.hostname
        if req.device_type:
            device.device_type = req.device_type
        device.last_seen = datetime.now(timezone.utc)

    db.commit()
    db.refresh(device)
    return {"message": "Baseline created", "device": device.to_dict()}
