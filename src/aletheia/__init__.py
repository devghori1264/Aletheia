"""
Aletheia - Enterprise-Grade Deepfake Detection Platform

Named after the Greek goddess of truth and disclosure, Aletheia is a production-ready,
research-backed deepfake detection system designed for enterprise deployment.

Key Features:
    - Multi-model ensemble architecture for high-accuracy detection
    - Real-time video analysis with explainable AI
    - Scalable async processing with Celery
    - RESTful API with comprehensive authentication
    - Modern React-based frontend

Architecture:
    - src/aletheia/: Django project configuration
    - src/core/: Shared utilities and base classes
    - src/detection/: Main detection domain logic
    - src/ml/: Machine learning models and inference
    - src/accounts/: User authentication and management
    - src/dashboard/: Analytics and monitoring

Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Aletheia Team"
__license__ = "MIT"

from typing import Final

# Application metadata
APP_NAME: Final[str] = "Aletheia"
APP_DESCRIPTION: Final[str] = "Enterprise-Grade Deepfake Detection Platform"
APP_VERSION: Final[str] = __version__

# Semantic versioning components
VERSION_MAJOR: Final[int] = 2
VERSION_MINOR: Final[int] = 0
VERSION_PATCH: Final[int] = 0
