"""
Tests for API v1 — Wearable device endpoints
  POST /api/v1/wearable/register
  POST /api/v1/wearable/<device_id>/sync
  GET  /api/v1/wearable/devices
  GET  /api/v1/wearable/<device_id>/readings
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from tests.conftest import make_user


# ── helpers ───────────────────────────────────────────────────────────────

_counter = 0


def _get_token(client, db, email=None):
    global _counter
    _counter += 1
    if not email:
        email = f'wear{_counter}@x.com'
    make_user(db, username=f'wearuser{_counter}', email=email,
              password=generate_password_hash('Wpass1!'))
    resp = client.post('/api/v1/auth/login',
                       json={'email': email, 'password': 'Wpass1!'})
    return resp.get_json()['access_token']


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


def _register_device(client, token, device_id='DEV-001', dtype='sweat_patch'):
    return client.post('/api/v1/wearable/register',
                       json={'device_id': device_id, 'device_type': dtype},
                       headers=_auth(token))


# ── Register device ───────────────────────────────────────────────────────

def test_wearable_register_success(client, db):
    token = _get_token(client, db)
    resp = _register_device(client, token)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['device_id'] == 'DEV-001'


def test_wearable_register_requires_auth(client, db):
    resp = client.post('/api/v1/wearable/register',
                       json={'device_id': 'X', 'device_type': 'sweat_patch'})
    assert resp.status_code == 401


def test_wearable_register_duplicate_device_id(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-DUP')
    resp = _register_device(client, token, device_id='DEV-DUP')
    assert resp.status_code == 409


def test_wearable_register_missing_device_id(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/wearable/register',
                       json={'device_type': 'sweat_patch'}, headers=_auth(token))
    assert resp.status_code == 400


def test_wearable_register_invalid_type(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/wearable/register',
                       json={'device_id': 'D1', 'device_type': 'magic_wand'},
                       headers=_auth(token))
    assert resp.status_code == 400


# ── List devices ──────────────────────────────────────────────────────────

def test_wearable_list_devices_empty(client, db):
    token = _get_token(client, db)
    resp = client.get('/api/v1/wearable/devices', headers=_auth(token))
    assert resp.status_code == 200
    assert resp.get_json()['devices'] == []


def test_wearable_list_devices_returns_registered(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-LIST')
    resp = client.get('/api/v1/wearable/devices', headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.get_json()['devices']) == 1


def test_wearable_list_requires_auth(client, db):
    resp = client.get('/api/v1/wearable/devices')
    assert resp.status_code == 401


# ── Sync readings ─────────────────────────────────────────────────────────

def test_wearable_sync_success(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-SYNC')
    # Activate the device first (set status active in DB)
    from app.models import WearableDevice
    dev = WearableDevice.query.filter_by(device_id='DEV-SYNC').first()
    dev.is_active = True
    dev.status = 'active'
    db.session.commit()
    resp = client.post('/api/v1/wearable/DEV-SYNC/sync',
                       json={
                           'readings': [{
                               'biomarker_type': 'ammonia',
                               'value': 20.0,
                               'unit': 'umol/L',
                               'quality_score': 0.95,
                               'timestamp': '2025-01-01T10:00:00Z',
                           }]
                       }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['saved'] == 1
    assert 'disclaimer' in data


def test_wearable_sync_unknown_device(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/wearable/GHOST-DEV/sync',
                       json={'readings': []}, headers=_auth(token))
    assert resp.status_code == 404


def test_wearable_sync_flags_anomaly(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-ANOM')
    from app.models import WearableDevice
    dev = WearableDevice.query.filter_by(device_id='DEV-ANOM').first()
    dev.is_active = True
    dev.status = 'active'
    db.session.commit()
    resp = client.post('/api/v1/wearable/DEV-ANOM/sync',
                       json={
                           'readings': [{
                               'biomarker_type': 'ammonia',
                               'value': 200.0,  # Way above normal
                               'unit': 'umol/L',
                               'timestamp': '2025-01-01T10:00:00Z',
                           }]
                       }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['anomaly_count'] == 1
    assert 'anomaly_notice' in data


def test_wearable_sync_invalid_biomarker_type(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-BAD')
    from app.models import WearableDevice
    dev = WearableDevice.query.filter_by(device_id='DEV-BAD').first()
    dev.is_active = True
    dev.status = 'active'
    db.session.commit()
    resp = client.post('/api/v1/wearable/DEV-BAD/sync',
                       json={
                           'readings': [{'biomarker_type': 'magic', 'value': 1.0}]
                       }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['saved'] == 0
    assert len(data['errors']) == 1


def test_wearable_sync_requires_auth(client, db):
    resp = client.post('/api/v1/wearable/DEV-X/sync', json={'readings': []})
    assert resp.status_code == 401


# ── Get readings ──────────────────────────────────────────────────────────

def test_wearable_get_readings(client, db):
    token = _get_token(client, db)
    _register_device(client, token, device_id='DEV-READ')
    from app.models import WearableDevice
    dev = WearableDevice.query.filter_by(device_id='DEV-READ').first()
    dev.is_active = True
    dev.status = 'active'
    db.session.commit()
    # Sync a reading
    client.post('/api/v1/wearable/DEV-READ/sync',
                json={'readings': [{
                    'biomarker_type': 'hydration',
                    'value': 0.65,
                    'timestamp': '2025-01-01T10:00:00Z',
                }]}, headers=_auth(token))
    resp = client.get('/api/v1/wearable/DEV-READ/readings', headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 1
    assert data['readings'][0]['biomarker_type'] == 'hydration'


def test_wearable_get_readings_unknown_device(client, db):
    token = _get_token(client, db)
    resp = client.get('/api/v1/wearable/GHOST/readings', headers=_auth(token))
    assert resp.status_code == 404


def test_wearable_get_readings_requires_auth(client, db):
    resp = client.get('/api/v1/wearable/DEV-X/readings')
    assert resp.status_code == 401
