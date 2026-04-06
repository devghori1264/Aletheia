"""
Aletheia Settings Module

This module provides environment-aware Django configuration with secure defaults.
Settings are split into base (common), development, production, and testing
configurations following the 12-factor app methodology.

Environment Selection:
    Set ALETHEIA_ENVIRONMENT to one of: 'development', 'production', 'testing'
    Defaults to 'development' if not specified.

Usage:
    export ALETHEIA_ENVIRONMENT=production
    python manage.py runserver

Security:
    - All secrets loaded from environment variables
    - Production enforces security headers
    - Debug mode automatically disabled in production
"""

import os
from typing import Final

# Environment identifier
ENVIRONMENT: Final[str] = os.getenv("ALETHEIA_ENVIRONMENT", "development").lower()

# Validate environment
VALID_ENVIRONMENTS: Final[tuple[str, ...]] = ("development", "production", "testing")

if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(
        f"Invalid ALETHEIA_ENVIRONMENT: '{ENVIRONMENT}'. "
        f"Must be one of: {', '.join(VALID_ENVIRONMENTS)}"
    )

# Dynamic settings import based on environment
if ENVIRONMENT == "production":
    from .production import *  # noqa: F401, F403
elif ENVIRONMENT == "testing":
    from .testing import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
