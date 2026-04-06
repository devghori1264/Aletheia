"""
WSGI Configuration for Aletheia

This module contains the WSGI application used by Django's development server
and production WSGI deployments (gunicorn, uWSGI, etc.).

The WSGI application is configured to use environment-based settings:
    - Set ALETHEIA_ENVIRONMENT to select settings module
    - Defaults to 'development' if not specified

Production Deployment:
    gunicorn aletheia.wsgi:application --bind 0.0.0.0:8000

For more information on WSGI, see:
    https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aletheia.settings")

# Create the WSGI application
application = get_wsgi_application()
