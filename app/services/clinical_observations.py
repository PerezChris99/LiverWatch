"""Clinical observation service.

The service is the safe write/read boundary for longitudinal measurements.
It validates provenance and quality without interpreting measurements as diagnoses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app import db
from app.models import ClinicalObservation
from app.services.measurement import (
    MeasurementProvenance,
    normalise_timestamp,
    validate_numeric_measurement,
)


def create_observation(
    *,
    code: str,
    value: Any,
    unit: Optional[str],
    observed_at: datetime,
    source_type: str,
    source_id: Optional[str] = None,
    validation_state: str = "pending",
    quality_score: Optional[float] = None,
    user_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    reference_metadata: Optional[dict] = None,
) -> ClinicalObservation:
    """Validate and construct an observation; caller controls transaction."""
    provenance = MeasurementProvenance(
        source_type=source_type,
        source_id=source_id,
        measured_at=observed_at,
        validation_state=validation_state,
        quality_score=quality_score,
    )
    validate_numeric_measurement(value)
    if not code or not code.strip():
        raise ValueError("Measurement code is required.")
    if user_id is None and patient_id is None:
        raise ValueError("An observation must belong to a user or patient.")

    observation = ClinicalObservation(
        code=code.strip(),
        value=float(value),
        unit=unit.strip() if isinstance(unit, str) else unit,
        observed_at=normalise_timestamp(provenance.measured_at),
        source_type=provenance.source_type,
        source_id=provenance.source_id,
        validation_state=provenance.validation_state,
        quality_score=provenance.quality_score,
        user_id=user_id,
        patient_id=patient_id,
    )
    if reference_metadata:
        observation.set_reference_metadata(reference_metadata)
    return observation


def save_observation(**kwargs) -> ClinicalObservation:
    observation = create_observation(**kwargs)
    db.session.add(observation)
    db.session.commit()
    return observation
