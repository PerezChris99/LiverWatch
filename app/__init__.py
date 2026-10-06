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
import secrets
import uuid

import pytz
from flask import Flask, g, jsonify, request
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy

# ── Extension singletons ─────────────────────────────────────────────────
db           = SQLAlchemy()
mail         = Mail()
csrf         = CSRFProtect()
cache        = Cache()
migrate      = Migrate()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour'],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'),
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

    # Only trust forwarded client metadata when the deployment explicitly
    # declares the number of trusted reverse-proxy hops.
    proxy_hops = max(int(app.config.get('TRUSTED_PROXY_HOPS', 0)), 0)
    if proxy_hops:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_hops, x_proto=proxy_hops, x_host=proxy_hops)

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple')})
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view         = 'auth.login'
    login_manager.login_message      = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    limiter.init_app(app)

    # ── Request/response hardening ───────────────────────────────────────
    @app.before_request
    def _request_context():
        g.request_id = request.headers.get('X-Request-ID', '')[:100] or str(uuid.uuid4())

    @app.after_request
    def _security_headers(response):
        response.headers['X-Request-ID'] = g.get('request_id', '')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "connect-src 'self'; object-src 'none'"
        )
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(500)
    def _internal_error(_error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'internal_error', 'message': 'An unexpected server error occurred.', 'request_id': g.get('request_id')}), 500
        return 'An unexpected server error occurred.', 500

    @app.teardown_request
    def _rollback_failed_request(exception):
        if exception is not None:
            db.session.rollback()

    @app.errorhandler(CSRFError)
    def _csrf_error(_error):
        return jsonify({'error': 'csrf_validation_failed', 'message': 'CSRF validation failed.'}), 400

    @app.errorhandler(413)
    def _payload_too_large(_error):
        return jsonify({'error': 'payload_too_large', 'message': 'Request body exceeds the allowed size.'}), 413

    @app.errorhandler(429)
    def _rate_limited(_error):
        return jsonify({'error': 'rate_limited', 'message': 'Too many requests. Please retry later.'}), 429

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
    # REST APIs authenticate with bearer tokens rather than browser cookies.
    # Keep CSRF protection enabled for the cookie-backed web/agent surfaces.
    csrf.exempt(legacy_api_bp)
    csrf.exempt(api_bp)

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
    # Do not create production schema implicitly. Migrations are the source of truth.
    with app.app_context():
        if app.config.get('TESTING') or app.config.get('DEBUG'):
            db.create_all()

    return app

