"""
QAEWO Backend - Vercel Serverless Entry Point
"""
import sys
import os

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add backend directory to path
backend_path = os.path.join(current_dir, '..', 'backend')
sys.path.insert(0, backend_path)

# Import Flask app
from app import app

# Vercel expects the app to be named 'app' or a handler function
# Export the Flask app directly
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, request.start_response)

# Also export app for direct use
app = app
