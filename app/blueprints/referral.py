"""
Referral Blueprint — Phase 4
================================

Routes:
  GET  /referrals/                       — user's referral list
  GET  /referrals/facilities             — searchable facility directory
  GET  /referrals/facilities/<id>        — facility detail
  POST /referrals/create/<assessment_id> — create a referral from an assessment
  GET  /referrals/<referral_code>        — referral status page
"""

from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models import (
    HealthcareFacility, Referral, ReferralStatus,
    RiskAssessment, UserRole, utcnow,
)

referral_bp = Blueprint('referral', __name__)


# ── User's referral list ──────────────────────────────────────────────────

@referral_bp.route('/')
@login_required
def index():
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    referrals = (Referral.query
                 .filter_by(user_id=current_user.id)
                 .order_by(Referral.created_at.desc(), Referral.id.desc())
                 .paginate(page=page, per_page=25, error_out=False))
    return render_template('referrals/index.html', referrals=referrals)


# ── Facility directory ────────────────────────────────────────────────────

@referral_bp.route('/facilities')
def facilities():
    district = request.args.get('district', '').strip()
    service  = request.args.get('service', '').strip()
    query    = HealthcareFacility.query.filter_by(is_active=True)
    if district:
        query = query.filter(HealthcareFacility.district.ilike(f'%{district}%'))
    if service == 'hepatitis':
        query = query.filter_by(hepatitis_treatment=True)
    elif service == 'specialist':
        query = query.filter_by(liver_specialist=True)
    facilities_list = (query.order_by(HealthcareFacility.district,
                                      HealthcareFacility.name)
                       .limit(200)
                       .all())
    districts = (db.session.query(HealthcareFacility.district)
                 .filter_by(is_active=True)
                 .distinct()
                 .order_by(HealthcareFacility.district)
                 .all())
    district_names = [d[0] for d in districts]
    return render_template('referrals/facilities.html',
                           facilities=facilities_list,
                           district_names=district_names,
                           selected_district=district,
                           selected_service=service)


@referral_bp.route('/facilities/<int:facility_id>')
def facility_detail(facility_id):
    facility = db.session.get(HealthcareFacility, facility_id)
    if not facility or not facility.is_active:
        abort(404)
    return render_template('referrals/facility_detail.html', facility=facility)


# ── Create referral ───────────────────────────────────────────────────────

@referral_bp.route('/create/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
def create_referral(assessment_id):
    assessment = db.session.get(RiskAssessment, assessment_id)
    if not assessment:
        abort(404)
    # Only the assessment owner or staff can create a referral
    if assessment.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        abort(403)

    if request.method == 'POST':
        facility_id = request.form.get('facility_id', type=int)
        if not facility_id:
            flash('Please select a facility.', 'error')
            return redirect(request.url)
        facility = db.session.get(HealthcareFacility, facility_id)
        if not facility or not facility.is_active:
            flash('Selected facility not found.', 'error')
            return redirect(request.url)
        urgency = request.form.get('urgency', 'routine')
        if urgency not in ('routine', 'urgent', 'emergency'):
            urgency = 'routine'

        referral = Referral(
            user_id=assessment.user_id,
            referred_by_id=current_user.id,
            facility_id=facility_id,
            risk_assessment_id=assessment_id,
            urgency=urgency,
            status=ReferralStatus.PENDING.value,
            referral_notes=request.form.get('notes', '').strip()[:1000],
        )
        db.session.add(referral)
        db.session.commit()
        flash(f'Referral {referral.referral_code} created.', 'success')
        return redirect(url_for('referral.referral_status',
                                referral_code=referral.referral_code))

    # GET — show facility selector
    facilities = (HealthcareFacility.query
                  .filter_by(is_active=True)
                  .order_by(HealthcareFacility.district, HealthcareFacility.name)
                  .all())
    return render_template('referrals/create.html',
                           assessment=assessment,
                           facilities=facilities)


# ── Referral status ───────────────────────────────────────────────────────

@referral_bp.route('/<referral_code>')
@login_required
def referral_status(referral_code):
    referral = Referral.query.filter_by(referral_code=referral_code).first_or_404()
    # Access control: owner or staff
    if referral.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        abort(403)
    return render_template('referrals/status.html', referral=referral)
