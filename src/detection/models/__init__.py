"""
Detection Models Package

Django ORM models for the detection domain:
    - Analysis: Core analysis job model
    - MediaFile: Uploaded video storage
    - AnalysisFrame: Frame-level analysis results
    - Report: Generated analysis reports
"""

from __future__ import annotations

from .analysis import Analysis, AnalysisFrame
from .media import MediaFile
from .report import Report

__all__ = [
    "Analysis",
    "AnalysisFrame",
    "MediaFile",
    "Report",
]
