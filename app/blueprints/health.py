"""
Health Blueprint — Phase 2
============================

Uganda Liver Risk Intelligence Platform
Phase 2: Liver Risk Engine UI

Routes:
  GET       /health/tracker           → personal health dashboard + longitudinal log
  GET/POST  /health/risk-assessment   → submit assessment form, save, redirect to result
  GET       /health/result/<id>       → view a stored risk assessment result
  GET/POST  /health/log               → add a longitudinal health record
  GET/POST  /health/chw/register      → CHW registers a new patient
"""

import logging
from datetime import date

from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.forms import CHWPatientForm, HealthLogForm, RiskAssessmentForm
from app.models import (
    LongitudinalRecord, Patient, RiskAssessment, RiskFactor,
    UserRole, generate_code,
)
from app.services.risk_engine import run_risk_assessment

logger    = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

MEDICAL_DISCLAIMER = (
    "This platform does not provide medical diagnosis. "
    "Please consult a licensed healthcare professional."
)


# ── Tracker dashboard ────────────────────────────────────────────────────

@health_bp.route('/tracker')
@login_required
def tracker():
    recent_assessments = (
        RiskAssessment.query
        .filter_by(user_id=current_user.id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(5)
        .all()
    )
    recent_records = (
        LongitudinalRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(LongitudinalRecord.record_date.desc())
        .limit(7)
        .all()
    )
    latest = recent_assessments[0] if recent_assessments else None
    log_form = HealthLogForm()
    return render_template(
        'health/tracker.html',
        latest_assessment=latest,
        recent_assessments=recent_assessments,
        recent_records=recent_records,
        log_form=log_form,
    )


# ── Risk assessment form ─────────────────────────────────────────────────

@health_bp.route('/risk-assessment', methods=['GET', 'POST'])
@login_required
def risk_assessment():
    form = RiskAssessmentForm()

    if form.validate_on_submit():
        # Build symptom list from individual boolean fields
        symptom_map = {
            'jaundice':        form.symptom_jaundice.data,
            'dark_urine':      form.symptom_dark_urine.data,
            'pale_stools':     form.symptom_pale_stools.data,
            'fatigue':         form.symptom_fatigue.data,
            'abdominal_pain':  form.symptom_abdominal_pain.data,
            'swollen_abdomen': form.symptom_swollen_abdomen.data,
            'nausea':          form.symptom_nausea.data,
            'itching':         form.symptom_itching.data,
            'vomiting_blood':  form.symptom_vomiting_blood.data,
            'confusion':       form.symptom_confusion.data,
            'bleeding_easily': form.symptom_bleeding_easily.data,
        }
        symptoms = [k for k, v in symptom_map.items() if v]

        assessment_input = {
            'hepatitis': {
                'hbsag_positive': form.hbsag_positive.data,
                'hcv_positive':   form.hcv_positive.data,
                'vaccinated_hbv': form.vaccinated_hbv.data,
                'exposure_risk':  form.hbv_exposure_risk.data,
                'family_history': form.hbv_family_history.data,
            },
            'alcohol': {
                'drinks_per_day': form.drinks_per_day.data or 0.0,
                'years_drinking': form.years_drinking.data or 0,
                'binge_drinking': form.binge_drinking.data,
            },
            'symptoms': symptoms,
            'medications': {
                'otc_painkillers':      form.otc_painkillers.data,
                'painkiller_frequency': form.painkiller_frequency.data,
                'tb_treatment':         form.tb_treatment.data,
                'herbal_remedies':      form.herbal_remedies.data,
                'multiple_medications': form.multiple_medications.data,
            },
            'environmental': {
                'aflatoxin_exposure': form.aflatoxin_exposure.data,
                'chemical_exposure':  form.chemical_exposure.data,
                'unsafe_water':       form.unsafe_water.data,
            },
            'family_history': {
                'liver_cancer_family': form.liver_cancer_family.data,
                'cirrhosis_family':    form.cirrhosis_family.data,
                'hbv_family':          form.hbv_family_history.data,
            },
            'nutrition': {
                'bmi':             form.bmi.data,
                'high_fat_diet':   form.high_fat_diet.data,
                'low_water_intake': form.low_water_intake.data,
                'diabetes':        form.diabetes.data,
            },
        }

        result = run_risk_assessment(assessment_input)

        # Persist to DB
        ra = RiskAssessment(
            user_id=current_user.id,
            risk_level=result.risk_level,
            overall_score=result.overall_score,
            confidence_level=result.confidence_level,
            explanation=result.explanation,
            recommendations='\n'.join(result.recommendations),
            requires_referral=result.requires_referral,
            referral_urgency=result.referral_urgency,
            disclaimer_acknowledged=True,
        )
        db.session.add(ra)
        db.session.flush()

        for f in result.factors:
            db.session.add(RiskFactor(
                assessment_id=ra.id,
                factor_name=f.name,
                factor_category=f.category,
                value=f.value,
                unit=f.unit,
                weight=f.weight,
                contribution=f.contribution,
                is_elevated=f.is_elevated,
                explanation=f.explanation,
            ))

        db.session.commit()
        logger.info("Risk assessment #%d saved (user=%d level=%s)",
                    ra.id, current_user.id, ra.risk_level)
        return redirect(url_for('health.result', assessment_id=ra.id))

    return render_template('health/risk_assessment.html', form=form,
                           disclaimer=MEDICAL_DISCLAIMER)


# ── Result view ──────────────────────────────────────────────────────────

@health_bp.route('/result/<int:assessment_id>')
@login_required
def result(assessment_id: int):
    ra = RiskAssessment.query.get_or_404(assessment_id)
    if ra.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        abort(403)
    factors = RiskFactor.query.filter_by(assessment_id=ra.id).all()
    recs = ra.recommendations.split('\n') if ra.recommendations else []
    return render_template(
        'health/risk_result.html',
        assessment=ra,
        factors=factors,
        recommendations=recs,
        disclaimer=MEDICAL_DISCLAIMER,
    )


# ── Longitudinal log entry ───────────────────────────────────────────────

@health_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log_entry():
    form = HealthLogForm()
    if form.validate_on_submit():
        record = LongitudinalRecord(
            user_id=current_user.id,
            record_date=date.today(),
            alcohol_units_per_day=form.alcohol_intake.data,
            water_intake_liters=form.water_intake.data,
            exercise_minutes=form.exercise_minutes.data,
            sleep_hours=form.sleep_hours.data,
            notes=(form.notes.data or '').strip()[:500],
            data_source='self_report',
        )
        db.session.add(record)
        db.session.commit()
        flash('Health log saved.', 'success')
        return redirect(url_for('health.tracker'))
    if request.method == 'POST':
        flash('Please correct the highlighted health log fields.', 'error')
    return redirect(url_for('health.tracker'))


# ── CHW patient registration ─────────────────────────────────────────────

@health_bp.route('/chw/register', methods=['GET', 'POST'])
@login_required
def chw_register():
    if current_user.role not in (
        UserRole.CHW.value, UserRole.CLINICIAN.value, UserRole.ADMIN.value
    ):
        flash('Only community health workers can register patients.', 'error')
        return redirect(url_for('main.index'))

    from app.models import HealthWorker
    hw = HealthWorker.query.filter_by(user_id=current_user.id).first()
    if hw is None:
        flash('Your account has not been set up as a health worker profile yet. '
              'Contact an administrator.', 'warning')
        return redirect(url_for('health.tracker'))

    form = CHWPatientForm()
    if form.validate_on_submit():
        patient = Patient(
            patient_code=generate_code('PT'),
            registered_by_id=hw.id,
            age=form.age.data,
            gender=form.gender.data,
            district=form.district.data,
            sub_county=form.sub_county.data or None,
            village=form.village.data or None,
            consent_given=form.consent_given.data,
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient registered: {patient.patient_code}', 'success')
        return redirect(url_for('health.tracker'))

    return render_template('health/chw_register.html', form=form)


# ── Helpers ──────────────────────────────────────────────────────────────

def _safe_float(v) -> float | None:
    try:
        return float(v) if v not in (None, '') else None
    except (ValueError, TypeError):
        return None


def _safe_int(v) -> int | None:
    try:
        return int(v) if v not in (None, '') else None
    except (ValueError, TypeError):
        return None
