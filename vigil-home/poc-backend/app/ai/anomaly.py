"""
Vigil Anomaly Detection Module
==============================
Statistical outlier detection for IoT device behaviour using
z-score thresholds and adaptive baseline comparison.

Core concepts
-------------
- **Baseline** – a recent window of observed metric values that
  represents "normal" behaviour for a device.
- **Z-score** – (observation - baseline_mean) / baseline_std.
  |z| > threshold → anomaly.
- **Adaptive** – a sliding-window baseline is maintained so normal
  changes in device behaviour don't generate endless false positives.

API
---
    AnomalyDetector(window_size=100, z_threshold=3.0)
        .record(value)              — add observation & auto-detect
        .is_anomaly(value)          — check without recording
        .anomaly_score(value)       — raw z-score
        .reset()                    — clear baseline
"""

import math
import statistics
from collections import deque
from typing import NamedTuple


# ── data structures ────────────────────────────────────────────────

class AnomalyResult(NamedTuple):
    is_anomaly: bool
    z_score: float
    mean: float
    std: float
    threshold: float


# ── detector ───────────────────────────────────────────────────────

class AnomalyDetector:
    """Sliding-window z-score anomaly detector.

    Parameters
    ----------
    window_size : int
        Number of recent observations to keep in the baseline window.
    z_threshold : float
        |z| above this value marks an observation as anomalous.
    min_samples : int
        Minimum observations required before detection is meaningful.
        Defaults to max(10, window_size // 10).
    """

    def __init__(
        self,
        window_size: int = 100,
        z_threshold: float = 3.0,
        min_samples: int | None = None,
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.min_samples = min_samples or max(10, window_size // 10)
        self._window: deque[float] = deque(maxlen=window_size)

    # ── public API ─────────────────────────────────────────────────

    def record(self, value: float) -> AnomalyResult | None:
        """Record a new observation, update baseline, and detect.

        Returns None if there aren't enough samples yet.
        """
        result = self.is_anomaly(value)
        self._window.append(value)
        return result

    def is_anomaly(self, value: float) -> AnomalyResult | None:
        """Check *without* adding to the baseline.

        Returns None if too few samples exist.
        """
        if len(self._window) < self.min_samples:
            return None

        mean, std = self._baseline_stats()
        z = self.anomaly_score(value, mean, std)
        return AnomalyResult(
            is_anomaly=abs(z) > self.z_threshold,
            z_score=z,
            mean=mean,
            std=std,
            threshold=self.z_threshold,
        )

    def anomaly_score(
        self,
        value: float,
        mean: float | None = None,
        std: float | None = None,
    ) -> float:
        """Compute z-score without checking anomaly status.

        Uses stored baseline if mean/std not provided.
        """
        if mean is None or std is None:
            if len(self._window) < self.min_samples:
                return 0.0
            mean, std = self._baseline_stats()
        return (value - mean) / std if std > 0 else 0.0

    def reset(self) -> None:
        """Clear all baseline data."""
        self._window.clear()

    # ── internals ──────────────────────────────────────────────────

    def _baseline_stats(self) -> tuple[float, float]:
        """Return (mean, std) of the current window."""
        if len(self._window) < 2:
            return (self._window[0] if self._window else 0.0, 0.0)
        m = statistics.mean(self._window)
        s = statistics.stdev(self._window)
        return m, s

    @property
    def size(self) -> int:
        return len(self._window)

    def __repr__(self) -> str:
        return (f"AnomalyDetector(window={self.size}/{self.window_size}, "
                f"z_threshold={self.z_threshold})")


# ── convenience: batch baseline from existing data ─────────────────

def baseline_from_samples(
    samples: list[float],
    z_threshold: float = 3.0,
) -> AnomalyDetector:
    """Create a pre-seeded detector from a list of past observations."""
    det = AnomalyDetector(window_size=len(samples), z_threshold=z_threshold)
    for v in samples:
        det._window.append(v)
    return det


# ── Example usage ──────────────────────────────────────────────────

if __name__ == "__main__":
    import random

    print("═" * 50)
    print("Vigil Anomaly Detection — Example")
    print("═" * 50)

    # Seed with "normal" network traffic (bytes/s)
    normal_traffic = [random.gauss(500, 50) for _ in range(50)]
    detector = baseline_from_samples(normal_traffic)

    print(f"\nBaseline seeded with {len(normal_traffic)} samples")
    print(f"  Mean: {statistics.mean(normal_traffic):.1f}")
    print(f"  Std:  {statistics.stdev(normal_traffic):.1f}")
    print(f"  Z-threshold: {detector.z_threshold}")

    # Test a normal value
    print("\n── Normal value (520) ──")
    r = detector.record(520)
    print(f"  Anomaly? {r.is_anomaly}  |  z={r.z_score:.2f}")

    # Test a suspicious value
    print("\n── Suspicious value (900) ──")
    r = detector.record(900)
    print(f"  Anomaly? {r.is_anomaly}  |  z={r.z_score:.2f}   "
          f"mean={r.mean:.1f}  std={r.std:.1f}")

    # Test an extreme outlier
    print("\n── Extreme value (3000) ──")
    r = detector.record(3000)
    print(f"  Anomaly? {r.is_anomaly}  |  z={r.z_score:.2f}   "
          f"mean={r.mean:.1f}  std={r.std:.1f}")

    # Record a burst of high values — baseline adapts
    print("\n── Adaptive baseline (5 high values) ──")
    for v in [1200, 1100, 1300, 1150, 1250]:
        r = detector.record(v)
    r = detector.record(1300)  # same range, should be normal now
    print(f"  After adaptation, 1300: anomaly? {r.is_anomaly}  "
          f"z={r.z_score:.2f}  mean={r.mean:.1f}")

    print("\nDone.")
