"""
Education Blueprint — Phase 3
================================

Routes:
  GET /education/              — list published modules by category
  GET /education/<slug>        — module detail page with sections
"""

from flask import Blueprint, abort, render_template

from app.models import EducationalModule

education_bp = Blueprint('education', __name__)

_CATEGORY_LABELS = {
    'hepatitis':     'Hepatitis',
    'alcohol_risk':  'Alcohol Risk',
    'aflatoxin':     'Aflatoxin',
    'medication':    'Medications',
    'prevention':    'Prevention',
    'screening':     'Screening',
    'nutrition':     'Nutrition',
}


@education_bp.route('/')
def index():
    modules = (EducationalModule.query
               .filter_by(is_published=True)
               .order_by(EducationalModule.category, EducationalModule.order_index)
               .all())
    # Group by category
    grouped: dict[str, list] = {}
    for m in modules:
        grouped.setdefault(m.category, []).append(m)
    return render_template('education/index.html',
                           grouped=grouped,
                           category_labels=_CATEGORY_LABELS)


@education_bp.route('/<slug>')
def detail(slug):
    module = EducationalModule.query.filter_by(slug=slug, is_published=True).first_or_404()
    contents = module.contents.filter_by(is_published=True).order_by('order_index').all()
    return render_template('education/detail.html', module=module, contents=contents)
