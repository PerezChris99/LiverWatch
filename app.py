from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from functools import wraps
import jwt
import datetime
from config import Config
from models import db, Post, Subscriber, Question, Answer, User, HealthLog, Recipe
from forms import SubscriptionForm, QuestionForm, AnswerForm, HealthLogForm
from utils import scrape_data, fetch_nearby_liver_specialists, fetch_medical_news
import pytz
import ipinfo
from timezonefinder import TimezoneFinder

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
limiter = Limiter(key_func=get_remote_address, default_limits=["2000 per day", "50 per hour"])
limiter.init_app(app)

# Exclude static files from rate limiting
limiter.limit("200 per day", exempt_when=lambda: request.path.startswith('/static'))

# Create database tables
with app.app_context():
    db.create_all()

# JWT Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return {'message': 'Token is missing!'}, 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return {'message': 'Token is invalid!'}, 403
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_timezone():
    def get_timezone():
        access_token = 'your_ipinfo_access_token'  # Replace with your ipinfo access token
        handler = ipinfo.getHandler(access_token)
        ip_address = request.remote_addr
        details = handler.getDetails(ip_address)
        if details and 'latitude' in details.all and 'longitude' in details.all:
            latitude = details.latitude
            longitude = details.longitude
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
            if timezone_str:
                return pytz.timezone(timezone_str)
        return pytz.utc
    return dict(get_timezone=get_timezone)

# Custom filter for strftime
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d'
    return date.strftime(fmt)

@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    form = SubscriptionForm()
    if form.validate_on_submit():
        email = form.email.data
        new_subscriber = Subscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()
        # Send confirmation email
        msg = Message("Subscription Confirmation", sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
        msg.body = "Thank you for subscribing to our newsletter!"
        mail.send(msg)
        return 'Subscribed!'
    return render_template('subscribe.html', form=form)

@app.route('/admin')
@token_required
def admin():
    posts = Post.query.all()
    return render_template('admin.html', posts=posts)

@app.route('/admin/post/new', methods=['GET', 'POST'])
@token_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content_url = request.form['content']
        # Scrape data and create post
        scraped_data = scrape_data(content_url)
        if scraped_data:
            new_post = Post(
                title=scraped_data['title'],
                content=scraped_data['content'],
                image_url=scraped_data['image_url'],
                source_url=content_url
            )
            db.session.add(new_post)
            db.session.commit()
            # Send email to subscribers
            with app.app_context():
                subscribers = Subscriber.query.all()
                for subscriber in subscribers:
                    msg = Message("New Post Alert", sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[subscriber.email])
                    msg.body = f"A new post '{title}' has been added to our blog!"
                    mail.send(msg)
            return redirect(url_for('admin'))
        else:
            return "Scraping failed."
    return render_template('new_post.html')

@app.route('/admin/post/edit/<int:post_id>', methods=['GET', 'POST'])
@token_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_post.html', post=post)

@app.route('/admin/post/delete/<int:post_id>')
@token_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/login')
@limiter.limit("5 per minute")
def login():
    token = jwt.encode({
        'user': 'admin',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return token

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    form = QuestionForm()
    if form.validate_on_submit():
        # For simplicity, assume a default user
        user = User.query.first()
        if not user:
            user = User(username='default_user', email='default@example.com')
            db.session.add(user)
            db.session.commit()
        question = Question(title=form.title.data, content=form.content.data, user=user)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('forum'))
    questions = Question.query.all()
    return render_template('forum.html', form=form, questions=questions)

@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question_detail(question_id):
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    if form.validate_on_submit():
        # For simplicity, assume a default user
        user = User.query.first()
        if not user:
            user = User(username='default_user', email='default@example.com')
            db.session.add(user)
            db.session.commit()
        answer = Answer(content=form.content.data, question=question, user=user)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('question_detail', question_id=question_id))
    return render_template('question_detail.html', question=question, form=form)

@app.route('/health_tracker', methods=['GET', 'POST'])
def health_tracker():
    form = HealthLogForm()
    if form.validate_on_submit():
        # For simplicity, assume a default user
        user = User.query.first()
        if not user:
            user = User(username='default_user', email='default@example.com')
            db.session.add(user)
            db.session.commit()
        health_log = HealthLog(
            date=form.date.data,
            alcohol_intake=form.alcohol_intake.data,
            fatty_foods=form.fatty_foods.data,
            sugar_intake=form.sugar_intake.data,
            water_intake=form.water_intake.data,
            exercise_level=form.exercise_level.data,
            medication_usage=form.medication_usage.data,
            user=user
        )
        db.session.add(health_log)
        db.session.commit()
        return redirect(url_for('health_tracker'))
    health_logs = HealthLog.query.all()
    return render_template('health_tracker.html', form=form, health_logs=health_logs)

@app.route('/diet_suggestions')
def diet_suggestions():
    recipes = Recipe.query.all()
    return render_template('diet_suggestions.html', recipes=recipes)

@app.route('/appointment_finder')
def appointment_finder():
    location = request.args.get('location', 'New York')  # Default location
    specialists = fetch_nearby_liver_specialists(location)
    return render_template('appointment_finder.html', specialists=specialists)

@app.route('/medical_news')
def medical_news():
    news = fetch_medical_news()
    return render_template('medical_news.html', news=news)

@app.route('/medical_news/<int:news_id>')
def medical_news_detail(news_id):
    news = fetch_medical_news()
    article = news[news_id]
    return render_template('medical_news_detail.html', article=article)

@app.route('/api/medical_news')
@cache.cached(timeout=300)
def api_medical_news():
    news = fetch_medical_news()
    return {'news': news}

@app.route('/child_health')
def child_health():
    return render_template('child_health.html')

def fetch_nearby_liver_specialists(location):
    api_key = get_google_maps_api_key()
    if not api_key:
        print("Google Maps API key not set.")
        return []

    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=10000&type=hospital&keyword=liver%20specialist&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching nearby specialists: {e}")
        return []

if __name__ == '__main__':
    app.run(debug=True)
