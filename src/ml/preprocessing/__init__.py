"""
Preprocessing Module

Video and image preprocessing pipeline for deepfake detection:
    - VideoProcessor: Frame extraction and processing
    - FaceDetector: Multi-backend face detection
    - Transforms: Augmentation and normalization
"""

from __future__ import annotations

from .video_processor import VideoProcessor, VideoMetadata, FrameSequence
from .face_detector import FaceDetector, FaceDetection, DetectorBackend
from .transforms import (
    get_train_transforms,
    get_inference_transforms,
    get_augmentation_pipeline,
    normalize_face,
)

__all__ = [
    "VideoProcessor",
    "VideoMetadata",
    "FrameSequence",
    "FaceDetector",
    "FaceDetection",
    "DetectorBackend",
    "get_train_transforms",
    "get_inference_transforms",
    "get_augmentation_pipeline",
    "normalize_face",
]
