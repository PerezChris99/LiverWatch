"""
Notifications Blueprint - Phase 1 Stub
=========================================

Full notifications (risk alerts, referral status) happens in Phase 3.
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def notification_center():
    notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template('notifications/center.html', notifications=notifications)


@notifications_bp.route('/count')
@login_required
def count():
    n = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': n})
