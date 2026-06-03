"""
Vigil Home — Shared Utilities
==============================
Consolidated helper functions used by both main.py (API) and
detection.py (Eve consumer), extracted to eliminate code duplication.

All four functions defined here formerly existed as identical or
near-identical copies in both modules.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.ai import Severity, TrustModel, AnomalyDetector
from app.ai_persistence import get_anomaly_detector as _get_ad, get_trust_model as _get_tm


def get_anomaly_detector(device_id: int, db: Session) -> AnomalyDetector:
    """Get the AnomalyDetector for a device, loading from DB if not cached.

    Delegates to ai_persistence.get_anomaly_detector() which owns the
    shared in-process cache.
    """
    return _get_ad(device_id, db)


def get_trust_model(device_id: int, db: Session) -> TrustModel:
    """Get the TrustModel for a device, loading from DB if not cached.

    Delegates to ai_persistence.get_trust_model() which owns the
    shared in-process cache.
    """
    return _get_tm(device_id, db)


def severity_to_severity_enum(sev_str: str) -> Severity:
    """Map backend severity string to narrative Severity enum."""
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return mapping.get(sev_str, Severity.INFO)


def build_classification_features(hostname: str | None) -> dict | None:
    """Build behavioural feature hints from hostname for device classification.

    Returns a dict of features (protocols, ports, traffic_kbps,
    connections_hour, active_hour) or None if no hostname is provided.
    """
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
