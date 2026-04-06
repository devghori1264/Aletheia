"""
Base Detection Model Architecture

Abstract base class and common utilities for all detection models.
Ensures consistent interface across different architectures.

Key Features:
    - Unified forward/predict interface
    - Device management
    - Checkpoint loading/saving
    - Feature extraction hooks
    - GradCAM layer access
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Final, Literal, TypeVar

import numpy as np
import torch
import torch.nn as nn
from torch import Tensor

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseDetectionModel")


@dataclass
class ModelOutput:
    """
    Structured output from model forward pass.
    
    Contains predictions, confidence scores, and optional
    intermediate features for explainability.
    
    Attributes:
        logits: Raw model output before softmax (batch_size, num_classes)
        probabilities: Softmax probabilities (batch_size, num_classes)
        prediction: Predicted class indices (batch_size,)
        confidence: Confidence scores for predictions (batch_size,)
        features: Optional intermediate feature maps for GradCAM
        attention_weights: Optional attention weights for visualization
    """
    
    logits: Tensor
    probabilities: Tensor
    prediction: Tensor
    confidence: Tensor
    features: Tensor | None = None
    attention_weights: Tensor | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "logits": self.logits.cpu().numpy().tolist(),
            "probabilities": self.probabilities.cpu().numpy().tolist(),
            "prediction": self.prediction.cpu().numpy().tolist(),
            "confidence": self.confidence.cpu().numpy().tolist(),
        }
    
    @property
    def is_fake(self) -> Tensor:
        """Boolean tensor indicating fake predictions (class 0)."""
        return self.prediction == 0
    
    @property
    def is_real(self) -> Tensor:
        """Boolean tensor indicating real predictions (class 1)."""
        return self.prediction == 1


class BaseDetectionModel(nn.Module, ABC):
    """
    Abstract base class for deepfake detection models.
    
    All detection models must inherit from this class and implement
    the required abstract methods. This ensures a consistent interface
    for training, inference, and explainability.
    
    Architecture Pattern:
        1. Feature Extraction (backbone CNN)
        2. Temporal Modeling (LSTM/Transformer)
        3. Classification Head (FC layers)
    
    Example:
        >>> class MyModel(BaseDetectionModel):
        ...     def __init__(self):
        ...         super().__init__(name="my_model", num_classes=2)
        ...         # Define layers
        ...
        ...     def forward(self, x):
        ...         # Implement forward pass
        ...         pass
    """
    
    # Class constants
    SUPPORTED_BACKBONES: Final[frozenset[str]] = frozenset({
        "efficientnet_b0", "efficientnet_b4", "efficientnet_b7",
        "resnext50_32x4d", "resnext101_32x8d",
        "xception",
    })
    
    def __init__(
        self,
        name: str,
        num_classes: int = 2,
        dropout_rate: float = 0.4,
        pretrained: bool = True,
    ) -> None:
        """
        Initialize base detection model.
        
        Args:
            name: Model identifier for logging and checkpoints.
            num_classes: Number of output classes (default: 2 for real/fake).
            dropout_rate: Dropout probability for regularization.
            pretrained: Whether to use pretrained backbone weights.
        """
        super().__init__()
        
        self._name = name
        self._num_classes = num_classes
        self._dropout_rate = dropout_rate
        self._pretrained = pretrained
        
        # Will be set by subclasses
        self._feature_dim: int = 0
        self._gradcam_layer: nn.Module | None = None
        
        # Feature extraction hooks
        self._feature_hooks: dict[str, Callable] = {}
        self._extracted_features: dict[str, Tensor] = {}
        
        logger.info(f"Initializing {name} model (classes={num_classes})")
    
    @property
    def name(self) -> str:
        """Model name/identifier."""
        return self._name
    
    @property
    def num_classes(self) -> int:
        """Number of output classes."""
        return self._num_classes
    
    @property
    def feature_dim(self) -> int:
        """Feature dimension from backbone."""
        return self._feature_dim
    
    @property
    def gradcam_layer(self) -> nn.Module | None:
        """Layer for GradCAM visualization."""
        return self._gradcam_layer
    
    @property
    def device(self) -> torch.device:
        """Get model's current device."""
        return next(self.parameters()).device
    
    @abstractmethod
    def forward(
        self,
        x: Tensor,
        return_features: bool = False,
    ) -> tuple[Tensor, Tensor] | tuple[Tensor, Tensor, Tensor]:
        """
        Forward pass through the model.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, channels, height, width)
            return_features: If True, also return intermediate features
        
        Returns:
            If return_features=False:
                Tuple of (feature_maps, logits)
            If return_features=True:
                Tuple of (feature_maps, logits, intermediate_features)
        """
        ...
    
    @abstractmethod
    def extract_features(self, x: Tensor) -> Tensor:
        """
        Extract feature vectors from input.
        
        Args:
            x: Input tensor (batch_size, sequence_length, channels, height, width)
        
        Returns:
            Feature tensor (batch_size, feature_dim)
        """
        ...
    
    def predict(self, x: Tensor) -> ModelOutput:
        """
        Make prediction with confidence scores.
        
        This is the primary inference method. It handles softmax,
        prediction extraction, and confidence calculation.
        
        Args:
            x: Input tensor (batch_size, sequence_length, C, H, W)
        
        Returns:
            ModelOutput containing predictions and metadata.
        """
        self.eval()
        
        with torch.no_grad():
            features, logits = self.forward(x)
            
            # Apply softmax for probabilities
            probabilities = torch.softmax(logits, dim=1)
            
            # Get predictions and confidence
            confidence, prediction = torch.max(probabilities, dim=1)
        
        return ModelOutput(
            logits=logits,
            probabilities=probabilities,
            prediction=prediction,
            confidence=confidence,
            features=features,
        )
    
    def predict_batch(
        self,
        x: Tensor,
        batch_size: int = 8,
    ) -> ModelOutput:
        """
        Batch prediction with automatic chunking.
        
        For large inputs, processes in chunks to avoid OOM.
        
        Args:
            x: Input tensor (total_samples, sequence_length, C, H, W)
            batch_size: Batch size for processing
        
        Returns:
            Combined ModelOutput for all samples.
        """
        total_samples = x.size(0)
        
        if total_samples <= batch_size:
            return self.predict(x)
        
        # Process in batches
        all_logits = []
        all_probs = []
        all_preds = []
        all_confs = []
        
        for i in range(0, total_samples, batch_size):
            batch = x[i:i + batch_size]
            output = self.predict(batch)
            
            all_logits.append(output.logits)
            all_probs.append(output.probabilities)
            all_preds.append(output.prediction)
            all_confs.append(output.confidence)
        
        return ModelOutput(
            logits=torch.cat(all_logits, dim=0),
            probabilities=torch.cat(all_probs, dim=0),
            prediction=torch.cat(all_preds, dim=0),
            confidence=torch.cat(all_confs, dim=0),
        )
    
    def load_checkpoint(
        self,
        checkpoint_path: Path | str,
        strict: bool = True,
        map_location: str | torch.device | None = None,
    ) -> dict[str, Any]:
        """
        Load model weights from checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file (.pt/.pth)
            strict: Whether to strictly enforce state dict matching
            map_location: Device to map tensors to
        
        Returns:
            Checkpoint dictionary with metadata
        
        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            RuntimeError: If state dict doesn't match model
        """
        checkpoint_path = Path(checkpoint_path)
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        
        # Load checkpoint
        checkpoint = torch.load(
            checkpoint_path,
            map_location=map_location or self.device,
            weights_only=False,
        )
        
        # Handle different checkpoint formats
        if "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        elif "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint
        
        # Remove 'module.' prefix if present (from DataParallel)
        state_dict = {
            k.replace("module.", ""): v
            for k, v in state_dict.items()
        }
        
        # Load weights
        self.load_state_dict(state_dict, strict=strict)
        
        logger.info(f"Loaded checkpoint: {checkpoint_path.name}")
        
        return checkpoint
    
    def save_checkpoint(
        self,
        checkpoint_path: Path | str,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Save model weights to checkpoint.
        
        Args:
            checkpoint_path: Path to save checkpoint
            metadata: Optional metadata to include
        
        Returns:
            Path to saved checkpoint
        """
        checkpoint_path = Path(checkpoint_path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            "model_name": self._name,
            "state_dict": self.state_dict(),
            "num_classes": self._num_classes,
            "feature_dim": self._feature_dim,
        }
        
        if metadata:
            checkpoint.update(metadata)
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint to {checkpoint_path}")
        
        return checkpoint_path
    
    def get_num_parameters(self, trainable_only: bool = False) -> int:
        """
        Count model parameters.
        
        Args:
            trainable_only: Count only trainable parameters
        
        Returns:
            Number of parameters
        """
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())
    
    def freeze_backbone(self) -> None:
        """Freeze backbone parameters for transfer learning."""
        if hasattr(self, "backbone"):
            for param in self.backbone.parameters():
                param.requires_grad = False
            logger.info(f"Froze backbone parameters in {self._name}")
    
    def unfreeze_backbone(self) -> None:
        """Unfreeze backbone parameters."""
        if hasattr(self, "backbone"):
            for param in self.backbone.parameters():
                param.requires_grad = True
            logger.info(f"Unfroze backbone parameters in {self._name}")
    
    def set_dropout_rate(self, rate: float) -> None:
        """
        Update dropout rate for all dropout layers.
        
        Args:
            rate: New dropout probability (0.0 to 1.0)
        """
        for module in self.modules():
            if isinstance(module, nn.Dropout):
                module.p = rate
        self._dropout_rate = rate
    
    def register_feature_hook(
        self,
        layer_name: str,
        layer: nn.Module,
    ) -> None:
        """
        Register hook to extract features from a layer.
        
        Args:
            layer_name: Identifier for the layer
            layer: Module to attach hook to
        """
        def hook(module: nn.Module, input: tuple, output: Tensor) -> None:
            self._extracted_features[layer_name] = output.detach()
        
        handle = layer.register_forward_hook(hook)
        self._feature_hooks[layer_name] = handle
    
    def get_extracted_features(self) -> dict[str, Tensor]:
        """Get features captured by registered hooks."""
        return self._extracted_features.copy()
    
    def clear_feature_hooks(self) -> None:
        """Remove all feature extraction hooks."""
        for handle in self._feature_hooks.values():
            handle.remove()
        self._feature_hooks.clear()
        self._extracted_features.clear()
    
    def __repr__(self) -> str:
        """String representation with model info."""
        total_params = self.get_num_parameters()
        trainable_params = self.get_num_parameters(trainable_only=True)
        
        return (
            f"{self.__class__.__name__}(\n"
            f"  name={self._name},\n"
            f"  num_classes={self._num_classes},\n"
            f"  feature_dim={self._feature_dim},\n"
            f"  total_params={total_params:,},\n"
            f"  trainable_params={trainable_params:,}\n"
            f")"
        )


def initialize_weights(module: nn.Module) -> None:
    """
    Initialize module weights using best practices.
    
    Uses Kaiming initialization for conv/linear layers
    and orthogonal initialization for RNNs.
    
    Args:
        module: Module to initialize
    """
    if isinstance(module, nn.Conv2d):
        nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    
    elif isinstance(module, nn.Linear):
        nn.init.xavier_uniform_(module.weight)
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    
    elif isinstance(module, nn.BatchNorm2d):
        nn.init.ones_(module.weight)
        nn.init.zeros_(module.bias)
    
    elif isinstance(module, nn.LayerNorm):
        nn.init.ones_(module.weight)
        nn.init.zeros_(module.bias)
    
    elif isinstance(module, (nn.LSTM, nn.GRU)):
        for name, param in module.named_parameters():
            if "weight_ih" in name:
                nn.init.xavier_uniform_(param)
            elif "weight_hh" in name:
                nn.init.orthogonal_(param)
            elif "bias" in name:
                nn.init.zeros_(param)
