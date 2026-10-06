"""
Tests for the Notifications blueprint — Phase 3
"""
from tests.conftest import make_user
from app.models import Notification


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh']   = True


def _make_notification(db, user, title='Test', is_read=False):
    n = Notification(
        user_id=user.id,
        title=title,
        message='This is a test notification.',
        notification_type='info',
        is_read=is_read,
    )
    db.session.add(n)
    db.session.commit()
    return n


# ── Notification center ───────────────────────────────────────────────────

def test_notifications_require_auth(client, db):
    resp = client.get('/notifications/', follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_notifications_page_loads(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/notifications/')
    assert resp.status_code == 200


def test_notifications_shows_empty_state(client, db):
    user = make_user(db)
    _login(client, user)
    resp = client.get('/notifications/')
    assert resp.status_code == 200
    assert b'No notifications' in resp.data


def test_notifications_shows_notification(client, db):
    user = make_user(db)
    _make_notification(db, user, title='Your risk result is ready')
    _login(client, user)
    resp = client.get('/notifications/')
    assert resp.status_code == 200
    assert b'Your risk result is ready' in resp.data


def test_notifications_shows_unread_badge(client, db):
    user = make_user(db)
    _make_notification(db, user, is_read=False)
    _login(client, user)
    resp = client.get('/notifications/')
    assert resp.status_code == 200
    assert b'New' in resp.data


def test_mark_single_read(client, db):
    user = make_user(db)
    n = _make_notification(db, user, is_read=False)
    _login(client, user)
    resp = client.post(f'/notifications/{n.id}/read', follow_redirects=True)
    assert resp.status_code == 200
    updated = db.session.get(Notification, n.id)
    assert updated.is_read is True


def test_mark_all_read(client, db):
    user = make_user(db)
    n1 = _make_notification(db, user, title='A', is_read=False)
    n2 = _make_notification(db, user, title='B', is_read=False)
    _login(client, user)
    resp = client.post('/notifications/read-all', follow_redirects=True)
    assert resp.status_code == 200
    assert db.session.get(Notification, n1.id).is_read is True
    assert db.session.get(Notification, n2.id).is_read is True


def test_mark_other_users_notification_fails(client, db):
    user1 = make_user(db, username='u1', email='u1@x.com')
    user2 = make_user(db, username='u2', email='u2@x.com')
    n = _make_notification(db, user1, is_read=False)
    _login(client, user2)
    resp = client.post(f'/notifications/{n.id}/read', follow_redirects=True)
    # Should 404 (filter_by user_id)
    assert resp.status_code == 404


def test_count_endpoint(client, db):
    user = make_user(db)
    _make_notification(db, user, is_read=False)
    _make_notification(db, user, is_read=False)
    _make_notification(db, user, is_read=True)
    _login(client, user)
    resp = client.get('/notifications/count')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['count'] == 2
