"""
Inference Engine

High-performance inference engine for deepfake detection.
Orchestrates model loading, preprocessing, and prediction.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence
from contextlib import contextmanager

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from core.exceptions import ModelNotFoundError, ProcessingError
from core.types import DetectionResult, ConfidenceLevel
from ml.config import MLConfig, get_ml_config
from ml.preprocessing.transforms import normalize_face, prepare_sequence

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True, slots=True)
class InferenceConfig:
    """
    Configuration for inference.
    
    Attributes:
        model_name: Name of model to use
        batch_size: Batch size for inference
        use_ensemble: Whether to use ensemble
        use_fp16: Use half precision
        use_tta: Use test-time augmentation
        num_tta: Number of TTA iterations
    """
    
    model_name: str = "ensemble"
    batch_size: int = 8
    use_ensemble: bool = True
    use_fp16: bool = True
    use_tta: bool = False
    num_tta: int = 5
    confidence_threshold: float = 0.5
    return_features: bool = False
    return_attention: bool = False


@dataclass
class InferenceResult:
    """
    Result of inference on a single input.
    
    Attributes:
        prediction: Predicted class (fake/real)
        confidence: Confidence score (0-1)
        probabilities: Class probabilities
        features: Optional extracted features
        attention_map: Optional attention map
        inference_time: Time taken for inference
    """
    
    prediction: str
    confidence: float
    probabilities: dict[str, float]
    features: np.ndarray | None = None
    attention_map: np.ndarray | None = None
    inference_time: float = 0.0
    model_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_fake(self) -> bool:
        """Check if prediction is fake."""
        return self.prediction.lower() == "fake"
    
    @property
    def confidence_percent(self) -> float:
        """Get confidence as percentage."""
        return self.confidence * 100
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level category."""
        return ConfidenceLevel.from_score(self.confidence_percent).value
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "confidence_percent": self.confidence_percent,
            "confidence_level": self.confidence_level,
            "probabilities": self.probabilities,
            "is_fake": self.is_fake,
            "inference_time_ms": self.inference_time * 1000,
            "model_name": self.model_name,
        }


@dataclass
class SequenceResult:
    """
    Result of inference on a frame sequence.
    
    Attributes:
        final_prediction: Aggregated prediction
        final_confidence: Aggregated confidence
        frame_results: Per-frame results
        aggregation_method: How results were aggregated
    """
    
    final_prediction: str
    final_confidence: float
    frame_results: list[InferenceResult]
    aggregation_method: str = "mean"
    temporal_consistency: float = 0.0
    
    @property
    def num_frames(self) -> int:
        return len(self.frame_results)
    
    @property
    def fake_frame_ratio(self) -> float:
        """Get ratio of frames predicted as fake."""
        if not self.frame_results:
            return 0.0
        fake_count = sum(1 for r in self.frame_results if r.is_fake)
        return fake_count / len(self.frame_results)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.final_prediction,
            "confidence": self.final_confidence,
            "confidence_percent": self.final_confidence * 100,
            "num_frames": self.num_frames,
            "fake_frame_ratio": self.fake_frame_ratio,
            "temporal_consistency": self.temporal_consistency,
            "aggregation_method": self.aggregation_method,
        }


# =============================================================================
# Inference Engine
# =============================================================================

class InferenceEngine:
    """
    High-performance inference engine for deepfake detection.
    
    Manages model loading, preprocessing, and prediction with
    support for single images, frame sequences, and batch processing.
    
    Example:
        >>> engine = InferenceEngine()
        >>> result = engine.predict(image)
        >>> print(f"Prediction: {result.prediction} ({result.confidence:.2%})")
        
        >>> # Sequence inference
        >>> seq_result = engine.predict_sequence(frames)
        >>> print(f"Video is {seq_result.final_prediction}")
    """
    
    def __init__(
        self,
        config: InferenceConfig | None = None,
        ml_config: MLConfig | None = None,
        model_registry: dict[str, Any] | None = None,
    ):
        """
        Initialize inference engine.
        
        Args:
            config: Inference configuration
            ml_config: ML system configuration
            model_registry: Pre-loaded model registry
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for inference")
        
        self._config = config or InferenceConfig()
        self._ml_config = ml_config or get_ml_config()
        self._model_registry = model_registry or {}
        self._loaded_models: dict[str, nn.Module] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize device
        self._device = torch.device(self._ml_config.device)
        self._dtype = torch.float16 if self._config.use_fp16 else torch.float32
    
    # =========================================================================
    # Model Management
    # =========================================================================
    
    def load_model(
        self,
        model_name: str,
        checkpoint_path: str | Path | None = None,
    ) -> nn.Module:
        """
        Load a model by name.
        
        Args:
            model_name: Name of model to load
            checkpoint_path: Optional path to checkpoint
        
        Returns:
            Loaded model in eval mode
        """
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        
        self._logger.info(f"Loading model: {model_name}")
        
        # Get model class from registry or create default
        if model_name == "efficientnet_lstm":
            from ml.architectures.efficientnet_lstm import EfficientNetLSTM
            
            if checkpoint_path:
                model = EfficientNetLSTM.from_checkpoint(checkpoint_path)
            else:
                model = EfficientNetLSTM()
        
        elif model_name == "ensemble":
            from ml.architectures.ensemble import EnsembleModel
            
            model = EnsembleModel()
        
        else:
            raise ModelNotFoundError(
                f"Unknown model: {model_name}",
                details={"available": list(self._loaded_models.keys())},
            )
        
        # Move to device and set precision
        model = model.to(self._device)
        
        if self._config.use_fp16 and self._device.type == "cuda":
            model = model.half()
        
        model.eval()
        
        self._loaded_models[model_name] = model
        
        self._logger.info(
            f"Model loaded: {model_name}",
            extra={
                "device": str(self._device),
                "precision": "fp16" if self._config.use_fp16 else "fp32",
            },
        )
        
        return model
    
    def get_model(self, model_name: str | None = None) -> nn.Module:
        """Get loaded model, loading if necessary."""
        model_name = model_name or self._config.model_name
        
        if model_name not in self._loaded_models:
            self.load_model(model_name)
        
        return self._loaded_models[model_name]
    
    def unload_model(self, model_name: str) -> None:
        """Unload model from memory."""
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            torch.cuda.empty_cache()
    
    def unload_all(self) -> None:
        """Unload all models."""
        self._loaded_models.clear()
        torch.cuda.empty_cache()
    
    # =========================================================================
    # Single Image Inference
    # =========================================================================
    
    @torch.no_grad()
    def predict(
        self,
        image: np.ndarray,
        model_name: str | None = None,
        return_features: bool = False,
    ) -> InferenceResult:
        """
        Predict on a single image.
        
        Args:
            image: Input image (RGB, HWC format)
            model_name: Model to use (defaults to config)
            return_features: Whether to return features
        
        Returns:
            InferenceResult with prediction
        """
        start_time = time.time()
        model_name = model_name or self._config.model_name
        model = self.get_model(model_name)
        
        # Preprocess
        tensor = self._preprocess_image(image)
        tensor = tensor.unsqueeze(0)  # Add batch dimension
        
        # Add sequence dimension if model expects it
        if hasattr(model, "forward") and "sequence" in str(model.forward.__code__.co_varnames):
            tensor = tensor.unsqueeze(0)  # (1, 1, C, H, W)
        
        tensor = tensor.to(self._device, dtype=self._dtype)
        
        # Inference
        if self._config.use_tta:
            output = self._predict_with_tta(model, tensor)
        else:
            output = model(tensor)
        
        # Process output
        if hasattr(output, "probabilities"):
            probs = output.probabilities.cpu().numpy()[0]
        else:
            probs = F.softmax(output, dim=1).cpu().numpy()[0]
        
        # Get prediction
        fake_prob = probs[1] if len(probs) > 1 else probs[0]
        real_prob = 1 - fake_prob
        
        prediction = "fake" if fake_prob >= self._config.confidence_threshold else "real"
        confidence = fake_prob if prediction == "fake" else real_prob
        
        # Extract features if requested
        features = None
        if return_features and hasattr(output, "features"):
            features = output.features.cpu().numpy()[0]
        
        inference_time = time.time() - start_time
        
        return InferenceResult(
            prediction=prediction,
            confidence=float(confidence),
            probabilities={"real": float(real_prob), "fake": float(fake_prob)},
            features=features,
            inference_time=inference_time,
            model_name=model_name,
        )
    
    def _predict_with_tta(
        self,
        model: nn.Module,
        tensor: torch.Tensor,
    ) -> torch.Tensor:
        """
        Predict with test-time augmentation.
        
        Applies horizontal flip and averages predictions.
        """
        outputs = []
        
        # Original
        outputs.append(model(tensor))
        
        # Horizontal flip
        flipped = torch.flip(tensor, dims=[-1])
        outputs.append(model(flipped))
        
        # Average
        stacked = torch.stack([
            o.logits if hasattr(o, "logits") else o
            for o in outputs
        ])
        
        return stacked.mean(dim=0)
    
    # =========================================================================
    # Sequence Inference
    # =========================================================================
    
    @torch.no_grad()
    def predict_sequence(
        self,
        frames: np.ndarray | Sequence[np.ndarray],
        model_name: str | None = None,
        aggregation: str = "mean",
    ) -> SequenceResult:
        """
        Predict on a frame sequence.
        
        Args:
            frames: Frame sequence (T, H, W, C) or list of frames
            model_name: Model to use
            aggregation: Aggregation method (mean/vote/max)
        
        Returns:
            SequenceResult with aggregated prediction
        """
        start_time = time.time()
        model_name = model_name or self._config.model_name
        model = self.get_model(model_name)
        
        # Convert to numpy array if list
        if isinstance(frames, (list, tuple)):
            frames = np.stack(frames)
        
        # Preprocess sequence
        tensor = self._preprocess_sequence(frames)
        tensor = tensor.to(self._device, dtype=self._dtype)
        
        # Check if model handles sequences natively
        if hasattr(model, "predict_sequence"):
            # Native sequence model
            output = model(tensor.unsqueeze(0))  # Add batch dim
            
            if hasattr(output, "probabilities"):
                probs = output.probabilities.cpu().numpy()[0]
            else:
                probs = F.softmax(output, dim=1).cpu().numpy()[0]
            
            fake_prob = probs[1] if len(probs) > 1 else probs[0]
            
            return SequenceResult(
                final_prediction="fake" if fake_prob >= 0.5 else "real",
                final_confidence=float(max(fake_prob, 1 - fake_prob)),
                frame_results=[],
                aggregation_method="native",
            )
        
        # Frame-by-frame inference with aggregation
        frame_results = []
        
        for i in range(len(frames)):
            frame_tensor = tensor[i:i+1]  # Keep batch dimension
            output = model(frame_tensor.unsqueeze(1))  # Add sequence dim
            
            if hasattr(output, "probabilities"):
                probs = output.probabilities.cpu().numpy()[0]
            else:
                probs = F.softmax(output, dim=1).cpu().numpy()[0]
            
            fake_prob = probs[1] if len(probs) > 1 else probs[0]
            real_prob = 1 - fake_prob
            
            prediction = "fake" if fake_prob >= 0.5 else "real"
            confidence = fake_prob if prediction == "fake" else real_prob
            
            frame_results.append(InferenceResult(
                prediction=prediction,
                confidence=float(confidence),
                probabilities={"real": float(real_prob), "fake": float(fake_prob)},
                model_name=model_name,
            ))
        
        # Aggregate results
        final_prediction, final_confidence = self._aggregate_results(
            frame_results, aggregation
        )
        
        # Calculate temporal consistency
        temporal_consistency = self._calculate_temporal_consistency(frame_results)
        
        return SequenceResult(
            final_prediction=final_prediction,
            final_confidence=final_confidence,
            frame_results=frame_results,
            aggregation_method=aggregation,
            temporal_consistency=temporal_consistency,
        )
    
    def _aggregate_results(
        self,
        results: list[InferenceResult],
        method: str,
    ) -> tuple[str, float]:
        """Aggregate frame-level results."""
        if not results:
            return "uncertain", 0.5
        
        fake_probs = [r.probabilities["fake"] for r in results]
        
        if method == "mean":
            avg_fake = np.mean(fake_probs)
            prediction = "fake" if avg_fake >= 0.5 else "real"
            confidence = avg_fake if prediction == "fake" else 1 - avg_fake
        
        elif method == "vote":
            fake_votes = sum(1 for r in results if r.is_fake)
            prediction = "fake" if fake_votes > len(results) / 2 else "real"
            confidence = max(fake_votes, len(results) - fake_votes) / len(results)
        
        elif method == "max":
            max_fake = max(fake_probs)
            max_real = 1 - min(fake_probs)
            
            if max_fake > max_real:
                prediction = "fake"
                confidence = max_fake
            else:
                prediction = "real"
                confidence = max_real
        
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        return prediction, float(confidence)
    
    def _calculate_temporal_consistency(
        self,
        results: list[InferenceResult],
    ) -> float:
        """
        Calculate temporal consistency of predictions.
        
        High consistency = predictions don't flip often.
        """
        if len(results) < 2:
            return 1.0
        
        predictions = [r.prediction for r in results]
        
        # Count transitions
        transitions = sum(
            1 for i in range(1, len(predictions))
            if predictions[i] != predictions[i-1]
        )
        
        # Consistency = 1 - (transitions / max_possible_transitions)
        max_transitions = len(predictions) - 1
        consistency = 1 - (transitions / max_transitions)
        
        return float(consistency)
    
    # =========================================================================
    # Batch Inference
    # =========================================================================
    
    @torch.no_grad()
    def predict_batch(
        self,
        images: Sequence[np.ndarray],
        model_name: str | None = None,
    ) -> list[InferenceResult]:
        """
        Predict on a batch of images.
        
        Args:
            images: List of images
            model_name: Model to use
        
        Returns:
            List of InferenceResult
        """
        start_time = time.time()
        model_name = model_name or self._config.model_name
        model = self.get_model(model_name)
        
        # Preprocess batch
        tensors = [self._preprocess_image(img) for img in images]
        batch = torch.stack(tensors)
        
        # Add sequence dimension if needed
        if hasattr(model, "expects_sequence") and model.expects_sequence:
            batch = batch.unsqueeze(1)
        
        batch = batch.to(self._device, dtype=self._dtype)
        
        # Inference
        output = model(batch)
        
        # Process outputs
        if hasattr(output, "probabilities"):
            probs = output.probabilities.cpu().numpy()
        else:
            probs = F.softmax(output, dim=1).cpu().numpy()
        
        batch_time = time.time() - start_time
        per_image_time = batch_time / len(images)
        
        results = []
        for i, prob in enumerate(probs):
            fake_prob = prob[1] if len(prob) > 1 else prob[0]
            real_prob = 1 - fake_prob
            
            prediction = "fake" if fake_prob >= self._config.confidence_threshold else "real"
            confidence = fake_prob if prediction == "fake" else real_prob
            
            results.append(InferenceResult(
                prediction=prediction,
                confidence=float(confidence),
                probabilities={"real": float(real_prob), "fake": float(fake_prob)},
                inference_time=per_image_time,
                model_name=model_name,
            ))
        
        return results
    
    # =========================================================================
    # Preprocessing
    # =========================================================================
    
    def _preprocess_image(
        self,
        image: np.ndarray,
    ) -> torch.Tensor:
        """Preprocess single image."""
        # Normalize and convert to tensor
        processed = normalize_face(
            image,
            target_size=self._ml_config.image_size,
        )
        
        return torch.from_numpy(processed).float()
    
    def _preprocess_sequence(
        self,
        frames: np.ndarray,
    ) -> torch.Tensor:
        """Preprocess frame sequence."""
        processed = prepare_sequence(
            frames,
            target_size=self._ml_config.image_size,
        )
        
        return torch.from_numpy(processed).float()
    
    # =========================================================================
    # Context Managers
    # =========================================================================
    
    @contextmanager
    def inference_mode(self):
        """Context manager for inference mode."""
        with torch.no_grad():
            with torch.cuda.amp.autocast(enabled=self._config.use_fp16):
                yield
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def device(self) -> torch.device:
        """Get current device."""
        return self._device
    
    @property
    def loaded_models(self) -> list[str]:
        """Get list of loaded model names."""
        return list(self._loaded_models.keys())
    
    @property
    def config(self) -> InferenceConfig:
        """Get inference configuration."""
        return self._config
