"""
Advanced analytics dashboard for liver health insights
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import HealthLog, User, Post, Question, db
from ai_recommendations import LiverHealthAI
import json
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

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
    
    return render_template('analytics/dashboard.html',
                         risk_score=risk_score,
                         recommendations=recommendations,
                         trends=trends,
                         total_logs=total_logs,
                         recent_logs=recent_logs)

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
        'exercise_level': [log.exercise_level or 0 for log in health_logs]
    }
    
    return jsonify(data)

@analytics_bp.route('/api/community-stats')
def community_stats():
    """Community-wide liver health statistics"""
    # Total users and engagement
    total_users = User.query.count()
    active_users = User.query.join(HealthLog).distinct().count()
    total_posts = Post.query.count()
    total_questions = Question.query.count()
    
    # Average risk scores (anonymized)
    ai_engine = LiverHealthAI()
    all_users = User.query.all()
    risk_scores = []
    
    for user in all_users:
        score = ai_engine.calculate_risk_score(user.id)
        if score > 0:  # Only include users with data
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
        'avg_risk_score': round(avg_risk_score, 3),
        'health_averages': {
            'alcohol_intake': round(health_stats[0] or 0, 2),
            'fatty_foods': round(health_stats[1] or 0, 2),
            'sugar_intake': round(health_stats[2] or 0, 2),
            'water_intake': round(health_stats[3] or 0, 2),
            'exercise_level': round(health_stats[4] or 0, 2)
        }
    })

@analytics_bp.route('/api/risk-assessment')
@login_required
def risk_assessment():
    """Detailed risk assessment for current user"""
    ai_engine = LiverHealthAI()
    
    # Get different time period risk scores
    risk_30_days = ai_engine.calculate_risk_score(current_user.id, 30)
    risk_90_days = ai_engine.calculate_risk_score(current_user.id, 90)
    risk_365_days = ai_engine.calculate_risk_score(current_user.id, 365)
    
    # Get specific risk factors
    recent_log = HealthLog.query.filter_by(user_id=current_user.id).order_by(HealthLog.date.desc()).first()
    
    risk_factors = {}
    if recent_log:
        risk_factors = {
            'alcohol_risk': (recent_log.alcohol_intake or 0) > 2,
            'diet_risk': (recent_log.fatty_foods or 0) > 3 or (recent_log.sugar_intake or 0) > 50,
            'hydration_risk': (recent_log.water_intake or 0) < 2,
            'exercise_risk': (recent_log.exercise_level or 0) < 30
        }
    
    return jsonify({
        'risk_scores': {
            '30_days': round(risk_30_days, 3),
            '90_days': round(risk_90_days, 3),
            '365_days': round(risk_365_days, 3)
        },
        'risk_factors': risk_factors,
        'overall_status': 'high' if risk_30_days > 0.7 else 'medium' if risk_30_days > 0.4 else 'low'
    })
