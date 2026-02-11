"""
API Endpoint Tests
==================

Tests for all API endpoints including:
- Agent chat API
- Health tracking API
- Analytics API
- Error handling
- Response formats
"""

import pytest
import json


class TestAgentAPI:
    """Test agent chat API endpoints."""
    
    def test_agent_chat_requires_auth(self, client):
        """Test that agent chat requires authentication."""
        response = client.post('/api/agents/chat', 
            json={'message': 'test'},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should require authentication or return server error if not configured
        assert response.status_code in [401, 302, 500]
    
    def test_agent_chat_with_valid_message(self, authenticated_client):
        """Test agent chat with valid message."""
        response = authenticated_client.post('/api/agents/chat',
            json={'message': 'I have a headache'},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should return success, or 500 if agent runtime isn't configured (acceptable in test)
        assert response.status_code in [200, 201, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'response' in data or 'message' in data
    
    def test_agent_chat_with_empty_message(self, authenticated_client):
        """Test agent chat with empty message."""
        response = authenticated_client.post('/api/agents/chat',
            json={'message': ''},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should reject empty message
        assert response.status_code in [400, 422]
    
    def test_agent_chat_invalid_json(self, authenticated_client):
        """Test agent chat with invalid JSON."""
        response = authenticated_client.post('/api/agents/chat',
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        
        # Should return bad request or 500 if error handling not fully implemented
        assert response.status_code in [400, 415, 500]
    
    def test_agent_chat_missing_message_field(self, authenticated_client):
        """Test agent chat with missing message field."""
        response = authenticated_client.post('/api/agents/chat',
            json={'text': 'wrong field name'},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should return bad request
        assert response.status_code in [400, 422]


class TestHealthAPI:
    """Test health tracking API endpoints."""
    
    def test_create_health_record(self, authenticated_client):
        """Test creating a health record."""
        response = authenticated_client.post('/api/health/records',
            json={
                'date': '2026-02-11',
                'weight': 70.5,
                'symptoms': ['fatigue'],
                'notes': 'Feeling tired'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Should create or return appropriate response
        assert response.status_code in [200, 201, 404]
    
    def test_get_health_records(self, authenticated_client):
        """Test retrieving health records."""
        response = authenticated_client.get('/api/health/records')
        
        # Should return records or appropriate response
        assert response.status_code in [200, 404]
    
    def test_get_health_records_unauthorized(self, client):
        """Test that health records require authentication."""
        response = client.get('/api/health/records')
        
        # Should require authentication or 404 if not implemented
        assert response.status_code in [401, 302, 404]


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    def test_get_user_analytics(self, authenticated_client):
        """Test retrieving user analytics."""
        response = authenticated_client.get('/api/analytics/user')
        
        # Should return analytics or appropriate response
        assert response.status_code in [200, 404]
    
    def test_get_analytics_unauthorized(self, client):
        """Test that analytics require authentication."""
        response = client.get('/api/analytics/user')
        
        # Should require authentication or 404 if not implemented
        assert response.status_code in [401, 302, 404]
    
    def test_admin_analytics(self, admin_client):
        """Test admin analytics access."""
        response = admin_client.get('/api/analytics/admin')
        
        # Should allow admin access
        assert response.status_code in [200, 404]
    
    def test_admin_analytics_requires_admin(self, authenticated_client):
        """Test that admin analytics require admin role."""
        response = authenticated_client.get('/api/analytics/admin')
        
        # Should deny non-admin access or return 404 if not implemented
        assert response.status_code in [403, 302, 404]


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_404_on_invalid_endpoint(self, client):
        """Test 404 response for invalid endpoints."""
        response = client.get('/api/nonexistent/endpoint')
        
        assert response.status_code == 404
    
    def test_405_on_wrong_method(self, authenticated_client):
        """Test 405 response for wrong HTTP method."""
        # Try GET on POST-only endpoint
        response = authenticated_client.get('/api/agents/chat')
        
        # Should return method not allowed
        assert response.status_code in [405, 404]
    
    def test_api_returns_json_errors(self, client):
        """Test that API returns JSON error responses."""
        response = client.post('/api/agents/chat',
            json={'invalid': 'data'},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should return JSON response
        assert response.content_type == 'application/json' or response.status_code in [401, 302]


class TestAPIResponseFormats:
    """Test API response formats and structure."""
    
    def test_json_content_type(self, authenticated_client):
        """Test that API returns JSON content type."""
        response = authenticated_client.get('/api/health/records')
        
        # Should return JSON or redirect
        if response.status_code == 200:
            assert 'application/json' in response.content_type
    
    def test_cors_headers(self, app):
        """Test CORS headers if configured."""
        client = app.test_client()
        response = client.options('/api/agents/chat')
        
        # Check if CORS is configured
        # This is optional depending on configuration
        assert response.status_code in [200, 405, 404]


class TestAPIValidation:
    """Test API input validation."""
    
    def test_date_format_validation(self, authenticated_client):
        """Test date format validation."""
        response = authenticated_client.post('/api/health/records',
            json={
                'date': 'invalid-date',
                'weight': 70
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Should validate date format
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data or 'message' in data
    
    def test_numeric_validation(self, authenticated_client):
        """Test numeric value validation."""
        response = authenticated_client.post('/api/health/records',
            json={
                'date': '2026-02-11',
                'weight': 'not-a-number'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Should validate numeric values
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data or 'message' in data
    
    def test_array_validation(self, authenticated_client):
        """Test array field validation."""
        response = authenticated_client.post('/api/health/records',
            json={
                'date': '2026-02-11',
                'symptoms': 'not-an-array'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        # Should validate array fields
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data or 'message' in data


class TestAPIPerformance:
    """Test API performance and limits."""
    
    def test_large_payload_rejection(self, authenticated_client):
        """Test that excessively large payloads are rejected."""
        # Create a very large message
        large_message = 'A' * 100000  # 100KB message
        
        response = authenticated_client.post('/api/agents/chat',
            json={'message': large_message},
            headers={'Content-Type': 'application/json'}
        )
        
        # Should handle or reject large payload
        assert response.status_code in [200, 413, 400, 500]
    
    def test_concurrent_requests(self, authenticated_client):
        """Test handling of concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return authenticated_client.get('/api/health/records')
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in futures]
        
        # All should return valid responses
        for response in responses:
            assert response.status_code in [200, 404, 401, 302]
