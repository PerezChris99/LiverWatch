"""
LiverWatch Agent API Blueprint
==============================

Flask API endpoints for interacting with the Google ADK agents.
"""

import asyncio
import sys
import os
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user, login_required
from functools import wraps
from app import limiter

# Add project root to path for liverwatch_agents import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the root agent
try:
    from liverwatch_agents import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google ADK agents not available: {e}")
    AGENTS_AVAILABLE = False
    root_agent = None

# Create Blueprint
agents_bp = Blueprint('agents', __name__)

# Session service for agent conversations
if AGENTS_AVAILABLE:
    session_service = InMemorySessionService()
else:
    session_service = None


def agents_required(f):
    """Decorator to check if agents are available."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AGENTS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'AI agents are not available. Please check server configuration.'
            }), 503
        return f(*args, **kwargs)
    return decorated_function


def get_or_create_session_id():
    """Get existing session ID or create a new one."""
    if 'agent_session_id' not in session:
        import uuid
        session['agent_session_id'] = str(uuid.uuid4())
    return session['agent_session_id']


async def run_agent_async(user_message: str, session_id: str, user_id: str):
    """Run the agent asynchronously and collect response."""
    try:
        # Create or get session
        agent_session = await session_service.get_session(
            app_name="liverwatch",
            user_id=user_id,
            session_id=session_id
        )
        
        if agent_session is None:
            agent_session = await session_service.create_session(
                app_name="liverwatch",
                user_id=user_id,
                session_id=session_id
            )
        
        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name="liverwatch",
            session_service=session_service
        )
        
        # Create user content
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
        
        # Collect response
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if hasattr(event, 'is_final_response') and event.is_final_response():
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
        
        return {
            'success': True,
            'response': response_text or "I apologize, but I couldn't generate a response. Please try again.",
            'session_id': session_id
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': 'AI service temporarily unavailable.',
            'session_id': session_id
        }


@agents_bp.route('/chat', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
@agents_required
def chat():
    """
    Main chat endpoint for agent conversations.
    
    Request JSON:
    {
        "message": "User's message",
        "session_id": "optional session ID for conversation continuity"
    }
    
    Response JSON:
    {
        "success": true,
        "response": "Agent's response",
        "session_id": "session ID for future requests"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = str(data['message']).strip()
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        if len(user_message) > 4000:
            return jsonify({
                'success': False,
                'error': 'Message exceeds the 4000-character limit.'
            }), 400
        
        # Get or use provided session ID
        session_id = data.get('session_id') or get_or_create_session_id()
        if not isinstance(session_id, str) or len(session_id) > 100:
            return jsonify({'success': False, 'error': 'Invalid session ID.'}), 400
        
        # Run the agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_agent_async(user_message, session_id, str(current_user.id)))
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'AI service temporarily unavailable.'
        }), 500


@agents_bp.route('/quick-assess', methods=['POST'])
@limiter.limit("20 per minute")
@agents_required
def quick_assess():
    """
    Quick symptom assessment endpoint - directly uses the symptom tool.
    
    Request JSON:
    {
        "symptoms": ["symptom1", "symptom2"],
        "duration_days": 7
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symptoms' not in data:
            return jsonify({
                'success': False,
                'error': 'Symptoms list is required'
            }), 400
        
        from liverwatch_agents.tools import assess_symptoms
        
        symptoms = data['symptoms']
        duration = data.get('duration_days', 1)
        
        result = assess_symptoms(symptoms, duration)
        
        return jsonify({
            'success': True,
            'assessment': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/interpret-labs', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@agents_required
def interpret_labs():
    """
    Lab results interpretation endpoint.
    
    Request JSON:
    {
        "results": {
            "ALT": 45,
            "AST": 38,
            "bilirubin": 1.2
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({
                'success': False,
                'error': 'Lab results are required'
            }), 400
        
        from liverwatch_agents.tools import interpret_liver_panel
        
        result = interpret_liver_panel(data['results'])
        
        return jsonify({
            'success': True,
            'interpretation': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/diet-advice', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@agents_required
def diet_advice():
    """
    Get diet recommendations for a condition.
    
    Request JSON:
    {
        "condition": "fatty_liver"
    }
    """
    try:
        data = request.get_json()
        condition = data.get('condition', 'general')
        
        from liverwatch_agents.tools import get_diet_recommendations
        
        result = get_diet_recommendations(condition)
        
        return jsonify({
            'success': True,
            'recommendations': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/find-healthcare', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@agents_required
def find_healthcare():
    """
    Find healthcare facilities.
    
    Request JSON:
    {
        "location": "Kampala",
        "specialty": "gastroenterology"
    }
    """
    try:
        data = request.get_json()
        location = data.get('location', '')
        specialty = data.get('specialty', '')
        
        from liverwatch_agents.tools import find_healthcare_facilities
        
        result = find_healthcare_facilities(location, specialty)
        
        return jsonify({
            'success': True,
            'facilities': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/health-info', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@agents_required
def health_info():
    """
    Get health education information on a topic.
    
    Request JSON:
    {
        "topic": "hepatitis_b"
    }
    """
    try:
        data = request.get_json()
        topic = data.get('topic', 'liver_health')
        
        from liverwatch_agents.tools import get_health_education
        
        result = get_health_education(topic)
        
        return jsonify({
            'success': True,
            'information': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/status', methods=['GET'])
@login_required
def status():
    """Check if agents are available and working."""
    return jsonify({
        'success': True,
        'agents_available': AGENTS_AVAILABLE,
        'message': 'Agents are ready' if AGENTS_AVAILABLE else 'Agents are not available'
    })
