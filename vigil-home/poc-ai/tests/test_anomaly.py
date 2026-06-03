"""
Unit tests for Vigil Anomaly Detection Module.

Run: python -m pytest tests/test_anomaly.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vigil.anomaly import AnomalyDetector, baseline_from_samples


# ── fixtures ───────────────────────────────────────────────────────

def _normal_samples(n=50, mean=500, std=50):
    import random
    return [random.gauss(mean, std) for _ in range(n)]


# ── tests ──────────────────────────────────────────────────────────

def test_initial_empty():
    det = AnomalyDetector(window_size=50)
    assert det.size == 0
    assert det.is_anomaly(100) is None  # not enough samples


def test_returns_none_before_min_samples():
    det = AnomalyDetector(window_size=100, min_samples=5)
    for i in range(4):
        det.record(float(i))
    assert det.size == 4
    assert det.is_anomaly(999) is None  # still below min_samples


def test_returns_result_after_min_samples():
    det = AnomalyDetector(window_size=50, min_samples=5)
    for v in [10, 12, 11, 9, 13]:
        det.record(float(v))
    r = det.is_anomaly(100)
    assert r is not None
    assert isinstance(r.is_anomaly, bool)
    assert isinstance(r.z_score, float)
    assert isinstance(r.mean, float)
    assert isinstance(r.std, float)


def test_normal_value_not_anomalous():
    samples = _normal_samples(50, 500, 50)
    det = baseline_from_samples(samples)
    r = det.record(510)
    assert r is not None
    assert not r.is_anomaly
    assert abs(r.z_score) < 2


def test_extreme_value_is_anomalous():
    samples = _normal_samples(50, 500, 50)
    det = baseline_from_samples(samples)
    r = det.record(5000)
    assert r is not None
    assert r.is_anomaly
    assert abs(r.z_score) > 3


def test_reset_clears_window():
    det = AnomalyDetector(window_size=10)
    for v in range(10):
        det.record(float(v))
    assert det.size == 10
    det.reset()
    assert det.size == 0
    assert det.is_anomaly(100) is None


def test_custom_z_threshold():
    """Lower threshold should flag moderate deviations."""
    samples = _normal_samples(50, 100, 10)
    det = baseline_from_samples(samples, z_threshold=1.0)
    r = det.record(130)
    assert r is not None
    assert r.is_anomaly  # 130 is 3σ above 100 with σ=10


def test_window_sliding():
    """Old values should slide out, allowing baseline to adapt."""
    det = AnomalyDetector(window_size=6, min_samples=3)
    for v in [100, 110, 105, 95, 105, 100]:
        det.record(float(v))
    r = det.record(1000)
    assert r is not None
    assert r.is_anomaly
    assert r.z_score > 3

    # Now fill window with high values — baseline should adapt
    for v in [1000, 1000, 1000, 1000, 1000, 1000]:
        det.record(float(v))
    # 1000 should now be normal after sliding
    r = det.record(1000)
    assert r is not None
    assert not r.is_anomaly


def test_anomaly_score_returns_zero_for_empty():
    det = AnomalyDetector(window_size=10)
    assert det.anomaly_score(50) == 0.0


def test_baseline_from_samples_seeding():
    samples = [10, 20, 30, 40, 50, 30, 25, 35, 40, 20]
    det = baseline_from_samples(samples, z_threshold=3.0)
    assert det.size == 10
    r = det.is_anomaly(500)
    assert r is not None
    assert r.is_anomaly


def test_single_value_std_handling():
    """With only one unique value, std=0. Should not crash."""
    det = AnomalyDetector(window_size=10, min_samples=3)
    for v in [42, 42, 42]:
        det.record(float(v))
    r = det.is_anomaly(999)
    assert r is not None
    # With std=0, anomaly_score returns 0 (edge case handled)
    assert not r.is_anomaly  # z_score = 0, not above threshold


def test_anomaly_result_fields():
    samples = _normal_samples(30, 100, 15)
    det = baseline_from_samples(samples, z_threshold=2.5)
    r = det.record(250)
    assert r is not None
    assert hasattr(r, "is_anomaly")
    assert hasattr(r, "z_score")
    assert hasattr(r, "mean")
    assert hasattr(r, "std")
    assert hasattr(r, "threshold")
    assert r.threshold == 2.5


def test_negative_z_score():
    """Values below mean should produce negative z-scores."""
    samples = _normal_samples(30, 500, 50)
    det = baseline_from_samples(samples)
    r = det.record(0)
    assert r is not None
    assert r.z_score < 0
