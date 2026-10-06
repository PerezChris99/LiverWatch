"""
Clinical measurement domain helpers.

This module defines the canonical provenance and validation vocabulary used by
future laboratory, CHW, clinician and device integrations. It deliberately
does not assign diagnostic meaning to measurements.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


VALID_SOURCES = {"patient", "chw", "clinician", "laboratory", "device", "research"}
VALID_STATES = {"pending", "validated", "rejected", "corrected"}
LIVER_BIOMARKERS = {
    "ALT": "U/L", "AST": "U/L", "ALP": "U/L", "GGT": "U/L",
    "bilirubin_total": "mg/dL", "albumin": "g/dL", "INR": "ratio",
}


@dataclass(frozen=True)
class MeasurementProvenance:
    source_type: str
    source_id: Optional[str] = None
    measured_at: Optional[datetime] = None
    quality_score: Optional[float] = None
    validation_state: str = "pending"

    def __post_init__(self):
        if self.source_type not in VALID_SOURCES:
            raise ValueError(f"Unsupported source_type: {self.source_type}")
        if self.validation_state not in VALID_STATES:
            raise ValueError(f"Unsupported validation_state: {self.validation_state}")
        if self.quality_score is not None and not 0 <= self.quality_score <= 1:
            raise ValueError("quality_score must be between 0 and 1")
        if self.measured_at is not None and self.measured_at.tzinfo is None:
            raise ValueError("measured_at must be timezone-aware")

    @property
    def is_currently_usable(self) -> bool:
        return self.validation_state == "validated" and (
            self.quality_score is None or self.quality_score >= 0.7
        )


def normalise_timestamp(value: Optional[datetime]) -> Optional[datetime]:
    """Return an aware UTC timestamp without changing an already-aware instant."""
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("Measurement timestamps must include timezone information")
    return value.astimezone(timezone.utc)


def validate_numeric_measurement(value, *, minimum=None, maximum=None) -> float:
    """Validate numeric input without assigning clinical interpretation."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("measurement value must be numeric") from None
    if minimum is not None and number < minimum:
        raise ValueError("measurement value is below the accepted data range")
    if maximum is not None and number > maximum:
        raise ValueError("measurement value is above the accepted data range")
    return number
