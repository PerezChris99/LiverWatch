"""
Tests for Referral blueprint
  GET  /referrals/
  GET  /referrals/facilities
  GET  /referrals/facilities/<id>
  GET  /referrals/create/<assessment_id>
  POST /referrals/create/<assessment_id>
  GET  /referrals/<referral_code>
"""
import pytest
from tests.conftest import make_user


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh']   = True


def make_facility(db, name='Test Clinic', district='Central',
                  hepatitis=True, specialist=False, active=True):
    from app.models import HealthcareFacility
    f = HealthcareFacility(
        name=name, district=district,
        facility_type='clinic',
        hepatitis_treatment=hepatitis,
        liver_specialist=specialist,
        is_active=active,
        is_verified=True,
    )
    db.session.add(f)
    db.session.commit()
    return f


def make_assessment(db, user_id):
    from app.models import RiskAssessment
    a = RiskAssessment(
        user_id=user_id,
        risk_level='moderate',
        overall_score=0.45,
        disclaimer_acknowledged=True,
    )
    db.session.add(a)
    db.session.commit()
    return a


def make_referral(db, user_id, facility_id, assessment_id, referred_by_id=None):
    from app.models import Referral, ReferralStatus
    r = Referral(
        user_id=user_id,
        referred_by_id=referred_by_id or user_id,
        facility_id=facility_id,
        risk_assessment_id=assessment_id,
        urgency='routine',
        status=ReferralStatus.PENDING.value,
    )
    db.session.add(r)
    db.session.commit()
    return r


# ── /referrals/ ───────────────────────────────────────────────────────────

def test_referrals_index_requires_login(client, db):
    resp = client.get('/referrals/')
    assert resp.status_code in (302, 401)


def test_referrals_index_empty(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/referrals/')
    assert resp.status_code == 200
    assert b'no referrals' in resp.data.lower() or b'referral' in resp.data.lower()


def test_referrals_index_shows_own(client, db):
    user = make_user(db)
    _login(client, user)
    facility = make_facility(db)
    assessment = make_assessment(db, user.id)
    make_referral(db, user.id, facility.id, assessment.id)
    resp = client.get('/referrals/')
    assert resp.status_code == 200
    assert b'REF' in resp.data


# ── /referrals/facilities ─────────────────────────────────────────────────

def test_facilities_public(client, db):
    """Facilities page is accessible without login."""
    resp = client.get('/referrals/facilities')
    assert resp.status_code == 200


def test_facilities_shows_active(client, db):
    make_facility(db, name='Active Clinic')
    make_facility(db, name='Inactive Clinic', active=False)
    resp = client.get('/referrals/facilities')
    assert b'Active Clinic' in resp.data
    assert b'Inactive Clinic' not in resp.data


def test_facilities_filter_by_district(client, db):
    make_facility(db, name='North Clinic', district='Northern')
    make_facility(db, name='South Clinic', district='Southern')
    resp = client.get('/referrals/facilities?district=Northern')
    assert resp.status_code == 200
    assert b'North Clinic' in resp.data


def test_facilities_filter_by_service_hepatitis(client, db):
    make_facility(db, name='Hep Clinic', hepatitis=True)
    make_facility(db, name='No Hep', hepatitis=False)
    resp = client.get('/referrals/facilities?service=hepatitis')
    assert resp.status_code == 200
    assert b'Hep Clinic' in resp.data


# ── /referrals/facilities/<id> ────────────────────────────────────────────

def test_facility_detail_exists(client, db):
    f = make_facility(db, name='Detail Clinic')
    resp = client.get(f'/referrals/facilities/{f.id}')
    assert resp.status_code == 200
    assert b'Detail Clinic' in resp.data


def test_facility_detail_404_inactive(client, db):
    f = make_facility(db, name='Gone', active=False)
    resp = client.get(f'/referrals/facilities/{f.id}')
    assert resp.status_code == 404


def test_facility_detail_404_missing(client, db):
    resp = client.get('/referrals/facilities/99999')
    assert resp.status_code == 404


# ── /referrals/create/<assessment_id> ────────────────────────────────────

def test_create_referral_get(client, db):
    user = make_user(db)
    _login(client, user)
    assessment = make_assessment(db, user.id)
    make_facility(db)
    resp = client.get(f'/referrals/create/{assessment.id}')
    assert resp.status_code == 200
    assert b'Select Facility' in resp.data


def test_create_referral_get_404_bad_assessment(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/referrals/create/99999')
    assert resp.status_code == 404


def test_create_referral_get_403_other_user(client, db):
    owner = make_user(db, username='owner1', email='owner@x.com')
    other = make_user(db, username='other1', email='other@x.com')
    assessment = make_assessment(db, owner.id)
    _login(client, other)
    resp = client.get(f'/referrals/create/{assessment.id}')
    assert resp.status_code == 403


def test_create_referral_post_creates_referral(client, db):
    user = make_user(db)
    _login(client, user)
    assessment = make_assessment(db, user.id)
    facility = make_facility(db)
    resp = client.post(f'/referrals/create/{assessment.id}', data={
        'facility_id': facility.id,
        'urgency': 'routine',
        'notes': 'Please review.',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'REF' in resp.data


def test_create_referral_post_missing_facility(client, db):
    user = make_user(db)
    _login(client, user)
    assessment = make_assessment(db, user.id)
    resp = client.post(f'/referrals/create/{assessment.id}', data={
        'urgency': 'routine',
    })
    assert resp.status_code in (200, 302)  # re-shows form


# ── /referrals/<referral_code> ────────────────────────────────────────────

def test_referral_status_page(client, db):
    user = make_user(db)
    _login(client, user)
    facility = make_facility(db)
    assessment = make_assessment(db, user.id)
    referral = make_referral(db, user.id, facility.id, assessment.id)
    resp = client.get(f'/referrals/{referral.referral_code}')
    assert resp.status_code == 200
    assert referral.referral_code.encode() in resp.data


def test_referral_status_403_other_user(client, db):
    owner = make_user(db, username='rslown', email='own@x.com')
    other = make_user(db, username='rsloth', email='oth@x.com')
    facility = make_facility(db)
    assessment = make_assessment(db, owner.id)
    referral = make_referral(db, owner.id, facility.id, assessment.id)
    _login(client, other)
    resp = client.get(f'/referrals/{referral.referral_code}')
    assert resp.status_code == 403


def test_referral_status_404_unknown_code(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/referrals/NOTREAL99')
    assert resp.status_code == 404


def test_referral_status_requires_login(client, db):
    owner = make_user(db, username='rslownr', email='rslowner@x.com')
    facility = make_facility(db)
    assessment = make_assessment(db, owner.id)
    referral = make_referral(db, owner.id, facility.id, assessment.id)
    resp = client.get(f'/referrals/{referral.referral_code}')
    assert resp.status_code in (302, 401)
