"""Add operational query indexes for high-volume tables.
Revision ID: 20261006_150000
"""
from alembic import op
import sqlalchemy as sa
revision="20261006_150000"
down_revision="20261006_140000"
branch_labels=None
depends_on=None

INDEXES = [
 ("ix_risk_user_created","risk_assessments",["user_id","created_at"]),
 ("ix_risk_level_created","risk_assessments",["risk_level","created_at"]),
 ("ix_reading_device_timestamp","biomarker_readings",["device_id","timestamp"]),
 ("ix_reading_user_timestamp","biomarker_readings",["user_id","timestamp"]),
 ("ix_notification_user_read_created","notifications",["user_id","is_read","created_at"]),
 ("ix_longitudinal_user_date","longitudinal_records",["user_id","record_date"]),
 ("ix_audit_user_created","audit_logs",["user_id","created_at"]),
 ("ix_observation_patient_time","clinical_observations",["patient_id","observed_at"]),
 ("ix_observation_user_time","clinical_observations",["user_id","observed_at"]),
]

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    for name,table,columns in INDEXES:
        if table in inspector.get_table_names():
            existing={x["name"] for x in inspector.get_indexes(table)}
            if name not in existing:
                op.create_index(name,table,columns)

def downgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    for name,table,_ in reversed(INDEXES):
        if table in inspector.get_table_names():
            existing={x["name"] for x in inspector.get_indexes(table)}
            if name in existing:
                op.drop_index(name,table_name=table)
