from datetime import datetime, timezone

import pytest

from app.services.clinical_observations import create_observation


def test_create_observation_requires_owner():
    with pytest.raises(ValueError, match="belong"):
        create_observation(
            code="ALT", value=40, unit="U/L",
            observed_at=datetime.now(timezone.utc),
            source_type="laboratory",
        )


def test_create_observation_rejects_bad_quality():
    with pytest.raises(ValueError):
        create_observation(
            code="ALT", value=40, unit="U/L",
            observed_at=datetime.now(timezone.utc),
            source_type="laboratory", patient_id=1, quality_score=2,
        )


def test_create_observation_normalises_timestamp():
    observation = create_observation(
        code="ALT", value=40, unit="U/L",
        observed_at=datetime(2026, 10, 6, 12, tzinfo=timezone.utc),
        source_type="laboratory", patient_id=1, quality_score=0.95,
    )
    assert observation.observed_at.tzinfo is timezone.utc
    assert observation.is_usable is False  # pending until explicitly validated
