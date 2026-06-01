"""
LiverWatch Forms — v3.0
========================

Uganda Liver Risk Intelligence Platform
Phase 1: Foundation Reset

New forms added:
  - RegistrationForm     (with consent checkboxes)
  - PasswordResetRequestForm
  - PasswordResetForm
  - RiskAssessmentForm   (single-page, multi-section)
  - CHWPatientForm       (CHW patient registration)

Legacy forms kept for backward compatibility with existing routes:
  - QuestionForm → ForumDiscussionForm
  - AnswerForm
  - SubscriptionForm
  - SearchForm
"""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, DateField, FloatField, IntegerField,
    PasswordField, SelectField, StringField, SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    NumberRange, Optional, ValidationError,
)


# ══════════════════════════════════════════════════════════════════
#  AUTHENTICATION FORMS
# ══════════════════════════════════════════════════════════════════

class LoginForm(FlaskForm):
    username   = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80),
    ])
    password   = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit     = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=80),
    ])
    email = StringField('Email Address', validators=[
        DataRequired(), Email(),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8, message='Password must be at least 8 characters'),
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match'),
    ])

    # Required consents (Uganda DPA 2019 + platform terms)
    consent_data = BooleanField(
        'I consent to LiverWatch collecting and processing my health data '
        'for liver risk screening purposes.',
        validators=[DataRequired(message='Data collection consent is required to use this platform.')],
    )
    consent_terms = BooleanField(
        'I have read and agree to the Terms of Service and Privacy Policy.',
        validators=[DataRequired(message='You must accept the Terms of Service.')],
    )

    submit = SubmitField('Create Account')


class PasswordResetRequestForm(FlaskForm):
    email  = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8),
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match'),
    ])
    submit = SubmitField('Reset Password')


# ══════════════════════════════════════════════════════════════════
#  RISK ASSESSMENT FORM
# ══════════════════════════════════════════════════════════════════

class RiskAssessmentForm(FlaskForm):
    """
    Single-page liver risk assessment form.
    Groups: hepatitis | alcohol | symptoms | medications |
            environmental | nutrition | family_history
    """

    # ── Hepatitis ──────────────────────────────────────────────
    hbsag_positive = BooleanField('I have been told I have Hepatitis B (HBsAg positive)')
    hcv_positive   = BooleanField('I have been told I have Hepatitis C')
    vaccinated_hbv = BooleanField('I have been vaccinated against Hepatitis B')
    hbv_exposure_risk = BooleanField(
        'I may have been exposed to Hepatitis B '
        '(shared needles, unprotected sex, occupational)'
    )
    hbv_family_history = BooleanField('A family member has/had Hepatitis B')

    # ── Alcohol ────────────────────────────────────────────────
    drinks_per_day = FloatField('Average number of standard drinks per day', validators=[
        Optional(), NumberRange(min=0, max=30),
    ])
    years_drinking = IntegerField('For how many years have you been drinking regularly?',
                                  validators=[Optional(), NumberRange(min=0, max=80)])
    binge_drinking = BooleanField('I sometimes have 4+ drinks in one sitting (binge drinking)')

    # ── Symptoms ───────────────────────────────────────────────
    symptom_jaundice         = BooleanField('Yellow skin or eyes (jaundice)')
    symptom_dark_urine       = BooleanField('Dark (cola-coloured) urine')
    symptom_pale_stools      = BooleanField('Pale or clay-coloured stools')
    symptom_fatigue          = BooleanField('Severe, persistent fatigue')
    symptom_abdominal_pain   = BooleanField('Pain in upper right abdomen')
    symptom_swollen_abdomen  = BooleanField('Swollen abdomen (ascites)')
    symptom_nausea           = BooleanField('Nausea or loss of appetite')
    symptom_itching          = BooleanField('Persistent itching without rash')
    symptom_vomiting_blood   = BooleanField('Vomiting blood (EMERGENCY)')
    symptom_confusion        = BooleanField('Confusion or difficulty thinking clearly')
    symptom_bleeding_easily  = BooleanField('Bleeding or bruising easily')

    # ── Medications ────────────────────────────────────────────
    otc_painkillers = BooleanField(
        'I regularly use paracetamol / acetaminophen or other OTC painkillers'
    )
    painkiller_frequency = SelectField(
        'How often do you use OTC painkillers?',
        choices=[
            ('rarely',  'Rarely / occasionally'),
            ('weekly',  'A few times per week'),
            ('daily',   'Daily'),
        ],
        validators=[Optional()],
    )
    tb_treatment   = BooleanField('I am currently on TB treatment (e.g. rifampicin, isoniazid)')
    herbal_remedies = BooleanField('I regularly use herbal or traditional medicines')
    multiple_medications = BooleanField('I take 4 or more different medications regularly')

    # ── Environmental ──────────────────────────────────────────
    aflatoxin_exposure = BooleanField(
        'I often eat stored grains (maize, groundnuts, cassava) that may be '
        'mouldy or discoloured'
    )
    chemical_exposure = BooleanField(
        'I regularly work with agricultural pesticides or industrial chemicals'
    )
    unsafe_water = BooleanField('I sometimes drink unboiled or untreated water')

    # ── Family history ─────────────────────────────────────────
    liver_cancer_family   = BooleanField('A parent or sibling has/had liver cancer')
    cirrhosis_family      = BooleanField('A parent or sibling has/had liver cirrhosis')

    # ── Nutrition ─────────────────────────────────────────────
    bmi = FloatField('Your BMI (if known)', validators=[
        Optional(), NumberRange(min=10, max=80),
    ])
    high_fat_diet   = BooleanField('My diet is mostly fried or processed foods')
    low_water_intake = BooleanField('I drink less than 4 glasses of water per day')
    diabetes        = BooleanField('I have been diagnosed with diabetes or pre-diabetes')

    # ── Consent ───────────────────────────────────────────────
    disclaimer_acknowledged = BooleanField(
        'I understand that this assessment does not provide a medical diagnosis '
        'and I will consult a healthcare professional for any health concerns.',
        validators=[DataRequired(message='You must acknowledge the disclaimer to proceed.')],
    )

    submit = SubmitField('Get My Risk Assessment')


# ══════════════════════════════════════════════════════════════════
#  CHW / PATIENT REGISTRATION FORMS
# ══════════════════════════════════════════════════════════════════

class CHWPatientForm(FlaskForm):
    """Community Health Worker: register a new patient."""
    full_name    = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    age          = IntegerField('Age (years)', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender       = SelectField('Gender', choices=[
        ('male', 'Male'), ('female', 'Female'), ('other', 'Other / Prefer not to say'),
    ])
    district     = StringField('District', validators=[DataRequired(), Length(max=100)])
    sub_county   = StringField('Sub-county', validators=[Optional(), Length(max=100)])
    village      = StringField('Village', validators=[Optional(), Length(max=100)])
    phone_number = StringField('Phone Number (optional)', validators=[Optional(), Length(max=20)])
    consent_given = BooleanField(
        'Patient has given verbal / written informed consent.',
        validators=[DataRequired(message='Patient consent must be recorded.')],
    )
    submit = SubmitField('Register Patient')


# ══════════════════════════════════════════════════════════════════
#  FORUM FORMS  (moderated)
# ══════════════════════════════════════════════════════════════════

class ForumDiscussionForm(FlaskForm):
    """Submit a community discussion (awaits moderation)."""
    title   = StringField('Title', validators=[DataRequired(), Length(min=10, max=200)])
    content = TextAreaField('Your message', validators=[DataRequired(), Length(min=30)])
    discussion_type = SelectField('Discussion type', choices=[
        ('awareness',        'Awareness / personal story'),
        ('experience',       'Sharing my experience'),
        ('education_qa',     'Educational question'),
        ('health_worker_tip', 'Health worker tip'),
    ])
    submit = SubmitField('Submit for Review')

    def validate_content(self, field):
        forbidden = ['diagnose', 'cure', 'definitely have', 'you have']
        lower = field.data.lower()
        for word in forbidden:
            if word in lower:
                raise ValidationError(
                    'Please avoid diagnostic language. '
                    'If you have medical concerns, consult a healthcare professional.'
                )


# Alias for backward compatibility with existing forum blueprint
QuestionForm = ForumDiscussionForm


class ForumReplyForm(FlaskForm):
    content = TextAreaField('Your reply', validators=[DataRequired(), Length(min=10)])
    submit  = SubmitField('Submit Reply')


# Alias
AnswerForm = ForumReplyForm


# ══════════════════════════════════════════════════════════════════
#  MISC / UTILITY FORMS
# ══════════════════════════════════════════════════════════════════

class SubscriptionForm(FlaskForm):
    email  = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')


class SearchForm(FlaskForm):
    query  = StringField('Search', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Search')


class ContactForm(FlaskForm):
    name    = StringField('Name',    validators=[DataRequired(), Length(min=2, max=100)])
    email   = StringField('Email',   validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=20, max=5000)])
    submit  = SubmitField('Send Message')



class SubscriptionForm(FlaskForm):
    """Newsletter subscription form"""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
class SearchForm(FlaskForm):
    query  = StringField('Search', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Search')


class HealthLogForm(FlaskForm):
    """Daily health log entry — linked to LongitudinalRecord."""
    alcohol_intake   = FloatField('Alcohol (units/day)', validators=[Optional()])
    water_intake     = FloatField('Water (litres)',       validators=[Optional()])
    exercise_minutes = IntegerField('Exercise (minutes)', validators=[Optional()])
    sleep_hours      = FloatField('Sleep (hours)',        validators=[Optional()])
    notes            = TextAreaField('Notes',             validators=[Optional(), Length(max=500)])
    submit           = SubmitField('Save Log')
