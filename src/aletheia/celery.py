"""
Celery Application Configuration

Sets up Celery for asynchronous task processing in Aletheia.
"""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aletheia.settings.development")

# Create Celery application
app = Celery("aletheia")

# Load config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# =============================================================================
# Celery Beat Schedule
# =============================================================================

app.conf.beat_schedule = {
    # Clean up stale analyses every hour
    "cleanup-stale-analyses": {
        "task": "detection.tasks.cleanup_stale_analyses",
        "schedule": crontab(minute=0),  # Every hour
        "kwargs": {"hours": 24},
    },
    
    # Clean up temporary files every 6 hours
    "cleanup-temp-files": {
        "task": "detection.tasks.cleanup_temp_files",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "kwargs": {"max_age_hours": 24},
    },
    
    # Clean up expired reports daily
    "cleanup-expired-reports": {
        "task": "detection.tasks.cleanup_expired_reports",
        "schedule": crontab(minute=0, hour=3),  # 3 AM daily
    },
}


# =============================================================================
# Task Configuration
# =============================================================================

app.conf.task_routes = {
    # Route analysis tasks to dedicated queue
    "detection.tasks.process_analysis": {"queue": "analysis"},
    "detection.tasks.batch_analysis": {"queue": "analysis"},
    
    # Webhook tasks to separate queue
    "detection.tasks.send_webhook_notification": {"queue": "webhooks"},
    
    # Report generation
    "detection.tasks.generate_report": {"queue": "reports"},
    
    # Maintenance tasks
    "detection.tasks.cleanup_*": {"queue": "maintenance"},
}

# Task serialization
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

# Task result settings
app.conf.result_expires = 3600  # 1 hour
app.conf.task_track_started = True

# Worker settings
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100


# =============================================================================
# Debug Task
# =============================================================================

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f"Request: {self.request!r}")
