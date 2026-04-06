"""
Aletheia Test Suite

Pytest configuration and shared fixtures for testing.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

# Set test environment before importing Django
os.environ.setdefault("ALETHEIA_ENVIRONMENT", "testing")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aletheia.settings.testing")


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if config.getoption("--run-slow", default=False):
        return
    
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )
    parser.addoption(
        "--run-gpu",
        action="store_true",
        default=False,
        help="Run GPU tests",
    )


# =============================================================================
# Async Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Django Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def django_db_setup():
    """Set up Django test database."""
    import django
    django.setup()


@pytest.fixture
def db_session(django_db_setup, db):
    """Provide database session for tests."""
    yield


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_image() -> np.ndarray:
    """Generate a sample RGB image for testing."""
    return np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)


@pytest.fixture
def sample_face_image() -> np.ndarray:
    """Generate a sample face-like image for testing."""
    # Create a basic face-like pattern
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    
    # Face outline (oval)
    center = (112, 112)
    img[50:194, 62:162] = 200
    
    # Eyes (dark circles)
    img[90:110, 80:95] = 50
    img[90:110, 130:145] = 50
    
    # Nose
    img[115:145, 107:117] = 150
    
    # Mouth
    img[155:165, 85:140] = 100
    
    return img


@pytest.fixture
def sample_video_frames() -> np.ndarray:
    """Generate sample video frames for testing."""
    num_frames = 30
    frames = np.random.randint(0, 255, (num_frames, 224, 224, 3), dtype=np.uint8)
    return frames


@pytest.fixture
def sample_video_path(tmp_path: Path, sample_video_frames: np.ndarray) -> Path:
    """Create a temporary video file for testing."""
    try:
        import cv2
    except ImportError:
        pytest.skip("OpenCV required for video tests")
    
    video_path = tmp_path / "test_video.mp4"
    
    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        str(video_path),
        fourcc,
        30.0,
        (224, 224),
    )
    
    for frame in sample_video_frames:
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    
    writer.release()
    
    return video_path


@pytest.fixture
def sample_image_path(tmp_path: Path, sample_image: np.ndarray) -> Path:
    """Create a temporary image file for testing."""
    try:
        import cv2
    except ImportError:
        pytest.skip("OpenCV required for image tests")
    
    image_path = tmp_path / "test_image.jpg"
    cv2.imwrite(str(image_path), cv2.cvtColor(sample_image, cv2.COLOR_RGB2BGR))
    
    return image_path


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_torch():
    """Mock PyTorch for tests that don't need actual GPU."""
    with patch.dict("sys.modules", {
        "torch": MagicMock(),
        "torch.nn": MagicMock(),
        "torch.nn.functional": MagicMock(),
        "torchvision": MagicMock(),
    }):
        yield


@pytest.fixture
def mock_model():
    """Create a mock ML model for testing."""
    model = MagicMock()
    
    # Mock forward pass
    def mock_forward(x):
        batch_size = x.shape[0] if hasattr(x, "shape") else 1
        
        # Create mock output
        output = MagicMock()
        output.logits = MagicMock()
        output.logits.cpu.return_value.numpy.return_value = np.random.rand(batch_size, 2)
        output.probabilities = MagicMock()
        output.probabilities.cpu.return_value.numpy.return_value = np.random.rand(batch_size, 2)
        
        return output
    
    model.return_value = mock_forward
    model.__call__ = mock_forward
    model.eval.return_value = model
    model.to.return_value = model
    model.half.return_value = model
    
    return model


@pytest.fixture
def mock_face_detector():
    """Create a mock face detector for testing."""
    detector = MagicMock()
    
    def mock_detect(image):
        return [
            {
                "box": [50, 50, 100, 100],
                "confidence": 0.99,
                "keypoints": {
                    "left_eye": (75, 70),
                    "right_eye": (125, 70),
                    "nose": (100, 100),
                    "mouth_left": (80, 130),
                    "mouth_right": (120, 130),
                },
            }
        ]
    
    detector.detect.side_effect = mock_detect
    
    return detector


# =============================================================================
# API Test Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Create Django REST Framework API client."""
    from rest_framework.test import APIClient
    
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, db_session):
    """Create an authenticated API client."""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )
    
    api_client.force_authenticate(user=user)
    
    return api_client


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture log messages."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# =============================================================================
# Factory Fixtures
# =============================================================================

@pytest.fixture
def analysis_factory(db_session):
    """Factory for creating Analysis instances."""
    from detection.models import Analysis, MediaFile
    
    def _create_analysis(**kwargs):
        defaults = {
            "status": "completed",
            "prediction": "fake",
            "confidence": 0.95,
            "fake_score": 0.95,
            "real_score": 0.05,
            "processing_time": 2.5,
        }
        defaults.update(kwargs)
        
        # Create media file first
        media_file = MediaFile.objects.create(
            file_name="test_video.mp4",
            file_size=1024 * 1024,
            mime_type="video/mp4",
            file_path="/tmp/test_video.mp4",
        )
        
        return Analysis.objects.create(
            media_file=media_file,
            **defaults,
        )
    
    return _create_analysis


@pytest.fixture
def media_file_factory(db_session):
    """Factory for creating MediaFile instances."""
    from detection.models import MediaFile
    
    def _create_media_file(**kwargs):
        defaults = {
            "file_name": "test_video.mp4",
            "file_size": 1024 * 1024,
            "mime_type": "video/mp4",
            "duration": 10.0,
            "width": 1920,
            "height": 1080,
            "frame_rate": 30.0,
        }
        defaults.update(kwargs)
        
        return MediaFile.objects.create(**defaults)
    
    return _create_media_file
