"""
Tests for the Education blueprint — Phase 3
"""
from app.models import EducationalContent, EducationalModule


def _make_module(db, slug='hepatitis-basics', category='hepatitis',
                 published=True, reviewed=False):
    m = EducationalModule(
        title='Hepatitis Basics',
        slug=slug,
        description='A guide to understanding hepatitis in Uganda.',
        category=category,
        target_audience='general',
        is_published=published,
        is_medically_reviewed=reviewed,
        order_index=0,
    )
    db.session.add(m)
    db.session.commit()
    return m


def _add_content(db, module, title='Section 1', ctype='text', published=True):
    c = EducationalContent(
        module_id=module.id,
        title=title,
        content_type=ctype,
        content='Some educational content here.',
        is_published=published,
        order_index=0,
    )
    db.session.add(c)
    db.session.commit()
    return c


# ── Index ─────────────────────────────────────────────────────────────────

def test_education_index_loads(client, db):
    resp = client.get('/education/')
    assert resp.status_code == 200


def test_education_index_shows_empty_state(client, db):
    resp = client.get('/education/')
    assert resp.status_code == 200
    assert b'No educational content' in resp.data


def test_education_index_shows_published_module(client, db):
    _make_module(db, published=True)
    resp = client.get('/education/')
    assert resp.status_code == 200
    assert b'Hepatitis Basics' in resp.data


def test_education_index_hides_unpublished_module(client, db):
    _make_module(db, published=False)
    resp = client.get('/education/')
    assert resp.status_code == 200
    assert b'Hepatitis Basics' not in resp.data


def test_education_index_groups_by_category(client, db):
    _make_module(db, slug='m1', category='hepatitis', published=True)
    _make_module(db, slug='m2', category='nutrition', published=True)
    m2 = EducationalModule.query.filter_by(slug='m2').first()
    m2.title = 'Nutrition Guide'
    db.session.commit()
    resp = client.get('/education/')
    assert resp.status_code == 200
    assert b'Hepatitis' in resp.data
    assert b'Nutrition' in resp.data


def test_education_index_shows_reviewed_badge(client, db):
    _make_module(db, reviewed=True)
    resp = client.get('/education/')
    assert resp.status_code == 200
    assert b'Reviewed' in resp.data


# ── Detail ────────────────────────────────────────────────────────────────

def test_education_detail_loads(client, db):
    m = _make_module(db)
    _add_content(db, m)
    resp = client.get('/education/hepatitis-basics')
    assert resp.status_code == 200
    assert b'Hepatitis Basics' in resp.data


def test_education_detail_shows_content(client, db):
    m = _make_module(db)
    _add_content(db, m, title='What is Hepatitis?')
    resp = client.get('/education/hepatitis-basics')
    assert resp.status_code == 200
    assert b'What is Hepatitis?' in resp.data


def test_education_detail_404_for_unpublished(client, db):
    _make_module(db, published=False)
    resp = client.get('/education/hepatitis-basics')
    assert resp.status_code == 404


def test_education_detail_404_for_unknown_slug(client, db):
    resp = client.get('/education/nonexistent-slug')
    assert resp.status_code == 404


def test_education_detail_shows_disclaimer(client, db):
    m = _make_module(db)
    resp = client.get('/education/hepatitis-basics')
    assert resp.status_code == 200
    assert b'does not provide medical diagnosis' in resp.data


def test_education_detail_hides_unpublished_section(client, db):
    m = _make_module(db)
    _add_content(db, m, title='Hidden Section', published=False)
    resp = client.get('/education/hepatitis-basics')
    assert resp.status_code == 200
    assert b'Hidden Section' not in resp.data


def test_education_accessible_without_login(client, db):
    m = _make_module(db)
    resp = client.get('/education/')
    assert resp.status_code == 200
    resp2 = client.get(f'/education/{m.slug}')
    assert resp2.status_code == 200
