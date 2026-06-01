"""
Tests for API v1 — Risk endpoints
  POST /api/v1/risk/assess
  GET  /api/v1/risk/history
  GET  /api/v1/risk/<id>
"""
from werkzeug.security import generate_password_hash
from tests.conftest import make_user


# ── helpers ───────────────────────────────────────────────────────────────

def _get_token(client, db, email='risk@x.com', password='Pass123!'):
    make_user(db, email=email, password=generate_password_hash(password))
    resp = client.post('/api/v1/auth/login',
                       json={'email': email, 'password': password})
    return resp.get_json()['access_token']


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


_VALID_PAYLOAD = {
    'hepatitis': {
        'hbsag_positive': False,
        'hcv_positive': False,
        'vaccinated_hbv': True,
    },
    'alcohol': {'drinks_per_day': 0, 'years_drinking': 0, 'binge_drinking': False},
    'symptoms': [],
    'medications': {
        'otc_painkillers': False,
        'painkiller_frequency': 'rarely',
    },
    'disclaimer_acknowledged': True,
}


# ── /assess ───────────────────────────────────────────────────────────────

def test_risk_assess_creates_record(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/risk/assess',
                       json=_VALID_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'assessment_id' in data
    assert 'risk_level' in data
    assert 'disclaimer' in data


def test_risk_assess_returns_factors(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/risk/assess',
                       json=_VALID_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.get_json()
    assert isinstance(data['factors'], list)


def test_risk_assess_high_alcohol(client, db):
    token = _get_token(client, db)
    payload = dict(_VALID_PAYLOAD)
    payload['alcohol'] = {'drinks_per_day': 8, 'years_drinking': 10, 'binge_drinking': True}
    resp = client.post('/api/v1/risk/assess', json=payload, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['risk_level'] in ('high', 'urgent', 'critical')


def test_risk_assess_requires_disclaimer(client, db):
    token = _get_token(client, db)
    payload = dict(_VALID_PAYLOAD)
    payload['disclaimer_acknowledged'] = False
    resp = client.post('/api/v1/risk/assess', json=payload, headers=_auth(token))
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'disclaimer' in data or 'error' in data


def test_risk_assess_requires_auth(client, db):
    resp = client.post('/api/v1/risk/assess', json=_VALID_PAYLOAD)
    assert resp.status_code == 401


def test_risk_assess_persists_to_db(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/risk/assess',
                       json=_VALID_PAYLOAD, headers=_auth(token))
    from app.models import RiskAssessment
    assert resp.status_code == 201
    aid = resp.get_json()['assessment_id']
    a = db.session.get(RiskAssessment, aid)
    assert a is not None
    assert a.disclaimer_acknowledged is True


def test_risk_assess_disclaimer_always_in_response(client, db):
    token = _get_token(client, db)
    resp = client.post('/api/v1/risk/assess',
                       json=_VALID_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 201
    assert 'does not provide medical diagnosis' in resp.get_json()['disclaimer']


# ── /history ──────────────────────────────────────────────────────────────

def test_risk_history_empty(client, db):
    token = _get_token(client, db)
    resp = client.get('/api/v1/risk/history', headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['assessments'] == []
    assert data['total'] == 0


def test_risk_history_returns_own_assessments(client, db):
    token = _get_token(client, db)
    # Create one assessment
    client.post('/api/v1/risk/assess', json=_VALID_PAYLOAD, headers=_auth(token))
    resp = client.get('/api/v1/risk/history', headers=_auth(token))
    assert resp.status_code == 200
    assert resp.get_json()['total'] == 1


def test_risk_history_requires_auth(client, db):
    resp = client.get('/api/v1/risk/history')
    assert resp.status_code == 401


def test_risk_history_pagination(client, db):
    token = _get_token(client, db)
    for _ in range(3):
        client.post('/api/v1/risk/assess', json=_VALID_PAYLOAD, headers=_auth(token))
    resp = client.get('/api/v1/risk/history?page=1&limit=2', headers=_auth(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['assessments']) == 2
    assert data['total'] == 3


# ── /<id> ─────────────────────────────────────────────────────────────────

def test_risk_get_assessment(client, db):
    token = _get_token(client, db)
    create = client.post('/api/v1/risk/assess',
                         json=_VALID_PAYLOAD, headers=_auth(token))
    aid = create.get_json()['assessment_id']
    resp = client.get(f'/api/v1/risk/{aid}', headers=_auth(token))
    assert resp.status_code == 200
    assert resp.get_json()['id'] == aid


def test_risk_get_assessment_404(client, db):
    token = _get_token(client, db)
    resp = client.get('/api/v1/risk/99999', headers=_auth(token))
    assert resp.status_code == 404


def test_risk_get_other_user_assessment_403(client, db):
    make_user(db, username='riskuser1', email='r1@x.com',
              password=generate_password_hash('Pass123!'))
    make_user(db, username='riskuser2', email='r2@x.com',
              password=generate_password_hash('Pass123!'))
    resp1 = client.post('/api/v1/auth/login',
                        json={'email': 'r1@x.com', 'password': 'Pass123!'})
    resp2 = client.post('/api/v1/auth/login',
                        json={'email': 'r2@x.com', 'password': 'Pass123!'})
    token1 = resp1.get_json()['access_token']
    token2 = resp2.get_json()['access_token']
    create = client.post('/api/v1/risk/assess',
                         json=_VALID_PAYLOAD, headers=_auth(token1))
    aid = create.get_json()['assessment_id']
    resp = client.get(f'/api/v1/risk/{aid}', headers=_auth(token2))
    assert resp.status_code == 403
