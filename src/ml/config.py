"""
ML Configuration

Centralized configuration for machine learning components:
    - Model hyperparameters
    - Training settings
    - Inference optimization
    - Device management
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Final, Literal

import torch

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Supported compute devices."""
    
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon
    
    @classmethod
    def auto_detect(cls) -> "DeviceType":
        """Auto-detect the best available device."""
        if torch.cuda.is_available():
            return cls.CUDA
        elif torch.backends.mps.is_available():
            return cls.MPS
        return cls.CPU


class PrecisionType(str, Enum):
    """Floating point precision modes."""
    
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    AMP = "amp"  # Automatic Mixed Precision


@dataclass(frozen=True)
class ImageConfig:
    """Image preprocessing configuration."""
    
    size: tuple[int, int] = (224, 224)
    channels: int = 3
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)
    
    @property
    def height(self) -> int:
        return self.size[0]
    
    @property
    def width(self) -> int:
        return self.size[1]


@dataclass(frozen=True)
class ModelArchitectureConfig:
    """Neural network architecture configuration."""
    
    # Feature extraction
    backbone: str = "efficientnet_b4"
    pretrained: bool = True
    feature_dim: int = 1792
    
    # Temporal modeling
    lstm_hidden_dim: int = 2048
    lstm_layers: int = 2
    lstm_bidirectional: bool = True
    
    # Transformer settings
    transformer_heads: int = 8
    transformer_layers: int = 4
    transformer_dim_feedforward: int = 2048
    
    # Classification
    num_classes: int = 2
    dropout_rate: float = 0.4
    
    # Attention
    use_attention: bool = True
    attention_type: Literal["self", "cross", "cbam"] = "self"


@dataclass
class InferenceConfig:
    """Inference runtime configuration."""
    
    # Batch processing
    batch_size: int = 8
    sequence_length: int = 60
    
    # Device settings
    device: DeviceType = field(default_factory=DeviceType.auto_detect)
    precision: PrecisionType = PrecisionType.FP32
    
    # Optimization
    use_torch_compile: bool = False
    use_cudnn_benchmark: bool = True
    num_workers: int = 4
    pin_memory: bool = True
    
    # Ensemble settings
    ensemble_mode: Literal["voting", "averaging", "stacking"] = "averaging"
    ensemble_weights: dict[str, float] = field(default_factory=lambda: {
        "efficientnet_lstm": 0.40,
        "resnext_transformer": 0.35,
        "xception_attention": 0.25,
    })
    
    # Thresholds
    fake_threshold: float = 0.5
    uncertainty_threshold: float = 0.15
    min_confidence_for_report: float = 0.70
    
    def __post_init__(self) -> None:
        """Validate and adjust configuration."""
        # Adjust workers for CPU
        if self.device == DeviceType.CPU:
            self.num_workers = min(self.num_workers, 2)
            self.pin_memory = False
        
        # Enable benchmark mode for CUDA
        if self.device == DeviceType.CUDA and self.use_cudnn_benchmark:
            torch.backends.cudnn.benchmark = True
    
    @property
    def torch_device(self) -> torch.device:
        """Get PyTorch device object."""
        if self.device == DeviceType.CUDA:
            return torch.device("cuda:0")
        elif self.device == DeviceType.MPS:
            return torch.device("mps")
        return torch.device("cpu")
    
    @property
    def torch_dtype(self) -> torch.dtype:
        """Get PyTorch dtype for precision setting."""
        if self.precision == PrecisionType.FP16:
            return torch.float16
        elif self.precision == PrecisionType.BF16:
            return torch.bfloat16
        return torch.float32


@dataclass
class TrainingConfig:
    """Training configuration (for fine-tuning)."""
    
    # Optimizer
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    optimizer: Literal["adam", "adamw", "sgd"] = "adamw"
    
    # Scheduler
    scheduler: Literal["cosine", "step", "plateau"] = "cosine"
    warmup_epochs: int = 5
    warmup_lr: float = 1e-6
    
    # Training loop
    epochs: int = 50
    early_stopping_patience: int = 10
    gradient_clip_norm: float = 1.0
    
    # Regularization
    label_smoothing: float = 0.1
    mixup_alpha: float = 0.2
    cutmix_alpha: float = 1.0
    
    # Augmentation
    augmentation_strength: Literal["light", "medium", "strong"] = "medium"
    
    # Checkpointing
    save_every_n_epochs: int = 5
    keep_top_k_checkpoints: int = 3


@dataclass
class FaceDetectionConfig:
    """Face detection configuration."""
    
    # Detection model
    detector: Literal["retinaface", "mtcnn", "dlib", "mediapipe"] = "retinaface"
    
    # Detection parameters
    confidence_threshold: float = 0.8
    nms_threshold: float = 0.4
    min_face_size: int = 40
    max_faces: int = 5
    
    # Face alignment
    align_faces: bool = True
    alignment_size: tuple[int, int] = (112, 112)
    
    # Tracking
    enable_tracking: bool = True
    tracking_iou_threshold: float = 0.5
    
    # Cropping
    face_padding: float = 0.25  # Padding as ratio of face size


@dataclass
class ExplainabilityConfig:
    """Explainability/XAI configuration."""
    
    # GradCAM settings
    enable_gradcam: bool = True
    gradcam_layer: str = "auto"  # Auto-detect best layer
    gradcam_variant: Literal["gradcam", "gradcam++", "scorecam"] = "gradcam++"
    
    # Attention visualization
    visualize_attention: bool = True
    attention_head: int = -1  # -1 for average of all heads
    
    # Output settings
    heatmap_colormap: str = "jet"
    heatmap_alpha: float = 0.5
    save_intermediate_features: bool = False


# =============================================================================
# GLOBAL CONFIGURATION INSTANCE
# =============================================================================

class MLConfig:
    """
    Global ML configuration manager.
    
    Provides singleton access to ML configuration with
    environment variable overrides.
    
    Example:
        >>> config = MLConfig.get()
        >>> print(config.inference.device)
        DeviceType.CUDA
    """
    
    _instance: "MLConfig | None" = None
    
    def __init__(self) -> None:
        self.image = ImageConfig()
        self.architecture = ModelArchitectureConfig()
        self.inference = InferenceConfig()
        self.training = TrainingConfig()
        self.face_detection = FaceDetectionConfig()
        self.explainability = ExplainabilityConfig()
        
        # Model paths
        self.models_dir = Path(os.getenv(
            "ALETHEIA_MODELS_DIR",
            Path(__file__).parent.parent.parent.parent / "models"
        ))
        
        # Apply environment overrides
        self._apply_env_overrides()
    
    # Convenience properties for direct access by InferenceEngine
    @property
    def device(self) -> str:
        """Get device string for torch.device()."""
        return self.inference.device.value
    
    @property
    def image_size(self) -> tuple[int, int]:
        """Get target image dimensions (H, W)."""
        return self.image.size
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Device override
        device_env = os.getenv("ALETHEIA_DEVICE")
        if device_env:
            try:
                self.inference.device = DeviceType(device_env.lower())
            except ValueError:
                logger.warning(f"Invalid device '{device_env}', using auto-detect")
        
        # Precision override
        precision_env = os.getenv("ALETHEIA_PRECISION")
        if precision_env:
            try:
                self.inference.precision = PrecisionType(precision_env.lower())
            except ValueError:
                logger.warning(f"Invalid precision '{precision_env}', using fp32")
        
        # Batch size override
        batch_env = os.getenv("ALETHEIA_BATCH_SIZE")
        if batch_env:
            try:
                self.inference.batch_size = int(batch_env)
            except ValueError:
                pass
    
    @classmethod
    def get(cls) -> "MLConfig":
        """Get singleton configuration instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset configuration to defaults."""
        cls._instance = None
    
    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "image": {
                "size": self.image.size,
                "channels": self.image.channels,
                "mean": self.image.mean,
                "std": self.image.std,
            },
            "architecture": {
                "backbone": self.architecture.backbone,
                "feature_dim": self.architecture.feature_dim,
                "lstm_hidden_dim": self.architecture.lstm_hidden_dim,
                "lstm_layers": self.architecture.lstm_layers,
                "num_classes": self.architecture.num_classes,
            },
            "inference": {
                "device": self.inference.device.value,
                "precision": self.inference.precision.value,
                "batch_size": self.inference.batch_size,
                "sequence_length": self.inference.sequence_length,
            },
        }


# Module-level convenience functions
def get_config() -> MLConfig:
    """Get global ML configuration."""
    return MLConfig.get()


def get_ml_config() -> MLConfig:
    """Get global ML configuration (alias for get_config)."""
    return MLConfig.get()
