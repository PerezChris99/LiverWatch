"""add clinical observations

Revision ID: 20261006_120000
Revises: 20250630_120000
"""
from alembic import op
import sqlalchemy as sa

revision = "20261006_120000"
down_revision = "20250630_120000"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clinical_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=True),
        sa.Column("validation_state", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("reference_metadata", sa.Text(), nullable=True),
        sa.Column("correction_of_id", sa.Integer(), sa.ForeignKey("clinical_observations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_obs_patient_time", "clinical_observations", ["patient_id", "observed_at"])
    op.create_index("ix_obs_user_time", "clinical_observations", ["user_id", "observed_at"])
    op.create_index("ix_clinical_observations_code", "clinical_observations", ["code"])
    op.create_index("ix_clinical_observations_source_type", "clinical_observations", ["source_type"])


def downgrade():
    op.drop_index("ix_clinical_observations_source_type", table_name="clinical_observations")
    op.drop_index("ix_clinical_observations_code", table_name="clinical_observations")
    op.drop_index("ix_obs_user_time", table_name="clinical_observations")
    op.drop_index("ix_obs_patient_time", table_name="clinical_observations")
    op.drop_table("clinical_observations")
