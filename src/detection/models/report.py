"""
Report Model

Handles analysis report generation, storage, and access control.
Reports provide detailed summaries of deepfake detection analyses.
"""

from __future__ import annotations

import uuid
from typing import Any, Final

from django.conf import settings
from django.db import models
from django.utils import timezone


def report_upload_path(instance: "Report", filename: str) -> str:
    """Generate upload path for report files."""
    now = timezone.now()
    return f"reports/{now.year}/{now.month:02d}/{instance.analysis_id}/{filename}"


class ReportManager(models.Manager):
    """Custom manager for Report model."""
    
    def for_user(self, user):
        """Get reports for a specific user."""
        return self.filter(analysis__user=user)
    
    def public(self):
        """Get public reports."""
        return self.filter(is_public=True)
    
    def recent(self, days: int = 30):
        """Get reports from the last N days."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)


class Report(models.Model):
    """
    Analysis report model.
    
    Stores generated reports with various output formats (PDF, JSON, CSV).
    Includes access control and download tracking.
    
    Attributes:
        analysis: Source analysis
        format: Report format (pdf/json/csv)
        file: Generated report file
        download_count: Number of downloads
    """
    
    FORMAT_CHOICES: Final = [
        ("pdf", "PDF"),
        ("json", "JSON"),
        ("csv", "CSV"),
        ("html", "HTML"),
    ]
    
    TYPE_CHOICES: Final = [
        ("summary", "Summary Report"),
        ("detailed", "Detailed Report"),
        ("technical", "Technical Report"),
        ("executive", "Executive Summary"),
    ]
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique report identifier",
    )
    
    # Relationships
    analysis = models.ForeignKey(
        "detection.Analysis",
        on_delete=models.CASCADE,
        related_name="reports",
        help_text="Source analysis",
    )
    
    # Report configuration
    report_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="summary",
        help_text="Type of report",
    )
    
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default="pdf",
        help_text="Report file format",
    )
    
    # Generated file
    file = models.FileField(
        upload_to=report_upload_path,
        blank=True,
        null=True,
        help_text="Generated report file",
    )
    
    file_size = models.BigIntegerField(
        default=0,
        help_text="Report file size in bytes",
    )
    
    # Report content (for JSON/HTML inline storage)
    content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Report content for JSON format",
    )
    
    # Access control
    is_public = models.BooleanField(
        default=False,
        help_text="Whether report is publicly accessible",
    )
    
    access_token = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Token for secure report access",
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Report expiration timestamp",
    )
    
    # Usage tracking
    download_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times report was downloaded",
    )
    
    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last download timestamp",
    )
    
    # Generation metadata
    generated_by = models.CharField(
        max_length=100,
        default="system",
        help_text="Who/what generated the report",
    )
    
    generation_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken to generate report in seconds",
    )
    
    # Report options used
    options = models.JSONField(
        default=dict,
        blank=True,
        help_text="Options used during generation",
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Report generation timestamp",
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp",
    )
    
    # Custom manager
    objects = ReportManager()
    
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["analysis", "format"]),
            models.Index(fields=["access_token"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.report_type} Report ({self.format}) for {self.analysis_id}"
    
    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type={self.report_type}, format={self.format})>"
    
    # ==========================================================================
    # Properties
    # ==========================================================================
    
    @property
    def is_expired(self) -> bool:
        """Check if report has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_accessible(self) -> bool:
        """Check if report can be accessed."""
        return not self.is_expired and (self.is_public or bool(self.access_token))
    
    @property
    def file_exists(self) -> bool:
        """Check if report file exists."""
        try:
            return self.file and self.file.storage.exists(self.file.name)
        except Exception:
            return False
    
    @property
    def filename(self) -> str:
        """Get report filename."""
        analysis_id = str(self.analysis_id)[:8]
        return f"aletheia_report_{analysis_id}_{self.report_type}.{self.format}"
    
    @property
    def size_kb(self) -> float:
        """Get file size in kilobytes."""
        return self.file_size / 1024 if self.file_size else 0.0
    
    # ==========================================================================
    # Methods
    # ==========================================================================
    
    def generate_access_token(self) -> str:
        """
        Generate a secure access token for the report.
        
        Returns:
            Generated access token
        """
        import secrets
        
        self.access_token = secrets.token_urlsafe(32)
        self.save(update_fields=["access_token"])
        return self.access_token
    
    def record_download(self) -> None:
        """Record a download event."""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=["download_count", "last_downloaded_at"])
    
    def set_expiration(self, hours: int = 24) -> None:
        """
        Set report expiration.
        
        Args:
            hours: Number of hours until expiration
        """
        self.expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.save(update_fields=["expires_at"])
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "analysis_id": str(self.analysis_id),
            "report_type": self.report_type,
            "format": self.format,
            "filename": self.filename,
            "file_size": self.file_size,
            "size_kb": round(self.size_kb, 2),
            "is_public": self.is_public,
            "download_count": self.download_count,
            "is_expired": self.is_expired,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def save(self, *args, **kwargs) -> None:
        """Override save to auto-generate access token."""
        if not self.access_token and not self.is_public:
            import secrets
            self.access_token = secrets.token_urlsafe(32)
        
        super().save(*args, **kwargs)


class ReportDownload(models.Model):
    """
    Tracks individual report download events.
    
    Provides detailed audit trail of who accessed reports and when.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_downloads",
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Requester IP address",
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/client user agent",
    )
    
    referer = models.URLField(
        blank=True,
        help_text="Referring URL",
    )
    
    # Timestamp
    downloaded_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    
    class Meta:
        verbose_name = "Report Download"
        verbose_name_plural = "Report Downloads"
        ordering = ["-downloaded_at"]
    
    def __str__(self) -> str:
        return f"Download of {self.report_id} at {self.downloaded_at}"
