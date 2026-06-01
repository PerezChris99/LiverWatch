"""
Admin Blueprint — Phase 3
============================

Full admin panel:
  dashboard  — key platform statistics
  users      — list, change role, soft-delete
  forum      — moderate pending discussions and replies
  chw        — list and verify community health workers
"""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import (
    DiscussionStatus, ForumDiscussion, ForumReply, HealthWorker,
    RiskAssessment, Subscriber, User, UserRole, utcnow,
)

admin_bp = Blueprint('admin', __name__)


# ── Access control ────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users_count       = User.query.filter_by(deleted_at=None).count()
    assessments_count = RiskAssessment.query.count()
    pending_posts     = ForumDiscussion.query.filter_by(
        status=DiscussionStatus.PENDING_REVIEW.value).count()
    chw_count         = HealthWorker.query.filter_by(is_active=True).count()
    subs_count        = Subscriber.query.filter_by(is_active=True).count()
    recent_users      = (User.query.filter_by(deleted_at=None)
                         .order_by(User.created_at.desc()).limit(5).all())
    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           assessments_count=assessments_count,
                           pending_posts=pending_posts,
                           chw_count=chw_count,
                           subs_count=subs_count,
                           recent_users=recent_users)


# ── User management ───────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page  = request.args.get('page', 1, type=int)
    query = User.query.filter_by(deleted_at=None).order_by(User.created_at.desc())
    users_page = query.paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/users.html', users_page=users_page,
                           roles=[r.value for r in UserRole])


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.users'))
    new_role = request.form.get('role', '')
    valid_roles = [r.value for r in UserRole]
    if new_role not in valid_roles:
        flash('Invalid role.', 'error')
        return redirect(url_for('admin.users'))
    user.role = new_role
    db.session.commit()
    flash(f'{user.username} role updated to {new_role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.users'))
    user.soft_delete()
    db.session.commit()
    flash(f'{user.username} has been deactivated.', 'success')
    return redirect(url_for('admin.users'))


# ── Forum moderation ──────────────────────────────────────────────────────

@admin_bp.route('/forum')
@login_required
@admin_required
def forum_moderation():
    pending_discussions = (ForumDiscussion.query
                           .filter_by(status=DiscussionStatus.PENDING_REVIEW.value)
                           .order_by(ForumDiscussion.created_at.asc()).all())
    pending_replies = (ForumReply.query
                       .filter_by(status=DiscussionStatus.PENDING_REVIEW.value)
                       .order_by(ForumReply.created_at.asc()).all())
    return render_template('admin/forum_moderation.html',
                           pending_discussions=pending_discussions,
                           pending_replies=pending_replies)


@admin_bp.route('/forum/discussion/<int:discussion_id>/<action>', methods=['POST'])
@login_required
@admin_required
def moderate_discussion(discussion_id, action):
    d = db.session.get(ForumDiscussion, discussion_id)
    if not d:
        abort(404)
    if action == 'approve':
        d.status         = DiscussionStatus.APPROVED.value
        d.moderated_by_id = current_user.id
        d.moderated_at    = utcnow()
        flash('Discussion approved.', 'success')
    elif action == 'reject':
        d.status          = DiscussionStatus.REJECTED.value
        d.moderated_by_id = current_user.id
        d.moderated_at    = utcnow()
        flash('Discussion rejected.', 'warning')
    else:
        abort(400)
    db.session.commit()
    return redirect(url_for('admin.forum_moderation'))


@admin_bp.route('/forum/reply/<int:reply_id>/<action>', methods=['POST'])
@login_required
@admin_required
def moderate_reply(reply_id, action):
    r = db.session.get(ForumReply, reply_id)
    if not r:
        abort(404)
    if action == 'approve':
        r.status = DiscussionStatus.APPROVED.value
        flash('Reply approved.', 'success')
    elif action == 'reject':
        r.status = DiscussionStatus.REJECTED.value
        flash('Reply rejected.', 'warning')
    else:
        abort(400)
    db.session.commit()
    return redirect(url_for('admin.forum_moderation'))


# ── CHW management ────────────────────────────────────────────────────────

@admin_bp.route('/chw')
@login_required
@admin_required
def chw_list():
    workers = (HealthWorker.query.filter_by(is_active=True)
               .order_by(HealthWorker.created_at.desc()).all())
    return render_template('admin/chw_list.html', workers=workers)


@admin_bp.route('/chw/<int:worker_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_chw(worker_id):
    worker = db.session.get(HealthWorker, worker_id)
    if not worker:
        abort(404)
    worker.is_verified    = True
    worker.verified_by_id = current_user.id
    worker.verified_at    = utcnow()
    db.session.commit()
    flash(f'{worker.full_name} has been verified.', 'success')
    return redirect(url_for('admin.chw_list'))

