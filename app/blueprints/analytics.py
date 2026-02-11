"""
Analytics Blueprint
===================

Analytics dashboard and health insights.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import HealthLog, User, Post, Question
from app.services.ai_recommendations import LiverHealthAI
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """Main analytics dashboard"""
    ai_engine = LiverHealthAI()
    
    # Get user's risk score and recommendations
    risk_score = ai_engine.calculate_risk_score(current_user.id)
    recommendations = ai_engine.get_personalized_recommendations(current_user.id)
    trends = ai_engine.get_health_trends(current_user.id)
    
    # Get user's health statistics
    total_logs = HealthLog.query.filter_by(user_id=current_user.id).count()
    recent_logs = HealthLog.query.filter(
        HealthLog.user_id == current_user.id,
        HealthLog.date >= datetime.now() - timedelta(days=30)
    ).count()
    
    # Get activity data for chart
    activity_data = get_activity_data(current_user.id)
    
    return render_template('analytics/dashboard.html',
                          risk_score=risk_score,
                          recommendations=recommendations,
                          trends=trends,
                          total_logs=total_logs,
                          recent_logs=recent_logs,
                          activity_data=activity_data)


@analytics_bp.route('/api/health-data')
@login_required
def health_data_api():
    """API endpoint for health data visualization"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    health_logs = HealthLog.query.filter(
        HealthLog.user_id == current_user.id,
        HealthLog.date >= start_date
    ).order_by(HealthLog.date).all()
    
    data = {
        'dates': [log.date.strftime('%Y-%m-%d') for log in health_logs],
        'alcohol_intake': [log.alcohol_intake or 0 for log in health_logs],
        'fatty_foods': [log.fatty_foods or 0 for log in health_logs],
        'sugar_intake': [log.sugar_intake or 0 for log in health_logs],
        'water_intake': [log.water_intake or 0 for log in health_logs],
        'exercise_level': [log.exercise_level or 0 for log in health_logs],
        'sleep_hours': [log.sleep_hours or 0 for log in health_logs]
    }
    
    return jsonify(data)


@analytics_bp.route('/api/risk-history')
@login_required
def risk_history():
    """Get historical risk score data"""
    ai_engine = LiverHealthAI()
    days = request.args.get('days', 90, type=int)
    
    # Calculate weekly risk scores
    risk_data = []
    for week in range(days // 7, 0, -1):
        end_date = datetime.now() - timedelta(days=week * 7)
        start_date = end_date - timedelta(days=7)
        
        logs = HealthLog.query.filter(
            HealthLog.user_id == current_user.id,
            HealthLog.date >= start_date,
            HealthLog.date < end_date
        ).all()
        
        if logs:
            score = ai_engine.calculate_risk_score(current_user.id, days=7)
            risk_data.append({
                'week': end_date.strftime('%Y-%m-%d'),
                'score': round(score * 100, 1)
            })
    
    return jsonify(risk_data)


@analytics_bp.route('/api/community-stats')
def community_stats():
    """Community-wide liver health statistics"""
    ai_engine = LiverHealthAI()
    
    # Total users and engagement
    total_users = User.query.count()
    active_users = User.query.join(HealthLog).distinct().count()
    total_posts = Post.query.count()
    total_questions = Question.query.count()
    
    # Average risk scores (anonymized)
    all_users = User.query.join(HealthLog).distinct().all()
    risk_scores = []
    
    for user in all_users:
        score = ai_engine.calculate_risk_score(user.id)
        if score > 0:
            risk_scores.append(score)
    
    avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
    
    # Health factor averages
    health_stats = db.session.query(
        func.avg(HealthLog.alcohol_intake),
        func.avg(HealthLog.fatty_foods),
        func.avg(HealthLog.sugar_intake),
        func.avg(HealthLog.water_intake),
        func.avg(HealthLog.exercise_level)
    ).first()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_posts': total_posts,
        'total_questions': total_questions,
        'avg_risk_score': round(avg_risk_score * 100, 1),
        'health_averages': {
            'alcohol_intake': round(health_stats[0] or 0, 2),
            'fatty_foods': round(health_stats[1] or 0, 2),
            'sugar_intake': round(health_stats[2] or 0, 2),
            'water_intake': round(health_stats[3] or 0, 2),
            'exercise_level': round(health_stats[4] or 0, 2)
        }
    })


@analytics_bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """Get personalized recommendations"""
    ai_engine = LiverHealthAI()
    recommendations = ai_engine.get_personalized_recommendations(current_user.id)
    return jsonify(recommendations)


@analytics_bp.route('/api/insights')
@login_required
def get_insights():
    """Get health insights and achievements"""
    insights = []
    
    # Check logging streak
    from app.blueprints.health import calculate_logging_streak
    streak = calculate_logging_streak(current_user.id)
    
    if streak >= 7:
        insights.append({
            'type': 'achievement',
            'title': 'Consistent Logger!',
            'message': f"You've logged your health for {streak} consecutive days!",
            'icon': 'trophy'
        })
    
    # Check improvement trends
    recent_logs = HealthLog.query.filter(
        HealthLog.user_id == current_user.id,
        HealthLog.date >= datetime.now() - timedelta(days=14)
    ).order_by(HealthLog.date).all()
    
    if len(recent_logs) >= 7:
        first_half = recent_logs[:len(recent_logs)//2]
        second_half = recent_logs[len(recent_logs)//2:]
        
        # Water intake improvement
        avg_water_first = sum(l.water_intake or 0 for l in first_half) / len(first_half)
        avg_water_second = sum(l.water_intake or 0 for l in second_half) / len(second_half)
        
        if avg_water_second > avg_water_first * 1.2:
            insights.append({
                'type': 'improvement',
                'title': 'Hydration Hero!',
                'message': "Your water intake has improved by 20% recently!",
                'icon': 'tint'
            })
        
        # Exercise improvement
        avg_exercise_first = sum(l.exercise_level or 0 for l in first_half) / len(first_half)
        avg_exercise_second = sum(l.exercise_level or 0 for l in second_half) / len(second_half)
        
        if avg_exercise_second > avg_exercise_first * 1.2:
            insights.append({
                'type': 'improvement',
                'title': 'Getting Active!',
                'message': "Your exercise level has increased significantly!",
                'icon': 'running'
            })
    
    return jsonify(insights)


def get_activity_data(user_id, days=30):
    """Get user activity data for heatmap"""
    start_date = datetime.now() - timedelta(days=days)
    
    logs = HealthLog.query.filter(
        HealthLog.user_id == user_id,
        HealthLog.date >= start_date
    ).all()
    
    activity = {}
    for log in logs:
        date_str = log.date.strftime('%Y-%m-%d')
        # Calculate activity score based on logged data
        score = 0
        if log.water_intake and log.water_intake >= 2:
            score += 1
        if log.exercise_level and log.exercise_level >= 30:
            score += 1
        if log.alcohol_intake is not None and log.alcohol_intake <= 1:
            score += 1
        activity[date_str] = score
    
    return activity
