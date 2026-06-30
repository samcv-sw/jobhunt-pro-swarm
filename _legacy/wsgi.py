"""
WSGI entry point for PythonAnywhere.
Auto-loads env vars and exports the FastAPI application.
"""
import os
import sys

# Add project root and web dir to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "web"))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Import the FastAPI app
from web.app_v2 import app as application
