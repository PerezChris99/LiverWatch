"""
Forum Blueprint - Phase 1 Stub
=================================

Redesigned forum uses ForumDiscussion / ForumReply models with
a moderation workflow. Full UI implemented in Phase 2.
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app import db
from app.models import ForumDiscussion, ForumReply
from app.forms import ForumDiscussionForm, ForumReplyForm

forum_bp = Blueprint('forum', __name__)


@forum_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    discussions = (
        ForumDiscussion.query
        .filter_by(status='approved')
        .order_by(ForumDiscussion.created_at.desc())
        .paginate(page=page, per_page=20)
    )
    return render_template('forum/index.html', discussions=discussions,
                           form=ForumDiscussionForm())


@forum_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_discussion():
    form = ForumDiscussionForm()
    if form.validate_on_submit():
        d = ForumDiscussion(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            discussion_type=form.discussion_type.data,
        )
        db.session.add(d)
        db.session.commit()
        flash('Your post has been submitted for review.', 'success')
        return redirect(url_for('forum.index'))
    return render_template('forum/new_discussion.html', form=form)
