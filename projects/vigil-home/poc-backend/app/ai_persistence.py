"""
Vigil Home — AI State Persistence
==================================
Load/store TrustModel and AnomalyDetector state from SQLite so that
AI models survive application restarts.

This module owns the **single shared runtime cache** for AI models.
Both main.py and detection.py import from here instead of maintaining
their own separate in-memory dicts.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import TrustScore as TrustScoreRow, AnomalyBaseline, Device
from app.ai import TrustModel, AnomalyDetector

logger = logging.getLogger("vigil.ai_persistence")


# ── Shared runtime cache (single source of truth in-process) ───────
# These dicts are populated lazily on first access and kept in sync
# with the database after every write. Both main.py and detection.py
# use the getter/setter functions below rather than their own dicts.

_anomaly_detectors: dict[int, AnomalyDetector] = {}
_trust_models: dict[int, TrustModel] = {}


# ── Trust model persistence ─────────────────────────────────────────

def load_trust_model(db: Session, device_id: int) -> TrustModel | None:
    """Load a TrustModel from the database, or return None."""
    row = db.query(TrustScoreRow).filter(
        TrustScoreRow.device_id == device_id
    ).first()
    if not row:
        return None
    return TrustModel.from_dict({
        "half_life": row.half_life,
        "alpha": row.alpha,
        "omega": row.omega,
        "last_update": row.last_update,
    })


def _upsert_trust_row(db: Session, device_id: int, model: TrustModel) -> None:
    """Insert or update the TrustScore row for a device."""
    row = db.query(TrustScoreRow).filter(
        TrustScoreRow.device_id == device_id
    ).first()
    if row:
        row.alpha = model.alpha
        row.omega = model.omega
        row.half_life = model.half_life
        row.last_update = model._last_update
    else:
        row = TrustScoreRow(
            device_id=device_id,
            alpha=model.alpha,
            omega=model.omega,
            half_life=model.half_life,
            last_update=model._last_update,
        )
        db.add(row)
    db.commit()


# ── Anomaly detector persistence ────────────────────────────────────

def load_anomaly_detector(db: Session, device_id: int) -> AnomalyDetector | None:
    """Load an AnomalyDetector from the database, or return None."""
    row = db.query(AnomalyBaseline).filter(
        AnomalyBaseline.device_id == device_id
    ).first()
    if not row:
        return None
    # window is stored as a JSON list; convert from any type-safe
    window = row.window if isinstance(row.window, list) else []
    return AnomalyDetector.from_dict({
        "window_size": row.window_size,
        "z_threshold": row.z_threshold,
        "min_samples": row.min_samples,
        "window": window,
    })


def _upsert_anomaly_row(db: Session, device_id: int, detector: AnomalyDetector) -> None:
    """Insert or update the AnomalyBaseline row for a device."""
    row = db.query(AnomalyBaseline).filter(
        AnomalyBaseline.device_id == device_id
    ).first()
    data = detector.to_dict()
    if row:
        row.window = data["window"]
        row.window_size = data["window_size"]
        row.z_threshold = data["z_threshold"]
        row.min_samples = data["min_samples"]
    else:
        row = AnomalyBaseline(
            device_id=device_id,
            window=data["window"],
            window_size=data["window_size"],
            z_threshold=data["z_threshold"],
            min_samples=data["min_samples"],
        )
        db.add(row)
    db.commit()


# ── Shared cache getters/setters (used by both main.py & detection.py) ──

def get_anomaly_detector(device_id: int, db: Session) -> AnomalyDetector:
    """Get the AnomalyDetector for a device, loading from DB if not cached.

    Uses the shared in-process cache so both the API server and the
    Eve consumer share one copy of each detector.
    """
    if device_id not in _anomaly_detectors:
        detector = load_anomaly_detector(db, device_id)
        if detector is None:
            detector = AnomalyDetector(window_size=100, z_threshold=3.0)
        _anomaly_detectors[device_id] = detector
    return _anomaly_detectors[device_id]


def get_trust_model(device_id: int, db: Session) -> TrustModel:
    """Get the TrustModel for a device, loading from DB if not cached.

    Uses the shared in-process cache so both the API server and the
    Eve consumer share one copy of each model.
    """
    if device_id not in _trust_models:
        model = load_trust_model(db, device_id)
        if model is None:
            model = TrustModel(half_life=86400)
        _trust_models[device_id] = model
    return _trust_models[device_id]


def store_trust_state(db: Session, device_id: int, model: TrustModel) -> None:
    """Persist trust model state after an update and refresh the cache."""
    _trust_models[device_id] = model
    _upsert_trust_row(db, device_id, model)


def store_anomaly_state(db: Session, device_id: int, detector: AnomalyDetector) -> None:
    """Persist anomaly detector state after a record operation and refresh the cache."""
    _anomaly_detectors[device_id] = detector
    _upsert_anomaly_row(db, device_id, detector)


def reload_all_ai_state(db: Session) -> None:
    """Warm the shared caches for all known devices on startup.

    Iterates all devices and loads their trust models and anomaly
    detectors from the database. If a device has no stored state,
    a fresh default is created and persisted.
    """
    devices = db.query(Device).all()
    loaded_trust = 0
    loaded_anomaly = 0
    created_trust = 0
    created_anomaly = 0

    for device in devices:
        did = device.id

        # Load trust model
        model = load_trust_model(db, did)
        if model is None:
            model = TrustModel(half_life=86400)
            _upsert_trust_row(db, did, model)
            created_trust += 1
        _trust_models[did] = model
        loaded_trust += 1

        # Load anomaly detector
        detector = load_anomaly_detector(db, did)
        if detector is None:
            detector = AnomalyDetector(window_size=100, z_threshold=3.0)
            _upsert_anomaly_row(db, did, detector)
            created_anomaly += 1
        _anomaly_detectors[did] = detector
        loaded_anomaly += 1

    logger.info(
        "AI state reloaded: %d trust models (%d new), %d anomaly detectors (%d new)",
        loaded_trust, created_trust,
        loaded_anomaly, created_anomaly,
    )


def evict_ai_state(device_id: int) -> None:
    """Remove a device's AI state from the shared cache (e.g. on device deletion)."""
    _trust_models.pop(device_id, None)
    _anomaly_detectors.pop(device_id, None)


def clear_ai_cache() -> None:
    """Clear the entire shared in-memory cache (for testing)."""
    _anomaly_detectors.clear()
    _trust_models.clear()
