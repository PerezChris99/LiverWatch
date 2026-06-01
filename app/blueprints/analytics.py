"""
Analytics Blueprint - Phase 1 Stub
=====================================

Full analytics (risk history charts, cohort data) happens in Phase 3.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app import db
from app.models import RiskAssessment

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    assessments = (
        RiskAssessment.query
        .filter_by(user_id=current_user.id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template('analytics/dashboard.html', assessments=assessments)
