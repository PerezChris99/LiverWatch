"""
LiverWatch Configuration — v3.0
=================================

Uganda Liver Risk Intelligence Platform
Phase 1: Foundation Reset

Environment hierarchy:
  .env → environment variables → Config defaults

SECURITY: SECRET_KEY *must* be set in production via environment variable.
          The app raises ValueError if SECRET_KEY is the fallback in production.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Shared base configuration."""

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME    = 'LiverWatch'
    APP_VERSION = '3.0'

    # SECRET_KEY must be set in production — never rely on the fallback
    SECRET_KEY = os.environ.get('SECRET_KEY', 'UNSAFE_DEV_KEY_CHANGE_IN_PRODUCTION')

    # ── Database ───────────────────────────────────────────────────────────
    # Default: SQLite for local dev. Production: set DATABASE_URL to postgres://...
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 'sqlite:///liverwatch.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '5')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '10')),
        'connect_args': {'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '10'))},
    }

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # ── Celery (async tasks) ───────────────────────────────────────────────
    CELERY_BROKER_URL  = os.environ.get('CELERY_BROKER_URL',  REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL)
    CELERY_TASK_SERIALIZER   = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT    = ['json']
    CELERY_TIMEZONE          = 'Africa/Kampala'

    # ── Caching ────────────────────────────────────────────────────────────
    # Phase 1: simple (in-memory). Phase 9: switch to 'redis'
    CACHE_TYPE            = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
    CACHE_REDIS_URL       = REDIS_URL
    SEND_FILE_MAX_AGE_DEFAULT = int(os.environ.get('STATIC_CACHE_SECONDS', '86400'))

    # ── Security ───────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED         = True
    SESSION_COOKIE_SECURE    = True
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # Token expiry
    JWT_ISSUER = os.environ.get('JWT_ISSUER', 'liverwatch')
    JWT_AUDIENCE = os.environ.get('JWT_AUDIENCE', 'liverwatch-api')

    PASSWORD_RESET_EXPIRY_HOURS = 2
    EMAIL_VERIFY_EXPIRY_HOURS   = 24

    # Account lockout
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES    = 30

    # ── Mail ───────────────────────────────────────────────────────────────
    MAIL_SERVER         = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS        = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL        = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@liverwatch.ug')

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATELIMIT_ENABLED         = True
    RATELIMIT_STORAGE_URL     = os.environ.get('RATELIMIT_STORAGE_URL', REDIS_URL)
    RATELIMIT_STRATEGY        = 'fixed-window'
    RATELIMIT_DEFAULT         = '200 per day, 50 per hour'
    MAX_CONTENT_LENGTH        = int(os.environ.get('MAX_CONTENT_LENGTH', str(2 * 1024 * 1024)))
    JSON_SORT_KEYS             = True
    JSONIFY_PRETTYPRINT_REGULAR = False
    TRUSTED_PROXY_HOPS         = int(os.environ.get('TRUSTED_PROXY_HOPS', '0'))
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_LOGIN           = '5 per minute, 20 per hour'
    RATELIMIT_REGISTER        = '3 per hour'
    RATELIMIT_API             = '100 per hour'
    RATELIMIT_AGENT           = '30 per minute, 300 per hour'

    # ── External APIs ──────────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY  = os.environ.get('GOOGLE_MAPS_API_KEY')
    IPINFO_ACCESS_TOKEN  = os.environ.get('IPINFO_ACCESS_TOKEN')
    GEMINI_API_KEY       = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

    # ── Encryption (for Patient PII fields) ───────────────────────────────
    # Must be a 32-byte Fernet-compatible base64 key.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

    # ── Medical Disclaimer (immutable) ────────────────────────────────────
    MEDICAL_DISCLAIMER = (
        "This platform does not provide medical diagnosis. "
        "Risk scores are for screening guidance only. "
        "Please consult a licensed healthcare professional."
    )

    # ── Feature Flags ─────────────────────────────────────────────────────
    FEATURE_WEARABLE_API   = os.environ.get('FEATURE_WEARABLE_API',   'false').lower() == 'true'
    FEATURE_SMS_REFERRALS  = os.environ.get('FEATURE_SMS_REFERRALS',  'false').lower() == 'true'
    FEATURE_PUBLIC_RESEARCH = os.environ.get('FEATURE_PUBLIC_RESEARCH', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Local development — relaxed security, verbose logging."""

    DEBUG                 = True
    SESSION_COOKIE_SECURE = False          # HTTPS not required locally
    RATELIMIT_ENABLED     = False          # Disable rate limiting in dev
    SQLALCHEMY_ECHO       = False          # Set True to log SQL queries


class ProductionConfig(Config):
    """Production — enforces security requirements at startup."""

    DEBUG = False

    def __init__(self):
        # Hard-fail if SECRET_KEY was not overridden
        if self.SECRET_KEY == 'UNSAFE_DEV_KEY_CHANGE_IN_PRODUCTION':
            raise ValueError(
                "SECRET_KEY must be set as an environment variable in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Hard-fail if using SQLite in production
        if 'sqlite' in (self.SQLALCHEMY_DATABASE_URI or '').lower():
            raise ValueError(
                "SQLite is not supported in production. "
                "Set DATABASE_URL to a PostgreSQL connection string."
            )

    CACHE_TYPE        = 'redis'           # Use Redis in production
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class TestingConfig(Config):
    """Isolated test environment — in-memory SQLite, no external services."""

    TESTING               = True
    DEBUG                 = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED      = False          # Disable CSRF for test client
    RATELIMIT_ENABLED     = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Override engine options — StaticPool (used by in-memory SQLite) doesn't
    # support pool_timeout, pool_pre_ping, or pool_recycle.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
    }
    MAIL_SUPPRESS_SEND    = True
    SERVER_NAME           = 'localhost'
    ENCRYPTION_KEY        = 'dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdA=='  # dummy 32-char


# Config registry
config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
