"""Alerts API router for Vigil - uses Event model."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import get_db, Event

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int]
    severity: str
    alert_type: str
    title: str
    narrative: Optional[str] = None
    acknowledged: bool
    timestamp: Optional[str]

    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    count: int
    alerts: List[AlertResponse]


@router.get("/", response_model=AlertsListResponse)
async def get_alerts(
    limit: int = 100,
    offset: int = 0,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get alerts/events with optional filtering."""
    query = db.query(Event)
    
    if severity:
        query = query.filter(Event.severity == severity)
    
    events = query.order_by(Event.timestamp.desc()).limit(limit).offset(offset).all()
    
    alerts = []
    for event in events:
        alerts.append(AlertResponse(
            id=event.id,
            device_id=event.device_id,
            severity=event.severity or 'low',
            alert_type=event.event_type or 'unknown',
            title=event.title or f"Event {event.id}",
            narrative=event.description,
            acknowledged=False,
            timestamp=event.timestamp.isoformat() if event.timestamp else None
        ))
    
    return AlertsListResponse(count=len(alerts), alerts=alerts)


@router.get("/count")
async def get_alert_count(db: Session = Depends(get_db)):
    """Get count of unacknowledged alerts."""
    count = db.query(Event).count()
    return {"count": count}
