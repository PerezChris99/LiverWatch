"""
Legacy API v0
=============

Deprecated endpoints kept for transition only.
All new work should use /api/v1 endpoints.
New models (Post, Recipe, etc.) have been removed in Phase 1.
These routes return 410 Gone so existing clients get a clear message.
"""

from flask import Blueprint, jsonify

legacy_api_bp = Blueprint('legacy_api', __name__)


def _gone(message='This endpoint has been deprecated. Use /api/v1 instead.'):
    return jsonify({'error': 'gone', 'message': message}), 410


@legacy_api_bp.route('/medical_news')
@legacy_api_bp.route('/posts')
@legacy_api_bp.route('/posts/<int:post_id>')
@legacy_api_bp.route('/questions')
@legacy_api_bp.route('/recipes')
@legacy_api_bp.route('/recipes/<int:recipe_id>')
@legacy_api_bp.route('/health/stats')
@legacy_api_bp.route('/community/stats')
@legacy_api_bp.route('/search')
def deprecated(**kwargs):
    return _gone()

