"""
Detection Tasks Package

Celery tasks for asynchronous video analysis processing.
"""

from __future__ import annotations

from .analysis import (
    process_analysis_task,
    batch_analysis_task,
    cleanup_stale_analyses_task,
    send_webhook_notification_task,
)

__all__ = [
    "process_analysis_task",
    "batch_analysis_task",
    "cleanup_stale_analyses_task",
    "send_webhook_notification_task",
]
