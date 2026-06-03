"""
Vigil - Events Router
Unified events endpoint for dashboard timeline.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.models_event import Event

router = APIRouter(prefix="/events", tags=["events"])


# ============ Pydantic Models ============

class EventResponse(BaseModel):
    id: str
    device_id: Optional[int]
    event_type: str
    timestamp: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    count: int
    events: List[EventResponse]


# ============ Routes ============

@router.get("", response_model=EventListResponse)
def list_events(
    device_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None, alias="type"),
    severity: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List unified events with optional filtering."""
    query = db.query(Event)
    
    if device_id is not None:
        query = query.filter(Event.device_id == device_id)
    if event_type:
        query = query.filter(Event.type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)
    if acknowledged is not None:
        query = query.filter(Event.acknowledged == acknowledged)
    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)
    
    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()
    
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "device_id": e.device_id,
                "event_type": e.type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "details": e.details or {},
            }
            for e in events
        ],
    }


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": event.id,
        "device_id": event.device_id,
        "event_type": event.type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "details": event.details or {},
    }


@router.post("/{event_id}/acknowledge")
def acknowledge_event(event_id: str, db: Session = Depends(get_db)):
    """Mark an event as acknowledged."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.acknowledged = True
    db.commit()
    return {"status": "acknowledged"}
