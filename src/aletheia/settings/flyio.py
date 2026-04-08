from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Final

from .base import *  # noqa: F401, F403

FLY_APP_NAME: str | None = os.getenv("FLY_APP_NAME")
FLY_REGION: str | None = os.getenv("FLY_REGION")
FLY_ALLOC_ID: str | None = os.getenv("FLY_ALLOC_ID")

IS_FLY_ENVIRONMENT: Final[bool] = FLY_APP_NAME is not None

if not IS_FLY_ENVIRONMENT:
    import warnings
    warnings.warn(
        "Fly.io settings loaded but FLY_APP_NAME not set. "
        "This may indicate incorrect environment configuration.",
        RuntimeWarning,
        stacklevel=2,
    )

DEBUG: Final[bool] = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if "collectstatic" in sys.argv or "migrate" in sys.argv:
        SECRET_KEY = "build-only-not-for-production-use"
    else:
        raise ValueError(
            "DJANGO_SECRET_KEY environment variable is required. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )

ALLOWED_HOSTS: list[str] = [
    f"{FLY_APP_NAME}.fly.dev" if FLY_APP_NAME else "localhost",
    ".fly.dev",
]

if custom_domain := os.getenv("CUSTOM_DOMAIN"):
    ALLOWED_HOSTS.append(custom_domain)
    ALLOWED_HOSTS.append(f"www.{custom_domain}")

CSRF_TRUSTED_ORIGINS: list[str] = [
    f"https://{FLY_APP_NAME}.fly.dev" if FLY_APP_NAME else "https://localhost",
]

if custom_domain := os.getenv("CUSTOM_DOMAIN"):
    CSRF_TRUSTED_ORIGINS.append(f"https://{custom_domain}")
    CSRF_TRUSTED_ORIGINS.append(f"https://www.{custom_domain}")

SECURE_PROXY_SSL_HEADER: Final[tuple[str, str]] = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT: Final[bool] = True

SECURE_HSTS_SECONDS: Final[int] = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS: Final[bool] = True
SECURE_HSTS_PRELOAD: Final[bool] = True

SESSION_COOKIE_SECURE: Final[bool] = True
SESSION_COOKIE_HTTPONLY: Final[bool] = True
SESSION_COOKIE_SAMESITE: Final[str] = "Lax"

CSRF_COOKIE_SECURE: Final[bool] = True
CSRF_COOKIE_HTTPONLY: Final[bool] = True
CSRF_COOKIE_SAMESITE: Final[str] = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF: Final[bool] = True
SECURE_BROWSER_XSS_FILTER: Final[bool] = True
X_FRAME_OPTIONS: Final[str] = "DENY"

DATABASES: dict[str, dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path("/tmp/aletheia.db"),
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}

CACHES: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aletheia-cache",
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

CELERY_TASK_ALWAYS_EAGER: Final[bool] = True
CELERY_TASK_EAGER_PROPAGATES: Final[bool] = True

CELERY_BROKER_URL: str | None = None
CELERY_RESULT_BACKEND: str | None = None

CELERY_TASK_TIME_LIMIT: Final[int] = 300
CELERY_TASK_SOFT_TIME_LIMIT: Final[int] = 270

STATIC_URL: Final[str] = "/static/"
STATIC_ROOT: Path = Path("/app/staticfiles")

STATICFILES_DIRS: list[Path] = [
    Path("/app/frontend/dist"),
    Path("/app/src/static"),
]

STATICFILES_STORAGE: Final[str] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL: Final[str] = "/media/"
MEDIA_ROOT: Path = Path("/tmp/media")

MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

CORS_ALLOW_ALL_ORIGINS: Final[bool] = False
CORS_ALLOWED_ORIGINS: list[str] = [
    f"https://{FLY_APP_NAME}.fly.dev" if FLY_APP_NAME else "https://localhost:8000",
]

if custom_domain := os.getenv("CUSTOM_DOMAIN"):
    CORS_ALLOWED_ORIGINS.append(f"https://{custom_domain}")
    CORS_ALLOWED_ORIGINS.append(f"https://www.{custom_domain}")

CORS_ALLOW_CREDENTIALS: Final[bool] = True

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "60/hour",
    "user": "500/hour",
    "analysis": "20/hour",
}

ML_DEVICE: Final[str] = os.getenv("ML_DEVICE", "cpu")
ML_PRECISION: Final[str] = os.getenv("ML_PRECISION", "fp32")

ML_DEFAULT_BATCH_SIZE: Final[int] = int(os.getenv("ML_BATCH_SIZE", "4"))
ML_NUM_WORKERS: Final[int] = int(os.getenv("ML_NUM_WORKERS", "2"))

ML_USE_ENSEMBLE: Final[bool] = False
ML_DEFAULT_MODEL: Final[str] = "efficientnet_lstm"

ML_DEFAULT_SEQUENCE_LENGTH: Final[int] = 30
ML_LAZY_LOAD: Final[bool] = True
ML_MODELS_DIR: Path = Path(os.getenv("ML_MODELS_DIR", "/app/models"))

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.utils.logging.JsonFormatter",
        },
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json" if os.getenv("LOG_FORMAT") == "json" else "verbose",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",  # Only log warnings and errors
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
        "urllib3": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "PIL": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

SENTRY_DSN: str | None = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
            ),
            LoggingIntegration(
                level=None,
                event_level="ERROR",
            ),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ALETHEIA_ENVIRONMENT", "production"),
        release=os.getenv("GIT_REV", "unknown"),
        send_default_pii=False,
        server_name=f"{FLY_REGION}-{FLY_ALLOC_ID[:8]}" if FLY_ALLOC_ID else None,
    )

TEMPLATES[0]["DIRS"] = [
    Path("/app/frontend/dist"),
    Path("/app/src/templates"),
]

from datetime import timedelta

SIMPLE_JWT: dict[str, Any] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

FILE_UPLOAD_MAX_MEMORY_SIZE: Final[int] = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE: Final[int] = 50 * 1024 * 1024
MAX_VIDEO_UPLOAD_SIZE: Final[int] = 100 * 1024 * 1024

FILE_UPLOAD_TEMP_DIR: Path = Path("/tmp/uploads")
FILE_UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)

CONN_MAX_AGE: Final[int] = 0

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

ADMIN_URL: Final[str] = os.getenv("ADMIN_URL", "admin/")

SILENCED_SYSTEM_CHECKS: list[str] = [
    "security.W020",
]

if not any(arg in sys.argv for arg in ["collectstatic", "migrate", "check"]):
    import logging
    logger = logging.getLogger("aletheia.settings")
    logger.info(
        "Fly.io configuration loaded",
        extra={
            "app_name": FLY_APP_NAME,
            "region": FLY_REGION,
            "debug": DEBUG,
            "ml_device": ML_DEVICE,
            "ml_model": ML_DEFAULT_MODEL,
            "celery_eager": CELERY_TASK_ALWAYS_EAGER,
        },
    )
