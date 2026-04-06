"""
Inference Module

High-performance inference engine for deepfake detection:
    - InferenceEngine: Main inference orchestrator
    - BatchProcessor: Efficient batch inference
    - GradCAM: Explainability and visualization
"""

from __future__ import annotations

from .engine import InferenceEngine, InferenceConfig, InferenceResult
from .batch_processor import BatchProcessor, BatchResult
from .explainability import GradCAMPlusPlus, visualize_attention

__all__ = [
    "InferenceEngine",
    "InferenceConfig",
    "InferenceResult",
    "BatchProcessor",
    "BatchResult",
    "GradCAMPlusPlus",
    "visualize_attention",
]
