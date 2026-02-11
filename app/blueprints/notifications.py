"""
Notifications Blueprint
=======================

User notifications and alerts system.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Notification, HealthLog, Post
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def notification_center():
    """Notification center page"""
    # Generate notifications based on user activity
    generate_user_notifications(current_user.id)
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc())\
                                      .limit(50)\
                                      .all()
    
    return render_template('notifications/center.html', notifications=notifications)


@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get notifications"""
    # Generate fresh notifications
    generate_user_notifications(current_user.id)
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc())\
                                      .limit(20)\
                                      .all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'action_url': n.action_url,
        'read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifications])


@notifications_bp.route('/api/notifications/count')
@login_required
def notification_count():
    """Get unread notification count"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})


@notifications_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_read():
    """Mark notification as read"""
    notification_id = request.json.get('notification_id')
    
    if notification_id:
        notification = Notification.query.get(notification_id)
        if notification and notification.user_id == current_user.id:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False}), 400


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/delete/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    """Clear all read notifications"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=True
    ).delete()
    
    db.session.commit()
    return jsonify({'success': True})


def generate_user_notifications(user_id):
    """Generate notifications based on user activity"""
    
    # Check health reminder
    check_health_reminder(user_id)
    
    # Check risk alerts
    check_risk_alerts(user_id)
    
    # Check new content
    check_new_content(user_id)


def check_health_reminder(user_id):
    """Check if user needs health logging reminder"""
    # Check for existing recent reminder
    existing = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.title.like('%Health%Reminder%'),
        Notification.created_at >= datetime.now() - timedelta(days=1)
    ).first()
    
    if existing:
        return
    
    # Check last health log
    last_log = HealthLog.query.filter_by(user_id=user_id)\
                             .order_by(HealthLog.date.desc())\
                             .first()
    
    if not last_log:
        create_notification(
            user_id,
            "Start Your Health Journey!",
            "Log your first health data to begin tracking your liver health.",
            "info",
            "/health/tracker"
        )
    elif last_log.date.date() < datetime.now().date() - timedelta(days=3):
        days_since = (datetime.now().date() - last_log.date.date()).days
        create_notification(
            user_id,
            "Health Check Reminder",
            f"It's been {days_since} days since your last health log. Stay consistent!",
            "warning",
            "/health/tracker"
        )


def check_risk_alerts(user_id):
    """Check for high-risk health patterns"""
    # Check for existing recent alert
    existing = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.type == 'error',
        Notification.created_at >= datetime.now() - timedelta(days=7)
    ).first()
    
    if existing:
        return
    
    # Get recent health logs
    recent_logs = HealthLog.query.filter(
        HealthLog.user_id == user_id,
        HealthLog.date >= datetime.now() - timedelta(days=7)
    ).all()
    
    if not recent_logs:
        return
    
    # Check for concerning patterns
    high_alcohol_days = sum(1 for log in recent_logs if log.alcohol_intake and log.alcohol_intake > 3)
    low_water_days = sum(1 for log in recent_logs if log.water_intake and log.water_intake < 1.5)
    no_exercise_days = sum(1 for log in recent_logs if log.exercise_level is not None and log.exercise_level < 10)
    
    if high_alcohol_days >= 3:
        create_notification(
            user_id,
            "High Alcohol Intake Alert",
            f"You've logged high alcohol intake for {high_alcohol_days} days this week. Consider reducing consumption for better liver health.",
            "error",
            "/analytics/dashboard"
        )
    
    if low_water_days >= 4:
        create_notification(
            user_id,
            "Hydration Reminder",
            "You've been drinking less water than recommended. Aim for 2-3 liters daily to support liver function.",
            "warning",
            "/health/tracker"
        )
    
    if no_exercise_days >= 5:
        create_notification(
            user_id,
            "Activity Alert",
            "Low physical activity detected this week. Regular exercise helps maintain liver health.",
            "warning",
            "/health/tracker"
        )


def check_new_content(user_id):
    """Check for new content notifications"""
    # Check for existing recent content notification
    existing = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.title.like('%New%Article%'),
        Notification.created_at >= datetime.now() - timedelta(days=1)
    ).first()
    
    if existing:
        return
    
    # Check for new posts in last 24 hours
    recent_posts = Post.query.filter(
        Post.date_posted >= datetime.now() - timedelta(days=1),
        Post.is_published == True
    ).count()
    
    if recent_posts > 0:
        create_notification(
            user_id,
            "New Health Articles",
            f"{recent_posts} new liver health article(s) have been published!",
            "info",
            "/"
        )


def create_notification(user_id, title, message, type='info', action_url=None):
    """Create a new notification"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        action_url=action_url
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification
