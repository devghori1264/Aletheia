"""
Aletheia Machine Learning Module

Advanced deepfake detection models and inference engine:

Architectures:
    - EfficientNet-B4 + Bidirectional LSTM
    - ResNeXt-101 + Transformer Encoder  
    - XceptionNet with Self-Attention
    - Ensemble Model Orchestrator

Features:
    - Model registry pattern for extensibility
    - Grad-CAM++ explainability
    - Batch inference optimization
    - GPU/CPU automatic device selection
    - Mixed precision support

Research Foundations:
    - Temporal inconsistency detection
    - Facial artifact analysis
    - Frequency domain features
    - Cross-attention mechanisms
"""

from __future__ import annotations

__all__ = [
    "config",
    "registry",
    "architectures",
    "preprocessing",
    "inference",
]
