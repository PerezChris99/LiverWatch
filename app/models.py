"""
LiverWatch Database Models — v3.0
==================================

Uganda Liver Risk Intelligence Platform
Phase 1: Foundation Reset

All models are rebuilt around the core mission:
  liver risk screening · community health · referral · monitoring · research

IMPORTANT: This platform does NOT diagnose diseases.
           Models store risk patterns and screening data only.
"""

import enum
import json
import secrets
import string
from datetime import datetime

import pytz
from flask_login import UserMixin
from app import db


# ── helpers ────────────────────────────────────────────────────────────────

def utcnow():
    return datetime.now(pytz.utc)


def generate_code(prefix: str, length: int = 8) -> str:
    """Generate a human-readable unique code, e.g. LW-A3F9KZ."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}-{suffix}"


# ── enumerations ───────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    PATIENT    = 'patient'
    CHW        = 'chw'         # Community Health Worker / VHT
    CLINICIAN  = 'clinician'
    ADMIN      = 'admin'
    RESEARCHER = 'researcher'
    NGO        = 'ngo'


class RiskLevel(str, enum.Enum):
    MINIMAL  = 'minimal'
    LOW      = 'low'
    MODERATE = 'moderate'
    HIGH     = 'high'
    URGENT   = 'urgent'
    CRITICAL = 'critical'


class ReferralStatus(str, enum.Enum):
    PENDING       = 'pending'
    SENT          = 'sent'
    ACKNOWLEDGED  = 'acknowledged'
    COMPLETED     = 'completed'
    CANCELLED     = 'cancelled'


class DiscussionStatus(str, enum.Enum):
    PENDING_REVIEW = 'pending_review'
    APPROVED       = 'approved'
    REJECTED       = 'rejected'
    FLAGGED        = 'flagged'


class DeviceStatus(str, enum.Enum):
    ACTIVE      = 'active'
    INACTIVE    = 'inactive'
    CALIBRATING = 'calibrating'
    ERROR       = 'error'


class MeasurementValidationState(str, enum.Enum):
    PENDING = 'pending'
    VALIDATED = 'validated'
    REJECTED = 'rejected'
    CORRECTED = 'corrected'


class MeasurementSource(str, enum.Enum):
    PATIENT = 'patient'
    CHW = 'chw'
    CLINICIAN = 'clinician'
    LABORATORY = 'laboratory'
    DEVICE = 'device'
    RESEARCH = 'research'


class BiomarkerType(str, enum.Enum):
    AMMONIA            = 'ammonia'
    HYDRATION          = 'hydration'
    PH                 = 'ph'
    ALCOHOL_METABOLITE = 'alcohol_metabolite'
    SODIUM             = 'sodium'
    POTASSIUM          = 'potassium'
    STRESS             = 'stress'
    ALT                = 'ALT'
    AST                = 'AST'
    ALP                = 'ALP'
    GGT                = 'GGT'
    BILIRUBIN_TOTAL    = 'bilirubin_total'
    ALBUMIN            = 'albumin'
    INR                = 'INR'


# ═══════════════════════════════════════════════════════════════════════════
#  1. USER & AUTH MODELS
# ═══════════════════════════════════════════════════════════════════════════

class User(db.Model, UserMixin):
    """Core user account with role-based access."""

    __tablename__ = 'users'

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email    = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False,
                     default=UserRole.PATIENT.value, index=True)

    # Email verification
    email_verified    = db.Column(db.Boolean,  default=False)
    email_verified_at = db.Column(db.DateTime, nullable=True)

    # Consent (required before accessing health features)
    consent_given = db.Column(db.Boolean,  default=False)
    consent_date  = db.Column(db.DateTime, nullable=True)

    # Profile
    full_name          = db.Column(db.String(200), nullable=True)
    preferred_language = db.Column(db.String(5),   default='en')   # 'en' | 'lg' | 'sw'
    district           = db.Column(db.String(100), nullable=True)
    phone_number       = db.Column(db.String(20),  nullable=True)

    # Status & tracking
    is_active         = db.Column(db.Boolean,  default=True)
    is_admin          = db.Column(db.Boolean,  default=False)   # backward-compat shortcut
    last_login_at     = db.Column(db.DateTime, nullable=True)
    last_activity_at  = db.Column(db.DateTime, nullable=True)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until      = db.Column(db.DateTime, nullable=True)

    # Soft-delete
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # ── relationships ───
    consents             = db.relationship('UserConsent',          backref='user',   lazy='dynamic')
    password_resets      = db.relationship('PasswordResetToken',   backref='user',   lazy='dynamic')
    email_verifications  = db.relationship('EmailVerificationToken', backref='user', lazy='dynamic')
    audit_logs           = db.relationship('AuditLog',             foreign_keys='AuditLog.user_id',
                                           backref='user', lazy='dynamic')
    risk_assessments     = db.relationship('RiskAssessment',       foreign_keys='RiskAssessment.user_id',
                                           backref='user', lazy='dynamic')
    longitudinal_records = db.relationship('LongitudinalRecord',   backref='user',   lazy='dynamic')
    wearable_devices     = db.relationship('WearableDevice',       backref='user',   lazy='dynamic')
    notifications        = db.relationship('Notification',         backref='user',   lazy='dynamic')
    forum_posts          = db.relationship('ForumDiscussion',      foreign_keys='ForumDiscussion.user_id',
                                           backref='author', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username!r} role={self.role}>'

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = utcnow()
        self.is_active  = False

    @property
    def is_locked(self):
        if not self.locked_until:
            return False
        lu = self.locked_until
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=pytz.utc)
        return datetime.now(pytz.utc) < lu


class UserConsent(db.Model):
    """Explicit, auditable consent records (Uganda DPA 2019 compliance)."""

    __tablename__ = 'user_consents'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'consent_type', name='uq_user_consent_type'),
    )

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    consent_type = db.Column(db.String(50), nullable=False)
    # types: 'data_collection' | 'ai_processing' | 'research' | 'contact' | 'terms'

    given     = db.Column(db.Boolean,  default=False)
    given_at  = db.Column(db.DateTime, default=utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    ip_address = db.Column(db.String(45),  nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<UserConsent {self.consent_type}: {self.given}>'


class PasswordResetToken(db.Model):
    """Secure time-limited password reset tokens (stored as SHA-256 hash)."""

    __tablename__ = 'password_reset_tokens'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at    = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    @property
    def is_expired(self):
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=pytz.utc)
        return datetime.now(pytz.utc) > exp

    @property
    def is_valid(self):
        return not self.is_expired and self.used_at is None


class EmailVerificationToken(db.Model):
    """Email address verification tokens."""

    __tablename__ = 'email_verification_tokens'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash  = db.Column(db.String(64), nullable=False, unique=True)
    expires_at  = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=utcnow)

    @property
    def is_valid(self):
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=pytz.utc)
        return self.verified_at is None and datetime.now(pytz.utc) < exp


class AuditLog(db.Model):
    """Immutable audit trail for all sensitive operations."""

    __tablename__ = 'audit_logs'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action        = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50),  nullable=True)
    resource_id   = db.Column(db.Integer,     nullable=True)
    details       = db.Column(db.Text,        nullable=True)   # JSON blob
    ip_address    = db.Column(db.String(45),  nullable=True)
    user_agent    = db.Column(db.String(500), nullable=True)
    created_at    = db.Column(db.DateTime, default=utcnow, index=True)

    def get_details(self) -> dict:
        try:
            return json.loads(self.details) if self.details else {}
        except (ValueError, TypeError):
            return {}

    def set_details(self, data: dict):
        self.details = json.dumps(data)


# ═══════════════════════════════════════════════════════════════════════════
#  2. HEALTHCARE FACILITY DIRECTORY
#     (defined early — referenced by Referral)
# ═══════════════════════════════════════════════════════════════════════════

class HealthcareFacility(db.Model):
    """Ugandan liver/hepatitis treatment facilities and referral points."""

    __tablename__ = 'healthcare_facilities'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(200), nullable=False)
    facility_type = db.Column(db.String(50),  nullable=False)
    # types: 'hospital' | 'health_center' | 'clinic' | 'specialist_center'

    district   = db.Column(db.String(100), nullable=False, index=True)
    sub_county = db.Column(db.String(100), nullable=True)
    address    = db.Column(db.String(500), nullable=True)

    phone_number = db.Column(db.String(20),  nullable=True)
    email        = db.Column(db.String(120), nullable=True)

    latitude  = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    services           = db.Column(db.Text, nullable=True)   # JSON list of services
    hepatitis_treatment = db.Column(db.Boolean, default=False)
    liver_specialist    = db.Column(db.Boolean, default=False)
    operating_hours    = db.Column(db.String(200), nullable=True)

    is_verified = db.Column(db.Boolean, default=False)
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=utcnow)
    updated_at  = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    referrals = db.relationship('Referral', backref='facility', lazy='dynamic')

    def get_services(self) -> list:
        try:
            return json.loads(self.services) if self.services else []
        except (ValueError, TypeError):
            return []

    def __repr__(self):
        return f'<HealthcareFacility {self.name!r} {self.district}>'


# ═══════════════════════════════════════════════════════════════════════════
#  3. COMMUNITY HEALTH WORKER MODELS
# ═══════════════════════════════════════════════════════════════════════════

class HealthWorker(db.Model):
    """Community Health Worker (VHT / NGO outreach) profile."""

    __tablename__ = 'health_workers'

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    worker_id    = db.Column(db.String(50),  unique=True, nullable=False)   # Official CHW ID
    full_name    = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    program      = db.Column(db.String(200), nullable=True)

    district    = db.Column(db.String(100), nullable=False)
    sub_county  = db.Column(db.String(100), nullable=True)
    village     = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    training_date  = db.Column(db.Date,    nullable=True)
    is_verified    = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at    = db.Column(db.DateTime, nullable=True)

    is_active  = db.Column(db.Boolean,  default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    user        = db.relationship('User', foreign_keys=[user_id], backref='health_worker_profile')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])
    patients    = db.relationship('Patient',        backref='registered_by_worker', lazy='dynamic')
    screening_events = db.relationship('ScreeningEvent', backref='organizer', lazy='dynamic')

    def __repr__(self):
        return f'<HealthWorker {self.worker_id} {self.full_name!r}>'


class Patient(db.Model):
    """CHW-registered patient (may not have a User account — offline/rural)."""

    __tablename__ = 'patients'

    id                 = db.Column(db.Integer, primary_key=True)
    registered_by_id   = db.Column(db.Integer, db.ForeignKey('health_workers.id'),
                                   nullable=False, index=True)
    patient_code       = db.Column(db.String(20), unique=True, nullable=False)

    # PII stored encrypted — use EncryptionService to read/write
    full_name_encrypted   = db.Column(db.Text, nullable=True)
    phone_number_encrypted = db.Column(db.Text, nullable=True)

    age    = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)   # 'male' | 'female' | 'other'

    district   = db.Column(db.String(100), nullable=True)
    sub_county = db.Column(db.String(100), nullable=True)
    village    = db.Column(db.String(100), nullable=True)

    consent_given = db.Column(db.Boolean,  default=False)
    consent_date  = db.Column(db.DateTime, nullable=True)

    is_active  = db.Column(db.Boolean,  default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    risk_assessments  = db.relationship('RiskAssessment',  foreign_keys='RiskAssessment.patient_id',
                                        backref='patient',  lazy='dynamic')
    screening_results = db.relationship('ScreeningResult', backref='patient', lazy='dynamic')
    referrals         = db.relationship('Referral',        foreign_keys='Referral.patient_id',
                                        backref='patient',  lazy='dynamic')
    longitudinal_records = db.relationship('LongitudinalRecord', backref='patient', lazy='dynamic')

    @staticmethod
    def next_patient_code() -> str:
        return generate_code('LW', 8)

    def __repr__(self):
        return f'<Patient {self.patient_code}>'


# ═══════════════════════════════════════════════════════════════════════════
#  4. LIVER RISK ENGINE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class RiskAssessment(db.Model):
    """
    Core liver risk screening record.

    DISCLAIMER: Stores risk patterns ONLY — not a diagnosis.
    All records must include disclaimer_acknowledged = True.
    """

    __tablename__ = 'risk_assessments'
    __table_args__ = (
        db.Index('ix_risk_user_date',    'user_id',    'created_at'),
        db.Index('ix_risk_patient_date', 'patient_id', 'created_at'),
    )

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=True, index=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True, index=True)
    assessed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=True)

    risk_level       = db.Column(db.String(20), nullable=False, default=RiskLevel.LOW.value, index=True)
    overall_score    = db.Column(db.Float,      nullable=False, default=0.0)
    confidence_level = db.Column(db.Float,      nullable=False, default=0.5)

    explanation     = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)   # JSON array

    requires_referral  = db.Column(db.Boolean, default=False)
    referral_urgency   = db.Column(db.String(20), nullable=True)  # 'routine'|'urgent'|'emergency'
    assessment_type    = db.Column(db.String(20), default='self') # 'self'|'chw_assisted'|'wearable'
    disclaimer_acknowledged = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    risk_factors = db.relationship('RiskFactor', backref='assessment',
                                   lazy='dynamic', cascade='all, delete-orphan')
    symptoms     = db.relationship('UserSymptomReport', backref='assessment', lazy='dynamic')
    referrals    = db.relationship('Referral', foreign_keys='Referral.risk_assessment_id',
                                   backref='risk_assessment', lazy='dynamic')
    assessed_by  = db.relationship('User', foreign_keys=[assessed_by_id])

    def get_recommendations(self) -> list:
        try:
            return json.loads(self.recommendations) if self.recommendations else []
        except (ValueError, TypeError):
            return []

    def set_recommendations(self, data: list):
        self.recommendations = json.dumps(data)

    @property
    def risk_percentage(self) -> float:
        return round(self.overall_score * 100, 1)

    def __repr__(self):
        return f'<RiskAssessment #{self.id} level={self.risk_level} score={self.overall_score:.2f}>'


class RiskFactor(db.Model):
    """Individual risk factor contributing to a RiskAssessment score."""

    __tablename__ = 'risk_factors'

    id            = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('risk_assessments.id'),
                              nullable=False, index=True)
    factor_name     = db.Column(db.String(100), nullable=False)
    factor_category = db.Column(db.String(50),  nullable=False, index=True)
    # categories: 'alcohol'|'hepatitis'|'medication'|'environmental'|'symptoms'|'nutrition'|'biomarker'

    value        = db.Column(db.String(200), nullable=True)
    unit         = db.Column(db.String(50),  nullable=True)
    weight       = db.Column(db.Float, default=0.0)
    contribution = db.Column(db.Float, default=0.0)
    is_elevated  = db.Column(db.Boolean, default=False)
    explanation  = db.Column(db.Text, nullable=True)


class UserSymptomReport(db.Model):
    """User/patient-reported symptoms linked to a risk assessment."""

    __tablename__ = 'user_symptom_reports'
    __table_args__ = (
        db.CheckConstraint('severity >= 1 AND severity <= 10', name='chk_severity_range'),
    )

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'),       nullable=True, index=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey('patients.id'),    nullable=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('risk_assessments.id'), nullable=True)

    symptom_name  = db.Column(db.String(100), nullable=False)
    severity      = db.Column(db.Integer,     nullable=False)   # 1–10
    duration_days = db.Column(db.Integer,     nullable=True)
    reported_at   = db.Column(db.DateTime,    default=utcnow)
    notes         = db.Column(db.Text,        nullable=True)


# ═══════════════════════════════════════════════════════════════════════════
#  5. REFERRAL MODELS
# ═══════════════════════════════════════════════════════════════════════════

class Referral(db.Model):
    """Structured referral from platform to a healthcare facility."""

    __tablename__ = 'referrals'

    id = db.Column(db.Integer, primary_key=True)

    patient_id          = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True, index=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=True, index=True)
    referred_by_id      = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    facility_id         = db.Column(db.Integer, db.ForeignKey('healthcare_facilities.id'),
                                    nullable=False, index=True)
    risk_assessment_id  = db.Column(db.Integer, db.ForeignKey('risk_assessments.id'), nullable=True)

    urgency       = db.Column(db.String(20), default='routine')  # 'routine'|'urgent'|'emergency'
    status        = db.Column(db.String(20), default=ReferralStatus.PENDING.value, index=True)
    referral_code = db.Column(db.String(20), unique=True, nullable=False,
                              default=lambda: generate_code('REF', 8))

    referral_notes   = db.Column(db.Text, nullable=True)
    sent_at          = db.Column(db.DateTime, nullable=True)
    acknowledged_at  = db.Column(db.DateTime, nullable=True)
    completed_at     = db.Column(db.DateTime, nullable=True)
    sms_sent         = db.Column(db.Boolean,  default=False)
    created_at       = db.Column(db.DateTime, default=utcnow)

    referred_by  = db.relationship('User', foreign_keys=[referred_by_id])
    referred_user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<Referral {self.referral_code} urgency={self.urgency} status={self.status}>'


# ═══════════════════════════════════════════════════════════════════════════
#  6. SCREENING EVENT MODELS
# ═══════════════════════════════════════════════════════════════════════════

class ScreeningEvent(db.Model):
    """A scheduled community liver screening campaign."""

    __tablename__ = 'screening_events'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(200), nullable=False)
    organized_by_id = db.Column(db.Integer, db.ForeignKey('health_workers.id'),
                                nullable=False, index=True)

    location_name  = db.Column(db.String(200), nullable=True)
    district       = db.Column(db.String(100), nullable=False)
    sub_county     = db.Column(db.String(100), nullable=True)
    latitude       = db.Column(db.Float, nullable=True)
    longitude      = db.Column(db.Float, nullable=True)

    scheduled_date = db.Column(db.Date, nullable=False)
    actual_date    = db.Column(db.Date, nullable=True)
    status         = db.Column(db.String(20), default='planned')
    # statuses: 'planned'|'ongoing'|'completed'|'cancelled'

    patient_count  = db.Column(db.Integer, default=0)
    notes          = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=utcnow)

    screening_results = db.relationship('ScreeningResult', backref='event', lazy='dynamic')

    def __repr__(self):
        return f'<ScreeningEvent {self.name!r} {self.district} {self.scheduled_date}>'


class ScreeningResult(db.Model):
    """Individual patient result within a screening event."""

    __tablename__ = 'screening_results'

    id            = db.Column(db.Integer, primary_key=True)
    event_id      = db.Column(db.Integer, db.ForeignKey('screening_events.id'), nullable=True, index=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey('patients.id'),         nullable=False, index=True)
    worker_id     = db.Column(db.Integer, db.ForeignKey('health_workers.id'),   nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('risk_assessments.id'), nullable=True)

    result_summary = db.Column(db.Text,    nullable=True)
    referred       = db.Column(db.Boolean, default=False)
    notes          = db.Column(db.Text,    nullable=True)
    created_at     = db.Column(db.DateTime, default=utcnow)

    worker     = db.relationship('HealthWorker', foreign_keys=[worker_id])
    assessment = db.relationship('RiskAssessment', foreign_keys=[assessment_id])


# ═══════════════════════════════════════════════════════════════════════════
#  7. WEARABLE / SENSOR MODELS
# ═══════════════════════════════════════════════════════════════════════════

class WearableDevice(db.Model):
    """Registered wearable sensor device (sweat patch, wristband, etc.)."""

    __tablename__ = 'wearable_devices'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    device_id        = db.Column(db.String(100), unique=True, nullable=False)  # Hardware UUID
    device_type      = db.Column(db.String(50),  nullable=False)   # 'sweat_patch'|'wristband'|'custom'
    manufacturer     = db.Column(db.String(100), nullable=True)
    model            = db.Column(db.String(100), nullable=True)
    firmware_version = db.Column(db.String(50),  nullable=True)
    status           = db.Column(db.String(20), default=DeviceStatus.INACTIVE.value)

    registered_at  = db.Column(db.DateTime, default=utcnow)
    last_sync_at   = db.Column(db.DateTime, nullable=True)
    is_active      = db.Column(db.Boolean,  default=True)
    calibration_data = db.Column(db.Text,   nullable=True)  # JSON

    biomarker_readings = db.relationship('BiomarkerReading', backref='device', lazy='dynamic')

    def get_calibration(self) -> dict:
        try:
            return json.loads(self.calibration_data) if self.calibration_data else {}
        except (ValueError, TypeError):
            return {}

    def __repr__(self):
        return f'<WearableDevice {self.device_id} type={self.device_type}>'


class BiomarkerReading(db.Model):
    """
    Single biomarker reading from a wearable sensor.

    DISCLAIMER: Readings identify patterns only — not diagnostic values.
    Anomaly flags should prompt screening, not diagnosis.
    """

    __tablename__ = 'biomarker_readings'
    __table_args__ = (
        db.Index('ix_bm_device_time', 'device_id', 'timestamp'),
        db.Index('ix_bm_user_time',   'user_id',   'timestamp'),
        db.CheckConstraint('quality_score >= 0 AND quality_score <= 1',
                           name='chk_quality_score'),
    )

    id              = db.Column(db.Integer, primary_key=True)
    device_id       = db.Column(db.Integer, db.ForeignKey('wearable_devices.id'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    biomarker_type  = db.Column(db.String(50), nullable=False, index=True)
    value           = db.Column(db.Float,      nullable=False)
    unit            = db.Column(db.String(20), nullable=True)
    quality_score   = db.Column(db.Float,      default=1.0)  # 0–1 signal quality

    is_anomaly    = db.Column(db.Boolean, default=False)
    anomaly_notes = db.Column(db.Text,    nullable=True)

    timestamp  = db.Column(db.DateTime, nullable=False, index=True)
    synced_at  = db.Column(db.DateTime, default=utcnow)
    raw_data   = db.Column(db.Text,     nullable=True)  # JSON original sensor output

    def __repr__(self):
        return f'<BiomarkerReading {self.biomarker_type}={self.value} @ {self.timestamp}>'


# ═══════════════════════════════════════════════════════════════════════════
#  8. EDUCATIONAL CONTENT MODELS  (replaces generic blog/recipes)
# ═══════════════════════════════════════════════════════════════════════════

class EducationalModule(db.Model):
    """
    Structured, medically-reviewed educational module.
    Replaces generic blog posts. Content is evidence-based, Uganda-localised.
    """

    __tablename__ = 'educational_modules'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    slug        = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    category = db.Column(db.String(50), nullable=False, index=True)
    # 'hepatitis'|'alcohol_risk'|'aflatoxin'|'medication'|'prevention'|'screening'|'nutrition'

    target_audience    = db.Column(db.String(20), default='general')  # 'general'|'chw'|'clinician'
    language           = db.Column(db.String(5),  default='en')
    is_published       = db.Column(db.Boolean, default=False)
    is_medically_reviewed = db.Column(db.Boolean, default=False)
    reviewed_by        = db.Column(db.String(200), nullable=True)
    order_index        = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    contents = db.relationship('EducationalContent', backref='module',
                               lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EducationalModule {self.slug!r} cat={self.category}>'


class EducationalContent(db.Model):
    """A section/unit within an EducationalModule."""

    __tablename__ = 'educational_contents'

    id           = db.Column(db.Integer, primary_key=True)
    module_id    = db.Column(db.Integer, db.ForeignKey('educational_modules.id'),
                             nullable=False, index=True)
    title        = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(30),  nullable=False)
    # 'text'|'video_link'|'infographic'|'checklist'|'quiz'

    content     = db.Column(db.Text, nullable=False)
    language    = db.Column(db.String(5),  default='en')
    order_index = db.Column(db.Integer,    default=0)
    is_published = db.Column(db.Boolean,   default=False)
    created_at  = db.Column(db.DateTime,   default=utcnow)


# ═══════════════════════════════════════════════════════════════════════════
#  9. LONGITUDINAL MONITORING
# ═══════════════════════════════════════════════════════════════════════════

class LongitudinalRecord(db.Model):
    """
    Periodic health record for trend analysis.
    Simplified from the old HealthLog — focused on liver risk indicators.
    """

    __tablename__ = 'longitudinal_records'
    __table_args__ = (
        db.Index('ix_longit_user_date', 'user_id', 'record_date'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=True, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)

    record_date  = db.Column(db.Date,   nullable=False, index=True)
    risk_level   = db.Column(db.String(20), nullable=True)
    risk_score   = db.Column(db.Float,      nullable=True)

    # Key liver-stress indicators
    alcohol_units_per_day = db.Column(db.Float,   nullable=True)
    water_intake_liters   = db.Column(db.Float,   nullable=True)
    exercise_minutes      = db.Column(db.Integer, nullable=True)
    sleep_hours           = db.Column(db.Float,   nullable=True)

    medication_notes = db.Column(db.String(500), nullable=True)
    symptom_notes    = db.Column(db.String(500), nullable=True)
    notes            = db.Column(db.Text,        nullable=True)

    data_source = db.Column(db.String(20), default='self_report')
    # 'self_report'|'chw'|'wearable'

    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f'<LongitudinalRecord user={self.user_id} date={self.record_date} risk={self.risk_level}>'


# ═══════════════════════════════════════════════════════════════════════════
#  10. MODERATED FORUM  (restricted — no open health advice)
# ═══════════════════════════════════════════════════════════════════════════

class ForumDiscussion(db.Model):
    """
    Moderated community discussion.
    All posts require admin approval before visibility.
    Types: awareness stories, educational Q&A, verified health worker tips.
    """

    __tablename__ = 'forum_discussions'

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    title           = db.Column(db.String(200), nullable=False, index=True)
    content         = db.Column(db.Text, nullable=False)
    discussion_type = db.Column(db.String(30), default='awareness')
    # 'awareness'|'experience'|'education_qa'|'health_worker_tip'

    status                  = db.Column(db.String(30),
                                        default=DiscussionStatus.PENDING_REVIEW.value, index=True)
    is_verified_contributor = db.Column(db.Boolean, default=False)

    moderated_by_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    moderated_at      = db.Column(db.DateTime, nullable=True)
    moderation_notes  = db.Column(db.Text, nullable=True)

    views      = db.Column(db.Integer,  default=0)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    replies       = db.relationship('ForumReply', backref='discussion',
                                    lazy='dynamic', cascade='all, delete-orphan')
    moderated_by  = db.relationship('User', foreign_keys=[moderated_by_id])

    def __repr__(self):
        return f'<ForumDiscussion #{self.id} status={self.status}>'


class ForumReply(db.Model):
    """Reply to a ForumDiscussion — also requires moderation."""

    __tablename__ = 'forum_replies'

    id            = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('forum_discussions.id'),
                              nullable=False, index=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    content                 = db.Column(db.Text, nullable=False)
    status                  = db.Column(db.String(30), default=DiscussionStatus.PENDING_REVIEW.value)
    is_verified_contributor = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    reply_author = db.relationship('User', foreign_keys=[user_id])


# ═══════════════════════════════════════════════════════════════════════════
#  11. NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════

class Notification(db.Model):
    """In-app notification — risk alerts, referral updates, screening reminders."""

    __tablename__ = 'notifications'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title             = db.Column(db.String(200), nullable=False)
    message           = db.Column(db.Text,        nullable=False)
    notification_type = db.Column(db.String(30),  default='info')
    # 'info'|'risk_alert'|'referral'|'screening'|'education'|'warning'

    action_url = db.Column(db.String(500), nullable=True)
    is_read    = db.Column(db.Boolean,  default=False)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)


# ═══════════════════════════════════════════════════════════════════════════
#  12. NEWSLETTER SUBSCRIBERS
# ═══════════════════════════════════════════════════════════════════════════

class Subscriber(db.Model):
    """Email newsletter subscriber."""

    __tablename__ = 'subscribers'

    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String(120), unique=True, nullable=False, index=True)
    subscribed_at  = db.Column(db.DateTime, default=utcnow)
    is_active      = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'
