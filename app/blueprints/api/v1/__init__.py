"""
API v1 Package
==============

All endpoints mounted under /api/v1/.

Sub-blueprints:
  auth_api_v1    → /api/v1/auth/*
  risk_api_v1    → /api/v1/risk/*
  wearable_api_v1 → /api/v1/wearable/*
"""

from flask import Blueprint

v1_bp = Blueprint('v1', __name__, url_prefix='/v1')

from app.blueprints.api.v1.auth     import auth_api_v1       # noqa: E402
from app.blueprints.api.v1.risk     import risk_api_v1        # noqa: E402
from app.blueprints.api.v1.wearable import wearable_api_v1    # noqa: E402

v1_bp.register_blueprint(auth_api_v1)
v1_bp.register_blueprint(risk_api_v1)
v1_bp.register_blueprint(wearable_api_v1)
