"""
Admin Blueprint - Phase 1 Stub
================================

Full admin dashboard (risk oversight, CHW management) happens in Phase 3.
This stub keeps routes importable without removed models.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Subscriber

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users_count = User.query.count()
    subs_count = Subscriber.query.filter_by(is_active=True).count()
    return render_template('admin.html', users_count=users_count, subs_count=subs_count)
