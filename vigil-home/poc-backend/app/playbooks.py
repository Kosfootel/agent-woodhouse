"""Vigil Playbooks — IF/THEN rule engine for automated containment.

All actions are SIMULATED in this POC. No real network changes.
"""

import json
import logging
from typing import Any

from app.database import SessionLocal
from app.models import Playbook, PlaybookRule, PlaybookExecution, Device, Alert

logger = logging.getLogger("vigil.playbooks")


# ── Condition metadata ───────────────────────────────────────────────────────

CONDITION_SCHEMA = {
    "trust_score_below": {
        "label": "Trust Score Below",
        "description": "Trigger when device trust score falls below threshold",
        "params": {"value": {"type": "float", "default": 0.3, "min": 0.0, "max": 1.0}},
    },
    "trust_score_above": {
        "label": "Trust Score Above",
        "description": "Trigger when device trust score rises above threshold",
        "params": {"value": {"type": "float", "default": 0.8, "min": 0.0, "max": 1.0}},
    },
    "device_offline": {
        "label": "Device Offline",
        "description": "Trigger when a device goes offline",
        "params": {},
    },
    "device_online": {
        "label": "Device Online",
        "description": "Trigger when a device comes online",
        "params": {},
    },
    "alert_severity": {
        "label": "Alert Severity",
        "description": "Trigger when alert severity matches",
        "params": {"value": {"type": "string", "default": "high", "options": ["critical", "high", "medium", "low", "info"]}},
    },
    "alert_type": {
        "label": "Alert Type",
        "description": "Trigger when alert type matches",
        "params": {"value": {"type": "string", "default": "anomaly"}},
    },
    "new_device": {
        "label": "New Device",
        "description": "Trigger when a new device is detected",
        "params": {},
    },
    "bandwidth_spike": {
        "label": "Bandwidth Spike",
        "description": "Trigger when bandwidth exceeds threshold (MB/s)",
        "params": {"value": {"type": "float", "default": 100.0, "min": 1.0}},
    },
}


# ── Action metadata ──────────────────────────────────────────────────────────

ACTION_SCHEMA = {
    "quarantine_device": {
        "label": "Quarantine Device",
        "description": "Move device to quarantine VLAN (simulated)",
        "params": {"duration_minutes": {"type": "int", "default": 30, "min": 1}},
    },
    "block_device": {
        "label": "Block Device",
        "description": "Block all traffic from device (simulated)",
        "params": {"duration_minutes": {"type": "int", "default": 60, "min": 1}},
    },
    "send_email": {
        "label": "Send Email Alert",
        "description": "Send email notification to admins (simulated)",
        "params": {"recipients": {"type": "list", "default": ["admin@vigil.local"]}, "subject": {"type": "string", "default": "Vigil Alert"}},
    },
    "send_webhook": {
        "label": "Send Webhook",
        "description": "POST to external webhook URL (simulated)",
        "params": {"url": {"type": "string", "default": "https://hooks.example.com/vigil"}},
    },
    "create_alert": {
        "label": "Create Alert",
        "description": "Create a new alert in the dashboard (simulated)",
        "params": {"severity": {"type": "string", "default": "high", "options": ["critical", "high", "medium", "low"]}},
    },
    "rate_limit": {
        "label": "Rate Limit",
        "description": "Throttle device bandwidth (simulated)",
        "params": {"max_mbps": {"type": "float", "default": 10.0, "min": 0.1}},
    },
}


# ── Condition evaluation ────────────────────────────────────────────────────

def evaluate_condition(condition: dict, context: dict) -> bool:
    """Evaluate a single condition against a context dictionary."""
    ctype = condition.get("type")
    params = condition.get("params", condition)  # Backwards compat

    if ctype == "trust_score_below":
        return context.get("trust_score", 0.5) < params.get("value", 0.3)
    if ctype == "trust_score_above":
        return context.get("trust_score", 0.5) > params.get("value", 0.8)
    if ctype == "device_offline":
        return not context.get("online", True)
    if ctype == "device_online":
        return context.get("online", False)
    if ctype == "alert_severity":
        return context.get("severity", "") == params.get("value", "high")
    if ctype == "alert_type":
        return context.get("type", "") == params.get("value", "anomaly")
    if ctype == "new_device":
        return context.get("is_new", False)
    if ctype == "bandwidth_spike":
        return context.get("bandwidth_mbps", 0) > params.get("value", 100.0)

    logger.warning("Unknown condition type: %s", ctype)
    return False


def evaluate_rule(rule: PlaybookRule, context: dict) -> bool:
    """Evaluate all conditions for a rule (AND logic)."""
    conditions = rule.conditions if isinstance(rule.conditions, list) else [rule.conditions]
    return all(evaluate_condition(c, context) for c in conditions)


# ── Action dispatch (simulated) ──────────────────────────────────────────────

def dispatch_action(action: dict, device: Device | None, alert: Alert | None) -> dict:
    """Dispatch a single action. All actions are simulated in this POC."""
    atype = action.get("type")
    params = action.get("params", action)
    device_mac = device.mac if device else "unknown"
    device_ip = device.ip if device else "unknown"

    if atype == "quarantine_device":
        duration = params.get("duration_minutes", 30)
        return {
            "status": "simulated",
            "action": "quarantine_device",
            "would_do": f"Move device {device_mac} to quarantine VLAN for {duration} minutes",
            "device": device_mac,
            "duration_minutes": duration,
        }

    if atype == "block_device":
        duration = params.get("duration_minutes", 60)
        return {
            "status": "simulated",
            "action": "block_device",
            "would_do": f"Block all traffic from device {device_mac} for {duration} minutes",
            "device": device_mac,
            "duration_minutes": duration,
        }

    if atype == "send_email":
        recipients = params.get("recipients", ["admin@vigil.local"])
        subject = params.get("subject", "Vigil Alert")
        return {
            "status": "simulated",
            "action": "send_email",
            "would_do": f"Send email to {recipients} with subject '{subject}'",
            "recipients": recipients,
            "subject": subject,
        }

    if atype == "send_webhook":
        url = params.get("url", "https://hooks.example.com/vigil")
        return {
            "status": "simulated",
            "action": "send_webhook",
            "would_do": f"POST alert data to {url}",
            "url": url,
        }

    if atype == "create_alert":
        severity = params.get("severity", "high")
        return {
            "status": "simulated",
            "action": "create_alert",
            "would_do": f"Create {severity} severity alert for device {device_mac}",
            "severity": severity,
        }

    if atype == "rate_limit":
        max_mbps = params.get("max_mbps", 10.0)
        return {
            "status": "simulated",
            "action": "rate_limit",
            "would_do": f"Throttle device {device_mac} to {max_mbps} Mbps",
            "device": device_mac,
            "max_mbps": max_mbps,
        }

    logger.warning("Unknown action type: %s", atype)
    return {"status": "unknown", "action": atype, "would_do": "No simulation defined"}


# ── Playbook execution ──────────────────────────────────────────────────────

def _build_device_context(device: Device) -> dict:
    """Build evaluation context from a Device object."""
    return {
        "trust_score": device.trust_score,
        "online": device.to_dict().get("online", True),
        "is_new": False,  # Determined by caller if needed
        "bandwidth_mbps": 0,  # Would come from real-time metrics
        "device_type": device.device_type,
        "mac": device.mac,
        "ip": device.ip,
    }


def _build_alert_context(alert: Alert, device: Device | None = None) -> dict:
    """Build evaluation context from an Alert object."""
    ctx = {
        "severity": alert.severity,
        "type": alert.type,
        "description": alert.description,
        "alert_id": alert.id,
    }
    if device:
        ctx.update(_build_device_context(device))
    return ctx


def run_playbooks_for_device(device: Device, db_session=None) -> list[dict]:
    """Evaluate all active playbooks against a device and execute actions."""
    db = db_session or SessionLocal()
    results = []
    try:
        playbooks = db.query(Playbook).filter(Playbook.is_active == 1).all()
        context = _build_device_context(device)

        for playbook in playbooks:
            for rule in playbook.rules:
                if rule.is_active == 0:
                    continue
                if evaluate_rule(rule, context):
                    actions_results = [dispatch_action(a, device, None) for a in rule.actions]
                    execution = PlaybookExecution(
                        playbook_id=playbook.id,
                        rule_id=rule.id,
                        device_id=device.id,
                        conditions_met=rule.conditions,
                        actions_executed=actions_results,
                        execution_context=context,
                    )
                    db.add(execution)
                    db.commit()
                    results.append({
                        "playbook_id": playbook.id,
                        "rule_id": rule.id,
                        "device_id": device.id,
                        "actions": actions_results,
                    })
        return results
    finally:
        if db_session is None:
            db.close()


def run_playbooks_for_alert(alert: Alert, device: Device | None = None, db_session=None) -> list[dict]:
    """Evaluate all active playbooks against an alert and execute actions."""
    db = db_session or SessionLocal()
    results = []
    try:
        playbooks = db.query(Playbook).filter(Playbook.is_active == 1).all()
        # Try to find the device associated with this alert
        if device is None:
            device = db.query(Device).filter(Device.id == alert.device_id).first()
        context = _build_alert_context(alert, device)

        for playbook in playbooks:
            for rule in playbook.rules:
                if rule.is_active == 0:
                    continue
                if evaluate_rule(rule, context):
                    actions_results = [dispatch_action(a, device, alert) for a in rule.actions]
                    execution = PlaybookExecution(
                        playbook_id=playbook.id,
                        rule_id=rule.id,
                        device_id=device.id if device else None,
                        alert_id=alert.id,
                        conditions_met=rule.conditions,
                        actions_executed=actions_results,
                        execution_context=context,
                    )
                    db.add(execution)
                    db.commit()
                    results.append({
                        "playbook_id": playbook.id,
                        "rule_id": rule.id,
                        "alert_id": alert.id,
                        "device_id": device.id if device else None,
                        "actions": actions_results,
                    })
        return results
    finally:
        if db_session is None:
            db.close()
