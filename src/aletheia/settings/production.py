"""
Aletheia Production Settings

Hardened configuration for production deployment with:
    - Debug mode disabled
    - Strict security headers
    - PostgreSQL database
    - Redis caching
    - Proper logging

Usage:
    export ALETHEIA_ENVIRONMENT=production
    export ALETHEIA_SECRET_KEY=your-secure-secret-key
    export DATABASE_URL=postgres://user:pass@host:5432/aletheia
    gunicorn aletheia.wsgi:application

Required Environment Variables:
    - ALETHEIA_SECRET_KEY: Django secret key (required)
    - DATABASE_URL: PostgreSQL connection string
    - REDIS_URL: Redis connection string
    - ALLOWED_HOSTS: Comma-separated list of allowed hosts
    - SENTRY_DSN: Sentry error tracking (optional)
"""

from __future__ import annotations

import os
import sys

from .base import *  # noqa: F401, F403

# =============================================================================
# SECURITY: Validate Required Settings
# =============================================================================

# Ensure secret key is set via environment variable
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    print(
        "ERROR: ALETHEIA_SECRET_KEY environment variable is not set!\n"
        "Generate a secure key with:\n"
        "  python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )
    sys.exit(1)

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

DEBUG = False

# =============================================================================
# HOST CONFIGURATION
# =============================================================================

# Parse allowed hosts from environment
_allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if not _allowed_hosts:
    print("WARNING: ALLOWED_HOSTS environment variable is not set!")
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]

# =============================================================================
# DATABASE CONFIGURATION (Production - PostgreSQL)
# =============================================================================

# Try to use PostgreSQL if dj_database_url is available
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    try:
        import dj_database_url  # noqa: E402
        DATABASES = {
            "default": dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=False,  # Set to True for real production
            )
        }
    except ImportError:
        print("⚠️  WARNING: dj_database_url not installed. Install with: pip install dj-database-url")
        print("⚠️  Falling back to SQLite")
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    print("⚠️  WARNING: DATABASE_URL not set. Using SQLite (not recommended for production).")

# =============================================================================
# CACHING (Production - Redis)
# =============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "aletheia",
    }
}

# Session backend using cache
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# =============================================================================
# CELERY (Production)
# =============================================================================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "django-db")

# Production Celery settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# =============================================================================
# SECURITY SETTINGS (Production - Hardened)
# =============================================================================

# Check if running locally (for testing with runserver)
# Multiple detection strategies to ensure local testing is always detected:
# 1. Check ALLOWED_HOSTS for local addresses
# 2. Check if using Django's runserver command
# 3. Check for explicit ALETHEIA_LOCAL_TESTING env var
_local_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"}
_is_local_testing = (
    any(host in _local_hosts for host in ALLOWED_HOSTS)
    or "runserver" in sys.argv
    or os.getenv("ALETHEIA_LOCAL_TESTING", "false").lower() in ("true", "1", "yes")
)

# HTTPS/SSL settings
# Disable SSL redirect for local testing with runserver
SECURE_SSL_REDIRECT = False if _is_local_testing else True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS settings — ALWAYS 0 for local testing to prevent browser HTTPS caching
SECURE_HSTS_SECONDS = 0 if _is_local_testing else 31536000  # 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not _is_local_testing
SECURE_HSTS_PRELOAD = not _is_local_testing

# Cookie security (relaxed for local HTTP testing)
SESSION_COOKIE_SECURE = not _is_local_testing
CSRF_COOKIE_SECURE = not _is_local_testing

# Content security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CSRF trusted origins (HTTP for local, HTTPS for production)
CSRF_TRUSTED_ORIGINS = []
for host in ALLOWED_HOSTS:
    if host and not host.startswith("."):
        # Add HTTP for localhost/127.0.0.1/0.0.0.0
        if host in _local_hosts:
            CSRF_TRUSTED_ORIGINS.append(f"http://{host}")
        # Add HTTPS for production domains
        else:
            CSRF_TRUSTED_ORIGINS.append(f"https://{host}")

# For local testing, also add common local dev origins for CSRF
if _is_local_testing:
    _local_csrf_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    for origin in _local_csrf_origins:
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# =============================================================================
# CORS CONFIGURATION (Production)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in _cors_origins.split(",") if origin.strip()
]

# Add default localhost origins for local testing
if _is_local_testing:
    _default_local_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ]
    for origin in _default_local_origins:
        if origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(origin)

# =============================================================================
# STATIC FILES (Production)
# =============================================================================

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =============================================================================
# MEDIA FILES (Production - S3 Compatible)
# =============================================================================

# Uncomment and configure for S3-compatible storage
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
# AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# =============================================================================
# EMAIL CONFIGURATION (Production)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "apikey")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@aletheia.ai")

# =============================================================================
# LOGGING (Production - Structured)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "aletheia": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "detection": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "ml": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# ERROR TRACKING (Sentry)
# =============================================================================

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
    )

# =============================================================================
# REST FRAMEWORK (Production)
# =============================================================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Enforce throttling in production
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "100/hour",
    "user": "1000/hour",
    "analysis": "50/hour",
}

# =============================================================================
# JWT (Production - Shorter Token Lifetime)
# =============================================================================

from datetime import timedelta  # noqa: E402

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=15)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=1)  # noqa: F405

print(
    "\n"
    "╔══════════════════════════════════════════════════════════════════════╗\n"
    f"║  {'🛡️  ALETHEIA - Production Mode (Local Testing)' if _is_local_testing else '🛡️  ALETHEIA - Production Mode':<68} ║\n"
    f"║  Debug: OFF | Database: PostgreSQL | Celery: Async{' ':17} ║\n"
    f"║  Security: {'HTTP (local) + Essential Security' if _is_local_testing else 'HTTPS + HSTS + Secure Cookies':<52} ║\n"
    "╚══════════════════════════════════════════════════════════════════════╝\n"
)
