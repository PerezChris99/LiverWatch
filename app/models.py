"""
LiverWatch Database Models
==========================

SQLAlchemy models for the LiverWatch application.
"""

from datetime import datetime
import pytz
from flask_login import UserMixin
from app import db


class User(db.Model, UserMixin):
    """User model for authentication and profile management"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    questions = db.relationship('Question', backref='author', lazy='dynamic')
    answers = db.relationship('Answer', backref='author', lazy='dynamic')
    health_logs = db.relationship('HealthLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Post(db.Model):
    """Blog post model for medical articles"""
    
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    source_url = db.Column(db.String(500), unique=True)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), index=True)
    is_published = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    @property
    def excerpt(self):
        """Return a short excerpt of the content"""
        return self.content[:200] + '...' if len(self.content) > 200 else self.content


class Subscriber(db.Model):
    """Newsletter subscriber model"""
    
    __tablename__ = 'subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Subscriber {self.email}>'


class Question(db.Model):
    """Forum question model"""
    
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.Column(db.String(200))
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    is_resolved = db.Column(db.Boolean, default=False)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.title}>'
    
    @property
    def score(self):
        """Calculate the net score"""
        return self.upvotes - self.downvotes
    
    @property
    def answer_count(self):
        """Get the number of answers"""
        return self.answers.count()


class Answer(db.Model):
    """Forum answer model"""
    
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    is_accepted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Answer {self.id}>'
    
    @property
    def score(self):
        """Calculate the net score"""
        return self.upvotes - self.downvotes


class HealthLog(db.Model):
    """User health log for tracking habits"""
    
    __tablename__ = 'health_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc), index=True)
    
    # Consumption metrics
    alcohol_intake = db.Column(db.Integer, nullable=True)  # units
    fatty_foods = db.Column(db.Integer, nullable=True)     # servings
    sugar_intake = db.Column(db.Integer, nullable=True)    # grams
    water_intake = db.Column(db.Float, nullable=True)      # liters
    
    # Activity metrics
    exercise_level = db.Column(db.Integer, nullable=True)  # minutes
    sleep_hours = db.Column(db.Float, nullable=True)       # hours
    
    # Health metrics
    medication_usage = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # User relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<HealthLog {self.date} - User {self.user_id}>'


class Recipe(db.Model):
    """Liver-friendly recipe model"""
    
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)  # minutes
    cook_time = db.Column(db.Integer)  # minutes
    servings = db.Column(db.Integer)
    nutritional_benefits = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(50))  # breakfast, lunch, dinner, snack
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    def __repr__(self):
        return f'<Recipe {self.title}>'
    
    @property
    def total_time(self):
        """Calculate total preparation time"""
        prep = self.prep_time or 0
        cook = self.cook_time or 0
        return prep + cook


class Notification(db.Model):
    """User notification model"""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, warning, success, error
    action_url = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Notification {self.title}>'
