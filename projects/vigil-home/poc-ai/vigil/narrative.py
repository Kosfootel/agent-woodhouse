"""
Vigil Narrative Generator
=========================
Template-based natural-language threat descriptions for IoT security
alerts.  Maps severity levels, device types, and anomaly characteristics
to human-readable alerts with recommended actions.

Severity levels
---------------
0 – INFO     (informational, no action needed)
1 – LOW      (mildly unusual, monitor)
2 – MEDIUM   (suspicious, investigate)
3 – HIGH     (likely malicious, intervene)
4 – CRITICAL (active compromise, isolate immediately)

API
---
    NarrativeGenerator()
        .alert(device_name, device_type, severity, anomaly_desc,
               trust_score=None, extra=None) -> Alert
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any


# ── enums ──────────────────────────────────────────────────────────

class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


SEVERITY_LABELS = {
    Severity.INFO:     "ℹ️  Info",
    Severity.LOW:      "⚠️  Low",
    Severity.MEDIUM:   "🔶 Medium",
    Severity.HIGH:     "🔴 High",
    Severity.CRITICAL: "🚨 Critical",
}


# ── output structure ───────────────────────────────────────────────

@dataclass
class Alert:
    """Structured alert produced by the narrative generator."""
    timestamp: datetime
    device_name: str
    device_type: str
    severity: Severity
    summary: str           # one-line headline
    description: str       # detailed narrative
    recommendation: str    # what to do
    anomaly_detail: str    # raw anomaly data
    raw: dict[str, Any] = field(default_factory=dict)

    def formatted(self) -> str:
        """Return a nicely formatted alert string."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        sev = SEVERITY_LABELS.get(self.severity, f"Level {self.severity}")
        lines = [
            f"{'─' * 60}",
            f"  {sev}  {self.summary}",
            f"{'─' * 60}",
            f"  Device:    {self.device_name} ({self.device_type})",
            f"  Time:      {ts}",
            f"",
            f"  {self.description}",
            f"",
            f"  🛡  Recommendation:  {self.recommendation}",
            f"  📊 Detail:          {self.anomaly_detail}",
            f"{'─' * 60}",
        ]
        if self.raw:
            lines.append(f"  [raw: {self.raw}]")
            lines.append(f"{'─' * 60}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.formatted()


# ── templates ──────────────────────────────────────────────────────

_TEMPLATES: dict[str, list[str]] = {
    "traffic_spike": [
        "Traffic burst detected from {device_name}. "
        "Data volume is {z_desc} standard deviations above baseline, "
        "suggesting {cause}.",
        "{device_name} is transmitting at an abnormal rate. "
        "Volume is {z_desc}σ above normal, consistent with {cause}.",
    ],
    "connection_burst": [
        "{device_name} opened {count} connections in {window}. "
        "This is {z_desc}σ above the norm and may indicate {cause}.",
        "Unusual connection behaviour: {device_name} initiated "
        "{count} connections ({z_desc}σ above baseline), "
        "suggesting {cause}.",
    ],
    "off_hours": [
        "{device_name} was active at {time} — an unusual time for "
        "this device. Activity outside normal hours may indicate "
        "{cause}.",
        "Off-hours activity: {device_name} communicated at {time}, "
        "which is outside its typical operating window.",
    ],
    "new_protocol": [
        "{device_name} used protocol {protocol} for the first time. "
        "This is unusual for a {device_type} and may indicate {cause}.",
        "Novel protocol detected on {device_name}: {protocol}. "
        "Not in the device's historical signature.",
    ],
    "trust_drop": [
        "Trust score for {device_name} dropped from {old_score:.2f} "
        "to {new_score:.2f}. This sustained decline suggests "
        "{cause}.",
    ],
    "low_trust_threshold": [
        "Trust score for {device_name} has fallen below the "
        "low-trust threshold ({threshold:.2f}). Current score: "
        "{score:.2f}. Recommendation: {cause}.",
    ],
    "default": [
        "Unusual behaviour detected on {device_name}. "
        "Details: {anomaly_detail}. This may indicate {cause}.",
    ],
}

_CAUSES: dict[int, list[str]] = {
    Severity.INFO: [
        "routine network activity",
        "normal variation in device behaviour",
    ],
    Severity.LOW: [
        "a minor configuration change",
        "temporary network fluctuation",
        "firmware update in progress",
    ],
    Severity.MEDIUM: [
        "a misconfiguration or software bug",
        "possible reconnaissance activity",
        "unauthorised access attempt",
    ],
    Severity.HIGH: [
        "a coordinated attack or active exploitation",
        "data exfiltration in progress",
        "malware infection or remote control",
    ],
    Severity.CRITICAL: [
        "an active compromise — device should be isolated immediately",
        "confirmed malicious command-and-control activity",
        "critical vulnerability being exploited in real time",
    ],
}

_RECOMMENDATIONS: dict[int, list[str]] = {
    Severity.INFO: [
        "No action needed. This is normal variation.",
        "Monitor for trends over the next hour.",
    ],
    Severity.LOW: [
        "Review device logs for any recent changes.",
        "Check if a firmware update was recently applied.",
    ],
    Severity.MEDIUM: [
        "Investigate device activity and review recent connections.",
        "Check for known CVEs affecting this device model.",
        "Consider adding a temporary network rule to restrict this device.",
    ],
    Severity.HIGH: [
        "Isolate the device from the network immediately.",
        "Run a full security scan on the device and its recent connections.",
        "Review all recent traffic from this device for exfiltration patterns.",
    ],
    Severity.CRITICAL: [
        "Isolate the device NOW. Block all traffic to/from it at the gateway.",
        "Initiate incident response. Preserve logs and network captures.",
        "Notify the user. This device is likely compromised and actively hostile.",
    ],
}


# ── generator ──────────────────────────────────────────────────────

class NarrativeGenerator:
    """Produces human-readable security alerts from anomaly data.

    Usage:
        gen = NarrativeGenerator()
        alert = gen.alert("Nest Hub", "smart_display",
                          Severity.HIGH,
                          "traffic up 5x in last 10 min",
                          trust_score=0.32)
    """

    def __init__(self, templates: dict | None = None):
        self._templates = templates or _TEMPLATES

    def alert(
        self,
        device_name: str,
        device_type: str,
        severity: Severity | int,
        anomaly_detail: str,
        trust_score: float | None = None,
        extra: dict | None = None,
    ) -> Alert:
        """Generate an Alert for a detected anomaly.

        Parameters
        ----------
        device_name : str
            Human-readable device name (e.g. "Nest Hub Kitchen").
        device_type : str
            Device category (e.g. "camera", "speaker", "plug").
        severity : Severity | int
            Severity level (0–4).
        anomaly_detail : str
            Description of what was detected.
        trust_score : float | None
            Current trust score (0.0–1.0) if available.
        extra : dict | None
            Additional context for template rendering.

        Returns
        -------
        Alert
        """
        sev = Severity(severity)
        extra = extra or {}

        # Build template context
        ctx = {
            "device_name": device_name,
            "device_type": device_type,
            "severity": sev,
            "anomaly_detail": anomaly_detail,
        }
        if trust_score is not None:
            ctx["score"] = trust_score
            ctx["threshold"] = 0.3  # low-trust threshold
        ctx.update(extra)

        # Pick cause and template
        import random
        cause = random.choice(_CAUSES.get(sev, _CAUSES[Severity.MEDIUM]))
        ctx["cause"] = cause

        # Pick descriptive label for z-score if present
        if "z_desc" not in ctx and "z_score" in extra:
            z = extra["z_score"]
            if abs(z) <= 2:
                ctx["z_desc"] = "within normal range"
            elif abs(z) <= 3:
                ctx["z_desc"] = "moderately elevated"
            elif abs(z) <= 5:
                ctx["z_desc"] = "significantly elevated"
            else:
                ctx["z_desc"] = "extremely elevated"

        # Generate narrative from templates
        template_key = self._pick_template(extra)
        templates = self._templates.get(template_key, self._templates["default"])
        description = random.choice(templates).format(**ctx)

        # Summary (one-liner)
        summary = f"{device_name}: {anomaly_detail}"
        if trust_score is not None:
            summary += f" (trust: {trust_score:.2f})"

        # Recommendation
        recommendation = random.choice(
            _RECOMMENDATIONS.get(sev, _RECOMMENDATIONS[Severity.MEDIUM])
        )

        # Build raw dict
        raw = {
            "device_name": device_name,
            "device_type": device_type,
            "severity": sev.value,
            "severity_label": SEVERITY_LABELS[sev],
            "trust_score": trust_score,
            "anomaly_detail": anomally_detail,
            "cause": cause,
        }
        if extra:
            raw.update(extra)

        return Alert(
            timestamp=datetime.utcnow(),
            device_name=device_name,
            device_type=device_type,
            severity=sev,
            summary=summary,
            description=description,
            recommendation=recommendation,
            anomaly_detail=anomaly_detail,
            raw=raw,
        )

    @staticmethod
    def _pick_template(extra: dict) -> str:
        """Heuristic: choose the best-matching template key."""
        if extra.get("protocol"):
            return "new_protocol"
        if extra.get("count") or extra.get("connection_count"):
            return "connection_burst"
        if extra.get("z_score", 0) > 2:
            return "traffic_spike"
        if extra.get("time"):
            return "off_hours"
        if extra.get("trust_drop"):
            return "trust_drop"
        if extra.get("below_threshold"):
            return "low_trust_threshold"
        return "default"


# ── Example usage ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 50)
    print("Vigil Narrative Generator — Examples")
    print("═" * 50)

    gen = NarrativeGenerator()

    # 1. Traffic burst on a camera
    print("\n\n── Example 1: Traffic spike (HIGH) ──")
    alert = gen.alert(
        device_name="Kitchen Cam",
        device_type="camera",
        severity=Severity.HIGH,
        anomaly_detail="Upload traffic 8× above baseline (2.4 Mbps vs 300 kbps)",
        trust_score=0.45,
        extra={"z_score": 6.2, "protocol": "MQTT"},
    )
    print(alert.formatted())

    # 2. Off-hours activity on a smart plug
    print("\n\n── Example 2: Off-hours activity (MEDIUM) ──")
    alert = gen.alert(
        device_name="Living Room Plug",
        device_type="smart_plug",
        severity=Severity.MEDIUM,
        anomaly_detail="Device turned on at 03:14 (no scheduled activity)",
        extra={"time": "03:14"},
    )
    print(alert.formatted())

    # 3. Critical compromise
    print("\n\n── Example 3: Critical compromise ──")
    alert = gen.alert(
        device_name="Front Door Lock",
        device_type="smart_lock",
        severity=Severity.CRITICAL,
        anomaly_detail="Multiple failed auth attempts + connection to known C2 IP",
        trust_score=0.12,
        extra={"below_threshold": True, "ip": "185.220.101.x"},
    )
    print(alert.formatted())

    print("\n\nDone.")
