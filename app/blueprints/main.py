"""
Main Blueprint - Phase 1 Stub
================================

Full homepage redesign (Uganda-focused landing page) happens in Phase 2.
This stub keeps routes importable without the removed Post/Recipe models.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user

from app import db
from app.models import Subscriber
from app.forms import SubscriptionForm

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    form = SubscriptionForm()
    return render_template('pages/index.html', form=form)


@main_bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    form = SubscriptionForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = Subscriber.query.filter_by(email=email).first()
        if existing and existing.is_active:
            flash('Already subscribed.', 'info')
        elif existing:
            existing.is_active = True
            db.session.commit()
            flash('Subscription reactivated!', 'success')
        else:
            db.session.add(Subscriber(email=email, is_active=True))
            db.session.commit()
            flash('Subscribed successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('pages/subscribe.html', form=form)


@main_bp.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email', '').lower().strip()
    sub = Subscriber.query.filter_by(email=email).first()
    if sub:
        sub.is_active = False
        db.session.commit()
        flash('Unsubscribed successfully.', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/about')
def about():
    return render_template('pages/index.html')
