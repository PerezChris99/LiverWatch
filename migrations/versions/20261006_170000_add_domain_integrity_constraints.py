"""Add core domain integrity constraints.

Revision ID: 20261006_170000
Revises: 20261006_160000
"""
from alembic import op
import sqlalchemy as sa

revision = "20261006_170000"
down_revision = "20261006_160000"
branch_labels = None
depends_on = None


CONSTRAINTS = [
    ("users", "chk_user_token_version", "token_version >= 0"),
    ("users", "chk_user_failed_login_count", "failed_login_count >= 0"),
    ("risk_assessments", "chk_risk_overall_score", "overall_score >= 0 AND overall_score <= 1"),
    ("risk_assessments", "chk_risk_confidence", "confidence_level >= 0 AND confidence_level <= 1"),
    ("monitoring_alerts", "chk_alert_severity", "severity IN ('minimal','low','moderate','high','urgent','critical')"),
    ("monitoring_alerts", "chk_alert_status", "status IN ('open','acknowledged','resolved')"),
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, name, expression in CONSTRAINTS:
        if table not in inspector.get_table_names():
            continue
        existing = {c.get("name") for c in inspector.get_check_constraints(table)}
        if name not in existing:
            with op.batch_alter_table(table) as batch_op:
                batch_op.create_check_constraint(name, expression)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, name, _ in reversed(CONSTRAINTS):
        if table not in inspector.get_table_names():
            continue
        existing = {c.get("name") for c in inspector.get_check_constraints(table)}
        if name in existing:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(name, type_="check")
