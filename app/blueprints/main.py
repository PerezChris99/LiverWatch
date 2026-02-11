"""
Main Blueprint
==============

Main routes for LiverWatch - homepage, posts, subscriptions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app import db, mail
from app.models import Post, Subscriber, Recipe
from app.forms import SubscriptionForm
from flask_mail import Message

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with latest posts and features"""
    posts = Post.query.filter_by(is_published=True).order_by(Post.date_posted.desc()).limit(6).all()
    form = SubscriptionForm()
    return render_template('index.html', posts=posts, form=form)


@main_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """Individual post detail page"""
    post = Post.query.get_or_404(post_id)
    
    # Increment view count
    post.views += 1
    db.session.commit()
    
    # Get related posts
    related_posts = Post.query.filter(
        Post.id != post_id,
        Post.is_published == True
    ).order_by(Post.date_posted.desc()).limit(3).all()
    
    return render_template('post_detail.html', post=post, related_posts=related_posts)


@main_bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Newsletter subscription"""
    form = SubscriptionForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = Subscriber.query.filter_by(email=email).first()
        
        if existing:
            if existing.is_active:
                flash('This email is already subscribed.', 'warning')
            else:
                # Reactivate subscription
                existing.is_active = True
                db.session.commit()
                flash('Your subscription has been reactivated!', 'success')
        else:
            # New subscriber
            subscriber = Subscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            
            # Send confirmation email
            try:
                msg = Message(
                    "Welcome to LiverWatch!",
                    recipients=[email]
                )
                msg.html = render_template('emails/subscription_confirmation.html', email=email)
                mail.send(msg)
            except Exception as e:
                print(f"Email error: {e}")
            
            flash('Successfully subscribed! Check your email for confirmation.', 'success')
        
        return redirect(url_for('main.index'))
    
    return render_template('subscribe.html', form=form)


@main_bp.route('/unsubscribe')
def unsubscribe():
    """Unsubscribe from newsletter"""
    email = request.args.get('email', '').lower().strip()
    
    if not email:
        flash('Invalid unsubscribe request.', 'error')
        return redirect(url_for('main.index'))
    
    subscriber = Subscriber.query.filter_by(email=email).first()
    
    if subscriber:
        subscriber.is_active = False
        db.session.commit()
        flash('You have been unsubscribed successfully.', 'success')
    else:
        flash('Email not found in our subscription list.', 'warning')
    
    return redirect(url_for('main.index'))


@main_bp.route('/recipes')
def recipes():
    """Liver-friendly recipes page"""
    category = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    
    query = Recipe.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)
    
    recipes = query.order_by(Recipe.created_at.desc()).all()
    
    return render_template('recipes.html', 
                          recipes=recipes, 
                          current_category=category,
                          current_difficulty=difficulty)


@main_bp.route('/child-health')
def child_health():
    """Child health information page"""
    return render_template('child_health.html')


@main_bp.route('/survival-rates')
def survival_rates():
    """Liver disease survival rates information"""
    return render_template('survival_rates.html')


@main_bp.route('/diet-suggestions')
def diet_suggestions():
    """Diet suggestions for liver health"""
    return render_template('diet_suggestions.html')


@main_bp.route('/medical-news')
def medical_news():
    """Medical news listing page"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_published=True)\
                     .order_by(Post.date_posted.desc())\
                     .paginate(page=page, per_page=12)
    return render_template('medical_news.html', posts=posts)


@main_bp.route('/medical-news/<int:id>')
def medical_news_detail(id):
    """Medical news detail page"""
    post = Post.query.get_or_404(id)
    post.views += 1
    db.session.commit()
    return render_template('medical_news_detail.html', post=post)


@main_bp.route('/appointment-finder')
def appointment_finder():
    """Find healthcare facilities"""
    return render_template('appointment_finder.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


@main_bp.route('/scrape')
def scrape_and_show():
    """Trigger article scraping"""
    from app.services.scraper import scrape_medical_news
    
    articles = scrape_medical_news()
    count = 0
    
    for article_data in articles:
        existing = Post.query.filter_by(source_url=article_data.get('link')).first()
        if not existing and article_data.get('link'):
            post = Post(
                title=article_data.get('title', 'Untitled'),
                content=article_data.get('summary', ''),
                source_url=article_data.get('link'),
                image_url=article_data.get('image_url')
            )
            db.session.add(post)
            count += 1
    
    db.session.commit()
    
    if count > 0:
        flash(f'Successfully scraped {count} new articles!', 'success')
    else:
        flash('No new articles found.', 'info')
    
    return redirect(url_for('main.index'))


@main_bp.route('/ai-assistant')
def ai_assistant():
    """AI Health Assistant chat interface"""
    return render_template('ai_assistant.html')


@main_bp.route('/liver-3d')
def liver_3d():
    """Interactive 3D liver visualization"""
    return render_template('liver_3d.html')
