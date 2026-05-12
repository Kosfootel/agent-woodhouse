"""Tests for NarrativeGenerator (via app/ai/narrative.py backend wrapper).

Tests cover severity levels, template selection, output structure, and
edge cases like missing data.
"""

import pytest
from datetime import datetime, timezone

from app.ai.narrative import (
    NarrativeGenerator,
    Severity,
    Alert,
    SEVERITY_LABELS,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def gen():
    return NarrativeGenerator()


# ── Tests: Severity enum ────────────────────────────────────────────


class TestSeverity:
    def test_severity_values(self):
        assert Severity.INFO == 0
        assert Severity.LOW == 1
        assert Severity.MEDIUM == 2
        assert Severity.HIGH == 3
        assert Severity.CRITICAL == 4

    def test_severity_from_int(self):
        assert Severity(0) == Severity.INFO
        assert Severity(4) == Severity.CRITICAL

    def test_severity_ordering(self):
        assert Severity.INFO < Severity.CRITICAL
        assert Severity.LOW < Severity.HIGH
        assert Severity.MEDIUM < Severity.CRITICAL

    def test_severity_labels_exist(self):
        for sev in Severity:
            assert sev in SEVERITY_LABELS
            assert isinstance(SEVERITY_LABELS[sev], str)


# ── Tests: Alert output structure ───────────────────────────────────


class TestAlertStructure:
    def test_alert_dataclass(self):
        ts = datetime.now(timezone.utc)
        alert = Alert(
            timestamp=ts,
            device_name="Kitchen Cam",
            device_type="camera",
            severity=Severity.HIGH,
            summary="Traffic spike",
            description="Upload traffic 8x above baseline",
            recommendation="Isolate the device",
            anomaly_detail="2.4 Mbps vs 300 kbps",
            raw={"z_score": 6.2},
        )
        assert alert.timestamp == ts
        assert alert.device_name == "Kitchen Cam"
        assert alert.severity == Severity.HIGH
        assert alert.formatted()  # should not raise
        assert str(alert)  # should not raise

    def test_alert_no_raw(self):
        alert = Alert(
            timestamp=datetime.now(timezone.utc),
            device_name="Test",
            device_type="unknown",
            severity=Severity.INFO,
            summary="Test",
            description="Description",
            recommendation="None",
            anomaly_detail="Nothing",
        )
        formatted = alert.formatted()
        assert "[raw:" not in formatted  # raw section omitted when empty

    def test_alert_formatted_contains_key_info(self, gen):
        alert = gen.alert(
            device_name="Nest Hub",
            device_type="smart_speaker",
            severity=Severity.HIGH,
            anomaly_detail="Traffic spike detected",
            trust_score=0.45,
            extra={"z_score": 4.5},
        )
        formatted = alert.formatted()
        assert "Nest Hub" in formatted
        assert "HIGH" in formatted or "🔴" in formatted
        assert "Recommendation" in formatted or "recommendation" in formatted.lower()
        assert "smart_speaker" in alert.raw["device_type"]


# ── Tests: Alert generation ─────────────────────────────────────────


class TestAlertGeneration:
    def test_generates_alert(self, gen):
        alert = gen.alert(
            device_name="Test Device",
            device_type="sensor",
            severity=Severity.MEDIUM,
            anomaly_detail="Unusual reading",
        )
        assert isinstance(alert, Alert)
        assert alert.device_name == "Test Device"
        assert alert.device_type == "sensor"
        assert alert.severity == Severity.MEDIUM
        assert alert.anomaly_detail == "Unusual reading"

    def test_generates_all_severity_levels(self, gen):
        for sev in Severity:
            alert = gen.alert(
                device_name="Device",
                device_type="generic",
                severity=sev,
                anomaly_detail=f"Test {sev.name}",
            )
            assert alert.severity == sev
            assert alert.raw["severity"] == sev.value

    def test_generates_summary(self, gen):
        alert = gen.alert(
            device_name="Kitchen Cam",
            device_type="camera",
            severity=Severity.HIGH,
            anomaly_detail="Traffic burst",
        )
        assert alert.summary.startswith("Kitchen Cam")
        assert alert.summary != ""

    def test_generates_recommendation(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.CRITICAL,
            anomaly_detail="Critical issue",
        )
        assert len(alert.recommendation) > 10
        assert "Isolate" in alert.recommendation or "isolate" in alert.recommendation.lower()

    def test_trust_score_in_summary(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.HIGH,
            anomaly_detail="Something wrong",
            trust_score=0.35,
        )
        assert "trust: 0.35" in alert.summary or "trust" in alert.summary.lower()

    def test_trust_score_not_always_present(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.LOW,
            anomaly_detail="Minor thing",
        )
        assert alert.raw["trust_score"] is None


# ── Tests: Template selection ───────────────────────────────────────


class TestTemplateSelection:
    def test_traffic_spike_template(self, gen):
        alert = gen.alert(
            device_name="Camera",
            device_type="camera",
            severity=Severity.HIGH,
            anomaly_detail="Traffic spike",
            extra={"z_score": 4.5},
        )
        desc = alert.description.lower()
        # Should mention traffic or volume
        assert any(word in desc for word in ("traffic", "volume", "transmitting", "baseline"))

    def test_connection_burst_template(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.MEDIUM,
            anomaly_detail="Connection burst",
            extra={"count": 150, "connection_count": 150},
        )
        desc = alert.description.lower()
        assert "connection" in desc or "opened" in desc

    def test_low_trust_threshold_template(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.CRITICAL,
            anomaly_detail="Trust below threshold",
            extra={"below_threshold": True, "z_score": 3.0},
        )
        # Should match low_trust_threshold or traffic_spike
        assert alert.description  # always present

    def test_default_template(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.LOW,
            anomaly_detail="Something unusual",
        )
        assert alert.description  # always present


# ── Tests: Z-score description mapping ──────────────────────────────


class TestZScoreDescription:
    def test_z_within_normal(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.LOW,
            anomaly_detail="Test",
            extra={"z_score": 1.5},
        )
        assert alert.raw.get("z_desc") == "within normal range"

    def test_z_moderately_elevated(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.MEDIUM,
            anomaly_detail="Test",
            extra={"z_score": 2.5},
        )
        assert alert.raw.get("z_desc") == "moderately elevated"

    def test_z_significantly_elevated(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.HIGH,
            anomaly_detail="Test",
            extra={"z_score": 4.0},
        )
        assert alert.raw.get("z_desc") == "significantly elevated"

    def test_z_extremely_elevated(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.CRITICAL,
            anomaly_detail="Test",
            extra={"z_score": 6.5},
        )
        assert alert.raw.get("z_desc") == "extremely elevated"


# ── Tests: Edge cases ──────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_device_name(self, gen):
        alert = gen.alert(
            device_name="",
            device_type="unknown",
            severity=Severity.INFO,
            anomaly_detail="Something",
        )
        assert isinstance(alert, Alert)
        assert alert.description  # non-empty description

    def test_empty_device_type(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="",
            severity=Severity.MEDIUM,
            anomaly_detail="Issue",
        )
        assert isinstance(alert, Alert)

    def test_empty_anomaly_detail(self, gen):
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.HIGH,
            anomaly_detail="",
        )
        assert isinstance(alert, Alert)

    def test_severity_as_int(self, gen):
        """Should accept raw integer severity values."""
        alert = gen.alert(
            device_name="D",
            device_type="t",
            severity=3,
            anomaly_detail="Test",
        )
        assert alert.severity == Severity.HIGH

    def test_extra_with_many_fields(self, gen):
        extra = {
            "z_score": 3.2,
            "protocol": "MQTT",
            "ip": "10.0.0.1",
            "signature": "ET MALWARE",
            "category": "Trojan",
            "count": 500,
            "time": "03:14",
        }
        alert = gen.alert(
            device_name="Device",
            device_type="unknown",
            severity=Severity.CRITICAL,
            anomaly_detail="Multiple indicators",
            trust_score=0.15,
            extra=extra,
        )
        for key in extra:
            assert key in alert.raw
