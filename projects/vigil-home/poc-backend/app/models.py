"""Vigil Home - Database models"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mac = Column(String(17), unique=True, nullable=False, index=True)
    ip = Column(String(45), nullable=False)
    hostname = Column(String(255), nullable=True)
    device_type = Column(String(64), nullable=True)
    trust_score = Column(Float, default=0.5)
    classified_type = Column(String(64), nullable=True)
    classified_confidence = Column(Float, nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "mac": self.mac,
            "ip": self.ip,
            "hostname": self.hostname,
            "device_type": self.device_type,
            "trust_score": self.trust_score,
            "classified_type": self.classified_type,
            "classified_confidence": self.classified_confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    event_type = Column(String(64), nullable=False)
    severity = Column(String(16), default="info")
    details = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "details": self.details,
        }


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    alert_type = Column(String(64), nullable=False)
    severity = Column(String(16), default="medium")
    narrative = Column(Text, nullable=True)
    status = Column(String(16), default="open")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "alert_type": self.alert_type,
            "severity": self.severity,
            "narrative": self.narrative,
            "status": self.status,
        }
