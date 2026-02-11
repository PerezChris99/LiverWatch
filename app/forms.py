"""
LiverWatch Forms
================

WTForms for the LiverWatch application.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, IntegerField, 
    FloatField, DateField, SelectField, BooleanField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, EqualTo, 
    NumberRange, ValidationError
)


class SubscriptionForm(FlaskForm):
    """Newsletter subscription form"""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    submit = SubmitField('Subscribe')


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')


class QuestionForm(FlaskForm):
    """Forum question form"""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=10, max=200, message='Title must be between 10 and 200 characters')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required'),
        Length(min=20, message='Please provide more detail (minimum 20 characters)')
    ])
    tags = StringField('Tags', validators=[
        Optional(),
        Length(max=200, message='Tags must be less than 200 characters')
    ])
    submit = SubmitField('Post Question')


class AnswerForm(FlaskForm):
    """Forum answer form"""
    content = TextAreaField('Your Answer', validators=[
        DataRequired(message='Answer content is required'),
        Length(min=10, message='Please provide a more detailed answer (minimum 10 characters)')
    ])
    submit = SubmitField('Post Answer')


class HealthLogForm(FlaskForm):
    """Health log entry form"""
    date = DateField('Date', validators=[
        DataRequired(message='Date is required')
    ])
    alcohol_intake = IntegerField('Alcohol Intake (units)', validators=[
        Optional(),
        NumberRange(min=0, max=50, message='Please enter a value between 0 and 50')
    ])
    fatty_foods = IntegerField('Fatty Foods (servings)', validators=[
        Optional(),
        NumberRange(min=0, max=20, message='Please enter a value between 0 and 20')
    ])
    sugar_intake = IntegerField('Sugar Intake (grams)', validators=[
        Optional(),
        NumberRange(min=0, max=500, message='Please enter a value between 0 and 500')
    ])
    water_intake = FloatField('Water Intake (liters)', validators=[
        Optional(),
        NumberRange(min=0, max=10, message='Please enter a value between 0 and 10')
    ])
    exercise_level = IntegerField('Exercise (minutes)', validators=[
        Optional(),
        NumberRange(min=0, max=480, message='Please enter a value between 0 and 480')
    ])
    sleep_hours = FloatField('Sleep (hours)', validators=[
        Optional(),
        NumberRange(min=0, max=24, message='Please enter a value between 0 and 24')
    ])
    medication_usage = StringField('Medication Usage', validators=[
        Optional(),
        Length(max=200, message='Must be less than 200 characters')
    ])
    notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=1000, message='Notes must be less than 1000 characters')
    ])
    submit = SubmitField('Save Log')


class PostForm(FlaskForm):
    """Blog post form for admin"""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required')
    ])
    summary = TextAreaField('Summary', validators=[
        Optional(),
        Length(max=500, message='Summary must be less than 500 characters')
    ])
    image_url = StringField('Image URL', validators=[
        Optional(),
        Length(max=500, message='URL must be less than 500 characters')
    ])
    source_url = StringField('Source URL', validators=[
        Optional(),
        Length(max=500, message='URL must be less than 500 characters')
    ])
    is_published = BooleanField('Publish')
    submit = SubmitField('Save Post')


class RecipeForm(FlaskForm):
    """Recipe form for admin"""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    ingredients = TextAreaField('Ingredients', validators=[
        DataRequired(message='Ingredients are required')
    ])
    instructions = TextAreaField('Instructions', validators=[
        DataRequired(message='Instructions are required')
    ])
    prep_time = IntegerField('Prep Time (minutes)', validators=[Optional()])
    cook_time = IntegerField('Cook Time (minutes)', validators=[Optional()])
    servings = IntegerField('Servings', validators=[Optional()])
    nutritional_benefits = TextAreaField('Nutritional Benefits', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('beverage', 'Beverage')
    ])
    difficulty = SelectField('Difficulty', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    submit = SubmitField('Save Recipe')


class SearchForm(FlaskForm):
    """Search form"""
    query = StringField('Search', validators=[
        DataRequired(message='Please enter a search term'),
        Length(min=2, max=100, message='Search term must be between 2 and 100 characters')
    ])
    submit = SubmitField('Search')


class ContactForm(FlaskForm):
    """Contact form"""
    name = StringField('Name', validators=[
        DataRequired(message='Name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    subject = StringField('Subject', validators=[
        DataRequired(message='Subject is required'),
        Length(min=5, max=200, message='Subject must be between 5 and 200 characters')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(message='Message is required'),
        Length(min=20, max=5000, message='Message must be between 20 and 5000 characters')
    ])
    submit = SubmitField('Send Message')
