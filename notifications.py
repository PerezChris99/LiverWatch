"""
Advanced notification system for LiverWatch
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, User, HealthLog, Post
from datetime import datetime, timedelta
import json

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

class NotificationSystem:
    """Handles all notification logic"""
    
    @staticmethod
    def create_notification(user_id, title, message, type='info', action_url=None):
        """Create a new notification"""
        notification = {
            'id': f"{user_id}_{datetime.now().timestamp()}",
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': type,  # info, warning, success, error
            'action_url': action_url,
            'created_at': datetime.now().isoformat(),
            'read': False
        }
        
        # In a real app, you'd save to database
        # For now, we'll use session/cache
        return notification
    
    @staticmethod
    def check_health_reminders(user_id):
        """Check if user needs health logging reminders"""
        notifications = []
        
        # Check last health log
        last_log = HealthLog.query.filter_by(user_id=user_id).order_by(HealthLog.date.desc()).first()
        
        if not last_log:
            notifications.append(
                NotificationSystem.create_notification(
                    user_id,
                    "Start Your Health Journey",
                    "Log your first health data to begin tracking your liver health!",
                    "info",
                    "/health_tracker"
                )
            )
        elif last_log.date < datetime.now().date() - timedelta(days=7):
            notifications.append(
                NotificationSystem.create_notification(
                    user_id,
                    "Health Check Reminder",
                    f"It's been {(datetime.now().date() - last_log.date).days} days since your last health log. Stay consistent!",
                    "warning",
                    "/health_tracker"
                )
            )
        
        return notifications
    
    @staticmethod
    def check_risk_alerts(user_id):
        """Check for high-risk health patterns"""
        notifications = []
        
        # Get recent health logs
        recent_logs = HealthLog.query.filter(
            HealthLog.user_id == user_id,
            HealthLog.date >= datetime.now().date() - timedelta(days=7)
        ).all()
        
        if recent_logs:
            # Check for concerning patterns
            high_alcohol_days = sum(1 for log in recent_logs if log.alcohol_intake and log.alcohol_intake > 3)
            low_water_days = sum(1 for log in recent_logs if log.water_intake and log.water_intake < 1.5)
            
            if high_alcohol_days >= 3:
                notifications.append(
                    NotificationSystem.create_notification(
                        user_id,
                        "High Alcohol Intake Alert",
                        f"You've logged high alcohol intake for {high_alcohol_days} days this week. Consider reducing consumption.",
                        "error",
                        "/analytics/dashboard"
                    )
                )
            
            if low_water_days >= 4:
                notifications.append(
                    NotificationSystem.create_notification(
                        user_id,
                        "Hydration Reminder",
                        "You've been drinking less water than recommended. Aim for 2-3 liters daily.",
                        "warning",
                        "/health_tracker"
                    )
                )
        
        return notifications
    
    @staticmethod
    def check_new_content(user_id):
        """Check for new posts and relevant content"""
        notifications = []
        
        # Check for new posts in last 24 hours
        recent_posts = Post.query.filter(
            Post.date_posted >= datetime.now() - timedelta(days=1)
        ).count()
        
        if recent_posts > 0:
            notifications.append(
                NotificationSystem.create_notification(
                    user_id,
                    "New Health Articles",
                    f"{recent_posts} new liver health articles have been published!",
                    "info",
                    "/"
                )
            )
        
        return notifications
    
    @staticmethod
    def get_all_notifications(user_id):
        """Get all notifications for a user"""
        notifications = []
        
        # Combine all notification types
        notifications.extend(NotificationSystem.check_health_reminders(user_id))
        notifications.extend(NotificationSystem.check_risk_alerts(user_id))
        notifications.extend(NotificationSystem.check_new_content(user_id))
        
        return sorted(notifications, key=lambda x: x['created_at'], reverse=True)

@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get all notifications for current user"""
    notifications = NotificationSystem.get_all_notifications(current_user.id)
    return jsonify(notifications)

@notifications_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark a notification as read"""
    notification_id = request.json.get('notification_id')
    # In a real app, you'd update the database
    return jsonify({'success': True})

@notifications_bp.route('/center')
@login_required
def notification_center():
    """Notification center page"""
    notifications = NotificationSystem.get_all_notifications(current_user.id)
    return render_template('notifications/center.html', notifications=notifications)
