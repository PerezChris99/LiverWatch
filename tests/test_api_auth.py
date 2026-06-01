"""
Tests for API v1 — Auth endpoints
  POST /api/v1/auth/login
  POST /api/v1/auth/register
  GET  /api/v1/auth/me
"""
import pytest
from werkzeug.security import generate_password_hash
from tests.conftest import make_user


# ── helpers ───────────────────────────────────────────────────────────────

def _login(client, email, password):
    return client.post('/api/v1/auth/login',
                       json={'email': email, 'password': password},
                       content_type='application/json')


def _auth_header(token):
    return {'Authorization': f'Bearer {token}'}


# ── Login ─────────────────────────────────────────────────────────────────

def test_api_login_success(client, db):
    make_user(db, email='api@x.com', password=generate_password_hash('MyPass123!'))
    resp = _login(client, 'api@x.com', 'MyPass123!')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'api@x.com'


def test_api_login_wrong_password(client, db):
    make_user(db, email='api2@x.com', password=generate_password_hash('Correct!'))
    resp = _login(client, 'api2@x.com', 'Wrong!')
    assert resp.status_code == 401
    assert 'error' in resp.get_json()


def test_api_login_unknown_email(client, db):
    resp = _login(client, 'ghost@x.com', 'pass')
    assert resp.status_code == 401


def test_api_login_missing_fields(client, db):
    resp = client.post('/api/v1/auth/login', json={})
    assert resp.status_code == 400


def test_api_login_locked_account(client, db):
    from datetime import datetime, timedelta
    import pytz
    user = make_user(db, email='locked@x.com', password=generate_password_hash('P!'))
    user.locked_until = datetime.now(pytz.utc) + timedelta(minutes=30)
    db.session.commit()
    resp = _login(client, 'locked@x.com', 'P!')
    assert resp.status_code == 429


def test_api_login_deleted_account(client, db):
    user = make_user(db, email='del@x.com', password=generate_password_hash('P1!'))
    user.soft_delete()
    db.session.commit()
    resp = _login(client, 'del@x.com', 'P1!')
    assert resp.status_code in (401, 403)


# ── Register ──────────────────────────────────────────────────────────────

def test_api_register_success(client, db):
    resp = client.post('/api/v1/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@x.com',
        'password': 'NewPass123!',
        'consent_data_collection': True,
        'consent_terms': True,
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'newuser'


def test_api_register_duplicate_email(client, db):
    make_user(db, email='dup@x.com')
    resp = client.post('/api/v1/auth/register', json={
        'username': 'dup2',
        'email': 'dup@x.com',
        'password': 'Pass1234!',
        'consent_data_collection': True,
        'consent_terms': True,
    })
    assert resp.status_code == 409


def test_api_register_duplicate_username(client, db):
    make_user(db, username='dupname', email='dupname@x.com')
    resp = client.post('/api/v1/auth/register', json={
        'username': 'dupname',
        'email': 'other@x.com',
        'password': 'Pass1234!',
        'consent_data_collection': True,
        'consent_terms': True,
    })
    assert resp.status_code == 409


def test_api_register_missing_consent(client, db):
    resp = client.post('/api/v1/auth/register', json={
        'username': 'nc',
        'email': 'nc@x.com',
        'password': 'Pass1234!',
    })
    assert resp.status_code == 422
    assert 'errors' in resp.get_json()


def test_api_register_short_password(client, db):
    resp = client.post('/api/v1/auth/register', json={
        'username': 'shortp',
        'email': 'sp@x.com',
        'password': 'abc',
        'consent_data_collection': True,
        'consent_terms': True,
    })
    assert resp.status_code == 422


def test_api_register_invalid_email(client, db):
    resp = client.post('/api/v1/auth/register', json={
        'username': 'bademail',
        'email': 'notanemail',
        'password': 'Pass1234!',
        'consent_data_collection': True,
        'consent_terms': True,
    })
    assert resp.status_code == 422


# ── /me ───────────────────────────────────────────────────────────────────

def test_api_me_returns_user(client, db):
    make_user(db, email='me@x.com', password=generate_password_hash('P1!'))
    token = _login(client, 'me@x.com', 'P1!').get_json()['access_token']
    resp = client.get('/api/v1/auth/me', headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()['user']['email'] == 'me@x.com'


def test_api_me_requires_token(client, db):
    resp = client.get('/api/v1/auth/me')
    assert resp.status_code == 401


def test_api_me_invalid_token(client, db):
    resp = client.get('/api/v1/auth/me',
                      headers={'Authorization': 'Bearer invalid.token.here'})
    assert resp.status_code == 401
