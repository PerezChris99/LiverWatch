import pytest
from datetime import datetime, timezone
from app import db
from app.models import ClinicalObservation, MeasurementValidationState, MeasurementSource


def test_clinical_observation_persists_provenance(app):
    with app.app_context():
        obs = ClinicalObservation(
            code="ALT",
            value=42.0,
            unit="U/L",
            observed_at=datetime.now(timezone.utc),
            source_type=MeasurementSource.LABORATORY.value,
            source_id="LAB-UG-001",
            validation_state=MeasurementValidationState.VALIDATED.value,
            quality_score=0.98,
        )
        db.session.add(obs)
        db.session.commit()

        saved = db.session.get(ClinicalObservation, obs.id)
        assert saved.code == "ALT"
        assert saved.source_type == "laboratory"
        assert saved.validation_state == "validated"
        assert saved.is_usable is True


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_clinical_observation_quality_constraint(app, score):
    with app.app_context():
        obs = ClinicalObservation(
            code="AST",
            value=30,
            unit="U/L",
            observed_at=datetime.now(timezone.utc),
            source_type="laboratory",
            quality_score=score,
        )
        db.session.add(obs)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
