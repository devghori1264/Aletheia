"""
Model Architecture Package

Advanced neural network architectures for deepfake detection:

    - base.py: Abstract base classes and protocols
    - efficientnet_lstm.py: EfficientNet-B4 with Bidirectional LSTM
    - resnext_transformer.py: ResNeXt-101 with Transformer Encoder
    - xception_network.py: XceptionNet with Self-Attention
    - attention_modules.py: CBAM, Self-Attention, Cross-Attention
    - ensemble.py: Multi-model ensemble orchestrator

Design Principles:
    - All models inherit from BaseDetectionModel
    - Consistent forward() and predict() interfaces
    - Built-in support for feature extraction
    - GradCAM-compatible layer access
"""

from __future__ import annotations

from .base import BaseDetectionModel, ModelOutput
from .efficientnet_lstm import EfficientNetLSTM
from .attention_modules import (
    CBAM,
    SelfAttention,
    TemporalAttention,
)
from .ensemble import EnsembleModel

__all__ = [
    "BaseDetectionModel",
    "ModelOutput",
    "EfficientNetLSTM",
    "CBAM",
    "SelfAttention",
    "TemporalAttention",
    "EnsembleModel",
]
