"""
Unit Tests for Core Utilities

Tests for exception handling, validation, and formatting utilities.
"""

from __future__ import annotations

import pytest
from decimal import Decimal

from core.exceptions import (
    AletheiaError,
    ValidationError,
    ProcessingError,
    ModelNotFoundError,
    ErrorCode,
)
from core.types import (
    AnalysisStatus,
    DetectionResult,
    ConfidenceLevel,
    ValidationResult,
)
from core.utils.validation import (
    validate_file_size,
    validate_file_extension,
    validate_video_file,
    validate_image_file,
)
from core.utils.formatting import (
    format_file_size,
    format_duration,
    format_confidence,
    truncate_string,
)


class TestExceptions:
    """Tests for custom exception classes."""
    
    def test_aletheia_error_basic(self):
        """Test basic AletheiaError creation."""
        error = AletheiaError("Test error")
        
        assert str(error) == "Test error"
        assert error.code is None
    
    def test_aletheia_error_with_code(self):
        """Test AletheiaError with error code."""
        error = AletheiaError(
            "Test error",
            code=ErrorCode.VALIDATION_ERROR,
        )
        
        assert error.code == ErrorCode.VALIDATION_ERROR
    
    def test_aletheia_error_with_details(self):
        """Test AletheiaError with details."""
        error = AletheiaError(
            "Test error",
            details={"field": "value"},
        )
        
        assert error.details == {"field": "value"}
    
    def test_validation_error(self):
        """Test ValidationError creation."""
        error = ValidationError(
            "Invalid input",
            field="email",
        )
        
        assert "Invalid input" in str(error)
        assert error.field == "email"
    
    def test_processing_error(self):
        """Test ProcessingError creation."""
        error = ProcessingError("Processing failed")
        
        assert isinstance(error, AletheiaError)
    
    def test_model_not_found_error(self):
        """Test ModelNotFoundError creation."""
        error = ModelNotFoundError("Model not found")
        
        assert isinstance(error, AletheiaError)


class TestEnums:
    """Tests for enum types."""
    
    def test_analysis_status_values(self):
        """Test AnalysisStatus enum values."""
        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.PROCESSING.value == "processing"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"
    
    def test_detection_result_values(self):
        """Test DetectionResult enum values."""
        assert DetectionResult.REAL.value == "real"
        assert DetectionResult.FAKE.value == "fake"
        assert DetectionResult.UNCERTAIN.value == "uncertain"
    
    def test_confidence_level_from_score(self):
        """Test ConfidenceLevel.from_score method."""
        assert ConfidenceLevel.from_score(98) == ConfidenceLevel.VERY_HIGH
        assert ConfidenceLevel.from_score(90) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(75) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(50) == ConfidenceLevel.LOW
    
    def test_confidence_level_edge_cases(self):
        """Test ConfidenceLevel edge cases."""
        assert ConfidenceLevel.from_score(95) == ConfidenceLevel.VERY_HIGH
        assert ConfidenceLevel.from_score(85) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(70) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0) == ConfidenceLevel.LOW


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        """Test valid ValidationResult."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.errors == []
    
    def test_validation_result_invalid(self):
        """Test invalid ValidationResult."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 2
    
    def test_validation_result_with_data(self):
        """Test ValidationResult with additional data."""
        result = ValidationResult(
            is_valid=True,
            data={"processed": True},
        )
        
        assert result.data == {"processed": True}


class TestValidationUtilities:
    """Tests for validation utility functions."""
    
    def test_validate_file_size_valid(self):
        """Test valid file size."""
        result = validate_file_size(100 * 1024 * 1024, max_size=500 * 1024 * 1024)
        assert result.is_valid
    
    def test_validate_file_size_invalid(self):
        """Test invalid file size."""
        result = validate_file_size(600 * 1024 * 1024, max_size=500 * 1024 * 1024)
        assert not result.is_valid
        assert "exceeds" in result.errors[0].lower()
    
    def test_validate_file_extension_valid(self):
        """Test valid file extension."""
        result = validate_file_extension("video.mp4", allowed=[".mp4", ".avi"])
        assert result.is_valid
    
    def test_validate_file_extension_invalid(self):
        """Test invalid file extension."""
        result = validate_file_extension("video.exe", allowed=[".mp4", ".avi"])
        assert not result.is_valid
    
    def test_validate_file_extension_case_insensitive(self):
        """Test case insensitive extension validation."""
        result = validate_file_extension("video.MP4", allowed=[".mp4"])
        assert result.is_valid


class TestFormattingUtilities:
    """Tests for formatting utility functions."""
    
    def test_format_file_size_bytes(self):
        """Test formatting bytes."""
        assert format_file_size(500) == "500 B"
    
    def test_format_file_size_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
    
    def test_format_file_size_megabytes(self):
        """Test formatting megabytes."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
    
    def test_format_file_size_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_format_duration_seconds(self):
        """Test formatting seconds."""
        assert format_duration(45) == "0:45"
    
    def test_format_duration_minutes(self):
        """Test formatting minutes."""
        assert format_duration(125) == "2:05"
    
    def test_format_duration_hours(self):
        """Test formatting hours."""
        assert format_duration(3725) == "1:02:05"
    
    def test_format_confidence_high(self):
        """Test formatting high confidence."""
        result = format_confidence(0.95)
        assert "95" in result
    
    def test_format_confidence_low(self):
        """Test formatting low confidence."""
        result = format_confidence(0.45)
        assert "45" in result
    
    def test_truncate_string_short(self):
        """Test truncating short string (no truncation needed)."""
        assert truncate_string("Hello", max_length=10) == "Hello"
    
    def test_truncate_string_long(self):
        """Test truncating long string."""
        result = truncate_string("Hello World", max_length=8)
        assert len(result) <= 8
        assert result.endswith("...")
    
    def test_truncate_string_exact(self):
        """Test truncating string at exact length."""
        result = truncate_string("Hello", max_length=5)
        assert result == "Hello"
