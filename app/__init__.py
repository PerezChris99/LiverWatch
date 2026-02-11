"""
LiverWatch Application Factory
==============================

Flask application factory with all extensions, blueprints, and configuration.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_caching import Cache
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import os

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
cache = Cache()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True,
    strategy="fixed-window"
)
scheduler = BackgroundScheduler(timezone=pytz.utc)


def create_app(config_class=None):
    """
    Application factory for creating Flask app instance.
    
    Args:
        config_class: Configuration class to use (default: Config)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    if config_class is None:
        from app.config import Config
        config_class = Config
    
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    limiter.init_app(app)
    
    # User loader for Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.forum import forum_bp
    from app.blueprints.health import health_bp
    from app.blueprints.api import api_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.agents import agents_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    
    # Context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'app_name': 'LiverWatch',
            'app_version': '2.0.0',
            'current_year': __import__('datetime').datetime.now().year
        }
    
    # Custom Jinja2 filters
    @app.template_filter('formatdate')
    def formatdate_filter(value, format='%B %d, %Y'):
        """Format a datetime object to a string"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                from datetime import datetime
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return value
        return value.strftime(format)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Setup scheduled tasks
    if not scheduler.running:
        from app.services.scraper import run_scheduled_scraper
        scheduler.add_job(
            func=lambda: run_scheduled_scraper(app),
            trigger="interval",
            hours=1,
            id='scraper_job',
            replace_existing=True
        )
        scheduler.start()
    
    return app
