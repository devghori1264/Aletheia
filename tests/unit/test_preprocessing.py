"""
Unit Tests for ML Preprocessing Module

Tests for video processing, face detection, and transforms.
"""

from __future__ import annotations

import numpy as np
import pytest

from ml.preprocessing.transforms import (
    normalize_face,
    prepare_sequence,
    get_inference_transforms,
    get_training_transforms,
)


class TestNormalizeFace:
    """Tests for face normalization function."""
    
    def test_normalize_basic(self, sample_image):
        """Test basic normalization."""
        result = normalize_face(sample_image)
        
        assert result is not None
        assert result.shape[0] == 3  # CHW format
        assert result.dtype == np.float32
    
    def test_normalize_with_target_size(self, sample_image):
        """Test normalization with custom target size."""
        target_size = (128, 128)
        result = normalize_face(sample_image, target_size=target_size)
        
        assert result.shape[1:] == target_size
    
    def test_normalize_maintains_range(self, sample_image):
        """Test that normalized values are in expected range."""
        result = normalize_face(sample_image)
        
        # After ImageNet normalization, values should be roughly in [-3, 3]
        assert result.min() >= -5
        assert result.max() <= 5
    
    def test_normalize_handles_grayscale(self):
        """Test normalization of grayscale image."""
        grayscale = np.random.randint(0, 255, (224, 224), dtype=np.uint8)
        
        # Should handle gracefully (convert to RGB)
        result = normalize_face(grayscale)
        
        assert result.shape[0] == 3


class TestPrepareSequence:
    """Tests for sequence preparation function."""
    
    def test_prepare_sequence_basic(self, sample_video_frames):
        """Test basic sequence preparation."""
        result = prepare_sequence(sample_video_frames)
        
        assert result is not None
        assert result.ndim == 4  # (T, C, H, W)
        assert result.shape[1] == 3  # RGB channels
    
    def test_prepare_sequence_with_target_size(self, sample_video_frames):
        """Test sequence preparation with custom size."""
        target_size = (128, 128)
        result = prepare_sequence(sample_video_frames, target_size=target_size)
        
        assert result.shape[2:] == target_size
    
    def test_prepare_sequence_preserves_temporal_order(self, sample_video_frames):
        """Test that temporal order is preserved."""
        # Mark first and last frames
        frames = sample_video_frames.copy()
        frames[0] = 0  # All black
        frames[-1] = 255  # All white
        
        result = prepare_sequence(frames)
        
        # First frame should have lower values (closer to -mean/std)
        # Last frame should have higher values (closer to (255-mean)/std)
        assert result[0].mean() < result[-1].mean()


class TestTransformPipelines:
    """Tests for transform pipelines."""
    
    def test_inference_transforms_exist(self):
        """Test that inference transforms can be created."""
        try:
            transforms = get_inference_transforms()
            assert transforms is not None
        except ImportError:
            pytest.skip("albumentations not installed")
    
    def test_training_transforms_exist(self):
        """Test that training transforms can be created."""
        try:
            transforms = get_training_transforms()
            assert transforms is not None
        except ImportError:
            pytest.skip("albumentations not installed")
    
    def test_inference_transforms_deterministic(self, sample_image):
        """Test that inference transforms are deterministic."""
        try:
            transforms = get_inference_transforms()
        except ImportError:
            pytest.skip("albumentations not installed")
        
        result1 = transforms(image=sample_image)["image"]
        result2 = transforms(image=sample_image)["image"]
        
        np.testing.assert_array_equal(result1, result2)
    
    def test_training_transforms_augment(self, sample_image):
        """Test that training transforms apply augmentation."""
        try:
            transforms = get_training_transforms()
        except ImportError:
            pytest.skip("albumentations not installed")
        
        # Run multiple times and check for variation
        results = [transforms(image=sample_image)["image"] for _ in range(10)]
        
        # Not all results should be identical (some augmentation should occur)
        unique_results = len(set(r.tobytes() for r in results))
        assert unique_results > 1, "Training transforms should produce variation"


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_image(self):
        """Test handling of empty image."""
        empty = np.array([])
        
        with pytest.raises((ValueError, IndexError)):
            normalize_face(empty)
    
    def test_single_pixel_image(self):
        """Test handling of single pixel image."""
        single_pixel = np.array([[[128, 128, 128]]], dtype=np.uint8)
        
        # Should handle gracefully
        result = normalize_face(single_pixel)
        assert result is not None
    
    def test_large_image(self):
        """Test handling of large image."""
        large = np.random.randint(0, 255, (4096, 4096, 3), dtype=np.uint8)
        
        result = normalize_face(large, target_size=(224, 224))
        assert result.shape[1:] == (224, 224)
    
    def test_float_input(self):
        """Test handling of float input."""
        float_img = np.random.rand(224, 224, 3).astype(np.float32)
        
        # Should handle or convert appropriately
        result = normalize_face(float_img)
        assert result is not None
