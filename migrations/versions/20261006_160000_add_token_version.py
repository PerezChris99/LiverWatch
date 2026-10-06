"""Add JWT token versioning.
Revision ID: 20261006_160000
"""
from alembic import op
import sqlalchemy as sa
revision="20261006_160000"; down_revision="20261006_150000"; branch_labels=None; depends_on=None
def upgrade(): op.add_column("users",sa.Column("token_version",sa.Integer(),nullable=False,server_default="0"))
def downgrade(): op.drop_column("users","token_version")
