"""
LiverWatch API Package
======================

Versioned REST API.
Current version: v1 (mounted at /api/v1/)

Usage in app/__init__.py:
    from app.blueprints.api import api_bp
    app.register_blueprint(api_bp)
"""

from flask import Blueprint

# Outer blueprint used purely to namespace /api/*
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import and register sub-blueprints
from app.blueprints.api.v1 import v1_bp          # noqa: E402
api_bp.register_blueprint(v1_bp)
