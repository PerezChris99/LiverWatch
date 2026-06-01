"""
Forum Blueprint — Phase 2
===========================

Moderated community forum using ForumDiscussion / ForumReply models.
All posts start as 'pending_review' and become visible only after admin approval.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import ForumDiscussionForm, ForumReplyForm
from app.models import DiscussionStatus, ForumDiscussion, ForumReply

forum_bp = Blueprint('forum', __name__)

APPROVED = DiscussionStatus.APPROVED.value


@forum_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    discussions = (
        ForumDiscussion.query
        .filter_by(status=APPROVED)
        .filter(ForumDiscussion.deleted_at.is_(None))
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


@forum_bp.route('/<int:discussion_id>')
def discussion_detail(discussion_id: int):
    d = ForumDiscussion.query.get_or_404(discussion_id)
    # Unpublished posts are visible only to author and moderators
    if d.status != APPROVED and not (
        current_user.is_authenticated and (
            current_user.id == d.user_id or
            current_user.role in ('admin', 'clinician')
        )
    ):
        abort(404)
    d.views = (d.views or 0) + 1
    db.session.commit()
    approved_replies = (
        ForumReply.query
        .filter_by(discussion_id=d.id, status=APPROVED)
        .filter(ForumReply.deleted_at.is_(None))
        .order_by(ForumReply.created_at.asc())
        .all()
    )
    reply_form = ForumReplyForm()
    return render_template(
        'forum/discussion_detail.html',
        discussion=d,
        replies=approved_replies,
        reply_form=reply_form,
    )


@forum_bp.route('/<int:discussion_id>/reply', methods=['POST'])
@login_required
def add_reply(discussion_id: int):
    d = ForumDiscussion.query.get_or_404(discussion_id)
    if d.status != APPROVED:
        abort(404)
    form = ForumReplyForm()
    if form.validate_on_submit():
        reply = ForumReply(
            discussion_id=d.id,
            user_id=current_user.id,
            content=form.content.data,
        )
        db.session.add(reply)
        db.session.commit()
        flash('Your reply has been submitted for review.', 'success')
    return redirect(url_for('forum.discussion_detail', discussion_id=d.id))

