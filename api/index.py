"""
QAEWO Backend - Vercel Serverless Entry Point
"""
import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from backend.app import app

# Export for Vercel
handler = app
