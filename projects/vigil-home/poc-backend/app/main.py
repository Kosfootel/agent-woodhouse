"""Vigil Home - FastAPI Application with AI integration."""

import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.models import Device, Event, Alert
from app.detection import start_eve_consumer
from app.ai import TrustModel, AnomalyDetector, NarrativeGenerator, Severity, DeviceClassifier

app = FastAPI(
    title="Vigil Home API",
    description="IoT threat detection backend with AI scoring",
    version="0.2.0",
)

# ── AI runtime instances ───────────────────────────────────────────

narrator = NarrativeGenerator()
classifier = DeviceClassifier()

# Per-device anomaly detectors and trust models (populated on demand)
_anomaly_detectors: dict[int, AnomalyDetector] = {}
_trust_models: dict[int, TrustModel] = {}


def _get_anomaly_detector(device_id: int) -> AnomalyDetector:
    """Get or create an AnomalyDetector for a device."""
    if device_id not in _anomaly_detectors:
        _anomaly_detectors[device_id] = AnomalyDetector(window_size=100, z_threshold=3.0)
    return _anomaly_detectors[device_id]


def _get_trust_model(device_id: int) -> TrustModel:
    """Get or create a TrustModel for a device."""
    if device_id not in _trust_models:
        _trust_models[device_id] = TrustModel(half_life=86400)
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


# ── Startup ─────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    init_db()
    start_eve_consumer()


# ── Device endpoints ────────────────────────────────────────────────


@app.get("/devices")
def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all known devices with trust scores and classifications."""
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


@app.post("/devices")
def create_device(req: BaselineRequest, db: Session = Depends(get_db)):
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

    # Store trust model in memory
    _trust_models[device.id] = trust_model

    return {"message": "Device created", "device": device.to_dict()}


# ── Event endpoints ─────────────────────────────────────────────────


@app.post("/events")
def ingest_event(req: EventIngest, db: Session = Depends(get_db)):
    """Manually ingest an event, triggering anomaly detection and trust update."""
    device = db.query(Device).filter(Device.id == req.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Anomaly detection
    is_anomalous = False
    z_score = None
    if req.value is not None:
        detector = _get_anomaly_detector(device.id)
        result = detector.record(req.value)
        if result and result.is_anomaly:
            is_anomalous = True
            z_score = round(result.z_score, 4)

    # Trust update
    trust_model = _get_trust_model(device.id)
    if is_anomalous:
        trust_model.update(positive=False)
    else:
        trust_model.update(positive=True)
    trust_model.decay()
    device.trust_score = round(trust_model.score, 4)

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
def get_alert(alert_id: int, db: Session = Depends(get_db)):
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
def get_alert_narrative(alert_id: int, db: Session = Depends(get_db)):
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


# ── Email notification endpoints ─────────────────────────────────────


@app.get("/email/status")
def email_status():
    """Get email notification system status."""
    return get_email_status()


@app.get("/email/test")
def email_test():
    """Send a test email to verify SMTP configuration."""
    return send_test_email()


@app.post("/email/send-alert")
def email_send_alert(alert_id: int, db: Session = Depends(get_db)):
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
def create_baseline(req: BaselineRequest, db: Session = Depends(get_db)):
    """Register or update a device behaviour baseline (legacy, delegates to POST /devices)."""
    # Check if device exists
    device = db.query(Device).filter(Device.mac == req.mac).first()
    if not device:
        # Delegate to the new create_device logic
        return create_device(req, db)

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
def classify_device(mac: str):
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
def known_device_types():
    """List all known device types with their behavioural signatures."""
    return classifier.known_devices()
