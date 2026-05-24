"""Alerts API router for Vigil - uses Alert model with proper endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import get_db, Alert
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["alerts"])


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
    new_count: int
    acknowledged_count: int


@router.get("/alerts", response_model=AlertsListResponse)
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering."""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    
    total = query.count()
    new_count = db.query(Alert).filter(Alert.acknowledged == False).count()
    acknowledged_count = db.query(Alert).filter(Alert.acknowledged == True).count()
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset).all()
    
    return AlertsListResponse(
        count=len(alerts),
        new_count=new_count,
        acknowledged_count=acknowledged_count,
        alerts=[
            AlertResponse(
                id=alert.id,
                device_id=alert.device_id,
                severity=alert.severity,
                alert_type=alert.type or 'unknown',
                title=alert.message[:50] + "..." if alert.message and len(alert.message) > 50 else (alert.message or 'Alert'),
                narrative=alert.message,
                acknowledged=alert.acknowledged,
                timestamp=alert.created_at.isoformat() if alert.created_at else None
            )
            for alert in alerts
        ]
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge a single alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {"status": "acknowledged", "alert_id": alert_id}


@router.post("/alerts/acknowledge-all")
async def acknowledge_all_alerts(db: Session = Depends(get_db)):
    """Acknowledge all unacknowledged alerts."""
    count = db.query(Alert).filter(Alert.acknowledged == False).update({
        "acknowledged": True,
        "acknowledged_at": datetime.utcnow()
    })
    db.commit()
    
    return {"status": "acknowledged", "count": count}


@router.get("/alerts/count")
async def get_alert_count(db: Session = Depends(get_db)):
    """Get count of unacknowledged alerts."""
    count = db.query(Alert).filter(Alert.acknowledged == False).count()
    return {"count": count}
