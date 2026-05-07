"""Vigil Home - Suricata eve.json consumer & detection logic"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.database import SessionLocal
from app.models import Device, Event, Alert

EVE_JSON_PATH = os.environ.get("VIGIL_EVE_JSON", "/var/log/suricata/eve.json")
POLL_INTERVAL = float(os.environ.get("VIGIL_POLL_INTERVAL", "2.0"))


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
    device = Device(
        mac=mac,
        ip=src_ip,
        hostname=hostname,
        device_type=_guess_device_type(hostname),
        trust_score=0.5,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


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


def _compute_trust_score(device_id: int, db) -> float:
    """Recalculate trust score based on recent events."""
    recent_events = (
        db.query(Event)
        .filter(Event.device_id == device_id)
        .order_by(Event.timestamp.desc())
        .limit(50)
        .all()
    )
    if not recent_events:
        return 0.5

    score = 0.5
    for ev in recent_events:
        if ev.severity == "critical":
            score -= 0.2
        elif ev.severity == "high":
            score -= 0.1
        elif ev.severity == "low":
            score += 0.02
        else:
            score += 0.01

    return max(0.0, min(1.0, score))


def process_eve_line(line: str, db):
    """Parse a single Suricata eve.json line and create events/alerts."""
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

        # Also create an alert record
        alert = Alert(
            device_id=device.id,
            timestamp=ts,
            alert_type=alert_type,
            severity=severity,
            narrative=signature,
            status="open",
        )
        db.add(alert)

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

    event = Event(
        device_id=device.id,
        timestamp=ts,
        event_type=event_type,
        severity=severity,
        details=details,
    )
    db.add(event)

    # Update trust score
    device.trust_score = _compute_trust_score(device.id, db)
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
