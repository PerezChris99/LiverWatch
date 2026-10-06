"""Harden clinical observation integrity.

Revision ID: 20261006_120100
"""
from alembic import op

revision = "20261006_120100"
down_revision = "20261006_120000"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "chk_clinical_observation_quality",
        "clinical_observations",
        "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
    )
    op.create_check_constraint(
        "chk_clinical_observation_source",
        "clinical_observations",
        "source_type IN ('patient','chw','clinician','laboratory','device','research')",
    )
    op.create_check_constraint(
        "chk_clinical_observation_state",
        "clinical_observations",
        "validation_state IN ('pending','validated','rejected','corrected')",
    )


def downgrade():
    op.drop_constraint("chk_clinical_observation_state", "clinical_observations", type_="check")
    op.drop_constraint("chk_clinical_observation_source", "clinical_observations", type_="check")
    op.drop_constraint("chk_clinical_observation_quality", "clinical_observations", type_="check")
