"""
Analytics Blueprint — Phase 2
================================

Personal risk analytics dashboard showing assessment history,
score trends, and referral status.
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import RiskAssessment

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    assessments = (
        RiskAssessment.query
        .filter_by(user_id=current_user.id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(20)
        .all()
    )
    latest = assessments[0] if assessments else None
    total_count = len(assessments)
    referrals_needed = sum(1 for a in assessments if a.requires_referral)
    return render_template(
        'analytics/dashboard.html',
        assessments=assessments,
        latest=latest,
        total_count=total_count,
        referrals_needed=referrals_needed,
    )

