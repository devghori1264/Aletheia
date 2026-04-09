"""
Aletheia Base Settings

Core Django configuration shared across all environments.
Environment-specific settings should override values in their respective modules.

This module follows Django best practices:
    - Explicit configuration over implicit
    - Security by default
    - Clear documentation
    - Type hints for IDE support

Note:
    Never import this module directly. Use the settings package which
    handles environment-based configuration automatically.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'
# BASE_DIR points to the project root (where manage.py lives)
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent

# Source directory containing all application code
SRC_DIR: Final[Path] = BASE_DIR / "src"

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# In production, this MUST be set via environment variable
SECRET_KEY: str = os.getenv(
    "ALETHEIA_SECRET_KEY",
    "django-insecure-CHANGE-ME-IN-PRODUCTION-use-python-c-from-django.core.management.utils-import-get_random_secret_key",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG: bool = False

# Allowed hosts - override in environment-specific settings
ALLOWED_HOSTS: list[str] = []

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS: list[str] = []

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

# Django built-in apps
DJANGO_APPS: Final[list[str]] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Third-party apps
THIRD_PARTY_APPS: Final[list[str]] = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
]

# Aletheia custom apps
LOCAL_APPS: Final[list[str]] = [
    "core",
    "detection",
    "accounts",
    "dashboard",
]

INSTALLED_APPS: list[str] = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.HSTSResetMiddleware",  # Clear browser HSTS cache in dev
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static file serving
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF: Final[str] = "aletheia.urls"

# =============================================================================
# TEMPLATES CONFIGURATION
# =============================================================================

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            SRC_DIR / "templates",
            BASE_DIR / "frontend" / "dist",
            BASE_DIR / "frontend",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION: Final[str] = "aletheia.wsgi.application"
ASGI_APPLICATION: Final[str] = "aletheia.asgi.application"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Default database - SQLite for development
# Override with PostgreSQL configuration in production
DATABASES: dict[str, dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Default primary key field type
DEFAULT_AUTO_FIELD: Final[str] = "django.db.models.BigAutoField"

# =============================================================================
# AUTHENTICATION & AUTHORIZATION
# =============================================================================

AUTH_USER_MODEL: Final[str] = "accounts.User"

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE: Final[str] = "en-us"
TIME_ZONE: Final[str] = "UTC"
USE_I18N: Final[bool] = True
USE_TZ: Final[bool] = True

# =============================================================================
# STATIC FILES CONFIGURATION
# =============================================================================

STATIC_URL: Final[str] = "/static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = [
    SRC_DIR / "static",
]

# WhiteNoise configuration for efficient static file serving
STATICFILES_STORAGE: Final[str] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =============================================================================
# MEDIA FILES CONFIGURATION
# =============================================================================

MEDIA_URL: Final[str] = "/media/"
MEDIA_ROOT: Path = BASE_DIR / "media"

# Upload constraints
FILE_UPLOAD_MAX_MEMORY_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB

# Maximum allowed video file size (in bytes)
MAX_VIDEO_UPLOAD_SIZE: Final[int] = 500 * 1024 * 1024  # 500 MB

# Allowed video content types
ALLOWED_VIDEO_CONTENT_TYPES: Final[tuple[str, ...]] = (
    "video/mp4",
    "video/avi",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/3gpp",
    "video/x-ms-wmv",
)

# Allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS: Final[tuple[str, ...]] = (
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".flv",
    ".3gp",
    ".wmv",
    ".gif",
)

# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Changed for development ease
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "analysis": "50/hour",  # Custom rate for analysis endpoints
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

from datetime import timedelta  # noqa: E402

SIMPLE_JWT: dict[str, Any] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOW_CREDENTIALS: Final[bool] = True
CORS_ALLOWED_ORIGINS: list[str] = []  # Set in environment-specific settings

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_TIMEZONE: Final[str] = TIME_ZONE
CELERY_TASK_TRACK_STARTED: Final[bool] = True
CELERY_TASK_TIME_LIMIT: Final[int] = 30 * 60  # 30 minutes
CELERY_RESULT_BACKEND: str = "django-db"
CELERY_CACHE_BACKEND: str = "django-cache"
CELERY_ACCEPT_CONTENT: Final[list[str]] = ["json"]
CELERY_TASK_SERIALIZER: Final[str] = "json"
CELERY_RESULT_SERIALIZER: Final[str] = "json"

# Redis broker URL - override in production
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

CACHES: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "()": "core.utils.logging.JsonFormatter",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "aletheia": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "detection": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "ml": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# =============================================================================
# API DOCUMENTATION (DRF Spectacular)
# =============================================================================

SPECTACULAR_SETTINGS: dict[str, Any] = {
    "TITLE": "Aletheia API",
    "DESCRIPTION": "Enterprise-Grade Deepfake Detection Platform API",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Authentication", "description": "User authentication endpoints"},
        {"name": "Analysis", "description": "Video analysis and detection endpoints"},
        {"name": "Reports", "description": "Detection report endpoints"},
        {"name": "Users", "description": "User management endpoints"},
    ],
}

# =============================================================================
# ML CONFIGURATION
# =============================================================================

# Model storage path
ML_MODELS_DIR: Path = BASE_DIR / "models"

# Default analysis parameters
ML_DEFAULT_SEQUENCE_LENGTH: Final[int] = 60
ML_DEFAULT_IMAGE_SIZE: Final[int] = 224
ML_DEFAULT_BATCH_SIZE: Final[int] = 8

# Model ensemble weights (normalized)
ML_ENSEMBLE_WEIGHTS: dict[str, float] = {
    "efficientnet_lstm": 0.4,
    "resnext_transformer": 0.35,
    "xception": 0.25,
}

# Face detection configuration
FACE_DETECTION_CONFIDENCE_THRESHOLD: Final[float] = 0.8
FACE_DETECTION_MIN_FACE_SIZE: Final[int] = 50
FACE_DETECTION_PADDING: Final[int] = 40

# Analysis thresholds
ANALYSIS_FAKE_THRESHOLD: Final[float] = 0.5
ANALYSIS_HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.85

# =============================================================================
# SECURITY HEADERS (Production)
# =============================================================================

# These are set to secure defaults; override in development if needed
SECURE_BROWSER_XSS_FILTER: Final[bool] = True
SECURE_CONTENT_TYPE_NOSNIFF: Final[bool] = True
X_FRAME_OPTIONS: Final[str] = "DENY"

# Session security
SESSION_COOKIE_SECURE: bool = True
SESSION_COOKIE_HTTPONLY: Final[bool] = True
SESSION_COOKIE_SAMESITE: Final[str] = "Lax"
CSRF_COOKIE_SECURE: bool = True
CSRF_COOKIE_HTTPONLY: Final[bool] = True
CSRF_COOKIE_SAMESITE: Final[str] = "Lax"
