"""
Aletheia Exception Hierarchy

This module defines a comprehensive exception hierarchy for the Aletheia platform.
All custom exceptions inherit from AletheiaError, enabling consistent error handling
across the application.

Exception Categories:
    - Validation Errors: Invalid input data
    - Processing Errors: Analysis/inference failures
    - Resource Errors: File/model not found
    - Service Errors: External service failures
    - Authentication Errors: Auth-related issues

Usage:
    from core.exceptions import VideoProcessingError, ModelNotFoundError
    
    try:
        result = analyze_video(video_path)
    except VideoProcessingError as e:
        logger.error(f"Analysis failed: {e.message}", extra=e.to_dict())
        raise

DRF Integration:
    The custom_exception_handler function integrates these exceptions
    with Django REST Framework for consistent API error responses.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final
from uuid import uuid4

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


# =============================================================================
# ERROR CODES
# =============================================================================

class ErrorCode:
    """
    Centralized error code definitions.
    
    Format: CATEGORY_SPECIFIC_ERROR
    Ranges:
        - 1000-1999: Validation errors
        - 2000-2999: Processing errors
        - 3000-3999: Resource errors
        - 4000-4999: Authentication/Authorization errors
        - 5000-5999: External service errors
        - 9000-9999: Internal/unexpected errors
    """
    
    # Validation errors (1000-1999)
    VALIDATION_ERROR: Final[str] = "E1000"
    INVALID_VIDEO_FORMAT: Final[str] = "E1001"
    INVALID_VIDEO_SIZE: Final[str] = "E1002"
    INVALID_SEQUENCE_LENGTH: Final[str] = "E1003"
    INVALID_PARAMETERS: Final[str] = "E1004"
    MISSING_REQUIRED_FIELD: Final[str] = "E1005"
    
    # Processing errors (2000-2999)
    PROCESSING_ERROR: Final[str] = "E2000"
    VIDEO_PROCESSING_FAILED: Final[str] = "E2001"
    FACE_DETECTION_FAILED: Final[str] = "E2002"
    MODEL_INFERENCE_FAILED: Final[str] = "E2003"
    FRAME_EXTRACTION_FAILED: Final[str] = "E2004"
    ENSEMBLE_VOTING_FAILED: Final[str] = "E2005"
    NO_FACES_DETECTED: Final[str] = "E2006"
    INSUFFICIENT_FRAMES: Final[str] = "E2007"
    
    # Resource errors (3000-3999)
    RESOURCE_ERROR: Final[str] = "E3000"
    FILE_NOT_FOUND: Final[str] = "E3001"
    MODEL_NOT_FOUND: Final[str] = "E3002"
    ANALYSIS_NOT_FOUND: Final[str] = "E3003"
    REPORT_NOT_FOUND: Final[str] = "E3004"
    
    # Authentication errors (4000-4999)
    AUTH_ERROR: Final[str] = "E4000"
    INVALID_CREDENTIALS: Final[str] = "E4001"
    TOKEN_EXPIRED: Final[str] = "E4002"
    PERMISSION_DENIED: Final[str] = "E4003"
    RATE_LIMIT_EXCEEDED: Final[str] = "E4004"
    
    # External service errors (5000-5999)
    SERVICE_ERROR: Final[str] = "E5000"
    GPU_UNAVAILABLE: Final[str] = "E5001"
    STORAGE_UNAVAILABLE: Final[str] = "E5002"
    QUEUE_UNAVAILABLE: Final[str] = "E5003"
    
    # Internal errors (9000-9999)
    INTERNAL_ERROR: Final[str] = "E9000"
    UNEXPECTED_ERROR: Final[str] = "E9999"


# =============================================================================
# BASE EXCEPTION
# =============================================================================

@dataclass
class AletheiaError(Exception):
    """
    Base exception for all Aletheia-specific errors.
    
    Provides structured error information including:
        - Unique error ID for tracing
        - Error code for categorization
        - Human-readable message
        - Additional context data
        - Timestamp
    
    Attributes:
        message: Human-readable error description.
        code: Error code from ErrorCode class.
        details: Additional context information.
        error_id: Unique identifier for this error instance.
        timestamp: When the error occurred.
        http_status: Suggested HTTP status code for API responses.
    
    Example:
        >>> raise AletheiaError(
        ...     message="Video processing failed",
        ...     code=ErrorCode.VIDEO_PROCESSING_FAILED,
        ...     details={"video_id": "abc123", "stage": "frame_extraction"}
        ... )
    """
    
    message: str
    code: str = ErrorCode.INTERNAL_ERROR
    details: dict[str, Any] = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __str__(self) -> str:
        """Return formatted error string."""
        return f"[{self.code}] {self.message} (ID: {self.error_id})"
    
    def __repr__(self) -> str:
        """Return detailed error representation."""
        return (
            f"{self.__class__.__name__}("
            f"code={self.code!r}, "
            f"message={self.message!r}, "
            f"error_id={self.error_id!r})"
        )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of the error.
        """
        return {
            "error_id": self.error_id,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "type": self.__class__.__name__,
        }
    
    def to_api_response(self) -> dict[str, Any]:
        """
        Convert exception to API response format.
        
        Returns:
            Dictionary suitable for JSON API response.
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "error_id": self.error_id,
            }
        }


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================

@dataclass
class ValidationError(AletheiaError):
    """Base exception for validation failures."""
    
    code: str = ErrorCode.VALIDATION_ERROR
    http_status: int = status.HTTP_400_BAD_REQUEST


@dataclass
class InvalidVideoFormatError(ValidationError):
    """Raised when video format is not supported."""
    
    code: str = ErrorCode.INVALID_VIDEO_FORMAT
    
    def __init__(
        self,
        message: str = "Unsupported video format",
        allowed_formats: tuple[str, ...] | None = None,
        received_format: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if allowed_formats:
            details["allowed_formats"] = list(allowed_formats)
        if received_format:
            details["received_format"] = received_format
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class InvalidVideoSizeError(ValidationError):
    """Raised when video size exceeds limits."""
    
    code: str = ErrorCode.INVALID_VIDEO_SIZE
    
    def __init__(
        self,
        message: str = "Video size exceeds maximum allowed",
        max_size_bytes: int | None = None,
        actual_size_bytes: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if max_size_bytes:
            details["max_size_mb"] = max_size_bytes / (1024 * 1024)
        if actual_size_bytes:
            details["actual_size_mb"] = actual_size_bytes / (1024 * 1024)
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class InvalidSequenceLengthError(ValidationError):
    """Raised when sequence length is invalid."""
    
    code: str = ErrorCode.INVALID_SEQUENCE_LENGTH
    
    def __init__(
        self,
        message: str = "Invalid sequence length",
        min_length: int | None = None,
        max_length: int | None = None,
        provided_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if min_length is not None:
            details["min_length"] = min_length
        if max_length is not None:
            details["max_length"] = max_length
        if provided_length is not None:
            details["provided_length"] = provided_length
        super().__init__(message=message, details=details, **kwargs)


# =============================================================================
# PROCESSING EXCEPTIONS
# =============================================================================

@dataclass
class ProcessingError(AletheiaError):
    """Base exception for processing failures."""
    
    code: str = ErrorCode.PROCESSING_ERROR
    http_status: int = status.HTTP_422_UNPROCESSABLE_ENTITY


@dataclass
class VideoProcessingError(ProcessingError):
    """Raised when video processing fails."""
    
    code: str = ErrorCode.VIDEO_PROCESSING_FAILED
    
    def __init__(
        self,
        message: str = "Failed to process video",
        video_path: str | None = None,
        stage: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if video_path:
            details["video_path"] = video_path
        if stage:
            details["processing_stage"] = stage
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class FaceDetectionError(ProcessingError):
    """Raised when face detection fails."""
    
    code: str = ErrorCode.FACE_DETECTION_FAILED


@dataclass
class NoFacesDetectedError(ProcessingError):
    """Raised when no faces are found in the video."""
    
    code: str = ErrorCode.NO_FACES_DETECTED
    
    def __init__(
        self,
        message: str = "No faces detected in the video",
        frames_analyzed: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if frames_analyzed is not None:
            details["frames_analyzed"] = frames_analyzed
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class InsufficientFramesError(ProcessingError):
    """Raised when video has insufficient frames for analysis."""
    
    code: str = ErrorCode.INSUFFICIENT_FRAMES
    
    def __init__(
        self,
        message: str = "Insufficient frames for analysis",
        required_frames: int | None = None,
        available_frames: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if required_frames is not None:
            details["required_frames"] = required_frames
        if available_frames is not None:
            details["available_frames"] = available_frames
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class ModelInferenceError(ProcessingError):
    """Raised when model inference fails."""
    
    code: str = ErrorCode.MODEL_INFERENCE_FAILED
    
    def __init__(
        self,
        message: str = "Model inference failed",
        model_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if model_name:
            details["model_name"] = model_name
        super().__init__(message=message, details=details, **kwargs)


# =============================================================================
# RESOURCE EXCEPTIONS
# =============================================================================

@dataclass
class ResourceError(AletheiaError):
    """Base exception for resource-related errors."""
    
    code: str = ErrorCode.RESOURCE_ERROR
    http_status: int = status.HTTP_404_NOT_FOUND


@dataclass
class ModelNotFoundError(ResourceError):
    """Raised when a required model file is not found."""
    
    code: str = ErrorCode.MODEL_NOT_FOUND
    
    def __init__(
        self,
        message: str = "Model file not found",
        model_name: str | None = None,
        model_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if model_name:
            details["model_name"] = model_name
        if model_path:
            details["model_path"] = model_path
        super().__init__(message=message, details=details, **kwargs)


@dataclass
class AnalysisNotFoundError(ResourceError):
    """Raised when an analysis record is not found."""
    
    code: str = ErrorCode.ANALYSIS_NOT_FOUND
    
    def __init__(
        self,
        message: str = "Analysis not found",
        analysis_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if analysis_id:
            details["analysis_id"] = analysis_id
        super().__init__(message=message, details=details, **kwargs)


# =============================================================================
# SERVICE EXCEPTIONS
# =============================================================================

@dataclass
class ServiceError(AletheiaError):
    """Base exception for external service failures."""
    
    code: str = ErrorCode.SERVICE_ERROR
    http_status: int = status.HTTP_503_SERVICE_UNAVAILABLE


@dataclass
class GPUUnavailableError(ServiceError):
    """Raised when GPU is required but not available."""
    
    code: str = ErrorCode.GPU_UNAVAILABLE
    message: str = "GPU is not available for processing"


class StorageError(AletheiaError):
    """Raised when file storage operations fail."""
    
    code: str = "STORAGE_ERROR"
    message: str = "File storage operation failed"


# =============================================================================
# DRF EXCEPTION HANDLER
# =============================================================================

def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler for Django REST Framework.
    
    Converts AletheiaError exceptions to consistent API responses.
    Falls back to default DRF handling for other exceptions.
    
    Args:
        exc: The exception that was raised.
        context: Dictionary containing request and view context.
    
    Returns:
        Response object or None to use default handling.
    
    Example Response:
        {
            "error": {
                "code": "E2001",
                "message": "Video processing failed",
                "details": {"stage": "frame_extraction"},
                "error_id": "abc12345"
            }
        }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle our custom exceptions
    if isinstance(exc, AletheiaError):
        # Log the error
        logger.error(
            f"API Error: {exc}",
            extra={
                "error_data": exc.to_dict(),
                "path": context.get("request", {}).get("path"),
                "method": context.get("request", {}).get("method"),
            },
        )
        
        return Response(
            exc.to_api_response(),
            status=exc.http_status,
        )
    
    # For unexpected exceptions in debug mode, include traceback
    if response is None:
        request = context.get("request")
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={
                "exception_type": type(exc).__name__,
                "path": request.path if request else None,
            },
        )
    
    return response
