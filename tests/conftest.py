"""
Pytest Configuration and Fixtures
==================================

Shared test fixtures for the LiverWatch test suite.
"""

import os
import sys
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure the app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application instance."""
    from app import create_app
    from app.config import Config
    
    # Test configuration
    class TestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SECRET_KEY = 'test-secret-key-for-testing-only'
        RATELIMIT_ENABLED = False  # Disable for most tests
        
    app = create_app(TestConfig)
    
    # Create application context
    with app.app_context():
        from app import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for tests."""
    from app import db
    
    # Clear all data before each test
    with app.app_context():
        # Drop and recreate all tables for a clean state
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        yield db.session
        
        # Cleanup after test
        db.session.rollback()


@pytest.fixture(scope='function')
def authenticated_client(client, app, db_session):
    """Create an authenticated test client with a logged-in user."""
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    # Create test user (within app context from db_session)
    user = User(
        username='testuser',
        email='test@example.com',
        password=generate_password_hash('testpassword123')
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    
    return client


@pytest.fixture(scope='function')
def admin_client(client, app, db_session):
    """Create an authenticated admin test client."""
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    # Create admin user (within app context from db_session)
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('adminpass123'),
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'adminpass123'
    }, follow_redirects=True)
    
    return client


@pytest.fixture(scope='session')
def sample_symptoms():
    """Sample symptoms for testing."""
    return {
        'mild': ['fatigue', 'mild discomfort'],
        'moderate': ['nausea', 'loss of appetite', 'dark urine'],
        'severe': ['jaundice', 'confusion', 'severe abdominal pain']
    }


@pytest.fixture(scope='session')
def sample_lab_results():
    """Sample lab results for testing."""
    return {
        'normal': {'ALT': 25, 'AST': 30, 'bilirubin': 0.8},
        'elevated': {'ALT': 150, 'AST': 120, 'bilirubin': 2.5},
        'critical': {'ALT': 500, 'AST': 450, 'bilirubin': 5.0}
    }
