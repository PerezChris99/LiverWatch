"""
LiverWatch Test Fixtures
========================

Shared pytest fixtures for all test modules.
"""

import pytest
from app import create_app, db as _db
from app.config import TestingConfig
from app.models import User


# ── Application / DB fixtures ────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """Session-scoped Flask application using in-memory SQLite."""
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Function-scoped DB — drops and recreates all tables for full isolation."""
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db
        _db.session.remove()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()


# ── User factories ────────────────────────────────────────────────────────

def make_user(db, **kwargs):
    """Helper: create and persist a User."""
    from werkzeug.security import generate_password_hash
    defaults = dict(
        username='testuser',
        email='testuser@example.com',
        password=generate_password_hash('TestPass123!'),
        role='patient',
        email_verified=True,
        consent_given=True,
    )
    defaults.update(kwargs)
    user = User(**defaults)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def regular_user(db):
    return make_user(db)


@pytest.fixture()
def chw_user(db):
    return make_user(
        db,
        username='chwworker',
        email='chw@example.com',
        role='chw',
    )


@pytest.fixture()
def admin_user(db):
    return make_user(
        db,
        username='adminuser',
        email='admin@example.com',
        role='admin',
    )


@pytest.fixture()
def auth_client(client, regular_user):
    """Test client already logged in as regular_user (session login)."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(regular_user.id)
        sess['_fresh']   = True
    return client
