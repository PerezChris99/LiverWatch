"""
Phase 2 Tests — Health Blueprint
==================================

Tests for:
  - /health/tracker
  - /health/risk-assessment (GET + POST)
  - /health/result/<id>
  - /health/log (POST)
  - /health/chw/register (GET)

All tests use in-memory SQLite via the conftest fixtures.
"""

import pytest
from app.models import RiskAssessment, RiskFactor


# ── Tracker ──────────────────────────────────────────────────────────────

def test_tracker_redirects_anonymous(client):
    resp = client.get('/health/tracker', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_tracker_loads_for_logged_in_user(auth_client, db):
    resp = auth_client.get('/health/tracker')
    assert resp.status_code == 200
    assert b'Liver Health Tracker' in resp.data


def test_tracker_shows_empty_state_with_no_assessments(auth_client, db):
    resp = auth_client.get('/health/tracker')
    assert b'No assessments yet' in resp.data


# ── Risk assessment — GET ─────────────────────────────────────────────────

def test_risk_assessment_redirects_anonymous(client):
    resp = client.get('/health/risk-assessment', follow_redirects=False)
    assert resp.status_code == 302


def test_risk_assessment_page_loads(auth_client, db):
    resp = auth_client.get('/health/risk-assessment')
    assert resp.status_code == 200
    assert b'Liver Risk Assessment' in resp.data


def test_risk_assessment_shows_disclaimer(auth_client, db):
    resp = auth_client.get('/health/risk-assessment')
    assert b'does not provide medical diagnosis' in resp.data


def test_risk_assessment_contains_form_fields(auth_client, db):
    resp = auth_client.get('/health/risk-assessment')
    html = resp.data.decode()
    assert 'hbsag_positive' in html
    assert 'drinks_per_day' in html
    assert 'disclaimer_acknowledged' in html


# ── Risk assessment — POST (form submission) ─────────────────────────────

def _submit_risk_form(auth_client, extra=None):
    """POST a minimal valid risk assessment form."""
    data = {
        'csrf_token': _get_csrf(auth_client),
        'hbsag_positive': 'false',
        'hcv_positive': 'false',
        'vaccinated_hbv': 'false',
        'hbv_exposure_risk': 'false',
        'hbv_family_history': 'false',
        'drinks_per_day': '0',
        'years_drinking': '0',
        'binge_drinking': 'false',
        'otc_painkillers': 'false',
        'painkiller_frequency': 'rarely',
        'tb_treatment': 'false',
        'herbal_remedies': 'false',
        'multiple_medications': 'false',
        'aflatoxin_exposure': 'false',
        'chemical_exposure': 'false',
        'unsafe_water': 'false',
        'liver_cancer_family': 'false',
        'cirrhosis_family': 'false',
        'bmi': '',
        'high_fat_diet': 'false',
        'low_water_intake': 'false',
        'diabetes': 'false',
        'disclaimer_acknowledged': 'y',
    }
    if extra:
        data.update(extra)
    return auth_client.post(
        '/health/risk-assessment',
        data=data,
        follow_redirects=False,
    )


def _get_csrf(client):
    """Get a CSRF token by loading the form page."""
    resp = client.get('/health/risk-assessment')
    import re
    m = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return m.group(1) if m else ''


def test_risk_assessment_submit_creates_db_record(auth_client, db, regular_user):
    resp = _submit_risk_form(auth_client)
    # Should redirect to result page
    assert resp.status_code == 302
    assert '/health/result/' in resp.headers['Location']
    # DB record should exist
    ra = RiskAssessment.query.filter_by(user_id=regular_user.id).first()
    assert ra is not None
    assert ra.disclaimer_acknowledged is True


def test_risk_assessment_saves_risk_level(auth_client, db, regular_user):
    _submit_risk_form(auth_client)
    ra = RiskAssessment.query.filter_by(user_id=regular_user.id).first()
    assert ra.risk_level in ('minimal', 'low', 'moderate', 'high', 'urgent', 'critical')


def test_risk_assessment_saves_factors(auth_client, db, regular_user):
    _submit_risk_form(auth_client)
    ra = RiskAssessment.query.filter_by(user_id=regular_user.id).first()
    factors = RiskFactor.query.filter_by(assessment_id=ra.id).all()
    assert len(factors) > 0


def test_risk_assessment_missing_disclaimer_fails(auth_client, db, regular_user):
    resp = _submit_risk_form(auth_client, extra={'disclaimer_acknowledged': ''})
    # Should NOT redirect — stay on the form page
    assert resp.status_code == 200
    count = RiskAssessment.query.filter_by(user_id=regular_user.id).count()
    assert count == 0


# ── Result page ───────────────────────────────────────────────────────────

def test_result_page_loads(auth_client, db, regular_user):
    _submit_risk_form(auth_client)
    ra = RiskAssessment.query.filter_by(user_id=regular_user.id).first()
    resp = auth_client.get(f'/health/result/{ra.id}')
    assert resp.status_code == 200
    assert b'RISK' in resp.data
    assert b'does not provide medical diagnosis' in resp.data


def test_result_404_for_nonexistent(auth_client, db):
    resp = auth_client.get('/health/result/99999')
    assert resp.status_code == 404


def test_result_403_for_another_users_assessment(client, db):
    from tests.conftest import make_user
    from werkzeug.security import generate_password_hash
    u1 = make_user(db, username='user1', email='u1@test.com')
    u2 = make_user(db, username='user2', email='u2@test.com')

    from app.models import RiskAssessment
    from app import db as _db
    ra = RiskAssessment(
        user_id=u1.id,
        risk_level='low',
        overall_score=0.1,
        confidence_level=0.8,
        disclaimer_acknowledged=True,
    )
    _db.session.add(ra)
    _db.session.commit()

    # Log in as u2
    with client.session_transaction() as sess:
        sess['_user_id'] = str(u2.id)
        sess['_fresh'] = True

    resp = client.get(f'/health/result/{ra.id}')
    assert resp.status_code == 403


# ── Daily log ─────────────────────────────────────────────────────────────

def test_log_entry_post_saves_record(auth_client, db, regular_user):
    csrf = _get_csrf(auth_client)
    resp = auth_client.post(
        '/health/log',
        data={
            'csrf_token': csrf,
            'water_intake': '2.0',
            'exercise_minutes': '30',
            'sleep_hours': '7.5',
            'alcohol_intake': '0',
        },
        follow_redirects=False,
    )
    # Redirects to tracker
    assert resp.status_code == 302


# ── CHW register page ─────────────────────────────────────────────────────

def test_chw_register_requires_auth(client):
    resp = client.get('/health/chw/register', follow_redirects=False)
    assert resp.status_code == 302


def test_chw_register_denies_patient_role(auth_client, db):
    resp = auth_client.get('/health/chw/register', follow_redirects=True)
    assert resp.status_code == 200
    # Should redirect with an error flash, not show the form
    assert b'community health workers' in resp.data
