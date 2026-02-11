"""
LiverWatch Blueprints
=====================

Blueprint initialization module.
"""

from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.admin import admin_bp
from app.blueprints.forum import forum_bp
from app.blueprints.health import health_bp
from app.blueprints.api import api_bp
from app.blueprints.analytics import analytics_bp
from app.blueprints.notifications import notifications_bp

__all__ = [
    'main_bp',
    'auth_bp', 
    'admin_bp',
    'forum_bp',
    'health_bp',
    'api_bp',
    'analytics_bp',
    'notifications_bp'
]
