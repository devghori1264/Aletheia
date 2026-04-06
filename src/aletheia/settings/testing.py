"""
Aletheia Testing Settings

Configuration optimized for automated testing with:
    - Fast in-memory database
    - Disabled external services
    - Synchronous task execution
    - Simplified authentication

Usage:
    pytest --ds=aletheia.settings.testing
    
Or:
    export ALETHEIA_ENVIRONMENT=testing
    python manage.py test
"""

from __future__ import annotations

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

DEBUG = False  # Ensure production-like behavior in tests

# =============================================================================
# HOST CONFIGURATION
# =============================================================================

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# =============================================================================
# DATABASE (In-Memory SQLite for Speed)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# =============================================================================
# PASSWORD HASHING (Faster for Tests)
# =============================================================================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# =============================================================================
# CACHING (Local Memory)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aletheia-test-cache",
    }
}

# =============================================================================
# CELERY (Synchronous Execution)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# EMAIL (In-Memory)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# =============================================================================
# SECURITY (Relaxed for Testing)
# =============================================================================

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# =============================================================================
# REST FRAMEWORK (Simplified for Testing)
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# =============================================================================
# LOGGING (Minimal)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# =============================================================================
# ML CONFIGURATION (Minimal for Fast Tests)
# =============================================================================

ML_DEFAULT_BATCH_SIZE = 1  # noqa: F811
ML_DEFAULT_SEQUENCE_LENGTH = 5  # noqa: F811

# =============================================================================
# MEDIA (Temporary Directory)
# =============================================================================

import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="aletheia_test_media_")

# =============================================================================
# STATIC FILES (Simplified)
# =============================================================================

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
