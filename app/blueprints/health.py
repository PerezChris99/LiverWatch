"""
Health Blueprint
================

Health tracking, diet suggestions, and medical resources.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import HealthLog, Recipe
from app.forms import HealthLogForm
from app.services.utils import fetch_nearby_liver_specialists
from datetime import datetime, timedelta

health_bp = Blueprint('health', __name__)


@health_bp.route('/tracker', methods=['GET', 'POST'])
def tracker():
    """Health tracker page"""
    form = HealthLogForm()
    logs = None
    stats = None
    
    if current_user.is_authenticated:
        if form.validate_on_submit():
            # Check if a log already exists for this date
            existing = HealthLog.query.filter(
                HealthLog.user_id == current_user.id,
                db.func.date(HealthLog.date) == form.date.data
            ).first()
            
            if existing:
                # Update existing log
                existing.alcohol_intake = form.alcohol_intake.data
                existing.fatty_foods = form.fatty_foods.data
                existing.sugar_intake = form.sugar_intake.data
                existing.water_intake = form.water_intake.data
                existing.exercise_level = form.exercise_level.data
                existing.sleep_hours = form.sleep_hours.data
                existing.medication_usage = form.medication_usage.data
                existing.notes = form.notes.data
                flash('Health log updated!', 'success')
            else:
                # Create new log
                log = HealthLog(
                    date=datetime.combine(form.date.data, datetime.min.time()),
                    alcohol_intake=form.alcohol_intake.data,
                    fatty_foods=form.fatty_foods.data,
                    sugar_intake=form.sugar_intake.data,
                    water_intake=form.water_intake.data,
                    exercise_level=form.exercise_level.data,
                    sleep_hours=form.sleep_hours.data,
                    medication_usage=form.medication_usage.data,
                    notes=form.notes.data,
                    user_id=current_user.id
                )
                db.session.add(log)
                flash('Health log saved!', 'success')
            
            db.session.commit()
            return redirect(url_for('health.tracker'))
        
        # Get user's health logs
        page = request.args.get('page', 1, type=int)
        logs = HealthLog.query.filter_by(user_id=current_user.id)\
                             .order_by(HealthLog.date.desc())\
                             .paginate(page=page, per_page=7)
        
        # Calculate stats
        stats = calculate_health_stats(current_user.id)
    
    return render_template('health/tracker.html',
                          form=form,
                          logs=logs,
                          stats=stats)


@health_bp.route('/tracker/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    """Delete a health log entry"""
    log = HealthLog.query.get_or_404(log_id)
    
    if log.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    db.session.delete(log)
    db.session.commit()
    
    return jsonify({'success': True})


@health_bp.route('/diet')
def diet_suggestions():
    """Diet suggestions and recipes"""
    category = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    search = request.args.get('search', '')
    
    query = Recipe.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(
            (Recipe.title.ilike(f'%{search}%')) |
            (Recipe.ingredients.ilike(f'%{search}%'))
        )
    
    recipes = query.order_by(Recipe.created_at.desc()).all()
    
    # Get liver health tips
    tips = get_liver_health_tips()
    
    return render_template('health/diet.html',
                          recipes=recipes,
                          current_category=category,
                          current_difficulty=difficulty,
                          search=search,
                          tips=tips)


@health_bp.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Recipe detail page"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Get related recipes
    related = Recipe.query.filter(
        Recipe.id != recipe_id,
        Recipe.category == recipe.category
    ).limit(3).all()
    
    return render_template('health/recipe.html', recipe=recipe, related=related)


@health_bp.route('/find-doctors')
def find_doctors():
    """Find nearby liver specialists"""
    location = request.args.get('location', '')
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    specialists = []
    
    if lat and lng:
        specialists = fetch_nearby_liver_specialists(f"{lat},{lng}")
    elif location:
        # Use location string with geocoding
        specialists = fetch_nearby_liver_specialists(location)
    
    return render_template('health/find_doctors.html',
                          specialists=specialists or [],
                          location=location)


@health_bp.route('/survival-rates')
def survival_rates():
    """Liver disease survival statistics"""
    return render_template('health/survival_rates.html')


@health_bp.route('/child-health')
def child_health():
    """Child liver health information"""
    return render_template('health/child_health.html')


@health_bp.route('/api/health-data')
@login_required
def health_data_api():
    """API endpoint for health chart data"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    logs = HealthLog.query.filter(
        HealthLog.user_id == current_user.id,
        HealthLog.date >= start_date
    ).order_by(HealthLog.date).all()
    
    data = {
        'dates': [log.date.strftime('%Y-%m-%d') for log in logs],
        'alcohol_intake': [log.alcohol_intake or 0 for log in logs],
        'fatty_foods': [log.fatty_foods or 0 for log in logs],
        'sugar_intake': [log.sugar_intake or 0 for log in logs],
        'water_intake': [log.water_intake or 0 for log in logs],
        'exercise_level': [log.exercise_level or 0 for log in logs],
        'sleep_hours': [log.sleep_hours or 0 for log in logs]
    }
    
    return jsonify(data)


def calculate_health_stats(user_id, days=30):
    """Calculate health statistics for a user"""
    start_date = datetime.now() - timedelta(days=days)
    
    logs = HealthLog.query.filter(
        HealthLog.user_id == user_id,
        HealthLog.date >= start_date
    ).all()
    
    if not logs:
        return None
    
    stats = {
        'total_logs': len(logs),
        'avg_water': sum(l.water_intake or 0 for l in logs) / len(logs),
        'avg_exercise': sum(l.exercise_level or 0 for l in logs) / len(logs),
        'avg_alcohol': sum(l.alcohol_intake or 0 for l in logs) / len(logs),
        'avg_sleep': sum(l.sleep_hours or 0 for l in logs) / len(logs),
        'streak': calculate_logging_streak(user_id)
    }
    
    # Calculate health score (0-100)
    score = 50  # Base score
    
    # Water intake bonus (target: 2L)
    if stats['avg_water'] >= 2:
        score += 15
    elif stats['avg_water'] >= 1.5:
        score += 10
    
    # Exercise bonus (target: 30 min)
    if stats['avg_exercise'] >= 30:
        score += 15
    elif stats['avg_exercise'] >= 15:
        score += 10
    
    # Alcohol penalty
    if stats['avg_alcohol'] > 3:
        score -= 20
    elif stats['avg_alcohol'] > 2:
        score -= 10
    
    # Sleep bonus (target: 7-9 hours)
    if 7 <= stats['avg_sleep'] <= 9:
        score += 10
    elif 6 <= stats['avg_sleep'] <= 10:
        score += 5
    
    stats['health_score'] = max(0, min(100, score))
    
    return stats


def calculate_logging_streak(user_id):
    """Calculate consecutive days of health logging"""
    logs = HealthLog.query.filter_by(user_id=user_id)\
                         .order_by(HealthLog.date.desc())\
                         .all()
    
    if not logs:
        return 0
    
    streak = 1
    prev_date = logs[0].date.date()
    
    for log in logs[1:]:
        log_date = log.date.date()
        if (prev_date - log_date).days == 1:
            streak += 1
            prev_date = log_date
        else:
            break
    
    return streak


def get_liver_health_tips():
    """Get liver health tips"""
    return [
        {
            'title': 'Stay Hydrated',
            'content': 'Drink at least 2-3 liters of water daily to help your liver flush out toxins.',
            'icon': 'fa-tint'
        },
        {
            'title': 'Limit Alcohol',
            'content': 'Excessive alcohol consumption is one of the leading causes of liver damage.',
            'icon': 'fa-wine-glass-alt'
        },
        {
            'title': 'Eat Leafy Greens',
            'content': 'Vegetables like spinach and kale help neutralize heavy metals and support liver function.',
            'icon': 'fa-leaf'
        },
        {
            'title': 'Exercise Regularly',
            'content': 'Physical activity helps burn triglycerides and reduce liver fat.',
            'icon': 'fa-running'
        },
        {
            'title': 'Avoid Processed Foods',
            'content': 'High sugar and preservatives in processed foods can strain your liver.',
            'icon': 'fa-hamburger'
        },
        {
            'title': 'Get Vaccinated',
            'content': 'Vaccines for Hepatitis A and B can protect your liver from viral infections.',
            'icon': 'fa-syringe'
        }
    ]
