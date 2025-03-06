from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Optional

class SubscriptionForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post Question')

class AnswerForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post Answer')

class HealthLogForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    alcohol_intake = IntegerField('Alcohol Intake', validators=[Optional()])
    fatty_foods = IntegerField('Fatty Foods', validators=[Optional()])
    sugar_intake = IntegerField('Sugar Intake', validators=[Optional()])
    water_intake = IntegerField('Water Intake', validators=[Optional()])
    exercise_level = IntegerField('Exercise Level', validators=[Optional()])
    medication_usage = StringField('Medication Usage', validators=[Optional()])
    submit = SubmitField('Log Health Data')
