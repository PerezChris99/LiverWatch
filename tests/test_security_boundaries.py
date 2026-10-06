from app.services.offline_sync import merge_operations
def test_sync_rejects_missing_operation_id():
    try: merge_operations(set(),[{}])
    except ValueError as exc: assert "operation_id" in str(exc)
    else: raise AssertionError("missing operation_id must fail")


def test_risk_assessment_object_access_is_denied_to_other_users(client, db, regular_user):
    from app.blueprints.api.v1.auth import _create_access_token
    from app.models import RiskAssessment

    other = __import__('tests.conftest', fromlist=['make_user']).make_user(
        db, username='otheruser', email='other@example.com'
    )
    assessment = RiskAssessment(
        user_id=other.id,
        risk_level='low',
        overall_score=0.1,
        confidence_level=0.8,
        disclaimer_acknowledged=True,
    )
    db.session.add(assessment)
    db.session.commit()

    token = _create_access_token(regular_user.id, regular_user.role)
    response = client.get(
        f'/api/v1/risk/{assessment.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 403


def test_invalid_api_jwt_subject_returns_401(client, db):
    import jwt
    from flask import current_app

    with client.application.app_context():
        token = jwt.encode(
            {
                'sub': 'not-an-integer',
                'role': 'patient',
                'typ': 'access',
                'iss': current_app.config['JWT_ISSUER'],
                'aud': current_app.config['JWT_AUDIENCE'],
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256',
        )
    response = client.get(
        '/api/v1/risk/history',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 401
