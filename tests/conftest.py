"""
Configuration file for pytest
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
