"""
Vigil - Statistics Router
Dashboard statistics and activity endpoints.
"""

from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import get_db, Device, Alert, Event

router = APIRouter(prefix="/stats", tags=["stats"])


# ============ Pydantic Models ============

class DashboardStats(BaseModel):
    device_count: int
    active_devices: int
    blocked_devices: int
    avg_trust_score: float
    alert_count: int
    unacknowledged_alerts: int
    critical_alerts: int


class EventResponse(BaseModel):
    id: int
    device_id: int
    type: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class EventsListResponse(BaseModel):
    events: List[EventResponse]
    total_count: int


# ============ Endpoints ============

@router.get("", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    # Device stats
    device_count = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.containment_status == "observing").count()
    blocked_devices = db.query(Device).filter(Device.containment_status == "blocked").count()
    
    # Average trust score
    avg_trust = db.query(func.avg(Device.trust_score)).scalar()
    avg_trust_score = round(avg_trust, 2) if avg_trust else 0.0
    
    # Alert stats
    alert_count = db.query(Alert).count()
    unacknowledged_alerts = db.query(Alert).filter(
        Alert.acknowledged == False
    ).count()
    critical_alerts = db.query(Alert).filter(
        Alert.severity == "critical"
    ).count()
    
    return DashboardStats(
        device_count=device_count,
        active_devices=active_devices,
        blocked_devices=blocked_devices,
        avg_trust_score=avg_trust_score,
        alert_count=alert_count,
        unacknowledged_alerts=unacknowledged_alerts,
        critical_alerts=critical_alerts
    )


@router.get("/events", response_model=EventsListResponse)
def get_events(
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent activity events."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    events = db.query(Event).filter(
        Event.created_at >= since
    ).order_by(Event.created_at.desc()).limit(limit).all()
    
    total_count = db.query(Event).filter(
        Event.created_at >= since
    ).count()
    
    return EventsListResponse(
        events=events,
        total_count=total_count
    )
