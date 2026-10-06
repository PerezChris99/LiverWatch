"""
Tests for Analytics Blueprint — Phase 5
  GET /analytics/dashboard
  GET /analytics/trend-data
  GET /analytics/summary
"""
from tests.conftest import make_user
from app.models import RiskAssessment


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh']   = True


def _make_assessment(db, user_id, score=0.30, level='low', referral=False):
    a = RiskAssessment(
        user_id=user_id,
        risk_level=level,
        overall_score=score,
        confidence_level=0.8,
        disclaimer_acknowledged=True,
        requires_referral=referral,
        referral_urgency='routine' if referral else None,
    )
    db.session.add(a)
    db.session.commit()
    return a


# ── Dashboard ─────────────────────────────────────────────────────────────

def test_dashboard_requires_login(client, db):
    resp = client.get('/analytics/dashboard')
    assert resp.status_code in (302, 401)


def test_dashboard_empty(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'No data yet' in resp.data or b'assessment' in resp.data.lower()


def test_dashboard_shows_assessment(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.55, level='moderate')
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'MODERATE' in resp.data


def test_dashboard_shows_total_count(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id)
    _make_assessment(db, user.id)
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'2' in resp.data


def test_dashboard_shows_trend(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.60, level='high')
    _make_assessment(db, user.id, score=0.30, level='low')   # newer, lower → improving
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'Trend' in resp.data


def test_dashboard_contains_chart_data(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.40)
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'riskTrendChart' in resp.data or b'spark_json' in resp.data or b'Chart' in resp.data


def test_dashboard_disclaimer_present(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'medical diagnosis' in resp.data.lower()


def test_dashboard_referrals_needed_count(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.80, level='high', referral=True)
    _make_assessment(db, user.id, score=0.20, level='low',  referral=False)
    resp = client.get('/analytics/dashboard')
    assert resp.status_code == 200
    assert b'1' in resp.data   # one referral needed


# ── /trend-data ───────────────────────────────────────────────────────────

def test_trend_data_requires_login(client, db):
    resp = client.get('/analytics/trend-data')
    assert resp.status_code in (302, 401)


def test_trend_data_empty(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/analytics/trend-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['count'] == 0
    assert data['labels'] == []
    assert 'disclaimer' in data


def test_trend_data_returns_scores(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.35)
    _make_assessment(db, user.id, score=0.55)
    resp = client.get('/analytics/trend-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['count'] == 2
    assert len(data['scores']) == 2


def test_trend_data_days_parameter(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/analytics/trend-data?days=30')
    assert resp.status_code == 200
    assert 'labels' in resp.get_json()


def test_trend_data_only_own(client, db):
    user1 = make_user(db, username='u1a', email='u1a@x.com')
    user2 = make_user(db, username='u2a', email='u2a@x.com')
    _make_assessment(db, user1.id, score=0.40)
    _make_assessment(db, user2.id, score=0.80)
    _login(client, user1)
    resp = client.get('/analytics/trend-data')
    data = resp.get_json()
    assert data['count'] == 1
    assert data['scores'][0] == 40.0


# ── /summary ──────────────────────────────────────────────────────────────

def test_summary_requires_login(client, db):
    resp = client.get('/analytics/summary')
    assert resp.status_code in (302, 401)


def test_summary_empty_user(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/analytics/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 0
    assert data['latest_risk_level'] is None
    assert 'disclaimer' in data


def test_summary_with_data(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.40, level='moderate')
    _make_assessment(db, user.id, score=0.20, level='low')
    resp = client.get('/analytics/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 2
    assert data['avg_score'] == 30.0
    assert 'distribution' in data


def test_summary_trend_improving(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.70, level='high')   # older
    _make_assessment(db, user.id, score=0.20, level='low')    # newer (lower = improving)
    resp = client.get('/analytics/summary')
    data = resp.get_json()
    assert data['trend'] == 'improving'


def test_summary_trend_worsening(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.20, level='low')    # older
    _make_assessment(db, user.id, score=0.70, level='high')   # newer (higher = worsening)
    resp = client.get('/analytics/summary')
    data = resp.get_json()
    assert data['trend'] == 'worsening'


def test_summary_referrals_count(client, db):
    user = make_user(db)
    _login(client, user)
    _make_assessment(db, user.id, score=0.80, level='high', referral=True)
    _make_assessment(db, user.id, score=0.20, level='low',  referral=False)
    resp = client.get('/analytics/summary')
    data = resp.get_json()
    assert data['referrals_needed'] == 1


def test_summary_only_own(client, db):
    user1 = make_user(db, username='su1', email='su1@x.com')
    user2 = make_user(db, username='su2', email='su2@x.com')
    _make_assessment(db, user1.id, score=0.40)
    _make_assessment(db, user2.id, score=0.80)
    _login(client, user1)
    resp = client.get('/analytics/summary')
    data = resp.get_json()
    assert data['total'] == 1
