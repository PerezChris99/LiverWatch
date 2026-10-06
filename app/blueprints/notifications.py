"""
Notifications Blueprint — Phase 3
=====================================

Routes:
  GET  /notifications/           — list all notifications
  POST /notifications/<id>/read  — mark one as read
  POST /notifications/read-all   — mark all as read
  GET  /notifications/count      — unread count (JSON)
"""

from flask import Blueprint, jsonify, redirect, render_template, url_for, request
from flask_login import current_user, login_required

from app import db, limiter
from app.models import Notification, utcnow

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
@limiter.limit('60 per minute')
def notification_center():
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    limit = min(max(request.args.get('limit', 25, type=int) or 25, 1), 50)
    pagination = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .paginate(page=page, per_page=limit, error_out=False)
    )
    notifications = pagination.items
    unread_count = sum(1 for n in notifications if not n.is_read)
    return render_template('notifications/center.html',
                           notifications=notifications,
                           unread_count=unread_count,
                           pagination=pagination)


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
@limiter.limit('60 per minute')
def mark_read(notification_id):
    n = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    return redirect(url_for('notifications.notification_center'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def mark_all_read():
    (Notification.query
     .filter_by(user_id=current_user.id, is_read=False)
     .update({'is_read': True}))
    db.session.commit()
    return redirect(url_for('notifications.notification_center'))


@notifications_bp.route('/count')
@login_required
@limiter.limit('120 per minute')
def count():
    n = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': n})

