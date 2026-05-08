"""Vigil Home - Email Poller Service

Runs as a standalone daemon that polls the Vigil API for new critical/high
alerts and sends email notifications. This is an alternative to embedding
email logic directly in the Vigil API.

Usage:
    python -m app.email_poller

Environment variables:
    VIGIL_API_URL      - Base URL of Vigil API (default: http://vigil-api:8000)
    VIGIL_POLL_SECONDS - Poll interval in seconds (default: 30)
    LAST_ALERT_ID_PATH - File to persist last processed alert ID (default: /data/last_alert_id.txt)
"""

import os
import time
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from app.email_notifier import AlertEmailContext, send_alert_email, get_email_status

logger = logging.getLogger("vigil.email_poller")

# ── Configuration ──────────────────────────────────────────────────

VIGIL_API_URL = os.environ.get("VIGIL_API_URL", "http://vigil-api:8000").rstrip("/")
POLL_SECONDS = int(os.environ.get("VIGIL_POLL_SECONDS", "30"))
LAST_ALERT_ID_PATH = os.environ.get("LAST_ALERT_ID_PATH", "/data/last_alert_id.txt")


def _fetch_json(url: str) -> dict | list | None:
    """Fetch JSON from a URL with error handling."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP {e.code} fetching {url}")
        return None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.warning(f"Connection error fetching {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error from {url}: {e}")
        return None


def _load_last_alert_id() -> int:
    """Load the last processed alert ID from disk."""
    path = Path(LAST_ALERT_ID_PATH)
    if path.exists():
        try:
            return int(path.read_text().strip())
        except (ValueError, OSError):
            pass
    return 0


def _save_last_alert_id(alert_id: int):
    """Persist the last processed alert ID."""
    try:
        Path(LAST_ALERT_ID_PATH).write_text(str(alert_id))
    except OSError as e:
        logger.error(f"Failed to persist last alert ID: {e}")


def _fetch_device_info(device_id: int) -> dict | None:
    """Fetch device details from Vigil API."""
    url = f"{VIGIL_API_URL}/devices/{device_id}"
    return _fetch_json(url)


def process_alert(alert: dict) -> bool:
    """Process a single alert and send email if applicable.

    Returns True if an email was sent.
    """
    severity = alert.get("severity", "info")
    if severity not in ("critical", "high"):
        return False

    device_id = alert.get("device_id")
    device_info = _fetch_device_info(device_id) if device_id else None

    dev_name = "unknown"
    mac_address = "00:00:00:00:00:00"
    trust_score = 0.5
    dev_type = "unknown"

    if device_info:
        dev_name = device_info.get("hostname") or device_info.get("mac", "unknown")
        mac_address = device_info.get("mac", "00:00:00:00:00:00")
        trust_score = device_info.get("trust_score", 0.5)
        dev_type = device_info.get("device_type", "unknown")

    ctx = AlertEmailContext(
        severity=severity,
        title=alert.get("alert_type", "Unknown Alert"),
        description=alert.get("narrative", "No description available."),
        timestamp=alert.get("timestamp", datetime.now(timezone.utc).isoformat()),
        device_name=dev_name,
        mac_address=mac_address,
        trust_score=trust_score,
        device_type=dev_type,
        device_id=device_id if device_id else 0,
        alert_id=alert.get("id", 0),
        alert_type=alert.get("alert_type", "unknown"),
    )

    return send_alert_email(ctx)


def poll_once(last_id: int) -> int:
    """Poll Vigil API for new alerts and process them.

    Returns the highest processed alert ID.
    """
    url = f"{VIGIL_API_URL}/alerts?status=open"
    data = _fetch_json(url)
    if not data:
        return last_id

    alerts = data.get("alerts", [])
    if not alerts:
        return last_id

    new_max = last_id

    # Process alerts from oldest to newest based on ID
    for alert in sorted(alerts, key=lambda a: a.get("id", 0)):
        alert_id = alert.get("id", 0)
        if alert_id > last_id:
            severity = alert.get("severity", "info")
            try:
                sent = process_alert(alert)
                if sent:
                    logger.info(
                        f"Alert {alert_id} ({severity}): "
                        f"{alert.get('alert_type', 'unknown')} -> email sent"
                    )
                else:
                    logger.debug(
                        f"Alert {alert_id} ({severity}): "
                        f"{alert.get('alert_type', 'unknown')} -> skipped"
                    )
            except Exception as e:
                logger.error(f"Failed to process alert {alert_id}: {e}")
            new_max = max(new_max, alert_id)

    return new_max


def run_poller():
    """Main polling loop."""
    logger.info(
        f"Email poller started: polling {VIGIL_API_URL} every {POLL_SECONDS}s"
    )
    logger.info(f"Email status: {get_email_status()}")

    last_id = _load_last_alert_id()
    logger.info(f"Resuming from alert ID {last_id}")

    while True:
        try:
            new_last_id = poll_once(last_id)
            if new_last_id > last_id:
                last_id = new_last_id
                _save_last_alert_id(last_id)
                logger.info(f"Checkpoint updated: last alert ID = {last_id}")
        except Exception as e:
            logger.error(f"Poll cycle error: {e}")

        time.sleep(POLL_SECONDS)


# ── CLI entry point ────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Vigil Email Poller starting...")
    run_poller()


if __name__ == "__main__":
    main()
