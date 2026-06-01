"""
Health Blueprint - Phase 1 Stub
==================================

Full health tracker redesign (LongitudinalRecord model, risk dashboard)
happens in Phase 2. This stub keeps routes importable.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import LongitudinalRecord

health_bp = Blueprint('health', __name__)


@health_bp.route('/tracker')
@login_required
def tracker():
    return render_template('health/tracker.html')


@health_bp.route('/risk-assessment')
@login_required
def risk_assessment():
    return redirect(url_for('main.index'))
