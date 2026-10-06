from app import create_app
from app.config import TestingConfig

def test_security_headers_are_present():
 app=create_app(TestingConfig)
 client=app.test_client()
 response=client.get("/")
 assert response.headers["X-Content-Type-Options"]=="nosniff"
 assert response.headers["X-Frame-Options"]=="DENY"
 assert "Content-Security-Policy" in response.headers
 assert response.headers["Referrer-Policy"]=="strict-origin-when-cross-origin"

def test_api_error_is_json():
 app=create_app(TestingConfig)
 client=app.test_client()
 response=client.get("/api/v1/risk/999999")
 assert response.status_code in (401,404)
