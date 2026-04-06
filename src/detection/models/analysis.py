"""
Analysis Models

Core models for deepfake detection analysis:
    - Analysis: Main analysis job entity
    - AnalysisFrame: Per-frame analysis results
"""

from __future__ import annotations

import uuid
from typing import Any, Final

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.types import AnalysisStatus, DetectionResult, ConfidenceLevel


class AnalysisManager(models.Manager):
    """Custom manager for Analysis model with common queries."""
    
    def pending(self):
        """Get pending analyses."""
        return self.filter(status=AnalysisStatus.PENDING.value)
    
    def processing(self):
        """Get analyses currently being processed."""
        return self.filter(status=AnalysisStatus.PROCESSING.value)
    
    def completed(self):
        """Get completed analyses."""
        return self.filter(status=AnalysisStatus.COMPLETED.value)
    
    def failed(self):
        """Get failed analyses."""
        return self.filter(status=AnalysisStatus.FAILED.value)
    
    def for_user(self, user):
        """Get analyses for a specific user."""
        return self.filter(user=user)
    
    def recent(self, days: int = 7):
        """Get analyses from the last N days."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)


class Analysis(models.Model):
    """
    Core analysis job model.
    
    Represents a deepfake detection analysis request. Tracks the
    full lifecycle from submission to completion.
    
    Attributes:
        id: Unique UUID identifier
        user: User who submitted the analysis
        media_file: Associated uploaded video
        status: Current job status
        result: Detection result (real/fake/uncertain)
        confidence: Confidence percentage
        processing_time: Time taken for analysis
    
    Example:
        >>> analysis = Analysis.objects.create(
        ...     user=request.user,
        ...     media_file=uploaded_video,
        ...     sequence_length=60,
        ... )
        >>> print(analysis.status)  # 'pending'
    """
    
    # Status choices for Django admin
    STATUS_CHOICES: Final = [
        (AnalysisStatus.PENDING.value, "Pending"),
        (AnalysisStatus.PROCESSING.value, "Processing"),
        (AnalysisStatus.COMPLETED.value, "Completed"),
        (AnalysisStatus.FAILED.value, "Failed"),
        (AnalysisStatus.CANCELLED.value, "Cancelled"),
    ]
    
    RESULT_CHOICES: Final = [
        (DetectionResult.REAL.value, "Real"),
        (DetectionResult.FAKE.value, "Fake"),
        (DetectionResult.UNCERTAIN.value, "Uncertain"),
    ]
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique analysis identifier",
    )
    
    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyses",
        help_text="User who submitted the analysis",
    )
    
    media_file = models.ForeignKey(
        "detection.MediaFile",
        on_delete=models.CASCADE,
        related_name="analyses",
        help_text="Associated video file",
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AnalysisStatus.PENDING.value,
        db_index=True,
        help_text="Current analysis status",
    )
    
    # Analysis configuration
    sequence_length = models.PositiveIntegerField(
        default=60,
        help_text="Number of frames to analyze",
    )
    
    model_used = models.CharField(
        max_length=100,
        blank=True,
        default="ensemble",
        help_text="ML model(s) used for analysis",
    )
    
    # Results
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Detection result (real/fake/uncertain)",
    )
    
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence percentage (0-100)",
    )
    
    confidence_level = models.CharField(
        max_length=20,
        blank=True,
        help_text="Confidence category (low/medium/high/very_high)",
    )
    
    # Metrics
    frames_analyzed = models.PositiveIntegerField(
        default=0,
        help_text="Number of frames actually analyzed",
    )
    
    faces_detected = models.PositiveIntegerField(
        default=0,
        help_text="Number of faces detected in video",
    )
    
    processing_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Analysis duration in seconds",
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if analysis failed",
    )
    
    error_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Error code for failed analyses",
    )
    
    # Celery task tracking
    task_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Celery task ID for async processing",
    )
    
    # Progress tracking
    progress = models.FloatField(
        default=0.0,
        help_text="Processing progress (0-100)",
    )
    
    progress_message = models.CharField(
        max_length=255,
        blank=True,
        help_text="Current processing stage description",
    )
    
    # Webhook notification
    webhook_url = models.URLField(
        blank=True,
        help_text="URL to notify when analysis completes",
    )
    
    webhook_sent = models.BooleanField(
        default=False,
        help_text="Whether webhook notification was sent",
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When analysis was submitted",
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When processing started",
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When analysis completed",
    )
    
    # Metadata (JSON field for extensibility)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional analysis metadata",
    )
    
    # Custom manager
    objects = AnalysisManager()
    
    class Meta:
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["result", "confidence"]),
        ]
    
    def __str__(self) -> str:
        return f"Analysis {self.id} ({self.status})"
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, status={self.status}, result={self.result})>"
    
    # ==========================================================================
    # Properties
    # ==========================================================================
    
    @property
    def is_pending(self) -> bool:
        """Check if analysis is pending."""
        return self.status == AnalysisStatus.PENDING.value
    
    @property
    def is_processing(self) -> bool:
        """Check if analysis is currently processing."""
        return self.status == AnalysisStatus.PROCESSING.value
    
    @property
    def is_completed(self) -> bool:
        """Check if analysis has completed."""
        return self.status == AnalysisStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """Check if analysis failed."""
        return self.status == AnalysisStatus.FAILED.value
    
    @property
    def is_terminal(self) -> bool:
        """Check if analysis is in a terminal state."""
        return self.status in (
            AnalysisStatus.COMPLETED.value,
            AnalysisStatus.FAILED.value,
            AnalysisStatus.CANCELLED.value,
        )
    
    @property
    def is_fake(self) -> bool | None:
        """Check if result indicates fake video."""
        if self.result is None:
            return None
        return self.result == DetectionResult.FAKE.value
    
    @property
    def is_real(self) -> bool | None:
        """Check if result indicates real video."""
        if self.result is None:
            return None
        return self.result == DetectionResult.REAL.value
    
    @property
    def duration(self) -> float | None:
        """Get analysis duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    # ==========================================================================
    # Methods
    # ==========================================================================
    
    def start_processing(self) -> None:
        """Mark analysis as started."""
        self.status = AnalysisStatus.PROCESSING.value
        self.started_at = timezone.now()
        self.progress = 0.0
        self.progress_message = "Starting analysis..."
        self.save(update_fields=[
            "status", "started_at", "progress", "progress_message"
        ])
    
    def update_progress(
        self,
        progress: float,
        message: str = "",
    ) -> None:
        """
        Update processing progress.
        
        Args:
            progress: Progress percentage (0-100)
            message: Current stage description
        """
        self.progress = min(max(progress, 0), 100)
        if message:
            self.progress_message = message
        self.save(update_fields=["progress", "progress_message"])
    
    def complete(
        self,
        result: str,
        confidence: float,
        frames_analyzed: int = 0,
        faces_detected: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Mark analysis as completed with results.
        
        Args:
            result: Detection result (real/fake/uncertain)
            confidence: Confidence percentage
            frames_analyzed: Number of frames processed
            faces_detected: Number of faces found
            metadata: Additional result metadata
        """
        self.status = AnalysisStatus.COMPLETED.value
        self.completed_at = timezone.now()
        self.result = result.lower()
        self.confidence = confidence
        self.confidence_level = ConfidenceLevel.from_score(confidence).value
        self.frames_analyzed = frames_analyzed
        self.faces_detected = faces_detected
        self.progress = 100.0
        self.progress_message = "Analysis complete"
        
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        
        if metadata:
            self.metadata.update(metadata)
        
        self.save()
    
    def fail(
        self,
        error_message: str,
        error_code: str = "",
    ) -> None:
        """
        Mark analysis as failed.
        
        Args:
            error_message: Human-readable error description
            error_code: Error code for categorization
        """
        self.status = AnalysisStatus.FAILED.value
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.error_code = error_code
        self.progress_message = "Analysis failed"
        
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
        
        self.save()
    
    def cancel(self) -> None:
        """Cancel pending or processing analysis."""
        if not self.is_terminal:
            self.status = AnalysisStatus.CANCELLED.value
            self.completed_at = timezone.now()
            self.progress_message = "Analysis cancelled"
            self.save(update_fields=[
                "status", "completed_at", "progress_message"
            ])
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "status": self.status,
            "result": self.result,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "frames_analyzed": self.frames_analyzed,
            "faces_detected": self.faces_detected,
            "processing_time": self.processing_time,
            "model_used": self.model_used,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "error_message": self.error_message if self.is_failed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AnalysisFrame(models.Model):
    """
    Frame-level analysis result.
    
    Stores detailed results for each analyzed frame, enabling
    frame-by-frame visualization and debugging.
    
    Attributes:
        analysis: Parent analysis
        frame_index: Frame position in video
        timestamp_ms: Frame timestamp in milliseconds
        prediction: Frame-level prediction
        confidence: Frame-level confidence
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name="frames",
    )
    
    frame_index = models.PositiveIntegerField(
        help_text="Frame position in video sequence",
    )
    
    timestamp_ms = models.FloatField(
        help_text="Frame timestamp in milliseconds",
    )
    
    # Detection results
    prediction = models.CharField(
        max_length=20,
        help_text="Frame-level prediction",
    )
    
    confidence = models.FloatField(
        help_text="Frame-level confidence (0-100)",
    )
    
    # Face detection
    face_detected = models.BooleanField(
        default=True,
        help_text="Whether a face was detected in this frame",
    )
    
    face_bbox = models.JSONField(
        null=True,
        blank=True,
        help_text="Face bounding box coordinates",
    )
    
    # Generated assets
    thumbnail_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to frame thumbnail",
    )
    
    heatmap_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to attention heatmap",
    )
    
    # Feature data (optional)
    features = models.JSONField(
        null=True,
        blank=True,
        help_text="Extracted feature data",
    )
    
    class Meta:
        verbose_name = "Analysis Frame"
        verbose_name_plural = "Analysis Frames"
        ordering = ["analysis", "frame_index"]
        unique_together = [["analysis", "frame_index"]]
    
    def __str__(self) -> str:
        return f"Frame {self.frame_index} of {self.analysis_id}"
