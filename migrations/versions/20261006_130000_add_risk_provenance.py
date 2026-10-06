"""Add risk assessment engine provenance.
Revision ID: 20261006_130000
"""
from alembic import op
import sqlalchemy as sa
revision="20261006_130000"
down_revision="20261006_120100"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("risk_assessments", sa.Column("engine_version", sa.String(30), nullable=False, server_default="3.1.0"))
    op.add_column("risk_assessments", sa.Column("input_fingerprint", sa.String(64), nullable=True))
    op.create_index("ix_risk_input_fingerprint", "risk_assessments", ["input_fingerprint"])
def downgrade():
    op.drop_index("ix_risk_input_fingerprint", table_name="risk_assessments")
    op.drop_column("risk_assessments","input_fingerprint")
    op.drop_column("risk_assessments","engine_version")
