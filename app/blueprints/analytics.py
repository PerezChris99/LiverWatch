"""
Analytics Blueprint — Phase 5
================================

Personal risk analytics dashboard with trend data, chart-ready JSON,
summary endpoint, and longitudinal records.
"""

import json
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db, cache
from app.models import RiskAssessment, RiskLevel

analytics_bp = Blueprint('analytics', __name__)

# ── Risk level ordering for trend context ─────────────────────────────────

_RISK_ORDER = {
    'minimal': 0, 'low': 1, 'moderate': 2,
    'high': 3, 'urgent': 4, 'critical': 5,
}


# ── Dashboard ─────────────────────────────────────────────────────────────

@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    assessments = (
        RiskAssessment.query
        .filter_by(user_id=current_user.id)
        .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        .limit(20)
        .all()
    )
    latest = assessments[0] if assessments else None
    total_count = len(assessments)
    referrals_needed = sum(1 for a in assessments if a.requires_referral)

    # Trend: compare latest two assessments
    trend = None
    if len(assessments) >= 2:
        delta = assessments[0].overall_score - assessments[1].overall_score
        trend = 'improving' if delta < -0.03 else 'worsening' if delta > 0.03 else 'stable'

    # Sparkline data (chronological, last 10)
    spark = [
        {
            'date': a.created_at.strftime('%d %b %Y') if a.created_at else '',
            'score': round(a.overall_score * 100, 1),
            'level': a.risk_level,
        }
        for a in reversed(assessments[:10])
    ]

    return render_template(
        'analytics/dashboard.html',
        assessments=assessments,
        latest=latest,
        total_count=total_count,
        referrals_needed=referrals_needed,
        trend=trend,
        spark_json=json.dumps(spark),
    )


# ── JSON: trend data ──────────────────────────────────────────────────────

@analytics_bp.route('/trend-data')
@login_required
def _trend_cache_key():
    """Build a user-scoped cache key; private health data must never share cache entries."""
    return f"analytics:trend:{current_user.get_id()}:{request.full_path}"


@cache.cached(timeout=60, key_prefix=_trend_cache_key)
def trend_data():
    """Chart-ready JSON for risk score trend (last 90 days)."""
    days = request.args.get('days', 90, type=int)
    days = min(max(days, 7), 365)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        RiskAssessment.query
        .filter(
            RiskAssessment.user_id == current_user.id,
            RiskAssessment.created_at >= since,
        )
        .order_by(RiskAssessment.created_at.asc(), RiskAssessment.id.asc())
        .limit(500)
        .all()
    )

    labels = []
    scores = []
    levels = []
    for r in rows:
        labels.append(r.created_at.strftime('%d %b %Y') if r.created_at else '')
        scores.append(round(r.overall_score * 100, 1))
        levels.append(r.risk_level)

    return jsonify({
        'labels': labels,
        'scores': scores,
        'levels': levels,
        'count': len(rows),
        'disclaimer': 'This data is for informational purposes only and does not provide medical diagnosis.',
    })


# ── JSON: summary ─────────────────────────────────────────────────────────

@analytics_bp.route('/summary')
@login_required
def summary():
    """High-level statistics for the authenticated user using database aggregates."""
    base = RiskAssessment.query.filter_by(user_id=current_user.id)
    total = base.with_entities(func.count(RiskAssessment.id)).scalar() or 0

    if not total:
        return jsonify({
            'total': 0,
            'latest_risk_level': None,
            'latest_score': None,
            'avg_score': None,
            'referrals_needed': 0,
            'trend': None,
            'distribution': {},
            'disclaimer': 'This data does not provide medical diagnosis.',
        })

    latest = (
        base.order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        .first()
    )
    previous = (
        base.filter(RiskAssessment.id != latest.id)
        .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        .first()
    )
    avg_score = base.with_entities(func.avg(RiskAssessment.overall_score)).scalar()
    referrals_needed = (
        base.filter(RiskAssessment.requires_referral.is_(True))
        .with_entities(func.count(RiskAssessment.id))
        .scalar() or 0
    )

    trend = None
    if previous is not None:
        delta = latest.overall_score - previous.overall_score
        trend = 'improving' if delta < -0.03 else 'worsening' if delta > 0.03 else 'stable'

    distribution_rows = (
        base.with_entities(
            RiskAssessment.risk_level,
            func.count(RiskAssessment.id),
        )
        .group_by(RiskAssessment.risk_level)
        .all()
    )
    dist = {level: count for level, count in distribution_rows}

    return jsonify({
        'total': total,
        'latest_risk_level': latest.risk_level,
        'latest_score': round(latest.overall_score * 100, 1),
        'avg_score': round(float(avg_score) * 100, 1) if avg_score is not None else None,
        'referrals_needed': referrals_needed,
        'trend': trend,
        'distribution': dist,
        'disclaimer': 'This data does not provide medical diagnosis.',
    })
