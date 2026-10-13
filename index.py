import os
import sys

# Set up module search paths so Vercel can locate backend and frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import the configured Flask WSGI application
from backend.app import app

# Expose app for Vercel Serverless Functions
# Vercel WSGI looks for 'app' in api/index.py
