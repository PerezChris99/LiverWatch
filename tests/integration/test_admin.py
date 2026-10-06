"""
Tests for the Admin blueprint — Phase 3
"""
import pytest
from tests.conftest import make_user
from app.models import (
    DiscussionStatus, ForumDiscussion, ForumReply, HealthWorker, Notification
)


# ── helpers ───────────────────────────────────────────────────────────────

def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh']   = True


def _make_admin(db):
    return make_user(db, username='admin2', email='admin2@x.com', role='admin')


def _make_patient(db):
    return make_user(db, username='pat2', email='pat2@x.com', role='patient')


# ── Dashboard access ──────────────────────────────────────────────────────

def test_admin_dashboard_requires_auth(client, db):
    resp = client.get('/admin/', follow_redirects=False)
    assert resp.status_code in (302, 401, 403)


def test_admin_dashboard_blocks_patient(client, db):
    user = _make_patient(db)
    _login(client, user)
    resp = client.get('/admin/')
    assert resp.status_code == 403


def test_admin_dashboard_loads_for_admin(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.get('/admin/')
    assert resp.status_code == 200
    assert b'Admin Dashboard' in resp.data or b'Dashboard' in resp.data


def test_admin_dashboard_shows_stats(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.get('/admin/')
    assert resp.status_code == 200
    # Stats cards should appear (numbers are rendered)
    assert b'Active Users' in resp.data or b'Assessments' in resp.data


# ── User management ───────────────────────────────────────────────────────

def test_admin_users_page_loads(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.get('/admin/users')
    assert resp.status_code == 200
    assert b'admin2' in resp.data


def test_admin_change_role(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    resp = client.post(f'/admin/users/{patient.id}/role',
                       data={'role': 'chw'}, follow_redirects=True)
    assert resp.status_code == 200
    from app.models import User
    updated = db.session.get(User, patient.id)
    assert updated.role == 'chw'


def test_admin_cannot_change_own_role(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.post(f'/admin/users/{admin.id}/role',
                       data={'role': 'patient'}, follow_redirects=True)
    assert resp.status_code == 200
    from app.models import User
    same = db.session.get(User, admin.id)
    assert same.role == 'admin'


def test_admin_invalid_role_rejected(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    resp = client.post(f'/admin/users/{patient.id}/role',
                       data={'role': 'superuser'}, follow_redirects=True)
    assert resp.status_code == 200
    from app.models import User
    same = db.session.get(User, patient.id)
    assert same.role == 'patient'  # unchanged


def test_admin_soft_delete_user(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    resp = client.post(f'/admin/users/{patient.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    from app.models import User
    deleted = db.session.get(User, patient.id)
    assert deleted.deleted_at is not None


def test_admin_cannot_delete_self(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.post(f'/admin/users/{admin.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    from app.models import User
    same = db.session.get(User, admin.id)
    assert same.deleted_at is None


# ── Forum moderation ──────────────────────────────────────────────────────

def test_forum_moderation_page_loads(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.get('/admin/forum')
    assert resp.status_code == 200
    assert b'Forum Moderation' in resp.data


def test_approve_discussion(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    d = ForumDiscussion(
        user_id=patient.id,
        title='Test Discussion',
        content='Some content about hepatitis awareness.',
        status=DiscussionStatus.PENDING_REVIEW.value,
    )
    db.session.add(d)
    db.session.commit()
    resp = client.post(f'/admin/forum/discussion/{d.id}/approve', follow_redirects=True)
    assert resp.status_code == 200
    updated = db.session.get(ForumDiscussion, d.id)
    assert updated.status == DiscussionStatus.APPROVED.value


def test_reject_discussion(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    d = ForumDiscussion(
        user_id=patient.id,
        title='Bad Discussion',
        content='Some content.',
        status=DiscussionStatus.PENDING_REVIEW.value,
    )
    db.session.add(d)
    db.session.commit()
    resp = client.post(f'/admin/forum/discussion/{d.id}/reject', follow_redirects=True)
    assert resp.status_code == 200
    updated = db.session.get(ForumDiscussion, d.id)
    assert updated.status == DiscussionStatus.REJECTED.value


def test_approve_reply(client, db):
    admin = _make_admin(db)
    patient = _make_patient(db)
    _login(client, admin)
    d = ForumDiscussion(
        user_id=patient.id, title='D', content='C',
        status=DiscussionStatus.APPROVED.value)
    db.session.add(d)
    db.session.flush()
    r = ForumReply(discussion_id=d.id, user_id=patient.id, content='A reply',
                   status=DiscussionStatus.PENDING_REVIEW.value)
    db.session.add(r)
    db.session.commit()
    resp = client.post(f'/admin/forum/reply/{r.id}/approve', follow_redirects=True)
    assert resp.status_code == 200
    updated = db.session.get(ForumReply, r.id)
    assert updated.status == DiscussionStatus.APPROVED.value


# ── CHW list ──────────────────────────────────────────────────────────────

def test_chw_list_page_loads(client, db):
    admin = _make_admin(db)
    _login(client, admin)
    resp = client.get('/admin/chw')
    assert resp.status_code == 200
    assert b'Community Health Workers' in resp.data


def test_verify_chw(client, db):
    admin = _make_admin(db)
    chw_user = make_user(db, username='chw3', email='chw3@x.com', role='chw')
    _login(client, admin)
    worker = HealthWorker(
        user_id=chw_user.id,
        worker_id='CHW-TEST01',
        full_name='Alice Nakato',
        district='Kampala',
        is_verified=False,
    )
    db.session.add(worker)
    db.session.commit()
    resp = client.post(f'/admin/chw/{worker.id}/verify', follow_redirects=True)
    assert resp.status_code == 200
    updated = db.session.get(HealthWorker, worker.id)
    assert updated.is_verified is True
