"""
Aletheia Type Definitions

This module provides type definitions, protocols, and type aliases used
throughout the Aletheia platform. Using these definitions ensures:

    - Consistent typing across modules
    - Better IDE support and autocomplete
    - Runtime type checking capability
    - Clear interface definitions

Categories:
    - Tensor Types: PyTorch tensor shapes and types
    - Analysis Types: Detection results and confidence
    - Media Types: Video/image metadata
    - Protocol Definitions: Interface contracts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    NamedTuple,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
    runtime_checkable,
)
from uuid import UUID

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    import torch


# =============================================================================
# GENERIC TYPE VARIABLES
# =============================================================================

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound="BaseModel")
ServiceT = TypeVar("ServiceT", bound="BaseService")


# =============================================================================
# NUMPY/TENSOR TYPE ALIASES
# =============================================================================

# NumPy array types
NDArrayFloat32: TypeAlias = npt.NDArray[np.float32]
NDArrayFloat64: TypeAlias = npt.NDArray[np.float64]
NDArrayUInt8: TypeAlias = npt.NDArray[np.uint8]
NDArrayInt32: TypeAlias = npt.NDArray[np.int32]
NDArrayBool: TypeAlias = npt.NDArray[np.bool_]

# Image types (H, W, C)
ImageArray: TypeAlias = NDArrayUInt8
GrayscaleImage: TypeAlias = NDArrayUInt8  # (H, W)
RGBImage: TypeAlias = NDArrayUInt8  # (H, W, 3)
RGBAImage: TypeAlias = NDArrayUInt8  # (H, W, 4)

# Batch image types (B, H, W, C)
BatchImageArray: TypeAlias = NDArrayUInt8

# Feature vectors
FeatureVector: TypeAlias = NDArrayFloat32  # (D,)
FeatureMatrix: TypeAlias = NDArrayFloat32  # (N, D)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class AnalysisStatus(str, Enum):
    """
    Status of an analysis job.
    
    Lifecycle: PENDING -> PROCESSING -> (COMPLETED | FAILED)
    """
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal (final) status."""
        return self in (
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        )
    
    def is_active(self) -> bool:
        """Check if analysis is still active."""
        return self in (AnalysisStatus.PENDING, AnalysisStatus.PROCESSING)


class DetectionResult(str, Enum):
    """Classification result of deepfake detection."""
    
    REAL = "real"
    FAKE = "fake"
    UNCERTAIN = "uncertain"
    
    @classmethod
    def from_prediction(cls, prediction: int) -> "DetectionResult":
        """
        Convert model prediction to detection result.
        
        Args:
            prediction: Model output (0 = fake, 1 = real)
        
        Returns:
            Corresponding DetectionResult
        """
        return cls.REAL if prediction == 1 else cls.FAKE


class ConfidenceLevel(str, Enum):
    """Confidence level categories."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    
    @classmethod
    def from_score(cls, confidence: float) -> "ConfidenceLevel":
        """
        Categorize confidence score into levels.
        
        Args:
            confidence: Confidence percentage (0-100)
        
        Returns:
            Appropriate confidence level
        """
        if confidence >= 95:
            return cls.VERY_HIGH
        elif confidence >= 85:
            return cls.HIGH
        elif confidence >= 70:
            return cls.MEDIUM
        else:
            return cls.LOW


class ModelArchitecture(str, Enum):
    """Supported model architectures."""
    
    EFFICIENTNET_LSTM = "efficientnet_lstm"
    RESNEXT_TRANSFORMER = "resnext_transformer"
    XCEPTION = "xception"
    ENSEMBLE = "ensemble"


class VideoCodec(str, Enum):
    """Supported video codecs."""
    
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"
    UNKNOWN = "unknown"


# =============================================================================
# TYPED DICTIONARIES
# =============================================================================

class BoundingBox(TypedDict):
    """Face bounding box coordinates."""
    
    x: int
    y: int
    width: int
    height: int


class FaceDetectionResult(TypedDict):
    """Result of face detection on a single frame."""
    
    frame_index: int
    faces: list[BoundingBox]
    confidence_scores: list[float]


class FrameAnalysis(TypedDict):
    """Analysis result for a single frame."""
    
    frame_index: int
    timestamp_ms: float
    prediction: str
    confidence: float
    face_bbox: BoundingBox | None
    attention_map: str | None  # Path to attention heatmap


class ModelPrediction(TypedDict):
    """Raw model prediction output."""
    
    logits: list[float]
    prediction: int
    confidence: float
    feature_map: Any | None


class EnsemblePrediction(TypedDict):
    """Combined ensemble model prediction."""
    
    prediction: str
    confidence: float
    model_predictions: dict[str, ModelPrediction]
    weights_used: dict[str, float]
    agreement_score: float


class VideoMetadata(TypedDict):
    """Video file metadata."""
    
    filename: str
    filepath: str
    duration_seconds: float
    frame_count: int
    fps: float
    width: int
    height: int
    codec: str
    file_size_bytes: int


class AnalysisConfig(TypedDict, total=False):
    """Configuration for analysis job."""
    
    sequence_length: int
    batch_size: int
    models: list[str]
    generate_heatmaps: bool
    generate_report: bool
    webhook_url: str | None


class AnalysisResult(TypedDict):
    """Complete analysis result."""
    
    analysis_id: str
    status: str
    result: str | None
    confidence: float | None
    confidence_level: str | None
    frames_analyzed: int
    faces_detected: int
    processing_time_seconds: float
    model_used: str
    frame_analyses: list[FrameAnalysis]
    video_metadata: VideoMetadata
    created_at: str
    completed_at: str | None


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass(frozen=True, slots=True)
class Point2D:
    """2D point coordinates."""
    
    x: int
    y: int
    
    def to_tuple(self) -> tuple[int, int]:
        """Convert to tuple."""
        return (self.x, self.y)


@dataclass(frozen=True, slots=True)
class Rectangle:
    """Rectangle defined by top-left corner and dimensions."""
    
    x: int
    y: int
    width: int
    height: int
    
    @property
    def top_left(self) -> Point2D:
        """Get top-left corner."""
        return Point2D(self.x, self.y)
    
    @property
    def bottom_right(self) -> Point2D:
        """Get bottom-right corner."""
        return Point2D(self.x + self.width, self.y + self.height)
    
    @property
    def center(self) -> Point2D:
        """Get center point."""
        return Point2D(
            self.x + self.width // 2,
            self.y + self.height // 2,
        )
    
    @property
    def area(self) -> int:
        """Calculate area."""
        return self.width * self.height
    
    def to_bbox(self) -> BoundingBox:
        """Convert to BoundingBox TypedDict."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
    
    def expand(self, padding: int) -> "Rectangle":
        """
        Create expanded rectangle with padding.
        
        Args:
            padding: Pixels to add on each side
        
        Returns:
            New Rectangle with expanded bounds
        """
        return Rectangle(
            x=max(0, self.x - padding),
            y=max(0, self.y - padding),
            width=self.width + 2 * padding,
            height=self.height + 2 * padding,
        )


@dataclass(slots=True)
class Face:
    """Detected face with metadata."""
    
    bbox: Rectangle
    confidence: float
    landmarks: dict[str, Point2D] = field(default_factory=dict)
    embedding: FeatureVector | None = None
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if detection confidence is high."""
        return self.confidence >= 0.8


@dataclass(slots=True)
class Frame:
    """Video frame with metadata."""
    
    index: int
    timestamp_ms: float
    image: ImageArray
    faces: list[Face] = field(default_factory=list)
    
    @property
    def has_faces(self) -> bool:
        """Check if frame has detected faces."""
        return len(self.faces) > 0


@dataclass(slots=True)
class AnalysisJob:
    """Analysis job metadata."""
    
    id: UUID
    video_path: Path
    status: AnalysisStatus
    config: AnalysisConfig
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: AnalysisResult | None = None
    error_message: str | None = None
    progress: float = 0.0
    
    @property
    def duration(self) -> float | None:
        """Get processing duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# =============================================================================
# NAMED TUPLES
# =============================================================================

class ImageSize(NamedTuple):
    """Image dimensions."""
    
    width: int
    height: int


class ModelConfig(NamedTuple):
    """Model configuration."""
    
    name: str
    architecture: ModelArchitecture
    input_size: ImageSize
    num_classes: int
    checkpoint_path: Path


# =============================================================================
# PROTOCOLS (Interface Definitions)
# =============================================================================

@runtime_checkable
class BaseModel(Protocol):
    """Protocol for all detection models."""
    
    def forward(self, x: "torch.Tensor") -> tuple["torch.Tensor", "torch.Tensor"]:
        """
        Forward pass through the model.
        
        Args:
            x: Input tensor of shape (B, T, C, H, W)
        
        Returns:
            Tuple of (feature_maps, logits)
        """
        ...
    
    def predict(self, x: "torch.Tensor") -> ModelPrediction:
        """
        Make prediction on input.
        
        Args:
            x: Input tensor
        
        Returns:
            ModelPrediction with logits, prediction, and confidence
        """
        ...
    
    @property
    def device(self) -> "torch.device":
        """Get model device."""
        ...


@runtime_checkable
class VideoProcessor(Protocol):
    """Protocol for video processing implementations."""
    
    def extract_frames(
        self,
        video_path: Path,
        num_frames: int,
    ) -> list[Frame]:
        """Extract frames from video."""
        ...
    
    def get_metadata(self, video_path: Path) -> VideoMetadata:
        """Get video metadata."""
        ...


@runtime_checkable
class FaceDetector(Protocol):
    """Protocol for face detection implementations."""
    
    def detect(self, image: ImageArray) -> list[Face]:
        """Detect faces in image."""
        ...
    
    def detect_batch(self, images: list[ImageArray]) -> list[list[Face]]:
        """Detect faces in batch of images."""
        ...


@runtime_checkable
class BaseService(Protocol):
    """Protocol for service layer implementations."""
    
    async def health_check(self) -> bool:
        """Check if service is healthy."""
        ...


# =============================================================================
# TYPE ALIASES
# =============================================================================

# Path types
PathLike: TypeAlias = Union[str, Path]

# Callback types
ProgressCallback: TypeAlias = Callable[[float, str], None]
ErrorCallback: TypeAlias = Callable[[Exception], None]

# Configuration types
ConfigDict: TypeAlias = dict[str, Any]

# ID types
AnalysisID: TypeAlias = Union[str, UUID]
UserID: TypeAlias = Union[int, UUID]

# Result types
DetectionLabel: TypeAlias = Literal["real", "fake", "uncertain"]
ConfidenceLevelStr: TypeAlias = Literal["low", "medium", "high", "very_high"]
