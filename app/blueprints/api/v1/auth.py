"""
API v1 — Auth Endpoints
========================

/api/v1/auth/login    POST   → obtain JWT access token
/api/v1/auth/register POST   → create account + send verification email
/api/v1/auth/me       GET    → current user profile (requires token)
/api/v1/auth/logout   POST   → invalidate session (stateless JWT note)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from functools import wraps

import pytz
import jwt
import uuid
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, limiter
from app.models import AuditLog, User, UserConsent
from app.services.token_service import generate_token, token_expiry
from app.models import EmailVerificationToken
from app.services.email_service import send_verification_email

logger = logging.getLogger(__name__)

auth_api_v1 = Blueprint('auth_api_v1', __name__, url_prefix='/auth')


# ── JWT helpers ───────────────────────────────────────────────────────────

def _create_access_token(user_id: int, role: str, expires_hours: int | None = None) -> str:
    expires_hours = expires_hours or current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)
    payload = {
        'sub':  str(user_id),
        'role': role,
        'typ': 'access',
        'tv': 0,
        'jti': str(uuid.uuid4()),
        'iss': current_app.config.get('JWT_ISSUER', 'liverwatch'),
        'aud': current_app.config.get('JWT_AUDIENCE', 'liverwatch-api'),
        'iat':  datetime.now(pytz.utc),
        'exp':  datetime.now(pytz.utc) + timedelta(hours=expires_hours),
    }
    payload['tv'] = user_token_version = db.session.get(User, user_id).token_version
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def jwt_required(f):
    """Decorator that verifies the Bearer JWT and sets g.current_user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token_str = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(
                token_str,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'],
                issuer=current_app.config.get('JWT_ISSUER', 'liverwatch'),
                audience=current_app.config.get('JWT_AUDIENCE', 'liverwatch-api'),
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        try:
            user_id = int(payload['sub'])
        except (KeyError, TypeError, ValueError):
            return jsonify({'error': 'Invalid token'}), 401

        if payload.get('typ') != 'access':
            return jsonify({'error': 'Invalid token'}), 401

        user = db.session.get(User, user_id)
        if not user or not user.is_active or user.is_deleted or payload.get('tv') != user.token_version:
            return jsonify({'error': 'User not found or inactive'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


# ── Endpoints ─────────────────────────────────────────────────────────────

@auth_api_v1.post('/login')
@limiter.limit('5 per minute')
def api_login():
    """
    POST /api/v1/auth/login
    Body: { "email": "...", "password": "..." }
    Returns: { "access_token": "...", "user": {...} }
    """
    data = request.get_json(silent=True) or {}
    email    = (data.get('email', '') or '').strip().lower()
    password = data.get('password', '') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    # Record audit regardless of outcome
    ip = request.remote_addr

    if not user or not check_password_hash(user.password, password):
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
            if user.failed_login_count >= max_attempts:
                lockout_mins = current_app.config.get('LOCKOUT_MINUTES', 30)
                user.locked_until = datetime.now(pytz.utc) + timedelta(minutes=lockout_mins)
            db.session.commit()
        _audit(None, 'login_failed', 'user', ip_address=ip,
               details={'identifier_type': 'email'})
        return jsonify({'error': 'Invalid email or password'}), 401

    if user.is_deleted:
        return jsonify({'error': 'Account has been deactivated'}), 403

    if user.is_locked:
        return jsonify({'error': 'Account temporarily locked due to multiple failed attempts'}), 429

    # Successful login
    user.failed_login_count = 0
    user.locked_until       = None
    user.last_login_at      = datetime.now(pytz.utc)
    db.session.commit()

    token = _create_access_token(user.id, user.role)
    _audit(user.id, 'login_success', 'user', resource_id=user.id, ip_address=ip)

    return jsonify({
        'access_token': token,
        'token_type':   'bearer',
        'user': _user_dict(user),
    }), 200


@auth_api_v1.post('/register')
@limiter.limit('3 per hour')
def api_register():
    """
    POST /api/v1/auth/register
    Body: {
        "username": "...", "email": "...", "password": "...",
        "consent_data_collection": true,
        "consent_ai_processing": true,
        "consent_terms": true
    }
    """
    data     = request.get_json(silent=True) or {}
    username = (data.get('username', '') or '').strip()
    email    = (data.get('email',    '') or '').strip().lower()
    password = data.get('password',  '') or ''
    ip       = request.remote_addr

    # Validate required fields
    errors = {}
    if not username or len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters.'
    if not email or '@' not in email:
        errors['email'] = 'A valid email address is required.'
    if not password or len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    if not data.get('consent_data_collection'):
        errors['consent'] = 'Data collection consent is required to use this platform.'
    if not data.get('consent_terms'):
        errors['terms'] = 'You must accept the Terms of Service.'
    if errors:
        return jsonify({'errors': errors}), 422

    if User.query.filter_by(email=email).first():
        return jsonify({'errors': {'email': 'An account with this email already exists.'}}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({'errors': {'username': 'This username is already taken.'}}), 409

    # Create user
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        consent_given=True,
        consent_date=datetime.now(pytz.utc),
    )
    db.session.add(user)
    db.session.flush()   # get user.id before commit

    # Record consents
    consent_types = {
        'data_collection': data.get('consent_data_collection', False),
        'ai_processing':   data.get('consent_ai_processing',   False),
        'research':        data.get('consent_research',        False),
        'terms':           data.get('consent_terms',           False),
    }
    for ctype, given in consent_types.items():
        consent = UserConsent(
            user_id=user.id,
            consent_type=ctype,
            given=bool(given),
            given_at=datetime.now(pytz.utc) if given else None,
            ip_address=ip,
            user_agent=request.headers.get('User-Agent', '')[:500],
        )
        db.session.add(consent)

    # Create email verification token
    plain_token, token_hash = generate_token()
    ev_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=token_expiry(current_app.config.get('EMAIL_VERIFY_EXPIRY_HOURS', 24)),
    )
    db.session.add(ev_token)
    db.session.commit()

    # Send verification email (non-blocking — log failure, don't fail request)
    verify_url = _build_url('auth.verify_email', token=plain_token)
    sent = send_verification_email(user, plain_token, verify_url)
    if not sent:
        logger.warning("Verification email failed for user %s", user.id)

    _audit(user.id, 'register', 'user', resource_id=user.id, ip_address=ip,
           details={'email': email, 'verification_email_sent': sent})

    access_token = _create_access_token(user.id, user.role)
    return jsonify({
        'message': 'Account created. Please verify your email address.',
        'access_token': access_token,
        'token_type':   'bearer',
        'user': _user_dict(user),
        'email_verification_sent': sent,
    }), 201


@auth_api_v1.post('/logout')
@limiter.limit('30 per minute')
@jwt_required
def api_logout():
    """Invalidate all currently issued access tokens for the authenticated user."""
    user = g.current_user
    user.token_version += 1
    db.session.commit()
    return jsonify({'message': 'Logged out successfully.'}), 200


@auth_api_v1.get('/me')
@jwt_required
def api_me():
    """GET /api/v1/auth/me — current authenticated user profile."""
    return jsonify({'user': _user_dict(g.current_user)}), 200


# ── Utilities ─────────────────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    return {
        'id':               user.id,
        'username':         user.username,
        'email':            user.email,
        'role':             user.role,
        'email_verified':   user.email_verified,
        'consent_given':    user.consent_given,
        'preferred_language': user.preferred_language,
        'district':         user.district,
    }


def _audit(user_id, action: str, resource_type: str,
           resource_id: int = None, ip_address: str = None, details: dict = None):
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
        )
        if details:
            log.set_details(details)
        db.session.add(log)
        db.session.commit()
    except Exception:
        logger.exception("Failed to write audit log: action=%s", action)


def _build_url(endpoint: str, **kwargs) -> str:
    """Build a full URL for an email link."""
    try:
        from flask import url_for
        return url_for(endpoint, _external=True, **kwargs)
    except Exception:
        base = current_app.config.get('BASE_URL', 'http://localhost:5000')
        qs   = '&'.join(f"{k}={v}" for k, v in kwargs.items())
        return f"{base}/{endpoint.replace('.', '/')}?{qs}"
