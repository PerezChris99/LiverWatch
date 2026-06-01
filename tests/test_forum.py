"""
Phase 2 Tests — Forum Blueprint
==================================

Tests for:
  - GET  /forum/           → index with approved discussions
  - GET  /forum/new        → requires auth
  - POST /forum/new        → creates ForumDiscussion (pending_review)
  - GET  /forum/<id>       → discussion detail
  - POST /forum/<id>/reply → requires auth, creates ForumReply
"""

import pytest
from app.models import ForumDiscussion, ForumReply


# ── Index ─────────────────────────────────────────────────────────────────

def test_forum_index_loads(client, db):
    resp = client.get('/forum/')
    assert resp.status_code == 200
    assert b'Community Forum' in resp.data


def test_forum_index_shows_login_link_when_anonymous(client, db):
    resp = client.get('/forum/')
    assert b'Log in' in resp.data


def test_forum_index_shows_new_discussion_button_when_logged_in(auth_client, db):
    resp = auth_client.get('/forum/')
    assert b'Start a Discussion' in resp.data


def test_forum_index_empty_state(client, db):
    resp = client.get('/forum/')
    assert b'No approved discussions' in resp.data


# ── New discussion ────────────────────────────────────────────────────────

def test_new_discussion_redirects_anonymous(client, db):
    resp = client.get('/forum/new', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_new_discussion_page_loads_for_user(auth_client, db):
    resp = auth_client.get('/forum/new')
    assert resp.status_code == 200
    assert b'Start a Discussion' in resp.data


def _get_csrf(client, url):
    resp = client.get(url)
    import re
    m = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return m.group(1) if m else ''


def test_create_discussion_saves_pending_review(auth_client, db, regular_user):
    csrf = _get_csrf(auth_client, '/forum/new')
    resp = auth_client.post(
        '/forum/new',
        data={
            'csrf_token': csrf,
            'title': 'My Hepatitis B Story',
            'discussion_type': 'awareness',
            'content': 'I want to share my experience to help others understand liver disease.',
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    d = ForumDiscussion.query.filter_by(user_id=regular_user.id).first()
    assert d is not None
    assert d.status == 'pending_review'
    assert d.title == 'My Hepatitis B Story'


def test_create_discussion_requires_minimum_length(auth_client, db, regular_user):
    csrf = _get_csrf(auth_client, '/forum/new')
    resp = auth_client.post(
        '/forum/new',
        data={
            'csrf_token': csrf,
            'title': 'Hi',
            'discussion_type': 'awareness',
            'content': 'Short',
        },
        follow_redirects=False,
    )
    # Should stay on form — validation fails
    assert resp.status_code == 200
    count = ForumDiscussion.query.filter_by(user_id=regular_user.id).count()
    assert count == 0


# ── Discussion detail ─────────────────────────────────────────────────────

def _make_approved_discussion(db, user):
    from app import db as _db
    d = ForumDiscussion(
        user_id=user.id,
        title='Test Discussion',
        content='A sufficiently long discussion post for testing purposes.',
        discussion_type='awareness',
        status='approved',
    )
    _db.session.add(d)
    _db.session.commit()
    return d


def test_discussion_detail_404_for_pending(client, db, regular_user):
    from app import db as _db
    d = ForumDiscussion(
        user_id=regular_user.id,
        title='Pending Post',
        content='This post is not approved.',
        discussion_type='awareness',
        status='pending_review',
    )
    _db.session.add(d)
    _db.session.commit()
    resp = client.get(f'/forum/{d.id}')
    assert resp.status_code == 404


def test_discussion_detail_loads_approved(client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    resp = client.get(f'/forum/{d.id}')
    assert resp.status_code == 200
    assert b'Test Discussion' in resp.data


def test_discussion_detail_increments_views(client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    client.get(f'/forum/{d.id}')
    from app import db as _db
    _db.session.refresh(d)
    assert d.views == 1


def test_discussion_detail_shows_reply_form_when_logged_in(auth_client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    resp = auth_client.get(f'/forum/{d.id}')
    assert b'Add a Reply' in resp.data


def test_discussion_detail_shows_login_cta_when_anonymous(client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    resp = client.get(f'/forum/{d.id}')
    assert b'Log in' in resp.data


# ── Add reply ─────────────────────────────────────────────────────────────

def test_add_reply_requires_auth(client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    resp = client.post(f'/forum/{d.id}/reply', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_add_reply_creates_pending_reply(auth_client, db, regular_user):
    d = _make_approved_discussion(db, regular_user)
    csrf = _get_csrf(auth_client, f'/forum/{d.id}')
    resp = auth_client.post(
        f'/forum/{d.id}/reply',
        data={
            'csrf_token': csrf,
            'content': 'Thank you for sharing this important awareness story.',
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    reply = ForumReply.query.filter_by(discussion_id=d.id).first()
    assert reply is not None
    assert reply.status == 'pending_review'


def test_add_reply_to_nonexistent_discussion(auth_client, db):
    csrf = _get_csrf(auth_client, '/forum/')
    resp = auth_client.post(
        '/forum/99999/reply',
        data={'csrf_token': csrf, 'content': 'Test reply content here.'},
    )
    assert resp.status_code == 404
