from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"Subscriber('{self.email}')"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('questions', lazy=True))
    tags = db.Column(db.String(100))  # Ensure this column is defined
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"Question('{self.title}', '{self.date_posted}')"

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))
    user = db.relationship('User', backref=db.backref('answers', lazy=True))
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"Answer('{self.content}', '{self.date_posted}')"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class HealthLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    alcohol_intake = db.Column(db.Integer, nullable=True)
    fatty_foods = db.Column(db.Integer, nullable=True)
    sugar_intake = db.Column(db.Integer, nullable=True)
    water_intake = db.Column(db.Integer, nullable=True)
    exercise_level = db.Column(db.Integer, nullable=True)
    medication_usage = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('health_logs', lazy=True))

    def __repr__(self):
        return f"HealthLog('{self.date}', '{self.user_id}')"

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    nutritional_benefits = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"Recipe('{self.title}')"
