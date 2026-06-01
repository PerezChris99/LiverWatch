"""
LiverWatch Application Factory — v3.0
=======================================

Uganda Liver Risk Intelligence Platform
Phase 1: Foundation Reset

Extensions initialised here:
  db, mail, cache, migrate, login_manager, limiter

Blueprints registered:
  main        → /
  auth        → /auth
  admin       → /admin
  forum       → /forum      (moderated)
  health      → /health
  analytics   → /analytics
  notifications → /notifications
  agents      → /api/agents (structured risk support ONLY)
  api         → /api        (legacy v0 kept for transition)
  api v1      → /api/v1     (versioned REST API — Phase 1+)
"""

import os

import pytz
from flask import Flask
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# ── Extension singletons ─────────────────────────────────────────────────
db           = SQLAlchemy()
mail         = Mail()
cache        = Cache()
migrate      = Migrate()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour'],
    storage_uri='memory://',
    headers_enabled=True,
    strategy='fixed-window',
)


def create_app(config_class=None):
    """
    Application factory.

    Args:
        config_class: A config class (default: DevelopmentConfig).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # ── Configuration ─────────────────────────────────────────────────────
    if config_class is None:
        from app.config import DevelopmentConfig
        config_class = DevelopmentConfig
    app.config.from_object(config_class)

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple')})
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view         = 'auth.login'
    login_manager.login_message      = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    limiter.init_app(app)

    # ── User loader ───────────────────────────────────────────────────────
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Blueprint registration ────────────────────────────────────────────
    from app.blueprints.main          import main_bp
    from app.blueprints.auth          import auth_bp
    from app.blueprints.admin         import admin_bp
    from app.blueprints.forum         import forum_bp
    from app.blueprints.health        import health_bp
    from app.blueprints.analytics     import analytics_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.education     import education_bp
    from app.blueprints.referral      import referral_bp
    from app.blueprints.agents        import agents_bp
    # Legacy API v0 (kept for transition)
    from app.blueprints.api_legacy    import legacy_api_bp
    # New versioned API
    from app.blueprints.api           import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,          url_prefix='/auth')
    app.register_blueprint(admin_bp,         url_prefix='/admin')
    app.register_blueprint(forum_bp,         url_prefix='/forum')
    app.register_blueprint(health_bp,        url_prefix='/health')
    app.register_blueprint(analytics_bp,     url_prefix='/analytics')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(education_bp,     url_prefix='/education')
    app.register_blueprint(referral_bp,      url_prefix='/referrals')
    app.register_blueprint(agents_bp,        url_prefix='/api/agents')
    app.register_blueprint(legacy_api_bp,    url_prefix='/api/v0')
    app.register_blueprint(api_bp)   # mounts /api with /api/v1 inside

    # ── Template context ──────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {
            'app_name':        app.config.get('APP_NAME', 'LiverWatch'),
            'app_version':     app.config.get('APP_VERSION', '3.0'),
            'current_year':    datetime.now().year,
            'medical_disclaimer': app.config.get('MEDICAL_DISCLAIMER', ''),
        }

    # ── Jinja2 filters ────────────────────────────────────────────────────
    @app.template_filter('formatdate')
    def formatdate_filter(value, fmt='%B %d, %Y'):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                from datetime import datetime
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return value
        return value.strftime(fmt)

    # ── Database setup ────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app

