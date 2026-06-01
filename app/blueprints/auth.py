"""
Authentication Blueprint — v3.0
=================================

Uganda Liver Risk Intelligence Platform
Phase 1: Foundation Reset

Routes:
  GET/POST /auth/login              → login
  GET/POST /auth/register           → register (with consent + email verification)
  GET      /auth/logout             → logout
  GET      /auth/verify-email/<tok> → verify email address
  GET/POST /auth/forgot-password    → request password reset
  GET/POST /auth/reset-password/<tok> → set new password
  GET      /auth/profile            → user profile
  GET/POST /auth/profile/edit       → edit profile
  GET/POST /auth/change-password    → change password
"""

from __future__ import annotations

import logging
from datetime import datetime

import pytz
from flask import (Blueprint, current_app, flash, redirect,
                   render_template, request, url_for)
from flask_login import (current_user, login_required,
                         login_user, logout_user)
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, limiter
from app.forms import (LoginForm, PasswordResetForm,
                        PasswordResetRequestForm, RegistrationForm)
from app.models import (AuditLog, EmailVerificationToken,
                         PasswordResetToken, User, UserConsent)
from app.services.email_service import (send_password_reset_email,
                                         send_verification_email)
from app.services.token_service import (generate_token, hash_token,
                                         token_expiry, verify_token)

logger   = logging.getLogger(__name__)
auth_bp  = Blueprint('auth', __name__)


# ── Helpers ────────────────────────────────────────────────────────────────

def _audit(user_id, action: str, ip: str = None, details: dict = None):
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type='user',
            resource_id=user_id,
            ip_address=ip or request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
        )
        if details:
            log.set_details(details)
        db.session.add(log)
        db.session.commit()
    except Exception:
        logger.exception("Audit log failed: action=%s", action)


# ── Login / Logout ────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user or not check_password_hash(user.password, form.password.data):
            if user:
                user.failed_login_count = (user.failed_login_count or 0) + 1
                max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
                if user.failed_login_count >= max_attempts:
                    from datetime import timedelta
                    mins = current_app.config.get('LOCKOUT_MINUTES', 30)
                    user.locked_until = datetime.now(pytz.utc) + timedelta(minutes=mins)
                db.session.commit()
            _audit(None, 'login_failed', details={'username': form.username.data})
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', form=form)

        if user.is_deleted:
            flash('This account has been deactivated. Contact support.', 'error')
            return render_template('auth/login.html', form=form)

        if user.is_locked:
            flash('Account temporarily locked due to multiple failed login attempts.', 'error')
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Your account is inactive. Contact support.', 'error')
            return render_template('auth/login.html', form=form)

        # Successful login
        user.failed_login_count = 0
        user.locked_until       = None
        user.last_login_at      = datetime.now(pytz.utc)
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        _audit(user.id, 'login_success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    _audit(current_user.id, 'logout')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ── Registration ──────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html', form=form)
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Email already registered. Please log in or use a different email.', 'error')
            return render_template('auth/register.html', form=form)
        if not form.consent_data.data:
            flash('You must consent to data collection to use this platform.', 'error')
            return render_template('auth/register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password=generate_password_hash(form.password.data),
            consent_given=True,
            consent_date=datetime.now(pytz.utc),
        )
        db.session.add(user)
        db.session.flush()

        # Record consents
        for ctype, given in [
            ('data_collection', form.consent_data.data),
            ('terms',           form.consent_terms.data),
        ]:
            db.session.add(UserConsent(
                user_id=user.id,
                consent_type=ctype,
                given=bool(given),
                given_at=datetime.now(pytz.utc),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
            ))

        # Email verification token
        plain, hashed = generate_token()
        ev = EmailVerificationToken(
            user_id=user.id,
            token_hash=hashed,
            expires_at=token_expiry(current_app.config.get('EMAIL_VERIFY_EXPIRY_HOURS', 24)),
        )
        db.session.add(ev)
        db.session.commit()

        verify_url = url_for('auth.verify_email', token=plain, _external=True)
        sent = send_verification_email(user, plain, verify_url)
        if not sent:
            logger.warning("Verification email failed for user %s", user.id)

        _audit(user.id, 'register',
               details={'email': user.email, 'verification_sent': sent})

        flash('Account created! Check your email to verify your address before logging in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


# ── Email verification ────────────────────────────────────────────────────

@auth_bp.route('/verify-email/<token>')
def verify_email(token: str):
    token_hash = hash_token(token)
    ev = EmailVerificationToken.query.filter_by(token_hash=token_hash).first()

    if not ev or not ev.is_valid:
        flash('Verification link is invalid or has expired. Request a new one.', 'error')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, ev.user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))

    user.email_verified    = True
    user.email_verified_at = datetime.now(pytz.utc)
    ev.verified_at         = datetime.now(pytz.utc)
    db.session.commit()

    _audit(user.id, 'email_verified')
    flash('Email verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


# ── Password reset ────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # Always show success message to prevent email enumeration
        if user and not user.is_deleted:
            plain, hashed = generate_token()
            pr = PasswordResetToken(
                user_id=user.id,
                token_hash=hashed,
                expires_at=token_expiry(
                    current_app.config.get('PASSWORD_RESET_EXPIRY_HOURS', 2)
                ),
            )
            db.session.add(pr)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=plain, _external=True)
            send_password_reset_email(user, reset_url)
            _audit(user.id, 'password_reset_requested')

        flash('If an account exists for that email, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    token_hash = hash_token(token)
    pr = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    if not pr or not pr.is_valid:
        flash('Password reset link is invalid or has expired. Request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = db.session.get(User, pr.user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.login'))

        user.password           = generate_password_hash(form.password.data)
        user.failed_login_count = 0
        user.locked_until       = None
        pr.used_at              = datetime.now(pytz.utc)
        db.session.commit()

        _audit(user.id, 'password_reset_completed')
        flash('Password reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


# ── Profile ───────────────────────────────────────────────────────────────

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        full_name = request.form.get('full_name', '').strip()
        district  = request.form.get('district', '').strip()
        language  = request.form.get('preferred_language', 'en').strip()

        existing = User.query.filter(
            User.email == email,
            User.id != current_user.id,
        ).first()
        if existing:
            flash('Email is already in use by another account.', 'error')
            return render_template('auth/edit_profile.html')

        current_user.email    = email
        current_user.full_name = full_name
        current_user.district = district
        current_user.preferred_language = language if language in ('en', 'lg', 'sw') else 'en'
        db.session.commit()
        _audit(current_user.id, 'profile_updated')
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')
        confirm_pw  = request.form.get('confirm_password', '')

        if not check_password_hash(current_user.password, current_pw):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        if len(new_pw) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/change_password.html')

        current_user.password = generate_password_hash(new_pw)
        db.session.commit()
        _audit(current_user.id, 'password_changed')
        flash('Password changed successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html')

