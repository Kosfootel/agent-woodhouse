"""
Unit tests for Vigil Trust Model.

Run: python -m pytest tests/test_trust.py -v
     (or pytest from the project root)
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vigil.trust import TrustModel, _adjust_evidence


# ── unit tests ─────────────────────────────────────────────────────

def test_initial_score_is_neutral():
    """Beta(1, 1) → score = 0.5."""
    tm = TrustModel()
    assert tm.score == 0.5
    assert tm.alpha == 1.0
    assert tm.omega == 1.0


def test_initial_certainty_zero():
    """At minimum evidence, certainty ≈ 0."""
    tm = TrustModel()
    assert tm.certainty == 0.0


def test_positive_updates_increase_score():
    tm = TrustModel()
    for _ in range(10):
        tm.update(positive=True)
    assert tm.score > 0.5
    assert tm.alpha > tm.omega


def test_negative_updates_decrease_score():
    tm = TrustModel()
    for _ in range(10):
        tm.update(positive=False)
    assert tm.score < 0.5
    assert tm.omega > tm.alpha


def test_mixed_evidence():
    tm = TrustModel()
    for _ in range(5):
        tm.update(positive=True)
    assert tm.score > 0.7  # 5 good, 0 bad → high trust
    for _ in range(5):
        tm.update(positive=False)
    # Now roughly 6 vs 6 (including prior of 1 each) → back near 0.5
    assert 0.4 < tm.score < 0.6


def test_certainty_increases_with_evidence():
    tm = TrustModel()
    assert tm.certainty == 0.0
    for _ in range(100):
        tm.update(positive=True)
    assert tm.certainty > 0.9


def test_decay_toward_neutral():
    tm = TrustModel(half_life=3600)  # 1 hour half-life
    for _ in range(20):
        tm.update(positive=True)
    score_before = tm.score
    assert score_before > 0.9

    # Simulate 4 hours passing
    future = time.time() + 14400
    score_after = tm.decay(future)
    assert score_after < score_before
    assert score_after > 0.5  # decayed toward neutral, not past it


def test_decay_does_not_cross_neutral():
    """Decay should head toward neutral (0.5), not past it."""
    tm = TrustModel(half_life=3600)
    for _ in range(20):
        tm.update(positive=True)
    # A very long decay
    far_future = time.time() + 30 * 86400  # 30 days
    tm.decay(far_future)
    # Should approach but not cross 0.5
    assert tm.score >= 0.5


def test_reset():
    tm = TrustModel()
    for _ in range(20):
        tm.update(positive=False)
    assert tm.score < 0.3
    tm.reset()
    assert tm.score == 0.5
    assert tm.alpha == 1.0
    assert tm.omega == 1.0


def test_score_with_decay_shortcut():
    tm = TrustModel(half_life=3600)
    for _ in range(10):
        tm.update(positive=True)
    score = tm.score_with_decay(time.time() + 7200)
    assert isinstance(score, float)


def test_adjust_evidence_returns_neutral_at_extreme_decay():
    """When half-life is exceeded by a huge margin, approach prior."""
    result = _adjust_evidence(100.0, 3600, 3600 * 100)
    assert 1.0 <= result < 2.0  # close to neutral


def test_adjust_evidence_no_decay():
    """Zero elapsed should return unchanged."""
    result = _adjust_evidence(5.0, 3600, 0)
    assert result == 5.0


def test_half_life_effect():
    """Check that shorter half-life causes faster decay."""
    tm_fast = TrustModel(half_life=10)   # 10 seconds
    tm_slow = TrustModel(half_life=3600) # 1 hour
    for _ in range(20):
        tm_fast.update(positive=True)
        tm_slow.update(positive=True)
    future = time.time() + 60  # 1 minute
    fast_score = tm_fast.decay(future)
    slow_score = tm_slow.decay(future)
    assert fast_score < slow_score


def test_update_custom_weight():
    tm = TrustModel()
    tm.update(positive=False, weight=5.0)
    assert tm.omega == 6.0  # default 1 + 5
    assert 0.2 < tm.score < 0.3  # α=1, ω=6 → ~0.14
