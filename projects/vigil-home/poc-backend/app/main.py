"""Vigil Home - FastAPI Application with AI integration and authentication."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.models import Device, Event, Alert, User, RefreshToken
from app.detection import start_eve_consumer
from app.ai import TrustModel, AnomalyDetector, NarrativeGenerator, Severity, DeviceClassifier
from app.email_notifier import AlertEmailContext, send_alert_email, send_test_email, get_email_status
from app.ai_persistence import load_trust_model, load_anomaly_detector, store_trust_state, store_anomaly_state
from app.auth import (
    require_auth,
    optional_auth,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_refresh_token_expiry,
    bootstrap_admin,
    AUTH_DISABLED,
)

app = FastAPI(
    title="Vigil Home API",
    description="IoT threat detection backend with AI scoring",
    version="0.3.0",
)

# ── CORS ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── AI runtime instances ───────────────────────────────────────────

narrator = NarrativeGenerator()
classifier = DeviceClassifier()

# Per-device anomaly detectors and trust models (populated on demand)
_anomaly_detectors: dict[int, AnomalyDetector] = {}
_trust_models: dict[int, TrustModel] = {}


def _get_anomaly_detector(device_id: int, db: Session) -> AnomalyDetector:
    """Get the AnomalyDetector for a device, loading from DB if not cached."""
    if device_id not in _anomaly_detectors:
        detector = load_anomaly_detector(db, device_id)
        if detector is None:
            detector = AnomalyDetector(window_size=100, z_threshold=3.0)
        _anomaly_detectors[device_id] = detector
    return _anomaly_detectors[device_id]


def _get_trust_model(device_id: int, db: Session) -> TrustModel:
    """Get the TrustModel for a device, loading from DB if not cached."""
    if device_id not in _trust_models:
        model = load_trust_model(db, device_id)
        if model is None:
            model = TrustModel(half_life=86400)
        _trust_models[device_id] = model
    return _trust_models[device_id]


def _severity_to_severity_enum(sev_str: str) -> Severity:
    """Map backend severity string to narrative Severity enum."""
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return mapping.get(sev_str, Severity.INFO)


# ── Request models ─────────────────────────────────────────────────


class BaselineRequest(BaseModel):
    """Request body for creating a device baseline."""
    mac: str
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None


class EventIngest(BaseModel):
    """Request body for ingesting an event manually."""
    device_id: int
    event_type: str = "generic"
    severity: str = "info"
    value: Optional[float] = None
    details: Optional[dict] = None


class LoginRequest(BaseModel):
    """Request body for admin login."""
    username: str
    password: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


# ── Startup ─────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    from app.database import init_db as _init_db
    _init_db()

    # Bootstrap admin user
    db = next(get_db())
    try:
        bootstrap_admin(db)
    finally:
        db.close()

    start_eve_consumer()


# ── Auth endpoints ─────────────────────────────────────────────────


@app.post("/auth/login")
def auth_login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username and password.

    Returns JWT access token + opaque refresh token.
    """
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token_str = create_refresh_token()
    token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=create_refresh_token_expiry(),
    )
    db.add(refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": user.to_dict(),
    }


@app.post("/auth/refresh")
def auth_refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh token pair.

    Implements refresh token rotation: the old token is revoked and a
    new one is issued. If the token is already revoked (possible theft),
    all tokens for the user are revoked.
    """
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if stored.revoked:
        # Token reuse detected — revoke all tokens for this user
        db.query(RefreshToken).filter(
            RefreshToken.user_id == stored.user_id,
            RefreshToken.revoked == 0,
        ).update({"revoked": 1})
        db.commit()
        raise HTTPException(
            status_code=401,
            detail="Refresh token revoked — all sessions invalidated",
        )

    if stored.is_expired():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Revoke the old token
    stored.revoked = 1
    db.commit()

    # Issue new tokens
    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(user.id, user.role)
    new_refresh_token_str = create_refresh_token()
    new_token_hash = hashlib.sha256(new_refresh_token_str.encode()).hexdigest()

    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=create_refresh_token_expiry(),
    )
    db.add(new_refresh)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": user.to_dict(),
    }


@app.post("/auth/logout")
def auth_logout(
    req: RefreshRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Revoke the provided refresh token (logout)."""
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.user_id == int(auth.get("sub", 0)),
    ).first()

    if stored:
        stored.revoked = 1
        db.commit()

    return {"message": "Logged out"}


# ── Health endpoint (unauthenticated, no sensitive data) ────────────


@app.get("/health")
def health_check():
    """Simple health check — no auth required, no sensitive data."""
    return {"status": "ok", "version": "0.3.0"}


# ── Device endpoints ────────────────────────────────────────────────


@app.get("/devices")
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """List all known devices with trust scores and classifications."""
    devices = db.query(Device).offset(skip).limit(limit).all()
    return {
        "count": len(devices),
        "devices": [d.to_dict() for d in devices],
    }


@app.get("/devices/{device_id}")
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
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


@app.post("/devices")
def create_device(
    req: BaselineRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Register a new device with trust scoring and auto-classification."""
    existing = db.query(Device).filter(Device.mac == req.mac).first()
    if existing:
        raise HTTPException(status_code=409, detail="Device with this MAC already exists")

    # Auto-classify the device
    features = {}
    if req.hostname:
        features["protocols"] = []
        features["ports"] = []
        hl = req.hostname.lower()
        if any(kw in hl for kw in ("cam", "nest", "ring")):
            features["protocols"] = ["RTSP", "HTTPS", "MQTT"]
            features["ports"] = [554, 443]
            features["traffic_kbps"] = 1200.0
            features["connections_hour"] = 120
        elif any(kw in hl for kw in ("plug", "light", "bulb", "hue")):
            features["protocols"] = ["MQTT", "HTTPS"]
            features["ports"] = [443, 1883]
            features["traffic_kbps"] = 0.5
            features["connections_hour"] = 5
        elif any(kw in hl for kw in ("tv", "roku", "chromecast")):
            features["protocols"] = ["HTTPS", "HTTP", "DNS", "SSDP"]
            features["ports"] = [443, 80, 1900]
            features["traffic_kbps"] = 2000.0
            features["connections_hour"] = 80
        elif any(kw in hl for kw in ("thermo", "sensor")):
            features["protocols"] = ["MQTT", "HTTPS"]
            features["ports"] = [443, 1883]
            features["traffic_kbps"] = 0.2
            features["connections_hour"] = 10
        elif any(kw in hl for kw in ("phone", "iphone", "android")):
            features["protocols"] = ["HTTPS", "HTTP", "DNS"]
            features["ports"] = [443, 80, 53]
            features["traffic_kbps"] = 500.0
            features["connections_hour"] = 100
        elif any(kw in hl for kw in ("laptop", "macbook", "thinkpad", "pc-", "desktop")):
            features["protocols"] = ["HTTPS", "HTTP", "DNS", "SSH"]
            features["ports"] = [443, 80, 53, 22]
            features["traffic_kbps"] = 1000.0
            features["connections_hour"] = 200
        features["active_hour"] = datetime.now(timezone.utc).hour

    classifications = classifier.classify(req.mac, features if features else None, top_n=1)
    classified_type = classifications[0].device_type if classifications else None
    classified_confidence = round(classifications[0].confidence, 4) if classifications else None

    # Initialize trust model — default 0.5
    trust_model = TrustModel(half_life=86400)
    trust_score = round(trust_model.score, 4)

    device = Device(
        mac=req.mac,
        ip=req.ip,
        hostname=req.hostname,
        device_type=req.device_type or classified_type,
        trust_score=trust_score,
        classified_type=classified_type,
        classified_confidence=classified_confidence,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    # Store trust model in memory and persist
    _trust_models[device.id] = trust_model
    store_trust_state(db, device.id, trust_model)

    return {"message": "Device created", "device": device.to_dict()}


# ── Event endpoints ─────────────────────────────────────────────────


@app.post("/events")
def ingest_event(
    req: EventIngest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Manually ingest an event, triggering anomaly detection and trust update."""
    device = db.query(Device).filter(Device.id == req.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Anomaly detection
    is_anomalous = False
    z_score = None
    if req.value is not None:
        detector = _get_anomaly_detector(device.id, db)
        result = detector.record(req.value)
        if result and result.is_anomaly:
            is_anomalous = True
            z_score = round(result.z_score, 4)
        store_anomaly_state(db, device.id, detector)

    # Trust update
    trust_model = _get_trust_model(device.id, db)
    if is_anomalous:
        trust_model.update(positive=False)
    else:
        trust_model.update(positive=True)
    trust_model.decay()
    device.trust_score = round(trust_model.score, 4)
    store_trust_state(db, device.id, trust_model)

    # Create alert if anomalous
    alert_data = None
    if is_anomalous:
        severity_enum = _severity_to_severity_enum(req.severity)
        device_info = db.query(Device).filter(Device.id == req.device_id).first()
        dev_name = device_info.hostname or device_info.mac
        dev_type = device_info.device_type or "unknown"

        alert_narrative = narrator.alert(
            device_name=dev_name,
            device_type=dev_type,
            severity=severity_enum,
            anomaly_detail=f"Value {req.value} is anomalous (z={z_score})",
            trust_score=trust_model.score,
            extra={"z_score": z_score},
        )

        alert = Alert(
            device_id=req.device_id,
            timestamp=datetime.now(timezone.utc),
            alert_type="anomaly",
            severity=req.severity,
            narrative=alert_narrative.description,
            status="open",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_data = alert.to_dict()

        # Send email for critical/high alerts from manual ingestion
        if req.severity in ("critical", "high"):
            try:
                dev_name = device.hostname or device.mac
                dev_type = device.device_type or "unknown"
                email_ctx = AlertEmailContext(
                    severity=req.severity,
                    title=f"Anomaly: {req.event_type}",
                    description=alert_narrative.description,
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    device_name=dev_name,
                    mac_address=device.mac,
                    trust_score=device.trust_score,
                    device_type=dev_type,
                    device_id=device.id,
                    alert_id=alert.id,
                    alert_type="anomaly",
                )
                send_alert_email(email_ctx)
            except Exception as e:
                # Don't fail the request if email fails
                import logging
                logging.getLogger("vigil.email").error(f"Failed to send alert email: {e}")

    # Create event record
    details = req.details or {}
    if z_score is not None:
        details["z_score"] = z_score
        details["is_anomalous"] = is_anomalous

    event = Event(
        device_id=req.device_id,
        timestamp=datetime.now(timezone.utc),
        event_type=req.event_type,
        severity=req.severity,
        details=details,
    )
    db.add(event)
    device.last_seen = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)

    return {
        "message": "Event ingested",
        "event": event.to_dict(),
        "anomaly_detected": is_anomalous,
        "z_score": z_score,
        "trust_score": device.trust_score,
        "alert": alert_data,
    }


@app.get("/events")
def list_events(
    device_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, pattern="^(info|low|medium|high|critical)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
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


# ── Alert endpoints ─────────────────────────────────────────────────


@app.get("/alerts")
def list_alerts(
    status: Optional[str] = Query(None, pattern="^(open|acknowledged|resolved)$"),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
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


@app.get("/alerts/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get a specific alert with full narrative text."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Attach device info
    device = db.query(Device).filter(Device.id == alert.device_id).first()

    result = alert.to_dict()
    if device:
        result["device"] = device.to_dict()

    return result


@app.get("/alerts/{alert_id}/narrative")
def get_alert_narrative(
    alert_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get the generated narrative for an alert, regenerating if missing."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # If narrative already exists, return it; otherwise generate from stored data
    if alert.narrative:
        return {
            "alert_id": alert.id,
            "narrative": alert.narrative,
            "regenerated": False,
        }

    # Try to regenerate from associated event/device info
    device = db.query(Device).filter(Device.id == alert.device_id).first()
    if not device:
        raise HTTPException(status_code=500, detail="Associated device not found")

    dev_name = device.hostname or device.mac
    dev_type = device.device_type or "unknown"
    severity_enum = _severity_to_severity_enum(alert.severity)

    # Find recent events for context
    recent_event = (
        db.query(Event)
        .filter(Event.device_id == alert.device_id)
        .order_by(Event.timestamp.desc())
        .first()
    )
    anomaly_detail = f"Alert type: {alert.alert_type}"
    extra = {}
    if recent_event and recent_event.details:
        if "z_score" in recent_event.details:
            extra["z_score"] = recent_event.details["z_score"]

    alert_obj = narrator.alert(
        device_name=dev_name,
        device_type=dev_type,
        severity=severity_enum,
        anomaly_detail=anomaly_detail,
        trust_score=device.trust_score,
        extra=extra,
    )

    # Store the generated narrative
    alert.narrative = alert_obj.description
    db.commit()

    return {
        "alert_id": alert.id,
        "narrative": alert_obj.description,
        "regenerated": True,
    }


@app.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Acknowledge an alert (status -> 'acknowledged')."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    db.commit()

    return {
        "message": "Alert acknowledged",
        "alert": alert.to_dict(),
    }


# ── Email notification endpoints ─────────────────────────────────────


@app.get("/email/status")
def email_status(auth: dict = Depends(require_auth)):
    """Get email notification system status."""
    return get_email_status()


@app.get("/email/test")
def email_test(auth: dict = Depends(require_auth)):
    """Send a test email to verify SMTP configuration."""
    return send_test_email()


@app.post("/email/send-alert")
def email_send_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Manually send an email for an existing alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    device = db.query(Device).filter(Device.id == alert.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Associated device not found")

    ctx = AlertEmailContext(
        severity=alert.severity,
        title=alert.alert_type,
        description=alert.narrative or f"Alert: {alert.alert_type}",
        timestamp=alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
        device_name=device.hostname or device.mac,
        mac_address=device.mac,
        trust_score=device.trust_score,
        device_type=device.device_type or "unknown",
        device_id=device.id,
        alert_id=alert.id,
        alert_type=alert.alert_type,
    )

    sent = send_alert_email(ctx)
    return {
        "alert_id": alert.id,
        "severity": alert.severity,
        "email_sent": sent,
        "status": get_email_status(),
    }


# ── Baseline endpoint (backward compat) ────────────────────────────


@app.post("/baseline")
def create_baseline(
    req: BaselineRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Register or update a device behaviour baseline (legacy, delegates to POST /devices)."""
    # Check if device exists
    device = db.query(Device).filter(Device.mac == req.mac).first()
    if not device:
        # Create new device (inlined to avoid FastAPI dependency passing issues)
        features_hl = req.hostname.lower() if req.hostname else ""
        features: dict = {}
        if req.hostname:
            if any(kw in features_hl for kw in ("cam", "nest", "ring")):
                features = {"protocols": ["RTSP", "HTTPS", "MQTT"], "ports": [554, 443], "traffic_kbps": 1200.0, "connections_hour": 120}
            elif any(kw in features_hl for kw in ("plug", "light", "bulb", "hue")):
                features = {"protocols": ["MQTT", "HTTPS"], "ports": [443, 1883], "traffic_kbps": 0.5, "connections_hour": 5}
            elif any(kw in features_hl for kw in ("tv", "roku", "chromecast")):
                features = {"protocols": ["HTTPS", "HTTP", "DNS", "SSDP"], "ports": [443, 80, 1900], "traffic_kbps": 2000.0, "connections_hour": 80}
            elif any(kw in features_hl for kw in ("thermo", "sensor")):
                features = {"protocols": ["MQTT", "HTTPS"], "ports": [443, 1883], "traffic_kbps": 0.2, "connections_hour": 10}
            elif any(kw in features_hl for kw in ("phone", "iphone", "android")):
                features = {"protocols": ["HTTPS", "HTTP", "DNS"], "ports": [443, 80, 53], "traffic_kbps": 500.0, "connections_hour": 100}
            elif any(kw in features_hl for kw in ("laptop", "macbook", "thinkpad", "pc-", "desktop")):
                features = {"protocols": ["HTTPS", "HTTP", "DNS", "SSH"], "ports": [443, 80, 53, 22], "traffic_kbps": 1000.0, "connections_hour": 200}
            features["active_hour"] = datetime.now(timezone.utc).hour

        classifications = classifier.classify(req.mac, features if features else None, top_n=1)
        classified_type = classifications[0].device_type if classifications else None
        classified_confidence = round(classifications[0].confidence, 4) if classifications else None
        trust_model = TrustModel(half_life=86400)
        trust_score = round(trust_model.score, 4)

        device = Device(
            mac=req.mac,
            ip=req.ip,
            hostname=req.hostname,
            device_type=req.device_type or classified_type,
            trust_score=trust_score,
            classified_type=classified_type,
            classified_confidence=classified_confidence,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        _trust_models[device.id] = trust_model
        return {"message": "Device created", "device": device.to_dict()}

    # Update existing device
    device.ip = req.ip
    if req.hostname:
        device.hostname = req.hostname
    if req.device_type:
        device.device_type = req.device_type
    device.last_seen = datetime.now(timezone.utc)

    db.commit()
    db.refresh(device)
    return {"message": "Baseline updated", "device": device.to_dict()}


# ── Classification endpoint ─────────────────────────────────────────


@app.get("/classify/{mac}")
def classify_device(
    mac: str,
    auth: dict = Depends(require_auth),
):
    """Classify a device by MAC address (standalone, no DB needed)."""
    classifications = classifier.classify(mac, top_n=3)
    vendor = classifier.oui_vendor(mac)
    return {
        "mac": mac,
        "vendor": vendor,
        "classifications": [
            {
                "device_type": c.device_type,
                "label": c.label,
                "confidence": round(c.confidence, 4),
                "source": c.source,
                "vendor": c.vendor,
            }
            for c in classifications
        ],
    }


@app.get("/known-device-types")
def known_device_types(auth: dict = Depends(require_auth)):
    """List all known device types with their behavioural signatures."""
    return classifier.known_devices()


# ── Trust trend endpoint ────────────────────────────────────────────


@app.get("/trust-trend")
def trust_trend(
    days: int = Query(7, ge=1, le=90),
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get historical trust score data for the trust trend chart.

    Replaces the previous Math.random() simulation with real data
    aggregated from events and trust scores.
    """
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get all devices (or a specific one)
    device_query = db.query(Device)
    if device_id is not None:
        device_query = device_query.filter(Device.id == device_id)
    devices = device_query.all()

    trend_data = []
    for device in devices:
        # For a real implementation, we'd store historical snapshots.
        # For now, simulate a trend based on the current trust score and
        # the number of anomalous events over the window. This is vastly
        # better than pure Math.random() as it reflects actual system state.
        anomalous_count = (
            db.query(Event)
            .filter(
                Event.device_id == device.id,
                Event.timestamp >= cutoff,
                Event.details["is_anomalous"].as_boolean() == True,  # noqa: E712
            )
            .count()
        )
        positive_count = (
            db.query(Event)
            .filter(
                Event.device_id == device.id,
                Event.timestamp >= cutoff,
                Event.severity.in_(["info", "low"]),
            )
            .count()
        )

        total_events = anomalous_count + positive_count
        if total_events > 0:
            trend_ratio = positive_count / total_events
        else:
            trend_ratio = 0.5

        trend_data.append({
            "device_id": device.id,
            "device_name": device.hostname or device.mac,
            "current_trust_score": device.trust_score,
            "trend_ratio": round(trend_ratio, 4),
            "anomalous_events": anomalous_count,
            "total_events": total_events,
            "days": days,
        })

    return {
        "count": len(trend_data),
        "data": trend_data,
    }


# ── Production error handler ────────────────────────────────────────


@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    """Generic 500 handler — no stack traces in production."""
    import logging
    logger = logging.getLogger("vigil.api")
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
