"""Add persistent monitoring alerts.
Revision ID: 20261006_140000
"""
from alembic import op
import sqlalchemy as sa
revision="20261006_140000"; down_revision="20261006_130000"; branch_labels=None; depends_on=None
def upgrade():
 op.create_table("monitoring_alerts",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id"),nullable=True),sa.Column("patient_id",sa.Integer(),sa.ForeignKey("patients.id"),nullable=True),sa.Column("alert_type",sa.String(50),nullable=False),sa.Column("severity",sa.String(20),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("message",sa.Text(),nullable=False),sa.Column("evidence",sa.Text(),nullable=True),sa.Column("source_observation_id",sa.Integer(),sa.ForeignKey("clinical_observations.id"),nullable=True),sa.Column("status",sa.String(20),nullable=False,server_default="open"),sa.Column("dedupe_key",sa.String(128),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("acknowledged_at",sa.DateTime(),nullable=True),sa.Column("resolved_at",sa.DateTime(),nullable=True))
 op.create_index("ix_alert_user_created","monitoring_alerts",["user_id","created_at"]); op.create_index("ix_alert_patient_created","monitoring_alerts",["patient_id","created_at"]); op.create_index("ix_alert_type","monitoring_alerts",["alert_type"]); op.create_index("ix_alert_status","monitoring_alerts",["status"]); op.create_index("ix_alert_dedupe","monitoring_alerts",["dedupe_key"])
def downgrade():
 for n in ["ix_alert_dedupe","ix_alert_status","ix_alert_type","ix_alert_patient_created","ix_alert_user_created"]: op.drop_index(n,table_name="monitoring_alerts")
 op.drop_table("monitoring_alerts")
