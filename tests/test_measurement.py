from datetime import datetime, timezone
import pytest

from app.services.measurement import (
    LIVER_BIOMARKERS, MeasurementProvenance,
    normalise_timestamp, validate_numeric_measurement,
)


def test_provenance_accepts_supported_source_and_quality():
    p = MeasurementProvenance(
        source_type="laboratory",
        source_id="LAB-001",
        measured_at=datetime(2026, 10, 6, 10, tzinfo=timezone.utc),
        quality_score=0.95,
        validation_state="validated",
    )
    assert p.is_currently_usable is True


@pytest.mark.parametrize("source", ["unknown", "", "sensor_vendor"])
def test_provenance_rejects_unknown_sources(source):
    with pytest.raises(ValueError):
        MeasurementProvenance(source_type=source)


def test_provenance_rejects_bad_quality():
    with pytest.raises(ValueError):
        MeasurementProvenance(source_type="device", quality_score=1.1)


def test_provenance_requires_aware_timestamp():
    with pytest.raises(ValueError):
        MeasurementProvenance(
            source_type="clinician",
            measured_at=datetime(2026, 10, 6, 10),
        )


def test_normalise_timestamp_converts_to_utc():
    value = datetime(2026, 10, 6, 13, tzinfo=timezone.utc)
    assert normalise_timestamp(value) == value


@pytest.mark.parametrize("value", ["bad", None])
def test_numeric_measurement_rejects_non_numeric(value):
    with pytest.raises(ValueError):
        validate_numeric_measurement(value)


def test_numeric_measurement_preserves_valid_value():
    assert validate_numeric_measurement("42.5") == 42.5


def test_canonical_liver_biomarker_units_exist():
    assert LIVER_BIOMARKERS["ALT"] == "U/L"
    assert LIVER_BIOMARKERS["AST"] == "U/L"
    assert LIVER_BIOMARKERS["bilirubin_total"] == "mg/dL"
