"""
Forum Blueprint
===============

Community forum routes for Q&A.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Question, Answer, User
from app.forms import QuestionForm, AnswerForm

forum_bp = Blueprint('forum', __name__)


@forum_bp.route('/')
def index():
    """Forum homepage with questions list"""
    form = QuestionForm()
    
    # Search and filter parameters
    search = request.args.get('search', '')
    filter_by = request.args.get('filter', 'date')
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    
    query = Question.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (Question.title.ilike(f'%{search}%')) |
            (Question.content.ilike(f'%{search}%'))
        )
    
    # Apply tag filter
    if tag:
        query = query.filter(Question.tags.ilike(f'%{tag}%'))
    
    # Apply sorting
    if filter_by == 'popularity':
        query = query.order_by((Question.upvotes - Question.downvotes).desc())
    elif filter_by == 'views':
        query = query.order_by(Question.views.desc())
    elif filter_by == 'unanswered':
        # Get questions without accepted answers
        query = query.filter(Question.is_resolved == False)
        query = query.order_by(Question.date_posted.desc())
    else:  # Default: date
        query = query.order_by(Question.date_posted.desc())
    
    questions = query.paginate(page=page, per_page=10)
    
    # Get popular tags
    popular_tags = get_popular_tags()
    
    return render_template('forum/index.html',
                          form=form,
                          questions=questions,
                          search=search,
                          filter_by=filter_by,
                          current_tag=tag,
                          popular_tags=popular_tags)


@forum_bp.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    """Ask a new question"""
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            title=form.title.data,
            content=form.content.data,
            tags=form.tags.data,
            user_id=current_user.id
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Your question has been posted!', 'success')
        return redirect(url_for('forum.question_detail', question_id=question.id))
    
    return render_template('forum/ask.html', form=form)


@forum_bp.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question_detail(question_id):
    """Question detail with answers"""
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    
    # Increment view count
    question.views += 1
    db.session.commit()
    
    # Handle answer submission
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please login to post an answer.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        answer = Answer(
            content=form.content.data,
            question_id=question.id,
            user_id=current_user.id
        )
        
        db.session.add(answer)
        db.session.commit()
        
        flash('Your answer has been posted!', 'success')
        return redirect(url_for('forum.question_detail', question_id=question_id))
    
    # Get answers with sorting
    sort_by = request.args.get('sort', 'votes')
    page = request.args.get('page', 1, type=int)
    
    query = Answer.query.filter_by(question_id=question_id)
    
    if sort_by == 'newest':
        query = query.order_by(Answer.date_posted.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Answer.date_posted.asc())
    else:  # Default: votes
        query = query.order_by((Answer.upvotes - Answer.downvotes).desc())
    
    answers = query.paginate(page=page, per_page=10)
    
    return render_template('forum/question.html',
                          question=question,
                          form=form,
                          answers=answers,
                          sort_by=sort_by)


@forum_bp.route('/vote/<string:item_type>/<int:item_id>/<string:action>', methods=['POST'])
@login_required
def vote(item_type, item_id, action):
    """Vote on a question or answer"""
    if item_type == 'question':
        item = Question.query.get_or_404(item_id)
    elif item_type == 'answer':
        item = Answer.query.get_or_404(item_id)
    else:
        return jsonify({'success': False, 'error': 'Invalid item type'}), 400
    
    if action == 'upvote':
        item.upvotes += 1
    elif action == 'downvote':
        item.downvotes += 1
    else:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'upvotes': item.upvotes,
        'downvotes': item.downvotes,
        'score': item.score
    })


@forum_bp.route('/answer/<int:answer_id>/accept', methods=['POST'])
@login_required
def accept_answer(answer_id):
    """Accept an answer as the solution"""
    answer = Answer.query.get_or_404(answer_id)
    question = answer.question
    
    # Only question author can accept answers
    if question.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    # Unaccept any previously accepted answer
    Answer.query.filter_by(question_id=question.id, is_accepted=True).update({'is_accepted': False})
    
    # Accept this answer
    answer.is_accepted = True
    question.is_resolved = True
    
    db.session.commit()
    
    return jsonify({'success': True})


@forum_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit a question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id and not current_user.is_admin:
        flash('Not authorized to edit this question.', 'error')
        return redirect(url_for('forum.question_detail', question_id=question_id))
    
    form = QuestionForm(obj=question)
    
    if form.validate_on_submit():
        question.title = form.title.data
        question.content = form.content.data
        question.tags = form.tags.data
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('forum.question_detail', question_id=question_id))
    
    return render_template('forum/edit_question.html', form=form, question=question)


@forum_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get_or_404(question_id)
    
    if question.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('forum.index'))


def get_popular_tags():
    """Get list of popular tags"""
    questions = Question.query.all()
    tag_counts = {}
    
    for q in questions:
        if q.tags:
            for tag in q.tags.split(','):
                tag = tag.strip().lower()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by count and return top 10
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return [tag for tag, count in sorted_tags]
