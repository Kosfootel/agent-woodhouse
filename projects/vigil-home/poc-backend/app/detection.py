"""Vigil Home - Suricata eve.json consumer & detection logic

Now integrates AI modules for anomaly detection, trust scoring,
and narrative generation on ingested events.
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.database import SessionLocal
from app.models import Device, Event, Alert
from app.ai import TrustModel, AnomalyDetector, NarrativeGenerator, Severity, DeviceClassifier
from app.email_notifier import AlertEmailContext, send_alert_email

EVE_JSON_PATH = os.environ.get("VIGIL_EVE_JSON", "/var/log/suricata/eve.json")
POLL_INTERVAL = float(os.environ.get("VIGIL_POLL_INTERVAL", "2.0"))

# ── AI runtime instances ───────────────────────────────────────────

narrator = NarrativeGenerator()
classifier = DeviceClassifier()

# Per-device in-memory state
_anomaly_detectors: dict[int, AnomalyDetector] = {}
_trust_models: dict[int, TrustModel] = {}


def _get_anomaly_detector(device_id: int) -> AnomalyDetector:
    if device_id not in _anomaly_detectors:
        _anomaly_detectors[device_id] = AnomalyDetector(window_size=100, z_threshold=3.0)
    return _anomaly_detectors[device_id]


def _get_trust_model(device_id: int) -> TrustModel:
    if device_id not in _trust_models:
        _trust_models[device_id] = TrustModel(half_life=86400)
    return _trust_models[device_id]


def _severity_to_severity_enum(sev_str: str) -> Severity:
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return mapping.get(sev_str, Severity.INFO)


def _extract_anomaly_value(record: dict) -> float | None:
    """Extract a numeric value from a Suricata record for anomaly detection."""
    flow = record.get("flow", {})
    if flow:
        # Use total bytes as a proxy metric
        toserver = flow.get("bytes_toserver", 0) or 0
        toclient = flow.get("bytes_toclient", 0) or 0
        return float(toserver + toclient)
    netflow = record.get("netflow", {})
    if netflow:
        return float(netflow.get("bytes", 0) or 0)
    return None

def _map_suricata_severity(suricata_prio: int) -> str:
    """Map Suricata priority 1-4 to our severity labels."""
    mapping = {1: "critical", 2: "high", 3: "medium", 4: "low"}
    return mapping.get(suricata_prio, "info")


def _get_or_create_device(db, src_ip: str, src_mac: str | None, hostname: str | None) -> Device:
    """Find or create a device record for the given IP/MAC."""
    device = db.query(Device).filter(Device.ip == src_ip).first()
    if device:
        device.last_seen = datetime.now(timezone.utc)
        if src_mac and device.mac != src_mac:
            device.mac = src_mac
        if hostname and not device.hostname:
            device.hostname = hostname
        db.commit()
        db.refresh(device)
        return device

    mac = src_mac or f"00:00:00:{src_ip.replace('.', ':')}"

    # Auto-classify the device
    features = _build_classification_features(hostname)
    classifications = classifier.classify(mac, features if features else None, top_n=1)
    classified_type = classifications[0].device_type if classifications else None
    classified_confidence = round(classifications[0].confidence, 4) if classifications else None

    device = Device(
        mac=mac,
        ip=src_ip,
        hostname=hostname,
        device_type=_guess_device_type(hostname),
        trust_score=0.5,
        classified_type=classified_type,
        classified_confidence=classified_confidence,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    # Initialize trust model
    _trust_models[device.id] = TrustModel(half_life=86400)

    return device


def _build_classification_features(hostname: str | None) -> dict | None:
    """Build behavioural feature hints from hostname for classification."""
    if not hostname:
        return None
    hl = hostname.lower()
    features: dict = {}
    if any(kw in hl for kw in ("cam", "nest", "ring")):
        features = {"protocols": ["RTSP", "HTTPS", "MQTT"], "ports": [554, 443], "traffic_kbps": 1200.0, "connections_hour": 120}
    elif any(kw in hl for kw in ("plug", "light", "bulb", "hue")):
        features = {"protocols": ["MQTT", "HTTPS"], "ports": [443, 1883], "traffic_kbps": 0.5, "connections_hour": 5}
    elif any(kw in hl for kw in ("tv", "roku", "chromecast")):
        features = {"protocols": ["HTTPS", "HTTP", "DNS", "SSDP"], "ports": [443, 80, 1900], "traffic_kbps": 2000.0, "connections_hour": 80}
    elif any(kw in hl for kw in ("thermo", "sensor")):
        features = {"protocols": ["MQTT", "HTTPS"], "ports": [443, 1883], "traffic_kbps": 0.2, "connections_hour": 10}
    elif any(kw in hl for kw in ("phone", "iphone", "android")):
        features = {"protocols": ["HTTPS", "HTTP", "DNS"], "ports": [443, 80, 53], "traffic_kbps": 500.0, "connections_hour": 100}
    elif any(kw in hl for kw in ("laptop", "macbook", "thinkpad", "pc-", "desktop")):
        features = {"protocols": ["HTTPS", "HTTP", "DNS", "SSH"], "ports": [443, 80, 53, 22], "traffic_kbps": 1000.0, "connections_hour": 200}
    if features:
        features["active_hour"] = datetime.now(timezone.utc).hour
    return features if features else None


def _guess_device_type(hostname: str | None) -> str | None:
    """Simple heuristic to guess device type from hostname."""
    if not hostname:
        return None
    hl = hostname.lower()
    if any(kw in hl for kw in ("phone", "iphone", "android", "galaxy")):
        return "phone"
    if any(kw in hl for kw in ("laptop", "macbook", "thinkpad", "pc-", "desktop")):
        return "computer"
    if any(kw in hl for kw in ("camera", "cam-", "nest", "ring")):
        return "camera"
    if any(kw in hl for kw in ("tv", "roku", "shield", "chromecast", "apple-tv")):
        return "media"
    if any(kw in hl for kw in ("thermostat", "ecobee", "honeywell", "sensor")):
        return "sensor"
    if any(kw in hl for kw in ("plug", "light", "bulb", "switch", "hue")):
        return "smart-home"
    return "unknown"


def _update_trust_score(device_id: int, severity_str: str, db) -> float:
    """Update a device's trust score using the Bayesian TrustModel.

    Positive events (info/low) increase trust; negative events (high/critical)
    decrease it.
    """
    model = _get_trust_model(device_id)
    model.decay(time.time())

    if severity_str in ("critical", "high"):
        model.update(positive=False)
    elif severity_str in ("info", "low"):
        model.update(positive=True)
    # medium: neutral — no update

    return round(model.score, 4)


def process_eve_line(line: str, db):
    """Parse a single Suricata eve.json line and create events/alerts with AI."""
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return

    event_type = record.get("event_type")
    if not event_type:
        return

    timestamp_str = record.get("timestamp")
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        ts = datetime.now(timezone.utc)

    src_ip = record.get("src_ip") or record.get("dest_ip", "0.0.0.0")
    src_mac = record.get("src_mac") or (
        record.get("eth", {}).get("src") if isinstance(record.get("eth"), dict) else None
    )
    hostname = record.get("host") or record.get("dns", {}).get("rrname") if isinstance(record.get("dns"), dict) else None

    device = _get_or_create_device(db, src_ip, src_mac, hostname)

    severity = "info"
    details = {}
    is_anomalous = False
    z_score = None

    # ── Anomaly detection on numeric metrics ──
    anomaly_value = _extract_anomaly_value(record)
    if anomaly_value is not None:
        detector = _get_anomaly_detector(device.id)
        result = detector.record(anomaly_value)
        if result and result.is_anomaly:
            is_anomalous = True
            z_score = round(result.z_score, 4)

    if event_type == "alert":
        alert_data = record.get("alert", {})
        suricata_prio = alert_data.get("severity", 3)
        severity = _map_suricata_severity(suricata_prio)
        alert_type = alert_data.get("category", "unknown")
        signature = alert_data.get("signature", "")
        details = {
            "gid": alert_data.get("gid"),
            "sid": alert_data.get("signature_id"),
            "rev": alert_data.get("rev"),
            "signature": signature,
            "category": alert_type,
            "proto": record.get("proto"),
            "dest_ip": record.get("dest_ip"),
            "dest_port": record.get("dest_port"),
            "src_port": record.get("src_port"),
        }
        if is_anomalous:
            details["z_score"] = z_score
            details["is_anomalous"] = True

        # Generate narrative for this alert using the AI module
        dev_name = device.hostname or device.mac
        dev_type = device.device_type or "unknown"
        severity_enum = _severity_to_severity_enum(severity)

        alert_obj = narrator.alert(
            device_name=dev_name,
            device_type=dev_type,
            severity=severity_enum,
            anomaly_detail=f"{signature} — {alert_type}",
            trust_score=device.trust_score,
            extra={
                "z_score": z_score,
                "category": alert_type,
                "signature": signature,
            },
        )

        alert = Alert(
            device_id=device.id,
            timestamp=ts,
            alert_type=alert_type,
            severity=severity,
            narrative=alert_obj.description,
            status="open",
        )
        db.add(alert)
        db.flush()

        # Send email for critical/high alerts
        if severity in ("critical", "high"):
            try:
                email_ctx = AlertEmailContext(
                    severity=severity,
                    title=alert_type,
                    description=alert_obj.description,
                    timestamp=ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    device_name=dev_name,
                    mac_address=device.mac,
                    trust_score=device.trust_score,
                    device_type=dev_type,
                    device_id=device.id,
                    alert_id=alert.id,
                    alert_type=alert_type,
                )
                send_alert_email(email_ctx)
            except Exception as e:
                logger.error(f"Failed to send alert email: {e}")

    elif event_type == "dns":
        dns_data = record.get("dns", {})
        details = {
            "rrname": dns_data.get("rrname"),
            "rrtype": dns_data.get("rrtype"),
            "rcode": dns_data.get("rcode"),
            "answers": dns_data.get("answers", []),
        }
        if dns_data.get("rcode") != "NOERROR":
            severity = "low"

    elif event_type == "http":
        http_data = record.get("http", {})
        details = {
            "hostname": http_data.get("hostname"),
            "url": http_data.get("url"),
            "method": http_data.get("http_method"),
            "status": http_data.get("status"),
            "user_agent": http_data.get("http_user_agent"),
            "content_type": http_data.get("content_type"),
        }
        status = details.get("status")
        if status and status >= 400:
            severity = "low"

    elif event_type == "flow":
        flow_data = record.get("flow", {})
        details = {
            "pkts_toserver": flow_data.get("pkts_toserver"),
            "pkts_toclient": flow_data.get("pkts_toclient"),
            "bytes_toserver": flow_data.get("bytes_toserver"),
            "bytes_toclient": flow_data.get("bytes_toclient"),
            "start": flow_data.get("start"),
            "end": flow_data.get("end"),
            "age": flow_data.get("age"),
            "state": flow_data.get("state"),
            "proto": record.get("proto"),
            "dest_ip": record.get("dest_ip"),
            "dest_port": record.get("dest_port"),
        }
        severity = "info"

    elif event_type == "tls":
        tls_data = record.get("tls", {})
        details = {
            "subject": tls_data.get("subject"),
            "issuerdn": tls_data.get("issuerdn"),
            "fingerprint": tls_data.get("fingerprint"),
            "version": tls_data.get("version"),
            "sni": tls_data.get("sni"),
            "dest_ip": record.get("dest_ip"),
            "dest_port": record.get("dest_port"),
        }

    elif event_type == "netflow":
        netflow = record.get("netflow", {})
        details = {
            "pkts": netflow.get("pkts"),
            "bytes": netflow.get("bytes"),
            "start": netflow.get("start"),
            "end": netflow.get("end"),
            "age": netflow.get("age"),
            "proto": record.get("proto"),
            "dest_ip": record.get("dest_ip"),
            "dest_port": record.get("dest_port"),
        }

    else:
        # Generic catch-all for uncategorised event types (stats, anomaly, flow, etc.)
        details = {k: record[k] for k in record if k not in ("event_type", "timestamp", "src_ip", "dest_ip", "src_mac", "dest_mac", "eth")}

    if is_anomalous:
        details["z_score"] = z_score
        details["is_anomalous"] = True

    event = Event(
        device_id=device.id,
        timestamp=ts,
        event_type=event_type,
        severity=severity,
        details=details,
    )
    db.add(event)

    # Update trust score using Bayesian model
    device.trust_score = _update_trust_score(device.id, severity, db)
    device.last_seen = datetime.now(timezone.utc)

    db.commit()


def tail_eve_json():
    """Background thread: tail the eve.json file and process new lines."""
    eve_path = Path(EVE_JSON_PATH)
    if not eve_path.parent.exists():
        eve_path.parent.mkdir(parents=True, exist_ok=True)

    # Create an empty file if it doesn't exist so we can tail it
    if not eve_path.exists():
        eve_path.touch()

    with open(eve_path, "r") as f:
        # Seek to end on first open
        f.seek(0, 2)

        while True:
            line = f.readline()
            if line:
                line = line.strip()
                if line:
                    try:
                        db = SessionLocal()
                        try:
                            process_eve_line(line, db)
                        finally:
                            db.close()
                    except Exception:
                        pass
            else:
                time.sleep(POLL_INTERVAL)


def start_eve_consumer():
    """Start the eve.json tailing thread (daemon so it exits with main)."""
    thread = threading.Thread(target=tail_eve_json, daemon=True)
    thread.start()
    return thread
