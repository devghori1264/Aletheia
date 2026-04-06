"""
Aletheia Development Settings

Configuration optimized for local development with:
    - Debug mode enabled
    - Relaxed security settings
    - SQLite database
    - Console email backend
    - Detailed error pages

Usage:
    Set ALETHEIA_ENVIRONMENT=development in .env file
    Then just run: python manage.py runserver

Warning:
    NEVER use these settings in production!
"""

from __future__ import annotations

import os
from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

# Read from .env file or default to True for development
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes", "on")

# =============================================================================
# SECURITY KEY (Development)
# =============================================================================

# Use a fixed key for development (easier) or read from env
SECRET_KEY = os.getenv(
    "ALETHEIA_SECRET_KEY",
    "django-insecure-dev-key-only-for-local-development-change-in-production"
)

# =============================================================================
# HOST CONFIGURATION
# =============================================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "[::1]",
    "0.0.0.0",
    ".localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

# =============================================================================
# CORS CONFIGURATION (Development)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True  # Only in development!
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:5173",
]

# =============================================================================
# DATABASE CONFIGURATION (Development)
# =============================================================================

# Using SQLite for easy local development
# No additional setup required
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =============================================================================
# SECURITY SETTINGS (Relaxed for Development)
# =============================================================================

# Disable HTTPS requirements for local development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# CSRF exemption for API in development
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

# Allow all CSRF trusted origins in development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# =============================================================================
# REST FRAMEWORK (Development - No CSRF)
# =============================================================================

# Override authentication to remove SessionAuthentication (which enforces CSRF)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

# =============================================================================
# EMAIL CONFIGURATION (Development)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# CACHING (Development)
# =============================================================================

# Use local memory cache for development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aletheia-dev-cache",
    }
}

# =============================================================================
# CELERY (Development)
# =============================================================================

# For development, tasks run synchronously for easier debugging
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# LOGGING (Development - More Verbose)
# =============================================================================

LOGGING["handlers"]["console"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["aletheia"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["detection"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["ml"]["level"] = "DEBUG"  # noqa: F405

# =============================================================================
# REST FRAMEWORK (Development)
# =============================================================================

# Add browsable API in development for easier testing
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Disable throttling in development
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405

# =============================================================================
# DEBUG TOOLBAR (Optional)
# =============================================================================

try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    }
except ImportError:
    pass  # Debug toolbar not installed, skip

# =============================================================================
# ML CONFIGURATION (Development)
# =============================================================================

# Use smaller models/batches in development
ML_DEFAULT_BATCH_SIZE = 4  # noqa: F811
ML_DEFAULT_SEQUENCE_LENGTH = 20  # noqa: F811

print(
    "\n"
    "╔══════════════════════════════════════════════════════════════════════╗\n"
    "║  🔬 ALETHEIA - Development Mode                                      ║\n"
    "║  Debug: ON | Database: SQLite | Celery: Eager Mode                   ║\n"
    "║  ⚠️  Do NOT use these settings in production!                        ║\n"
    "╚══════════════════════════════════════════════════════════════════════╝\n"
)
