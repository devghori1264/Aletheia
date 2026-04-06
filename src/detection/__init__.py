"""
Detection Application

Main application for deepfake video analysis:

Components:
    - models/: Django ORM models for persistence
    - services/: Business logic and orchestration
    - api/: REST API endpoints
    - web/: Web interface views
    - tasks/: Celery async tasks
    - tests/: Test suite

Domain Concepts:
    - Analysis: A deepfake detection job
    - MediaFile: Uploaded video/image
    - Report: Generated analysis report
"""

from __future__ import annotations

default_app_config = "detection.apps.DetectionConfig"
