"""
Vigil Trust Scoring Module
==========================
Bayesian trust model for IoT device behavior on a 0.0–1.0 scale.

Framework:
    Trust is modelled as a Beta distribution: Beta(α, ω) where
      α = positive evidence count, ω = negative evidence count.
    The trust score = α / (α + ω), initialised to 0.5 by starting
    with α = ω = 1 (a uniform prior, i.e. Beta(1, 1)).

Decay:
    Trust decays toward 0.5 over time to reflect that old observations
    become less informative.  The half-life controls the decay rate:
    after `half_life` seconds without an update, the effective weight
    of accumulated evidence drops by half.

API
---
    TrustModel(half_life=86400)   — half-life in seconds (default 1 day)
        .score                    — current trust (0.0–1.0)
        .update(positive=True)    — incorporate new evidence
        .decay(timestamp)         — apply time-based decay
        .reset()                  — back to neutral
"""

import math
import time


def _adjust_evidence(value, half_life, elapsed):
    """Scale evidence weight toward neutral using exponential decay."""
    if half_life <= 0 or elapsed <= 0:
        return value
    factor = 0.5 ** (elapsed / half_life)
    neutral = 1  # neutral prior weight per bucket (α=1, ω=1)
    return neutral + (value - neutral) * factor


class TrustModel:
    """Bayesian trust model for a single IoT device.

    Parameters
    ----------
    half_life : float
        Time in seconds after which accumulated evidence is "half as
        informative" (decays halfway toward the neutral prior).
    """

    def __init__(self, half_life: float = 86400):
        self.half_life = half_life
        self.alpha = 1.0   # positive evidence count (incl. prior)
        self.omega = 1.0   # negative evidence count (incl. prior)
        self._last_update = time.time()

    # ── computed properties ────────────────────────────────────────

    @property
    def score(self) -> float:
        """Current trust score in [0.0, 1.0]."""
        return self.alpha / (self.alpha + self.omega)

    @property
    def certainty(self) -> float:
        """How much evidence underpins the score [0, 1].  At low
        evidence (α+ω≈2) certainty is ~0; it asymptotically approaches 1."""
        total = self.alpha + self.omega
        return 1.0 - (2.0 / total) if total > 2 else 0.0

    # ── core operations ────────────────────────────────────────────

    def update(self, positive: bool = True, weight: float = 1.0) -> float:
        """Incorporate a new behavioural observation.

        Parameters
        ----------
        positive : bool
            True if the observation supports trust, False otherwise.
        weight : float
            Relative importance of this observation (1.0 = normal).

        Returns
        -------
        float  — the updated trust score.
        """
        if positive:
            self.alpha += weight
        else:
            self.omega += weight
        self._last_update = time.time()
        return self.score

    def decay(self, timestamp: float | None = None) -> float:
        """Apply time-based decay toward neutral.

        Should be called periodically (e.g. once per minute) or on
        every access if staleness matters.

        Parameters
        ----------
        timestamp : float
            Current epoch time.  Defaults to time.time().

        Returns
        -------
        float  — the (potentially unchanged) trust score.
        """
        now = timestamp if timestamp is not None else time.time()
        elapsed = now - self._last_update
        if elapsed <= 0:
            return self.score

        self.alpha = _adjust_evidence(self.alpha, self.half_life, elapsed)
        self.omega = _adjust_evidence(self.omega, self.half_life, elapsed)
        self._last_update = now
        return self.score

    def reset(self) -> None:
        """Reset trust to neutral Beta(1, 1)."""
        self.alpha = 1.0
        self.omega = 1.0
        self._last_update = time.time()

    # ── convenience helpers ────────────────────────────────────────

    def score_with_decay(self, timestamp: float | None = None) -> float:
        """Convenience: decay then return score."""
        self.decay(timestamp)
        return self.score

    def __repr__(self) -> str:
        return (f"TrustModel(score={self.score:.3f}, "
                f"certainty={self.certainty:.3f}, "
                f"α={self.alpha:.1f}, ω={self.omega:.1f})")


# ── Example usage (runs when file is executed directly) ────────────

if __name__ == "__main__":
    print("═" * 50)
    print("Vigil Trust Model — Example")
    print("═" * 50)

    tm = TrustModel(half_life=3600)   # 1-hour half-life for demo
    print(f"\nInitial state: {tm}")
    print(f"  Trust score: {tm.score:.3f}")
    print(f"  Certainty:   {tm.certainty:.3f}")

    # Simulate a series of good behaviours
    print("\n── Positive observations ──")
    for i in range(5):
        tm.update(positive=True)
        print(f"  After good event #{i + 1}: score={tm.score:.3f}, "
              f"certainty={tm.certainty:.3f}")

    # One bad event
    print("\n── Negative observation ──")
    tm.update(positive=False)
    print(f"  After bad event: score={tm.score:.3f}, "
          f"certainty={tm.certainty:.3f}")

    # Simulate time passing (no new observations)
    print("\n── Time decay (2 hours later) ──")
    future = time.time() + 7200
    tm.decay(future)
    print(f"  After decay:     score={tm.score:.3f}, "
          f"certainty={tm.certainty:.3f}")

    # Reset
    print("\n── Reset ──")
    tm.reset()
    print(f"  After reset:     score={tm.score:.3f}, "
          f"certainty={tm.certainty:.3f}")

    print("\nDone.")
