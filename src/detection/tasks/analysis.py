"""
Analysis Celery Tasks

Asynchronous tasks for deepfake detection processing:
    - process_analysis_task: Main analysis execution
    - batch_analysis_task: Batch processing multiple files
    - cleanup_stale_analyses_task: Maintenance cleanup
    - send_webhook_notification_task: Webhook delivery
"""

from __future__ import annotations

import logging
import time
from typing import Any

from celery import shared_task, Task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Task Base
# =============================================================================

class AnalysisTask(Task):
    """
    Base task class for analysis operations.
    
    Provides:
        - Automatic error handling and logging
        - Progress tracking integration
        - Retry logic with exponential backoff
    """
    
    abstract = True
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    max_retries = 3
    soft_time_limit = 600  # 10 minutes
    time_limit = 660  # 11 minutes (hard limit)
    
    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Handle task failure."""
        logger.error(
            f"Task {self.name}[{task_id}] failed: {exc}",
            exc_info=einfo,
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
            },
        )
        
        # Mark analysis as failed if we have an analysis_id
        if args:
            analysis_id = args[0]
            try:
                from detection.models import Analysis
                analysis = Analysis.objects.get(id=analysis_id)
                if not analysis.is_terminal:
                    analysis.fail(
                        error_message=str(exc),
                        error_code="E3099",
                    )
            except Exception as e:
                logger.error(f"Failed to update analysis status: {e}")
    
    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Handle task retry."""
        logger.warning(
            f"Task {self.name}[{task_id}] retrying due to: {exc}",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "retry_count": self.request.retries,
            },
        )
    
    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Handle task success."""
        logger.info(
            f"Task {self.name}[{task_id}] completed successfully",
            extra={
                "task_name": self.name,
                "task_id": task_id,
            },
        )


# =============================================================================
# Analysis Tasks
# =============================================================================

@shared_task(
    bind=True,
    base=AnalysisTask,
    name="detection.tasks.process_analysis",
    queue="analysis",
    track_started=True,
)
def process_analysis_task(
    self: AnalysisTask,
    analysis_id: str,
) -> dict[str, Any]:
    """
    Process a deepfake detection analysis.
    
    Main entry point for asynchronous analysis processing.
    Executes the full detection pipeline and stores results.
    
    Args:
        analysis_id: UUID of the analysis to process
    
    Returns:
        Dictionary with analysis results
    
    Raises:
        SoftTimeLimitExceeded: If processing exceeds time limit
    """
    from detection.services import AnalysisService
    from detection.models import Analysis
    
    logger.info(
        f"Starting analysis processing",
        extra={"analysis_id": analysis_id, "task_id": self.request.id},
    )
    
    start_time = time.time()
    
    try:
        service = AnalysisService()
        
        # Define progress callback for Celery state updates
        def progress_callback(progress: float, message: str) -> None:
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "message": message,
                    "analysis_id": analysis_id,
                },
            )
        
        # Run analysis
        result = service.run_analysis(
            analysis_id=analysis_id,
            progress_callback=progress_callback,
        )
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Analysis completed",
            extra={
                "analysis_id": analysis_id,
                "result": result.get("result"),
                "confidence": result.get("confidence"),
                "elapsed_time": elapsed,
            },
        )
        
        # Trigger webhook notification if configured
        analysis = Analysis.objects.get(id=analysis_id)
        if analysis.webhook_url and not analysis.webhook_sent:
            send_webhook_notification_task.delay(
                analysis_id=analysis_id,
                webhook_url=analysis.webhook_url,
            )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "result": result.get("result"),
            "confidence": result.get("confidence"),
            "elapsed_time": elapsed,
        }
    
    except SoftTimeLimitExceeded:
        logger.error(
            f"Analysis timed out",
            extra={"analysis_id": analysis_id},
        )
        
        # Mark as failed
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            analysis.fail(
                error_message="Analysis exceeded time limit",
                error_code="E3002",
            )
        except Exception:
            pass
        
        return {
            "success": False,
            "analysis_id": analysis_id,
            "error": "Analysis timed out",
        }
    
    except Exception as e:
        logger.error(
            f"Analysis failed: {e}",
            extra={"analysis_id": analysis_id},
            exc_info=True,
        )
        raise


@shared_task(
    bind=True,
    base=AnalysisTask,
    name="detection.tasks.batch_analysis",
    queue="analysis",
)
def batch_analysis_task(
    self: AnalysisTask,
    analysis_ids: list[str],
    priority: str = "normal",
) -> dict[str, Any]:
    """
    Process multiple analyses in batch.
    
    Dispatches individual analysis tasks and tracks overall progress.
    
    Args:
        analysis_ids: List of analysis UUIDs to process
        priority: Processing priority (low/normal/high)
    
    Returns:
        Dictionary with batch results
    """
    from celery import group
    
    logger.info(
        f"Starting batch analysis",
        extra={
            "batch_size": len(analysis_ids),
            "priority": priority,
            "task_id": self.request.id,
        },
    )
    
    # Create task group
    tasks = group(
        process_analysis_task.s(analysis_id)
        for analysis_id in analysis_ids
    )
    
    # Execute batch
    result = tasks.apply_async()
    
    # Wait for completion (with timeout)
    try:
        results = result.get(timeout=3600)  # 1 hour timeout
        
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        
        return {
            "success": True,
            "total": len(analysis_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
        }
    
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        return {
            "success": False,
            "total": len(analysis_ids),
            "error": str(e),
        }


@shared_task(
    name="detection.tasks.cleanup_stale_analyses",
    queue="maintenance",
)
def cleanup_stale_analyses_task(hours: int = 24) -> dict[str, Any]:
    """
    Clean up stale analyses.
    
    Marks analyses stuck in processing state as failed.
    Should be run periodically via Celery Beat.
    
    Args:
        hours: Hours after which to consider analysis stale
    
    Returns:
        Dictionary with cleanup results
    """
    from detection.services import AnalysisService
    
    logger.info(f"Running stale analysis cleanup (threshold: {hours} hours)")
    
    try:
        service = AnalysisService()
        count = service.cleanup_stale_analyses(hours=hours)
        
        return {
            "success": True,
            "cleaned_up": count,
            "threshold_hours": hours,
        }
    
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    bind=True,
    name="detection.tasks.send_webhook_notification",
    queue="webhooks",
    max_retries=5,
    default_retry_delay=60,
)
def send_webhook_notification_task(
    self,
    analysis_id: str,
    webhook_url: str,
) -> dict[str, Any]:
    """
    Send webhook notification for completed analysis.
    
    Delivers analysis results to registered webhook URL.
    Retries with exponential backoff on failure.
    
    Args:
        analysis_id: Analysis UUID
        webhook_url: Destination webhook URL
    
    Returns:
        Dictionary with delivery status
    """
    import requests
    from detection.models import Analysis
    
    logger.info(
        f"Sending webhook notification",
        extra={
            "analysis_id": analysis_id,
            "webhook_url": webhook_url,
        },
    )
    
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        
        # Build payload
        payload = {
            "event": "analysis.completed",
            "analysis_id": str(analysis.id),
            "status": analysis.status,
            "result": analysis.result,
            "confidence": analysis.confidence,
            "timestamp": analysis.completed_at.isoformat() if analysis.completed_at else None,
        }
        
        # Send webhook
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Aletheia-Webhook/1.0",
                "X-Aletheia-Event": "analysis.completed",
                "X-Aletheia-Delivery": self.request.id,
            },
            timeout=30,
        )
        
        response.raise_for_status()
        
        # Mark as sent
        analysis.webhook_sent = True
        analysis.save(update_fields=["webhook_sent"])
        
        logger.info(
            f"Webhook delivered successfully",
            extra={
                "analysis_id": analysis_id,
                "status_code": response.status_code,
            },
        )
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "status_code": response.status_code,
        }
    
    except requests.RequestException as e:
        logger.warning(
            f"Webhook delivery failed: {e}",
            extra={
                "analysis_id": analysis_id,
                "webhook_url": webhook_url,
                "retry_count": self.request.retries,
            },
        )
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(
                f"Webhook delivery permanently failed after {self.max_retries} retries",
                extra={"analysis_id": analysis_id},
            )
            return {
                "success": False,
                "analysis_id": analysis_id,
                "error": str(e),
            }
    
    except Exception as e:
        logger.error(f"Webhook notification error: {e}")
        return {
            "success": False,
            "analysis_id": analysis_id,
            "error": str(e),
        }


# =============================================================================
# Report Tasks
# =============================================================================

@shared_task(
    name="detection.tasks.generate_report",
    queue="reports",
)
def generate_report_task(
    analysis_id: str,
    report_type: str = "summary",
    format: str = "pdf",
) -> dict[str, Any]:
    """
    Generate analysis report asynchronously.
    
    Args:
        analysis_id: Analysis UUID
        report_type: Report type (summary/detailed/technical/executive)
        format: Output format (pdf/json/csv/html)
    
    Returns:
        Dictionary with report information
    """
    from detection.services import ReportService
    from detection.services.report_service import ReportOptions
    
    logger.info(
        f"Generating report",
        extra={
            "analysis_id": analysis_id,
            "report_type": report_type,
            "format": format,
        },
    )
    
    try:
        service = ReportService()
        options = ReportOptions(
            report_type=report_type,
            format=format,
        )
        
        report = service.generate_report(
            analysis_id=analysis_id,
            options=options,
        )
        
        return {
            "success": True,
            "report_id": str(report.id),
            "analysis_id": analysis_id,
            "format": format,
            "filename": report.filename,
        }
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "success": False,
            "analysis_id": analysis_id,
            "error": str(e),
        }


# =============================================================================
# Maintenance Tasks
# =============================================================================

@shared_task(
    name="detection.tasks.cleanup_temp_files",
    queue="maintenance",
)
def cleanup_temp_files_task(max_age_hours: int = 24) -> dict[str, Any]:
    """Clean up temporary files older than specified hours."""
    from detection.services import MediaService
    
    logger.info(f"Cleaning up temp files (age > {max_age_hours} hours)")
    
    try:
        service = MediaService()
        count = service.cleanup_temp_files(max_age_hours=max_age_hours)
        
        return {
            "success": True,
            "files_deleted": count,
        }
    
    except Exception as e:
        logger.error(f"Temp file cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(
    name="detection.tasks.cleanup_expired_reports",
    queue="maintenance",
)
def cleanup_expired_reports_task() -> dict[str, Any]:
    """Delete expired reports."""
    from detection.services import ReportService
    
    logger.info("Cleaning up expired reports")
    
    try:
        service = ReportService()
        count = service.delete_expired_reports()
        
        return {
            "success": True,
            "reports_deleted": count,
        }
    
    except Exception as e:
        logger.error(f"Report cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
