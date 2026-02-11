"""
API Blueprint
=============

REST API endpoints for LiverWatch.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import cache
from app.models import Post, Question, HealthLog, Recipe, User
from app.services.utils import fetch_medical_news

api_bp = Blueprint('api', __name__)


@api_bp.route('/medical_news')
@cache.cached(timeout=300)
def medical_news():
    """Get medical news articles"""
    news = fetch_medical_news()
    return jsonify({'news': news, 'count': len(news)})


@api_bp.route('/posts')
@cache.cached(timeout=60)
def get_posts():
    """Get published posts"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = Post.query.filter_by(is_published=True)\
                     .order_by(Post.date_posted.desc())\
                     .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'posts': [{
            'id': p.id,
            'title': p.title,
            'excerpt': p.excerpt,
            'image_url': p.image_url,
            'date_posted': p.date_posted.isoformat(),
            'views': p.views
        } for p in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': posts.page
    })


@api_bp.route('/posts/<int:post_id>')
@cache.cached(timeout=60)
def get_post(post_id):
    """Get single post"""
    post = Post.query.get_or_404(post_id)
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'summary': post.summary,
        'image_url': post.image_url,
        'source_url': post.source_url,
        'date_posted': post.date_posted.isoformat(),
        'views': post.views
    })


@api_bp.route('/questions')
def get_questions():
    """Get forum questions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    questions = Question.query.order_by(Question.date_posted.desc())\
                              .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'questions': [{
            'id': q.id,
            'title': q.title,
            'content': q.content[:200] + '...' if len(q.content) > 200 else q.content,
            'author': q.author.username,
            'date_posted': q.date_posted.isoformat(),
            'upvotes': q.upvotes,
            'downvotes': q.downvotes,
            'answer_count': q.answer_count,
            'is_resolved': q.is_resolved,
            'tags': q.tags
        } for q in questions.items],
        'total': questions.total,
        'pages': questions.pages,
        'current_page': questions.page
    })


@api_bp.route('/recipes')
@cache.cached(timeout=300)
def get_recipes():
    """Get recipes"""
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    
    query = Recipe.query
    
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    recipes = query.order_by(Recipe.created_at.desc()).all()
    
    return jsonify({
        'recipes': [{
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'category': r.category,
            'difficulty': r.difficulty,
            'prep_time': r.prep_time,
            'cook_time': r.cook_time,
            'total_time': r.total_time,
            'image_url': r.image_url
        } for r in recipes],
        'count': len(recipes)
    })


@api_bp.route('/recipes/<int:recipe_id>')
@cache.cached(timeout=300)
def get_recipe(recipe_id):
    """Get single recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'description': recipe.description,
        'ingredients': recipe.ingredients,
        'instructions': recipe.instructions,
        'prep_time': recipe.prep_time,
        'cook_time': recipe.cook_time,
        'servings': recipe.servings,
        'nutritional_benefits': recipe.nutritional_benefits,
        'category': recipe.category,
        'difficulty': recipe.difficulty,
        'image_url': recipe.image_url
    })


@api_bp.route('/health/stats')
@login_required
def health_stats():
    """Get user's health statistics"""
    from app.blueprints.health import calculate_health_stats
    
    days = request.args.get('days', 30, type=int)
    stats = calculate_health_stats(current_user.id, days)
    
    if not stats:
        return jsonify({'error': 'No health data found'}), 404
    
    return jsonify(stats)


@api_bp.route('/community/stats')
@cache.cached(timeout=300)
def community_stats():
    """Get community statistics"""
    from sqlalchemy import func
    
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_questions = Question.query.count()
    
    # Get average health metrics (anonymized)
    avg_stats = HealthLog.query.with_entities(
        func.avg(HealthLog.water_intake).label('avg_water'),
        func.avg(HealthLog.exercise_level).label('avg_exercise'),
        func.avg(HealthLog.alcohol_intake).label('avg_alcohol')
    ).first()
    
    return jsonify({
        'total_users': total_users,
        'total_posts': total_posts,
        'total_questions': total_questions,
        'community_averages': {
            'water_intake': round(avg_stats.avg_water or 0, 2),
            'exercise': round(avg_stats.avg_exercise or 0, 2),
            'alcohol': round(avg_stats.avg_alcohol or 0, 2)
        }
    })


@api_bp.route('/search')
def search():
    """Global search endpoint"""
    q = request.args.get('q', '')
    
    if len(q) < 2:
        return jsonify({'error': 'Search query too short'}), 400
    
    # Search posts
    posts = Post.query.filter(
        Post.is_published == True,
        (Post.title.ilike(f'%{q}%')) | (Post.content.ilike(f'%{q}%'))
    ).limit(5).all()
    
    # Search questions
    questions = Question.query.filter(
        (Question.title.ilike(f'%{q}%')) | (Question.content.ilike(f'%{q}%'))
    ).limit(5).all()
    
    # Search recipes
    recipes = Recipe.query.filter(
        (Recipe.title.ilike(f'%{q}%')) | (Recipe.ingredients.ilike(f'%{q}%'))
    ).limit(5).all()
    
    return jsonify({
        'posts': [{'id': p.id, 'title': p.title, 'type': 'post'} for p in posts],
        'questions': [{'id': q.id, 'title': q.title, 'type': 'question'} for q in questions],
        'recipes': [{'id': r.id, 'title': r.title, 'type': 'recipe'} for r in recipes]
    })
