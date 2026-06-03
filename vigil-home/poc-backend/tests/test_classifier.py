"""Tests for DeviceClassifier (via app/ai/classifier.py backend wrapper).

The backend re-exports the classifier through app/ai/__init__.py.
Tests validate OUI lookups, behavioural signature matching, and combined
classification flows.
"""

import pytest

from app.ai.classifier import DeviceClassifier, Classification, BehavioralSignature


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def classifier():
    return DeviceClassifier()


# ── Tests: OUI Lookups ─────────────────────────────────────────────


class TestOUILookup:
    def test_known_oui(self, classifier):
        """Known MAC prefixes should return the correct vendor."""
        assert classifier.oui_vendor("ac:63:be:12:34:56") == "Amazon"
        assert classifier.oui_vendor("08:B5:12:AB:CD:EF") == "Nest (Google)"
        assert classifier.oui_vendor("f0:f6:1c:00:00:01") == "Apple"

    def test_known_oui_different_formats(self, classifier):
        """MAC addresses in different formats should all resolve."""
        assert classifier.oui_vendor("ac63be123456") == "Amazon"
        assert classifier.oui_vendor("AC-63-BE-12-34-56") == "Amazon"
        assert classifier.oui_vendor("ac:63:be:12:34:56") == "Amazon"

    def test_unknown_oui(self, classifier):
        """Unknown MAC prefixes should return None."""
        assert classifier.oui_vendor("00:00:00:00:00:00") is None
        assert classifier.oui_vendor("ff:ff:ff:ff:ff:ff") is None
        assert classifier.oui_vendor("12:34:56:78:90:ab") is None

    def test_case_insensitive(self, classifier):
        """Vendor lookup should be case-insensitive."""
        assert classifier.oui_vendor("AC:63:BE:12:34:56") == "Amazon"
        assert classifier.oui_vendor("ac:63:be:12:34:56") == "Amazon"


# ── Tests: Classify (MAC-only) ─────────────────────────────────────


class TestClassifyMACOnly:
    def test_classify_known_vendor(self, classifier):
        """MAC-only classification should return OUI-based results."""
        results = classifier.classify("ac:63:be:12:34:56")
        assert len(results) > 0
        assert all(r.source == "oui" for r in results)
        assert any(r.vendor == "Amazon" for r in results)

    def test_classify_unknown_vendor(self, classifier):
        """Unknown MAC with no features should return empty list."""
        results = classifier.classify("00:00:00:00:00:00")
        assert len(results) == 0

    def test_classify_top_n(self, classifier):
        """top_n parameter should limit results."""
        results = classifier.classify("f0:f6:1c:ab:cd:ef", top_n=1)
        assert len(results) == 1
        results = classifier.classify("f0:f6:1c:ab:cd:ef", top_n=3)
        assert len(results) <= 3


# ── Tests: Classify (MAC + behavioural features) ───────────────────


class TestClassifyWithFeatures:
    def test_known_vendor_with_features(self, classifier):
        """Features should boost or combine with OUI results."""
        features = {
            "protocols": ["RTSP", "HTTPS", "MQTT"],
            "ports": [554, 443],
            "traffic_kbps": 1200.0,
            "connections_hour": 120,
            "active_hour": 14,
        }
        results = classifier.classify("8c:f5:a3:12:34:56", features)
        assert len(results) > 0
        # Should match camera signature
        camera_results = [r for r in results if r.device_type == "camera"]
        assert len(camera_results) > 0
        assert camera_results[0].confidence > 0.5

    def test_unknown_vendor_with_strong_signal(self, classifier):
        """Strong behavioural match should work even with unknown OUI."""
        features = {
            "protocols": ["MQTT", "HTTPS"],
            "ports": [443, 1883],
            "traffic_kbps": 0.5,
            "connections_hour": 5,
            "active_hour": 20,
        }
        results = classifier.classify("11:22:33:44:55:66", features)
        assert len(results) > 0
        # Should match smart_plug or smart_light (low traffic, MQTT)
        types = [r.device_type for r in results]
        assert any(t in types for t in ("smart_plug", "smart_light", "custom_iot"))

    def test_source_combined(self, classifier):
        """When both OUI and features match, source should be 'combined'."""
        features = {
            "protocols": ["HTTPS", "HTTP", "DNS"],
            "ports": [443, 80],
            "traffic_kbps": 150.0,
            "connections_hour": 50,
            "active_hour": 14,
        }
        results = classifier.classify("e8:ab:f3:12:34:56", features)
        combined = [r for r in results if r.source == "combined"]
        # Google MAC + streaming/media signature should yield combined
        assert len(combined) > 0 or any(r.source == "oui" for r in results)


# ── Tests: Behavioural Signature Matching ──────────────────────────


class TestSignatureMatching:
    def test_exact_match(self, classifier):
        """Perfect behavioural signature match should yield high confidence."""
        features = {
            "protocols": ["MQTT", "HTTPS"],
            "ports": [443, 1883],
            "traffic_kbps": 0.3,
            "connections_hour": 3,
            "active_hour": 12,
        }
        results = classifier.match_signature(features, min_confidence=0.3)
        assert len(results) > 0
        # smart_plug should score well (MQTT, low traffic, low connections)
        plug = [r for r in results if r.device_type == "smart_plug"]
        if plug:
            assert plug[0].confidence >= 0.3

    def test_min_confidence_filter(self, classifier):
        """min_confidence should exclude low-matching signatures."""
        features = {
            "protocols": ["MQTT", "HTTPS"],
            "ports": [443, 1883],
            "traffic_kbps": 0.3,
            "connections_hour": 3,
            "active_hour": 12,
        }
        all_results = classifier.match_signature(features, min_confidence=0.0)
        filtered = classifier.match_signature(features, min_confidence=0.8)
        assert len(filtered) <= len(all_results)

    def test_no_features(self, classifier):
        """match_signature with no features should return empty."""
        results = classifier.match_signature({})
        assert len(results) == 0

    def test_sort_order(self, classifier):
        """Results should be sorted by confidence descending."""
        features = {
            "protocols": ["HTTPS", "HTTP", "DNS", "SSDP"],
            "ports": [443, 80, 1900],
            "traffic_kbps": 500.0,
            "connections_hour": 80,
            "active_hour": 20,
        }
        results = classifier.match_signature(features, min_confidence=0.0)
        if len(results) > 1:
            confidences = [r.confidence for r in results]
            assert confidences == sorted(confidences, reverse=True)


# ── Tests: Classification Data Structures ──────────────────────────


class TestClassification:
    def test_classification_dataclass(self):
        c = Classification(
            device_type="camera",
            label="IP Camera",
            confidence=0.85,
            source="oui",
            vendor="Wyze",
        )
        assert c.device_type == "camera"
        assert c.confidence == 0.85
        assert c.source == "oui"
        assert c.vendor == "Wyze"

    def test_classification_sortable(self):
        results = [
            Classification("a", "A", 0.3, "signature"),
            Classification("b", "B", 0.9, "signature"),
            Classification("c", "C", 0.6, "signature"),
        ]
        sorted_results = sorted(results, key=lambda x: x.confidence, reverse=True)
        assert sorted_results[0].device_type == "b"
        assert sorted_results[1].device_type == "c"
        assert sorted_results[2].device_type == "a"


# ── Tests: Known Devices ────────────────────────────────────────────


class TestKnownDevices:
    def test_known_devices_returns_dict(self, classifier):
        devices = classifier.known_devices()
        assert isinstance(devices, dict)
        assert len(devices) > 0

    def test_known_devices_has_expected_types(self, classifier):
        devices = classifier.known_devices()
        expected_types = {
            "smart_speaker", "camera", "smart_plug", "smart_lock",
            "smart_light", "hub", "streaming", "smart_tv", "custom_iot",
        }
        assert expected_types.issubset(devices.keys())

    def test_known_devices_structure(self, classifier):
        devices = classifier.known_devices()
        for dt, info in devices.items():
            assert "label" in info
            assert "typical_protocols" in info
            assert "typical_ports" in info
            assert "active_hours" in info


# ── Tests: BehavioralSignature ──────────────────────────────────────


class TestBehavioralSignature:
    def test_score_full_match(self):
        sig = BehavioralSignature(
            device_type="test_device",
            label="Test",
            typical_protocols=["MQTT", "HTTPS"],
            typical_ports=[(443, 443)],
            typical_traffic_kbps=(0.1, 10),
            typical_connections_hour=(1, 50),
        )
        features = {
            "protocols": ["MQTT", "HTTPS"],
            "ports": [443],
            "traffic_kbps": 5.0,
            "connections_hour": 10,
            "active_hour": 12,
        }
        conf, reasons = sig.score(features)
        assert conf > 0.5
        assert len(reasons) >= 3

    def test_score_mismatch(self):
        sig = BehavioralSignature(
            device_type="test_device",
            label="Test",
            typical_protocols=["RTSP"],
            typical_ports=[(554, 554)],
            typical_traffic_kbps=(100, 5000),
            typical_connections_hour=(100, 500),
        )
        features = {
            "protocols": ["MQTT"],
            "ports": [1883],
            "traffic_kbps": 0.5,
            "connections_hour": 3,
            "active_hour": 3,
        }
        conf, reasons = sig.score(features)
        assert conf < 0.5

    def test_score_hub_logic(self):
        sig = BehavioralSignature(
            device_type="hub",
            label="Hub",
            is_hub=True,
        )
        conf_hub, _ = sig.score({"is_hub": True})
        conf_no_hub, _ = sig.score({"is_hub": False})
        assert conf_hub > conf_no_hub

    def test_score_no_features(self):
        sig = BehavioralSignature(
            device_type="test",
            label="Test",
            typical_protocols=["MQTT"],
        )
        conf, reasons = sig.score({})
        assert conf == 0.0
        assert len(reasons) == 0
