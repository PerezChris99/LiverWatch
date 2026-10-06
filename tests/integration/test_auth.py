"""
Auth Blueprint Tests
====================

Tests for HTML auth routes: register, login, logout,
email verification, password reset.
"""

import pytest
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import (
    User, PasswordResetToken, EmailVerificationToken,
    AuditLog, UserConsent, utcnow,
)
from app.services.token_service import generate_token, token_expiry


# ── Registration ──────────────────────────────────────────────────────────

class TestRegister:
    def test_register_page_loads(self, client):
        r = client.get('/auth/register')
        assert r.status_code == 200

    def test_successful_registration(self, client, db):
        r = client.post('/auth/register', data={
            'username':         'newuser',
            'email':            'newuser@example.com',
            'password':         'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'consent_data':     'y',
            'consent_terms':    'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.email_verified is False  # pending verification

    def test_duplicate_email_rejected(self, client, db, regular_user):
        r = client.post('/auth/register', data={
            'username':         'another',
            'email':            regular_user.email,
            'password':         'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            'consent_data':     'y',
            'consent_terms':    'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        # Should show error, not create second user
        count = User.query.filter_by(email=regular_user.email).count()
        assert count == 1

    def test_missing_consent_rejected(self, client, db):
        r = client.post('/auth/register', data={
            'username':         'noconsent',
            'email':            'noconsent@example.com',
            'password':         'StrongPass1!',
            'confirm_password': 'StrongPass1!',
            # consent_data and consent_terms omitted
        }, follow_redirects=True)
        assert r.status_code == 200
        user = User.query.filter_by(email='noconsent@example.com').first()
        assert user is None

    def test_weak_password_rejected(self, client, db):
        r = client.post('/auth/register', data={
            'username':         'weakpass',
            'email':            'weakpass@example.com',
            'password':         'short',
            'confirm_password': 'short',
            'consent_data':     'y',
            'consent_terms':    'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        user = User.query.filter_by(email='weakpass@example.com').first()
        assert user is None


# ── Login ─────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_page_loads(self, client):
        r = client.get('/auth/login')
        assert r.status_code == 200

    def test_successful_login(self, client, db, regular_user):
        r = client.post('/auth/login', data={
            'username': regular_user.username,
            'password': 'TestPass123!',
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_wrong_password(self, client, db, regular_user):
        r = client.post('/auth/login', data={
            'username': regular_user.username,
            'password': 'WrongPassword!',
        }, follow_redirects=True)
        assert r.status_code == 200
        # failed_login_count incremented
        db.session.refresh(regular_user)
        assert regular_user.failed_login_count > 0

    def test_nonexistent_user(self, client):
        r = client.post('/auth/login', data={
            'username': 'doesnotexist',
            'password': 'SomePass1!',
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_locked_account_rejected(self, client, db, regular_user):
        from datetime import datetime, timezone, timedelta
        regular_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        regular_user.failed_login_count = 10
        db.session.commit()

        r = client.post('/auth/login', data={
            'username': regular_user.username,
            'password': 'TestPass123!',
        }, follow_redirects=True)
        assert r.status_code == 200
        data = r.data.decode()
        assert 'locked' in data.lower() or 'too many' in data.lower()


# ── Logout ────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_redirects(self, auth_client):
        r = auth_client.get('/auth/logout', follow_redirects=True)
        assert r.status_code == 200


# ── Email verification ────────────────────────────────────────────────────

class TestEmailVerification:
    def test_valid_token_verifies(self, client, db, regular_user):
        regular_user.email_verified = False
        db.session.commit()

        plain, h = generate_token()
        evt = EmailVerificationToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=token_expiry(hours=24),
        )
        db.session.add(evt)
        db.session.commit()

        r = client.get(f'/auth/verify-email/{plain}', follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.email_verified is True

    def test_expired_token_rejected(self, client, db, regular_user):
        from datetime import datetime, timezone
        plain, h = generate_token()
        evt = EmailVerificationToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        db.session.add(evt)
        db.session.commit()

        r = client.get(f'/auth/verify-email/{plain}', follow_redirects=True)
        assert r.status_code == 200
        data = r.data.decode()
        assert 'invalid' in data.lower() or 'expired' in data.lower()

    def test_invalid_token_rejected(self, client):
        r = client.get('/auth/verify-email/completelyfaketoken', follow_redirects=True)
        assert r.status_code == 200


# ── Password reset ────────────────────────────────────────────────────────

class TestPasswordReset:
    def test_forgot_password_page_loads(self, client):
        r = client.get('/auth/forgot-password')
        assert r.status_code == 200

    def test_forgot_password_nonexistent_email(self, client):
        """Email enumeration: same response regardless of whether email exists."""
        r = client.post('/auth/forgot-password', data={
            'email': 'nobody@example.com',
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_reset_with_valid_token(self, client, db, regular_user):
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=token_expiry(hours=2),
        )
        db.session.add(prt)
        db.session.commit()

        r = client.post(f'/auth/reset-password/{plain}', data={
            'password':         'NewStrongPass1!',
            'confirm_password': 'NewStrongPass1!',
        }, follow_redirects=True)
        assert r.status_code == 200
        db.session.refresh(regular_user)
        assert check_password_hash(regular_user.password, 'NewStrongPass1!')

    def test_reset_with_expired_token(self, client, db, regular_user):
        from datetime import datetime, timezone
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        db.session.add(prt)
        db.session.commit()

        r = client.post(f'/auth/reset-password/{plain}', data={
            'password':         'NewPass1!',
            'confirm_password': 'NewPass1!',
        }, follow_redirects=True)
        assert r.status_code == 200
        data = r.data.decode()
        assert 'invalid' in data.lower() or 'expired' in data.lower()

    def test_reset_token_used_once(self, client, db, regular_user):
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=token_expiry(hours=2),
        )
        db.session.add(prt)
        db.session.commit()

        # First use: should succeed
        client.post(f'/auth/reset-password/{plain}', data={
            'password':         'FirstNewPass1!',
            'confirm_password': 'FirstNewPass1!',
        }, follow_redirects=True)

        # Second use of same token: should be rejected
        r = client.post(f'/auth/reset-password/{plain}', data={
            'password':         'SecondNewPass1!',
            'confirm_password': 'SecondNewPass1!',
        }, follow_redirects=True)
        assert r.status_code == 200
        # Password should NOT be SecondNewPass1!
        db.session.refresh(regular_user)
        assert not check_password_hash(regular_user.password, 'SecondNewPass1!')


# ── Profile ───────────────────────────────────────────────────────────────

class TestProfile:
    def test_profile_requires_auth(self, client):
        r = client.get('/auth/profile', follow_redirects=True)
        assert r.status_code == 200
        data = r.data.decode()
        assert 'login' in data.lower()

    def test_profile_accessible_when_authed(self, auth_client):
        r = auth_client.get('/auth/profile')
        assert r.status_code == 200
