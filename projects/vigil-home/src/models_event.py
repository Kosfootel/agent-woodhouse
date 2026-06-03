"""
Vigil Unified Event Model
Matches the events table schema for dashboard timeline.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import Session

from app.models import Base


class Event(Base):
    """Unified activity events for dashboard timeline."""
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)  # device_discovered, prompt_blocked, etc.
    severity = Column(String, nullable=False, default='info')  # low, medium, high, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    device_id = Column(Integer, nullable=True, index=True)
    agent_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    acknowledged = Column(Boolean, default=False, index=True)


def create_event(
    db: Session,
    event_id: str,
    event_type: str,
    title: str,
    severity: str = 'info',
    device_id: Optional[int] = None,
    agent_id: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Event:
    """Create a new event record."""
    event = Event(
        id=event_id,
        type=event_type,
        severity=severity,
        device_id=device_id,
        agent_id=agent_id,
        title=title,
        description=description,
        details=details or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
