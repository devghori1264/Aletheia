"""
Aletheia Application Constants

Centralized constants used throughout the Aletheia platform.
These constants are frozen and should never be modified at runtime.

Categories:
    - Application metadata
    - File constraints
    - Model parameters
    - Analysis thresholds
    - API rate limits
    - Cache keys

Note:
    For environment-specific configuration, use Django settings instead.
    Constants defined here are invariant across all environments.
"""

from __future__ import annotations

from typing import Final


# =============================================================================
# APPLICATION METADATA
# =============================================================================

APP_NAME: Final[str] = "Aletheia"
APP_DESCRIPTION: Final[str] = "Enterprise-Grade Deepfake Detection Platform"
APP_VERSION: Final[str] = "2.0.0"
APP_CODENAME: Final[str] = "Truth Unveiled"


# =============================================================================
# FILE CONSTRAINTS
# =============================================================================

# Maximum file sizes (in bytes)
MAX_VIDEO_SIZE_BYTES: Final[int] = 500 * 1024 * 1024  # 500 MB
MAX_IMAGE_SIZE_BYTES: Final[int] = 50 * 1024 * 1024  # 50 MB
MAX_BATCH_SIZE_BYTES: Final[int] = 2 * 1024 * 1024 * 1024  # 2 GB

# Allowed video extensions (lowercase, with dot prefix)
ALLOWED_VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".3gp",
    ".m4v",
    ".gif",
})

# Allowed video MIME types
ALLOWED_VIDEO_MIME_TYPES: Final[frozenset[str]] = frozenset({
    "video/mp4",
    "video/avi",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/3gpp",
    "video/x-ms-wmv",
    "video/x-m4v",
    "image/gif",  # Animated GIFs
})

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
})


# =============================================================================
# VIDEO PROCESSING
# =============================================================================

# Frame extraction
MIN_FRAMES_REQUIRED: Final[int] = 5
MAX_FRAMES_ALLOWED: Final[int] = 300
DEFAULT_SEQUENCE_LENGTH: Final[int] = 60

# Frame rate handling
MIN_FPS: Final[float] = 1.0
MAX_FPS: Final[float] = 120.0
TARGET_FPS: Final[float] = 30.0

# Video duration limits (seconds)
MIN_VIDEO_DURATION: Final[float] = 0.5
MAX_VIDEO_DURATION: Final[float] = 600.0  # 10 minutes


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

# Standard image sizes for model input
MODEL_INPUT_SIZES: Final[dict[str, tuple[int, int]]] = {
    "efficientnet": (224, 224),
    "resnext": (224, 224),
    "xception": (299, 299),
}

DEFAULT_IMAGE_SIZE: Final[tuple[int, int]] = (224, 224)

# ImageNet normalization parameters
IMAGENET_MEAN: Final[tuple[float, float, float]] = (0.485, 0.456, 0.406)
IMAGENET_STD: Final[tuple[float, float, float]] = (0.229, 0.224, 0.225)

# Color channels
RGB_CHANNELS: Final[int] = 3
RGBA_CHANNELS: Final[int] = 4
GRAYSCALE_CHANNELS: Final[int] = 1


# =============================================================================
# FACE DETECTION
# =============================================================================

# Detection thresholds
FACE_DETECTION_CONFIDENCE_THRESHOLD: Final[float] = 0.7
FACE_DETECTION_NMS_THRESHOLD: Final[float] = 0.3

# Face size constraints (pixels)
MIN_FACE_SIZE: Final[int] = 40
MAX_FACE_SIZE: Final[int] = 1000
OPTIMAL_FACE_SIZE: Final[int] = 150

# Face cropping
FACE_PADDING_RATIO: Final[float] = 0.25
FACE_PADDING_PIXELS: Final[int] = 40

# Tracking parameters
MAX_FACES_TO_TRACK: Final[int] = 5
FACE_TRACKING_IOU_THRESHOLD: Final[float] = 0.5


# =============================================================================
# MODEL PARAMETERS
# =============================================================================

# Architecture parameters
LSTM_HIDDEN_DIM: Final[int] = 2048
LSTM_LAYERS: Final[int] = 1
TRANSFORMER_HEADS: Final[int] = 8
TRANSFORMER_LAYERS: Final[int] = 4
DROPOUT_RATE: Final[float] = 0.4

# Feature dimensions
RESNEXT_FEATURE_DIM: Final[int] = 2048
EFFICIENTNET_FEATURE_DIM: Final[int] = 1792
XCEPTION_FEATURE_DIM: Final[int] = 2048

# Batch processing
DEFAULT_BATCH_SIZE: Final[int] = 8
MIN_BATCH_SIZE: Final[int] = 1
MAX_BATCH_SIZE: Final[int] = 64

# Number of classes (real, fake)
NUM_CLASSES: Final[int] = 2


# =============================================================================
# ANALYSIS THRESHOLDS
# =============================================================================

# Classification threshold
FAKE_THRESHOLD: Final[float] = 0.5

# Confidence levels
CONFIDENCE_LOW_THRESHOLD: Final[float] = 70.0
CONFIDENCE_MEDIUM_THRESHOLD: Final[float] = 85.0
CONFIDENCE_HIGH_THRESHOLD: Final[float] = 95.0

# Uncertainty threshold
UNCERTAINTY_THRESHOLD: Final[float] = 0.15

# Ensemble agreement
MIN_ENSEMBLE_AGREEMENT: Final[float] = 0.6


# =============================================================================
# ENSEMBLE CONFIGURATION
# =============================================================================

DEFAULT_ENSEMBLE_WEIGHTS: Final[dict[str, float]] = {
    "efficientnet_lstm": 0.40,
    "resnext_transformer": 0.35,
    "xception": 0.25,
}


# =============================================================================
# API CONFIGURATION
# =============================================================================

# Rate limiting (requests per time window)
RATE_LIMIT_ANON_REQUESTS: Final[int] = 100
RATE_LIMIT_ANON_WINDOW: Final[str] = "hour"
RATE_LIMIT_USER_REQUESTS: Final[int] = 1000
RATE_LIMIT_USER_WINDOW: Final[str] = "hour"
RATE_LIMIT_ANALYSIS_REQUESTS: Final[int] = 50
RATE_LIMIT_ANALYSIS_WINDOW: Final[str] = "hour"

# Pagination
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Request timeouts (seconds)
REQUEST_TIMEOUT: Final[int] = 30
ANALYSIS_TIMEOUT: Final[int] = 1800  # 30 minutes
WEBHOOK_TIMEOUT: Final[int] = 30


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache key prefixes
CACHE_PREFIX: Final[str] = "aletheia"
CACHE_KEY_ANALYSIS: Final[str] = f"{CACHE_PREFIX}:analysis"
CACHE_KEY_USER: Final[str] = f"{CACHE_PREFIX}:user"
CACHE_KEY_MODEL: Final[str] = f"{CACHE_PREFIX}:model"
CACHE_KEY_RATE_LIMIT: Final[str] = f"{CACHE_PREFIX}:ratelimit"

# Cache TTL (seconds)
CACHE_TTL_ANALYSIS: Final[int] = 3600  # 1 hour
CACHE_TTL_USER: Final[int] = 300  # 5 minutes
CACHE_TTL_MODEL_METADATA: Final[int] = 86400  # 24 hours
CACHE_TTL_RATE_LIMIT: Final[int] = 3600  # 1 hour


# =============================================================================
# CELERY TASK CONFIGURATION
# =============================================================================

# Task names
TASK_ANALYZE_VIDEO: Final[str] = "detection.tasks.analyze_video"
TASK_GENERATE_REPORT: Final[str] = "detection.tasks.generate_report"
TASK_CLEANUP_FILES: Final[str] = "detection.tasks.cleanup_files"

# Queue names
QUEUE_DEFAULT: Final[str] = "default"
QUEUE_ANALYSIS: Final[str] = "analysis"
QUEUE_REPORTS: Final[str] = "reports"

# Task retry configuration
MAX_TASK_RETRIES: Final[int] = 3
RETRY_BACKOFF_BASE: Final[int] = 60  # seconds


# =============================================================================
# LOGGING
# =============================================================================

# Log message formats
LOG_FORMAT_SIMPLE: Final[str] = "{levelname} {asctime} {module} {message}"
LOG_FORMAT_VERBOSE: Final[str] = (
    "{levelname} {asctime} {module} {process:d} {thread:d} {message}"
)
LOG_FORMAT_JSON: Final[str] = "%(asctime)s %(levelname)s %(name)s %(message)s"

# Log file settings
LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: Final[int] = 5


# =============================================================================
# HTTP STATUS MESSAGES
# =============================================================================

HTTP_MESSAGES: Final[dict[int, str]] = {
    200: "Success",
    201: "Created",
    202: "Accepted - Analysis queued",
    204: "No Content",
    400: "Bad Request - Invalid input",
    401: "Unauthorized - Authentication required",
    403: "Forbidden - Insufficient permissions",
    404: "Not Found",
    413: "Payload Too Large - File size exceeds limit",
    415: "Unsupported Media Type - Invalid file format",
    422: "Unprocessable Entity - Validation failed",
    429: "Too Many Requests - Rate limit exceeded",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


# =============================================================================
# DETECTION LABELS
# =============================================================================

LABEL_REAL: Final[str] = "REAL"
LABEL_FAKE: Final[str] = "FAKE"
LABEL_UNCERTAIN: Final[str] = "UNCERTAIN"

LABEL_DESCRIPTIONS: Final[dict[str, str]] = {
    LABEL_REAL: "The video appears to be authentic",
    LABEL_FAKE: "The video shows signs of manipulation",
    LABEL_UNCERTAIN: "Unable to determine authenticity with confidence",
}


# =============================================================================
# STRUCTURED CONSTANTS (Class-based)
# =============================================================================


class FileConstraints:
    """File size and dimension constraints for uploads."""
    
    MAX_VIDEO_SIZE_BYTES: Final[int] = MAX_VIDEO_SIZE_BYTES
    MAX_IMAGE_SIZE_BYTES: Final[int] = MAX_IMAGE_SIZE_BYTES  
    MAX_BATCH_SIZE_BYTES: Final[int] = MAX_BATCH_SIZE_BYTES
    MIN_VIDEO_DIMENSION: Final[int] = 224  # Minimum width or height in pixels
    MAX_VIDEO_DURATION_SECONDS: Final[float] = MAX_VIDEO_DURATION


class SupportedFormats:
    """Supported file formats for media uploads."""
    
    VIDEO_EXTENSIONS: Final[tuple[str, ...]] = ("mp4", "avi", "mov", "mkv", "webm", "flv", "wmv")
    IMAGE_EXTENSIONS: Final[tuple[str, ...]] = ("jpg", "jpeg", "png", "webp", "bmp")
    ALL_EXTENSIONS: Final[tuple[str, ...]] = VIDEO_EXTENSIONS + IMAGE_EXTENSIONS


class AnalysisSettings:
    """Default settings for analysis operations."""
    
    DEFAULT_SEQUENCE_LENGTH: Final[int] = DEFAULT_SEQUENCE_LENGTH
    DEFAULT_BATCH_SIZE: Final[int] = DEFAULT_BATCH_SIZE
    USE_ENSEMBLE: Final[bool] = True
    GENERATE_HEATMAPS: Final[bool] = True
    FAKE_THRESHOLD: Final[float] = FAKE_THRESHOLD


class ModelSettings:
    """Model configuration settings."""
    
    ENSEMBLE_ENABLED: Final[bool] = True
    DEFAULT_MODEL: Final[str] = "efficientnet_lstm"
    AVAILABLE_MODELS: Final[tuple[str, ...]] = (
        "efficientnet_lstm",
        "xception",
        "efficientnet_b4",
        "ensemble",
    )
    CONFIDENCE_THRESHOLD: Final[float] = 0.5
    HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.85


__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "MAX_VIDEO_SIZE_BYTES",
    "MAX_IMAGE_SIZE_BYTES",
    "ALLOWED_VIDEO_EXTENSIONS",
    "ALLOWED_IMAGE_EXTENSIONS",
    "FAKE_THRESHOLD",
    "FileConstraints",
    "SupportedFormats",
    "AnalysisSettings",
    "ModelSettings",
]
