#!/usr/bin/env python
"""
LiverWatch Application Entry Point
==================================

This is the main entry point for the LiverWatch Flask application.
A liver health awareness platform specifically focused on Uganda.

Usage:
    python run.py                  # Development server
    gunicorn "app:create_app()"    # Production server

Author: LiverWatch Team
License: MIT
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
