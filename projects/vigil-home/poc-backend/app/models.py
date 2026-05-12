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
        # Import here to avoid circular dependency with main.py
        from app.main import is_online
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
            "online": is_online(self.last_seen.isoformat()),
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


class TrustScore(Base):
    """Persistent state for a device's Bayesian trust model."""
    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, unique=True, nullable=False, index=True)
    alpha = Column(Float, default=1.0)
    omega = Column(Float, default=1.0)
    half_life = Column(Float, default=86400.0)
    last_update = Column(Float, default=lambda: datetime.now(timezone.utc).timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "alpha": self.alpha,
            "omega": self.omega,
            "half_life": self.half_life,
            "last_update": self.last_update,
        }


class AnomalyBaseline(Base):
    """Persistent state for a device's anomaly detector baseline."""
    __tablename__ = "anomaly_baselines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, unique=True, nullable=False, index=True)
    window = Column(JSON, default=list)
    window_size = Column(Integer, default=100)
    z_threshold = Column(Float, default=3.0)
    min_samples = Column(Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "window_size": self.window_size,
            "z_threshold": self.z_threshold,
            "min_samples": self.min_samples,
            "window_len": len(self.window) if isinstance(self.window, list) else 0,
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
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(64), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "alert_type": self.alert_type,
            "severity": self.severity,
            "narrative": self.narrative,
            "status": self.status,
            "acknowledged": self.status in ("acknowledged", "resolved"),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
        }


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="admin")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Integer, default=0)  # 0 = active, 1 = revoked
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    def is_active(self) -> bool:
        return not self.revoked and not self.is_expired()


class ApiKey(Base):
    """API key for programmatic/auth-headless access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    label = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="admin")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key_prefix": self.key_prefix,
            "label": self.label,
            "role": self.role,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
