"""
Admin Blueprint
===============

Admin dashboard and content management routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db, mail
from app.models import Post, Subscriber, User, Recipe
from app.forms import PostForm, RecipeForm
from app.services.scraper import scrape_single_article
from flask_mail import Message
import jwt
from datetime import datetime, timedelta
from flask import current_app

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            flash('Access token required.', 'error')
            return redirect(url_for('main.index'))
        try:
            jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            flash('Token has expired.', 'error')
            return redirect(url_for('main.index'))
        except jwt.InvalidTokenError:
            flash('Invalid token.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@token_required
def dashboard():
    """Admin dashboard"""
    stats = {
        'total_posts': Post.query.count(),
        'total_users': User.query.count(),
        'total_subscribers': Subscriber.query.filter_by(is_active=True).count(),
        'total_recipes': Recipe.query.count()
    }
    
    recent_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          stats=stats,
                          recent_posts=recent_posts,
                          recent_users=recent_users)


@admin_bp.route('/posts')
@token_required
def posts():
    """Manage posts"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('admin/posts.html', posts=posts)


@admin_bp.route('/post/new', methods=['GET', 'POST'])
@token_required
def new_post():
    """Create new post"""
    form = PostForm()
    
    if form.validate_on_submit():
        # Check if source URL provided for scraping
        if form.source_url.data:
            scraped = scrape_single_article(form.source_url.data)
            if scraped:
                form.title.data = scraped.get('title') or form.title.data
                form.content.data = scraped.get('content') or form.content.data
                form.image_url.data = scraped.get('image_url') or form.image_url.data
        
        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            image_url=form.image_url.data,
            source_url=form.source_url.data,
            is_published=form.is_published.data
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Notify subscribers if published
        if post.is_published:
            notify_subscribers(post)
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.posts', token=request.args.get('token')))
    
    return render_template('admin/post_form.html', form=form, title='New Post')


@admin_bp.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(post_id):
    """Edit existing post"""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    
    if form.validate_on_submit():
        was_published = post.is_published
        
        post.title = form.title.data
        post.content = form.content.data
        post.summary = form.summary.data
        post.image_url = form.image_url.data
        post.source_url = form.source_url.data
        post.is_published = form.is_published.data
        
        db.session.commit()
        
        # Notify if newly published
        if not was_published and post.is_published:
            notify_subscribers(post)
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.posts', token=request.args.get('token')))
    
    return render_template('admin/post_form.html', form=form, title='Edit Post', post=post)


@admin_bp.route('/post/delete/<int:post_id>')
@token_required
def delete_post(post_id):
    """Delete post"""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.posts', token=request.args.get('token')))


@admin_bp.route('/users')
@token_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/subscribers')
@token_required
def subscribers():
    """Manage subscribers"""
    page = request.args.get('page', 1, type=int)
    subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/subscribers.html', subscribers=subscribers)


@admin_bp.route('/recipes')
@token_required
def recipes():
    """Manage recipes"""
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/recipes.html', recipes=recipes)


@admin_bp.route('/recipe/new', methods=['GET', 'POST'])
@token_required
def new_recipe():
    """Create new recipe"""
    form = RecipeForm()
    
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            prep_time=form.prep_time.data,
            cook_time=form.cook_time.data,
            servings=form.servings.data,
            nutritional_benefits=form.nutritional_benefits.data,
            image_url=form.image_url.data,
            category=form.category.data,
            difficulty=form.difficulty.data
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        flash('Recipe created successfully!', 'success')
        return redirect(url_for('admin.recipes', token=request.args.get('token')))
    
    return render_template('admin/recipe_form.html', form=form, title='New Recipe')


@admin_bp.route('/token')
def get_token():
    """Generate admin access token"""
    token = jwt.encode({
        'user': 'admin',
        'exp': datetime.utcnow() + timedelta(hours=2)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    return {'token': token}


def notify_subscribers(post):
    """Send email notification to all active subscribers"""
    subscribers = Subscriber.query.filter_by(is_active=True).all()
    
    for subscriber in subscribers:
        try:
            msg = Message(
                f"New Article: {post.title}",
                recipients=[subscriber.email]
            )
            msg.html = f"""
            <h2>{post.title}</h2>
            <p>{post.excerpt}</p>
            <p><a href="{url_for('main.post_detail', post_id=post.id, _external=True)}">Read More</a></p>
            <hr>
            <p><small><a href="{url_for('main.unsubscribe', email=subscriber.email, _external=True)}">Unsubscribe</a></small></p>
            """
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email to {subscriber.email}: {e}")
