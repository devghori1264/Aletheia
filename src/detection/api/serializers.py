"""
API Serializers

Django REST Framework serializers for deepfake detection API.
Handles request validation and response formatting.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.constants import (
    AnalysisSettings,
    FileConstraints,
    SupportedFormats,
)


User = get_user_model()


# =============================================================================
# Media Serializers
# =============================================================================

class MediaUploadSerializer(serializers.Serializer):
    """
    Serializer for media file uploads.
    
    Validates uploaded files against size and format constraints.
    """
    
    file = serializers.FileField(
        help_text="Video or image file to analyze",
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size
        max_size = FileConstraints.MAX_VIDEO_SIZE_BYTES
        if value.size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = value.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large: {actual_mb:.1f}MB (maximum: {max_mb}MB)"
            )
        
        # Check extension
        filename = value.name.lower()
        allowed_extensions = (
            SupportedFormats.VIDEO_EXTENSIONS +
            SupportedFormats.IMAGE_EXTENSIONS
        )
        
        has_valid_ext = any(filename.endswith(f".{ext}") for ext in allowed_extensions)
        if not has_valid_ext:
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        return value


class MediaFileSerializer(serializers.Serializer):
    """
    Serializer for MediaFile model output.
    """
    
    id = serializers.UUIDField(read_only=True)
    original_filename = serializers.CharField(read_only=True)
    media_type = serializers.CharField(read_only=True)
    mime_type = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    size_mb = serializers.FloatField(read_only=True)
    status = serializers.CharField(read_only=True)
    resolution = serializers.CharField(read_only=True)
    duration = serializers.FloatField(read_only=True, allow_null=True)
    duration_formatted = serializers.CharField(read_only=True)
    fps = serializers.FloatField(read_only=True, allow_null=True)
    frame_count = serializers.IntegerField(read_only=True, allow_null=True)
    has_audio = serializers.BooleanField(read_only=True)
    thumbnail_url = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


# =============================================================================
# Analysis Serializers
# =============================================================================

class AnalysisConfigSerializer(serializers.Serializer):
    """
    Serializer for analysis configuration options.
    """
    
    sequence_length = serializers.IntegerField(
        required=False,
        default=AnalysisSettings.DEFAULT_SEQUENCE_LENGTH,
        min_value=1,
        max_value=300,
        help_text="Number of frames to analyze",
    )
    
    model_name = serializers.ChoiceField(
        required=False,
        default="ensemble",
        choices=[
            ("ensemble", "Ensemble (Recommended)"),
            ("efficientnet_lstm", "EfficientNet + LSTM"),
            ("resnext_transformer", "ResNeXt + Transformer"),
        ],
        help_text="Detection model to use",
    )
    
    use_ensemble = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Use ensemble of multiple models",
    )
    
    generate_heatmaps = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Generate attention heatmaps",
    )
    
    webhook_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL for completion webhook notification",
    )


class AnalysisSubmitSerializer(serializers.Serializer):
    """
    Serializer for analysis submission.
    
    Combines file upload with configuration options.
    """
    
    file = serializers.FileField(
        help_text="Video or image file to analyze",
    )
    
    config = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Analysis configuration options (JSON)",
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        upload_serializer = MediaUploadSerializer(data={"file": value})
        upload_serializer.is_valid(raise_exception=True)
        return value
    
    def validate_config(self, value):
        """Validate and parse config field."""
        import json
        
        # Handle empty string or None
        if not value or value == '':
            return {}
        
        # If it's already a dict, validate it
        if isinstance(value, dict):
            config_serializer = AnalysisConfigSerializer(data=value)
            if config_serializer.is_valid():
                return config_serializer.validated_data
            return value
        
        # If it's a string, try to parse as JSON
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    config_serializer = AnalysisConfigSerializer(data=parsed)
                    if config_serializer.is_valid():
                        return config_serializer.validated_data
                    return parsed
            except json.JSONDecodeError:
                pass
        
        return {}


class AnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for analysis response.
    """
    
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    result = serializers.CharField(read_only=True, allow_null=True)
    confidence = serializers.FloatField(read_only=True, allow_null=True)
    confidence_level = serializers.CharField(read_only=True)
    frames_analyzed = serializers.IntegerField(read_only=True)
    faces_detected = serializers.IntegerField(read_only=True)
    processing_time = serializers.FloatField(read_only=True, allow_null=True)
    model_used = serializers.CharField(read_only=True)
    progress = serializers.FloatField(read_only=True)
    progress_message = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    
    # Related media
    media_file = MediaFileSerializer(read_only=True)


class AnalysisStatusSerializer(serializers.Serializer):
    """
    Lightweight serializer for status polling.
    """
    
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    progress = serializers.FloatField(read_only=True)
    progress_message = serializers.CharField(read_only=True)
    result = serializers.CharField(read_only=True, allow_null=True)
    confidence = serializers.FloatField(read_only=True, allow_null=True)
    is_terminal = serializers.BooleanField(read_only=True)
    error_message = serializers.CharField(read_only=True, allow_null=True)


class AnalysisListSerializer(serializers.Serializer):
    """
    Serializer for analysis list view.
    """
    
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    result = serializers.CharField(read_only=True, allow_null=True)
    confidence = serializers.FloatField(read_only=True, allow_null=True)
    media_filename = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    
    def get_media_filename(self, obj) -> str:
        return obj.media_file.original_filename if obj.media_file else "Unknown"


class FrameAnalysisSerializer(serializers.Serializer):
    """
    Serializer for frame-level analysis data.
    """
    
    frame_index = serializers.IntegerField(read_only=True)
    timestamp_ms = serializers.FloatField(read_only=True)
    prediction = serializers.CharField(read_only=True)
    confidence = serializers.FloatField(read_only=True)
    face_detected = serializers.BooleanField(read_only=True)
    face_bbox = serializers.JSONField(read_only=True, allow_null=True)
    thumbnail_url = serializers.CharField(read_only=True, allow_null=True)
    heatmap_url = serializers.CharField(read_only=True, allow_null=True)


# =============================================================================
# Report Serializers
# =============================================================================

class ReportOptionsSerializer(serializers.Serializer):
    """
    Serializer for report generation options.
    """
    
    report_type = serializers.ChoiceField(
        required=False,
        default="summary",
        choices=[
            ("summary", "Summary Report"),
            ("detailed", "Detailed Report"),
            ("technical", "Technical Report"),
            ("executive", "Executive Summary"),
        ],
        help_text="Type of report to generate",
    )
    
    format = serializers.ChoiceField(
        required=False,
        default="pdf",
        choices=[
            ("pdf", "PDF"),
            ("json", "JSON"),
            ("csv", "CSV"),
            ("html", "HTML"),
        ],
        help_text="Report output format",
    )
    
    include_frames = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Include frame-level analysis",
    )
    
    include_heatmaps = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Include attention heatmaps",
    )


class ReportResponseSerializer(serializers.Serializer):
    """
    Serializer for report response.
    """
    
    id = serializers.UUIDField(read_only=True)
    analysis_id = serializers.UUIDField(read_only=True)
    report_type = serializers.CharField(read_only=True)
    format = serializers.CharField(read_only=True)
    filename = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    size_kb = serializers.FloatField(read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    download_count = serializers.IntegerField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


# =============================================================================
# Batch Serializers
# =============================================================================

class BatchSubmitSerializer(serializers.Serializer):
    """
    Serializer for batch analysis submission.
    """
    
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        max_length=20,
        help_text="List of files to analyze (max 20)",
    )
    
    config = AnalysisConfigSerializer(
        required=False,
        help_text="Configuration applied to all analyses",
    )
    
    def validate_files(self, value):
        """Validate all files in batch."""
        for file in value:
            upload_serializer = MediaUploadSerializer(data={"file": file})
            upload_serializer.is_valid(raise_exception=True)
        return value


class BatchStatusSerializer(serializers.Serializer):
    """
    Serializer for batch status response.
    """
    
    batch_id = serializers.CharField(read_only=True)
    total = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    failed = serializers.IntegerField(read_only=True)
    pending = serializers.IntegerField(read_only=True)
    progress = serializers.FloatField(read_only=True)
    analyses = AnalysisStatusSerializer(many=True, read_only=True)


# =============================================================================
# Model Info Serializers
# =============================================================================

class ModelInfoSerializer(serializers.Serializer):
    """
    Serializer for ML model information.
    """
    
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    architecture = serializers.CharField(read_only=True)
    input_size = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True,
    )
    parameters = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    metrics = serializers.DictField(read_only=True)


class ModelMetricsSerializer(serializers.Serializer):
    """
    Serializer for model performance metrics.
    """
    
    accuracy = serializers.FloatField(read_only=True)
    precision = serializers.FloatField(read_only=True)
    recall = serializers.FloatField(read_only=True)
    f1_score = serializers.FloatField(read_only=True)
    auc_roc = serializers.FloatField(read_only=True)
    inference_time_ms = serializers.FloatField(read_only=True)
    dataset = serializers.CharField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)


# =============================================================================
# Webhook Serializers
# =============================================================================

class WebhookRegisterSerializer(serializers.Serializer):
    """
    Serializer for webhook registration.
    """
    
    url = serializers.URLField(
        help_text="Webhook endpoint URL",
    )
    
    events = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ("analysis.completed", "Analysis Completed"),
            ("analysis.failed", "Analysis Failed"),
            ("batch.completed", "Batch Completed"),
        ]),
        help_text="Events to subscribe to",
    )
    
    secret = serializers.CharField(
        required=False,
        max_length=128,
        help_text="Shared secret for webhook signature verification",
    )


class WebhookResponseSerializer(serializers.Serializer):
    """
    Serializer for webhook response.
    """
    
    id = serializers.UUIDField(read_only=True)
    url = serializers.URLField(read_only=True)
    events = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_triggered_at = serializers.DateTimeField(read_only=True, allow_null=True)


# =============================================================================
# Error Serializers
# =============================================================================

class ErrorSerializer(serializers.Serializer):
    """
    Serializer for error responses.
    """
    
    error = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    details = serializers.DictField(read_only=True, allow_null=True)
    timestamp = serializers.DateTimeField(read_only=True)


class ValidationErrorSerializer(serializers.Serializer):
    """
    Serializer for validation error responses.
    """
    
    error = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    fields = serializers.DictField(read_only=True)
