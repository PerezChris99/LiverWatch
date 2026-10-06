"""
API v1 — Risk Assessment Endpoints
====================================

POST /api/v1/risk/assess    → run a risk assessment
GET  /api/v1/risk/history   → user's assessment history
GET  /api/v1/risk/<id>      → single assessment detail

IMPORTANT: All responses include the medical disclaimer.
           This API NEVER diagnoses diseases.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pytz
from flask import Blueprint, g, jsonify, request

from app import db, limiter
from app.blueprints.api.v1.auth import jwt_required
from app.models import (
    AuditLog, RiskAssessment, RiskFactor, RiskLevel, UserSymptomReport
)
from app.services.risk_engine import run_risk_assessment, MEDICAL_DISCLAIMER

logger = logging.getLogger(__name__)

risk_api_v1 = Blueprint('risk_api_v1', __name__, url_prefix='/risk')

DISCLAIMER = MEDICAL_DISCLAIMER


@risk_api_v1.post('/assess')
@limiter.limit('20 per minute')
@jwt_required
def assess():
    """
    POST /api/v1/risk/assess

    Run a liver risk assessment for the authenticated user.

    Body (all sections are optional — more data = higher confidence):
    {
        "hepatitis": {
            "hbsag_positive": false,
            "hcv_positive": false,
            "vaccinated_hbv": true,
            "exposure_risk": false,
            "family_history": false
        },
        "alcohol": {
            "drinks_per_day": 0,
            "years_drinking": 0,
            "binge_drinking": false
        },
        "symptoms": ["jaundice", "dark_urine"],
        "medications": {
            "otc_painkillers": false,
            "painkiller_frequency": "rarely",
            "tb_treatment": false,
            "herbal_remedies": false,
            "multiple_medications": false
        },
        "environmental": {
            "aflatoxin_exposure": false,
            "chemical_exposure": false,
            "unsafe_water": false
        },
        "family_history": {
            "liver_cancer_family": false,
            "cirrhosis_family": false,
            "hbv_family": false
        },
        "nutrition": {
            "bmi": null,
            "high_fat_diet": false,
            "low_water_intake": false,
            "diabetes": false
        },
        "disclaimer_acknowledged": true
    }

    Returns: full AssessmentResult + stored assessment id.
    """
    data = request.get_json(silent=True) or {}
    user = g.current_user

    if not data.get('disclaimer_acknowledged'):
        return jsonify({
            'error': (
                'You must acknowledge the disclaimer before submitting a risk assessment. '
                'Set disclaimer_acknowledged: true in your request.'
            ),
            'disclaimer': DISCLAIMER,
        }), 400

    result = run_risk_assessment(data)

    # Persist the assessment
    assessment = RiskAssessment(
        user_id=user.id,
        risk_level=result.risk_level,
        overall_score=result.overall_score,
        confidence_level=result.confidence_level,
        explanation=result.explanation,
        requires_referral=result.requires_referral,
        referral_urgency=result.referral_urgency,
        assessment_type='self',
        disclaimer_acknowledged=True,
    )
    assessment.set_recommendations(result.recommendations)
    db.session.add(assessment)
    db.session.flush()

    # Persist risk factors
    for f in result.factors:
        rf = RiskFactor(
            assessment_id=assessment.id,
            factor_name=f.name,
            factor_category=f.category,
            value=str(f.value),
            unit=f.unit,
            weight=f.weight,
            contribution=f.contribution,
            is_elevated=f.is_elevated,
            explanation=f.explanation,
        )
        db.session.add(rf)

    # Persist reported symptoms
    for symptom_name in data.get('symptoms', []):
        sr = UserSymptomReport(
            user_id=user.id,
            assessment_id=assessment.id,
            symptom_name=symptom_name,
            severity=5,   # default severity — detailed severity collected in form
        )
        db.session.add(sr)

    # Audit
    audit = AuditLog(
        user_id=user.id,
        action='risk_assessment_created',
        resource_type='risk_assessment',
        resource_id=assessment.id,
        ip_address=request.remote_addr,
    )
    audit.set_details({
        'risk_level':   result.risk_level,
        'overall_score': result.overall_score,
    })
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        'assessment_id':    assessment.id,
        'risk_level':       result.risk_level,
        'overall_score':    result.overall_score,
        'risk_percentage':  round(result.overall_score * 100, 1),
        'confidence_level': result.confidence_level,
        'explanation':      result.explanation,
        'recommendations':  result.recommendations,
        'requires_referral': result.requires_referral,
        'referral_urgency': result.referral_urgency,
        'emergency_symptoms': result.emergency_symptoms,
        'factors': [
            {
                'name':         f.name,
                'category':     f.category,
                'contribution': round(f.contribution, 3),
                'is_elevated':  f.is_elevated,
                'explanation':  f.explanation,
            }
            for f in result.factors
        ],
        'disclaimer': DISCLAIMER,
    }), 201


@risk_api_v1.get('/history')
@limiter.limit('60 per minute')
@jwt_required
def history():
    """GET /api/v1/risk/history — paginated assessment history for current user."""
    user  = g.current_user
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    limit = min(max(request.args.get('limit', 10, type=int) or 10, 1), 50)

    pagination = (
        RiskAssessment.query
        .filter_by(user_id=user.id)
        .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        .paginate(page=page, per_page=limit, error_out=False)
    )

    items = [
        {
            'id':               a.id,
            'risk_level':       a.risk_level,
            'overall_score':    a.overall_score,
            'risk_percentage':  a.risk_percentage,
            'requires_referral': a.requires_referral,
            'assessment_type':  a.assessment_type,
            'created_at':       a.created_at.isoformat(),
        }
        for a in pagination.items
    ]

    return jsonify({
        'assessments': items,
        'total':       pagination.total,
        'page':        page,
        'pages':       pagination.pages,
        'disclaimer':  DISCLAIMER,
    }), 200


@risk_api_v1.get('/<int:assessment_id>')
@limiter.limit('120 per minute')
@jwt_required
def get_assessment(assessment_id: int):
    """GET /api/v1/risk/<id> — full assessment detail."""
    user = g.current_user
    a    = db.session.get(RiskAssessment, assessment_id)

    if not a:
        return jsonify({'error': 'Assessment not found'}), 404

    # Object-level authorization: default deny. Administrative access must be explicit.
    # CHW/clinician workflows should resolve through their scoped patient/referral
    # relationships rather than accepting an arbitrary assessment ID.
    if a.user_id != user.id and user.role != 'admin':
        logger.warning(
            "risk_object_access_denied user_id=%s assessment_id=%s target_user_id=%s",
            user.id, assessment_id, a.user_id,
        )
        return jsonify({'error': 'Access denied'}), 403

    factors = [
        {
            'name':         f.factor_name,
            'category':     f.factor_category,
            'value':        f.value,
            'weight':       f.weight,
            'contribution': round(f.contribution, 3),
            'is_elevated':  f.is_elevated,
            'explanation':  f.explanation,
        }
        for f in a.risk_factors
    ]

    return jsonify({
        'id':               a.id,
        'risk_level':       a.risk_level,
        'overall_score':    a.overall_score,
        'risk_percentage':  a.risk_percentage,
        'confidence_level': a.confidence_level,
        'explanation':      a.explanation,
        'recommendations':  a.get_recommendations(),
        'requires_referral': a.requires_referral,
        'referral_urgency': a.referral_urgency,
        'assessment_type':  a.assessment_type,
        'factors':          factors,
        'created_at':       a.created_at.isoformat(),
        'disclaimer':       DISCLAIMER,
    }), 200
