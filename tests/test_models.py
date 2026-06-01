"""
Model Tests
===========

Tests for database models: User, RiskAssessment, Patient, etc.
"""

import pytest
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

from app.models import (
    User, UserConsent, PasswordResetToken, EmailVerificationToken,
    AuditLog, RiskAssessment, Patient, WearableDevice, BiomarkerReading,
    ForumDiscussion, Notification, Subscriber, utcnow, generate_code,
    UserRole, RiskLevel,
)
from app.services.token_service import generate_token, hash_token


# ── User ─────────────────────────────────────────────────────────────────

class TestUser:
    def test_create_user(self, db):
        u = User(
            username='alice',
            email='alice@example.com',
            password=generate_password_hash('secret'),
        )
        db.session.add(u)
        db.session.commit()
        assert u.id is not None
        assert u.role == UserRole.PATIENT
        assert u.email_verified is False
        assert u.is_active is True

    def test_email_unique(self, db):
        from sqlalchemy.exc import IntegrityError
        u1 = User(username='bob1', email='dup@example.com',
                  password=generate_password_hash('p'))
        u2 = User(username='bob2', email='dup@example.com',
                  password=generate_password_hash('p'))
        db.session.add(u1)
        db.session.commit()
        db.session.add(u2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_soft_delete(self, db):
        u = User(username='softy', email='softy@example.com',
                 password=generate_password_hash('p'))
        db.session.add(u)
        db.session.commit()
        u.soft_delete()
        db.session.commit()
        # is_active should reflect deleted state
        assert u.is_active is False

    def test_account_lockout(self, db):
        u = User(username='lockme', email='lockme@example.com',
                 password=generate_password_hash('p'))
        db.session.add(u)
        db.session.commit()
        assert u.is_locked is False
        # Simulate too many failed attempts
        u.failed_login_count = 10
        u.locked_until = datetime(2099, 1, 1, tzinfo=timezone.utc)
        db.session.commit()
        assert u.is_locked is True

    def test_roles(self, db):
        for role in ['patient', 'chw', 'clinician', 'admin', 'researcher', 'ngo']:
            u = User(
                username=f'user_{role}',
                email=f'{role}@example.com',
                password=generate_password_hash('p'),
                role=role,
            )
            db.session.add(u)
        db.session.commit()


# ── UserConsent ───────────────────────────────────────────────────────────

class TestUserConsent:
    def test_create_consent(self, db, regular_user):
        c = UserConsent(
            user_id=regular_user.id,
            consent_type='data_processing',
            given=True,
        )
        db.session.add(c)
        db.session.commit()
        assert c.id is not None
        assert c.given_at is not None

    def test_unique_consent_per_type(self, db, regular_user):
        from sqlalchemy.exc import IntegrityError
        c1 = UserConsent(user_id=regular_user.id, consent_type='terms', given=True)
        c2 = UserConsent(user_id=regular_user.id, consent_type='terms', given=True)
        db.session.add(c1)
        db.session.commit()
        db.session.add(c2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


# ── PasswordResetToken ────────────────────────────────────────────────────

class TestPasswordResetToken:
    def test_token_valid(self, db, regular_user):
        from app.services.token_service import token_expiry
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=token_expiry(hours=2),
        )
        db.session.add(prt)
        db.session.commit()
        assert prt.is_valid is True

    def test_token_expired(self, db, regular_user):
        from datetime import timedelta
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        db.session.add(prt)
        db.session.commit()
        assert prt.is_valid is False

    def test_token_used(self, db, regular_user):
        from app.services.token_service import token_expiry
        plain, h = generate_token()
        prt = PasswordResetToken(
            user_id=regular_user.id,
            token_hash=h,
            expires_at=token_expiry(hours=2),
            used_at=utcnow(),
        )
        db.session.add(prt)
        db.session.commit()
        assert prt.is_valid is False


# ── AuditLog ──────────────────────────────────────────────────────────────

class TestAuditLog:
    def test_create_audit(self, db, regular_user):
        log = AuditLog(
            user_id=regular_user.id,
            action='login',
            resource_type='user',
            resource_id=str(regular_user.id),
        )
        db.session.add(log)
        db.session.commit()
        assert log.id is not None

    def test_details_json(self, db, regular_user):
        log = AuditLog(user_id=regular_user.id, action='test_action')
        log.set_details({'key': 'value', 'num': 42})
        db.session.add(log)
        db.session.commit()
        assert log.get_details()['key'] == 'value'


# ── RiskAssessment ────────────────────────────────────────────────────────

class TestRiskAssessment:
    def test_create_assessment(self, db, regular_user):
        ra = RiskAssessment(
            user_id=regular_user.id,
            risk_level=RiskLevel.MODERATE,
            overall_score=0.45,
            confidence_level=0.7,
            explanation='Moderate risk due to alcohol consumption.',
            disclaimer_acknowledged=True,
        )
        db.session.add(ra)
        db.session.commit()
        assert ra.id is not None
        assert ra.created_at is not None

    def test_disclaimer_required(self, db, regular_user):
        # disclaimer_acknowledged defaults to False — should be set explicitly
        ra = RiskAssessment(
            user_id=regular_user.id,
            risk_level=RiskLevel.LOW,
            overall_score=0.1,
        )
        db.session.add(ra)
        db.session.commit()
        assert ra.disclaimer_acknowledged is False


# ── ForumDiscussion ───────────────────────────────────────────────────────

class TestForumDiscussion:
    def test_create_discussion(self, db, regular_user):
        d = ForumDiscussion(
            user_id=regular_user.id,
            title='My experience with jaundice',
            content='I noticed my skin turning yellow last week...',
            discussion_type='experience',
        )
        db.session.add(d)
        db.session.commit()
        assert d.status == 'pending_review'


# ── Helpers ───────────────────────────────────────────────────────────────

class TestHelpers:
    def test_generate_code(self):
        code = generate_code('LW', 8)
        assert code.startswith('LW-')
        assert len(code) == 11  # 'LW-' + 8 chars

    def test_utcnow(self):
        now = utcnow()
        assert now.tzinfo is not None

    def test_token_hash_deterministic(self):
        plain, h = generate_token()
        assert hash_token(plain) == h

    def test_token_hash_not_plaintext(self):
        plain, h = generate_token()
        assert plain not in h
