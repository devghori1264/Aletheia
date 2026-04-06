"""
Input Validation Utilities

Comprehensive validation functions for user inputs:
    - Video file validation
    - Parameter validation
    - Structured validation results

Design principles:
    - Return detailed validation results, not just bool
    - Early validation to fail fast
    - Composable validators
    - Human-readable error messages
"""

from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Final, Literal

from core.constants import (
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_VIDEO_MIME_TYPES,
    MAX_VIDEO_SIZE_BYTES,
    MIN_FRAMES_REQUIRED,
    MAX_FRAMES_ALLOWED,
    MIN_VIDEO_DURATION,
    MAX_VIDEO_DURATION,
)


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class ValidationResult:
    """
    Structured result of a validation operation.
    
    Provides detailed information about validation outcome including
    specific errors for user feedback.
    
    Attributes:
        is_valid: Whether validation passed.
        errors: List of error messages (empty if valid).
        warnings: List of warning messages (non-fatal issues).
        metadata: Additional validation metadata.
    
    Example:
        >>> result = validate_video_file(file)
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(f"Error: {error}")
    """
    
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, message: str) -> "ValidationResult":
        """Add an error and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False
        return self
    
    def add_warning(self, message: str) -> "ValidationResult":
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(message)
        return self
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.metadata.update(other.metadata)
        return self
    
    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.is_valid


def _format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# =============================================================================
# VIDEO VALIDATION
# =============================================================================

def validate_video_file(
    file: BinaryIO | Path | str,
    max_size: int = MAX_VIDEO_SIZE_BYTES,
    allowed_extensions: frozenset[str] = ALLOWED_VIDEO_EXTENSIONS,
) -> ValidationResult:
    """
    Validate a video file for processing.
    
    Performs comprehensive validation including:
        1. File existence (for paths)
        2. File extension check
        3. MIME type verification
        4. File size validation
        5. Basic file integrity (magic bytes)
    
    Args:
        file: File object, Path, or string path.
        max_size: Maximum allowed file size in bytes.
        allowed_extensions: Set of allowed file extensions.
    
    Returns:
        ValidationResult with detailed status.
    
    Example:
        >>> result = validate_video_file("video.mp4")
        >>> if result.is_valid:
        ...     process_video(file)
        ... else:
        ...     print(result.errors)
    """
    result = ValidationResult()
    
    # Convert to Path if string
    if isinstance(file, str):
        file = Path(file)
    
    # Handle Path objects
    if isinstance(file, Path):
        # Check existence
        if not file.exists():
            return result.add_error(f"File not found: {file}")
        
        filename = file.name
        file_size = file.stat().st_size
        
        result.metadata["filename"] = filename
        result.metadata["file_size"] = file_size
        result.metadata["file_path"] = str(file)
    else:
        # Handle file objects
        filename = getattr(file, "name", "unknown")
        
        # Get file size
        current_pos = file.tell()
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(current_pos)  # Restore position
        
        result.metadata["filename"] = filename
        result.metadata["file_size"] = file_size
    
    # Validate file extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in allowed_extensions:
        result.add_error(
            f"Unsupported file format: '{ext}'. "
            f"Allowed formats: {', '.join(sorted(allowed_extensions))}"
        )
    
    result.metadata["extension"] = ext
    
    # Validate MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and mime_type not in ALLOWED_VIDEO_MIME_TYPES:
        result.add_warning(
            f"MIME type '{mime_type}' may not be fully supported"
        )
    
    result.metadata["mime_type"] = mime_type
    
    # Validate file size
    if file_size > max_size:
        result.add_error(
            f"File size ({_format_size(file_size)}) exceeds maximum "
            f"allowed size ({_format_size(max_size)})"
        )
    elif file_size == 0:
        result.add_error("File is empty")
    
    # Validate magic bytes (basic integrity check)
    if isinstance(file, Path):
        with open(file, "rb") as f:
            magic_result = _validate_video_magic_bytes(f, ext)
    else:
        magic_result = _validate_video_magic_bytes(file, ext)
    
    result.merge(magic_result)
    
    return result


def _validate_video_magic_bytes(file: BinaryIO, extension: str) -> ValidationResult:
    """
    Validate video file magic bytes (file signature).
    
    Checks the first few bytes of the file to verify it matches
    the expected format for the given extension.
    """
    result = ValidationResult()
    
    # Save current position
    current_pos = file.tell()
    file.seek(0)
    
    # Read magic bytes
    header = file.read(32)
    file.seek(current_pos)  # Restore position
    
    if len(header) < 4:
        return result.add_error("File too small to validate")
    
    # Magic byte signatures
    MAGIC_BYTES: Final[dict[str, list[bytes]]] = {
        ".mp4": [b"\x00\x00\x00", b"ftyp"],  # May start with size + "ftyp"
        ".avi": [b"RIFF"],
        ".mkv": [b"\x1a\x45\xdf\xa3"],  # EBML header
        ".webm": [b"\x1a\x45\xdf\xa3"],  # Same as MKV
        ".mov": [b"\x00\x00\x00", b"ftyp", b"moov"],
        ".wmv": [b"\x30\x26\xb2\x75"],  # ASF header
        ".flv": [b"FLV"],
        ".gif": [b"GIF87a", b"GIF89a"],
    }
    
    # Check if extension has known signatures
    if extension in MAGIC_BYTES:
        signatures = MAGIC_BYTES[extension]
        matched = False
        
        for sig in signatures:
            if sig in header[:20]:
                matched = True
                break
        
        if not matched:
            result.add_warning(
                f"File signature doesn't match expected format for {extension}"
            )
    
    return result


def validate_video_metadata(
    duration: float | None = None,
    frame_count: int | None = None,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
) -> ValidationResult:
    """
    Validate video metadata values.
    
    Args:
        duration: Video duration in seconds.
        frame_count: Total number of frames.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second.
    
    Returns:
        ValidationResult with detailed status.
    """
    result = ValidationResult()
    
    if duration is not None:
        if duration < MIN_VIDEO_DURATION:
            result.add_error(
                f"Video duration ({duration:.1f}s) is too short. "
                f"Minimum: {MIN_VIDEO_DURATION}s"
            )
        elif duration > MAX_VIDEO_DURATION:
            result.add_error(
                f"Video duration ({duration:.1f}s) exceeds maximum. "
                f"Maximum: {MAX_VIDEO_DURATION}s"
            )
    
    if frame_count is not None:
        if frame_count < MIN_FRAMES_REQUIRED:
            result.add_error(
                f"Video has too few frames ({frame_count}). "
                f"Minimum: {MIN_FRAMES_REQUIRED}"
            )
    
    if width is not None and height is not None:
        if width < 64 or height < 64:
            result.add_error(
                f"Video resolution ({width}x{height}) is too small. "
                f"Minimum: 64x64"
            )
        elif width > 7680 or height > 4320:
            result.add_warning(
                f"Video resolution ({width}x{height}) is very high. "
                f"Processing may be slow."
            )
    
    if fps is not None:
        if fps < 1.0:
            result.add_error(f"Invalid frame rate: {fps} fps")
        elif fps > 120.0:
            result.add_warning(f"High frame rate ({fps} fps) may affect processing")
    
    return result


# =============================================================================
# PARAMETER VALIDATION
# =============================================================================

def validate_sequence_length(
    sequence_length: int,
    min_length: int = MIN_FRAMES_REQUIRED,
    max_length: int = MAX_FRAMES_ALLOWED,
) -> ValidationResult:
    """
    Validate sequence length parameter.
    
    Args:
        sequence_length: Requested number of frames to analyze.
        min_length: Minimum allowed sequence length.
        max_length: Maximum allowed sequence length.
    
    Returns:
        ValidationResult with detailed status.
    
    Example:
        >>> result = validate_sequence_length(60)
        >>> result.is_valid
        True
    """
    result = ValidationResult()
    
    if not isinstance(sequence_length, int):
        return result.add_error(
            f"Sequence length must be an integer, got {type(sequence_length).__name__}"
        )
    
    if sequence_length < min_length:
        result.add_error(
            f"Sequence length ({sequence_length}) is too short. "
            f"Minimum: {min_length}"
        )
    elif sequence_length > max_length:
        result.add_error(
            f"Sequence length ({sequence_length}) exceeds maximum. "
            f"Maximum: {max_length}"
        )
    
    # Add optimal sequence length recommendations
    optimal_lengths = [10, 20, 40, 60, 80, 100]
    if sequence_length not in optimal_lengths:
        closest = min(optimal_lengths, key=lambda x: abs(x - sequence_length))
        result.add_warning(
            f"Consider using sequence length {closest} for optimal model performance"
        )
    
    result.metadata["sequence_length"] = sequence_length
    
    return result


def validate_batch_size(
    batch_size: int,
    min_size: int = 1,
    max_size: int = 64,
) -> ValidationResult:
    """
    Validate batch size parameter.
    
    Args:
        batch_size: Requested batch size.
        min_size: Minimum allowed batch size.
        max_size: Maximum allowed batch size.
    
    Returns:
        ValidationResult with detailed status.
    """
    result = ValidationResult()
    
    if not isinstance(batch_size, int):
        return result.add_error(
            f"Batch size must be an integer, got {type(batch_size).__name__}"
        )
    
    if batch_size < min_size:
        result.add_error(
            f"Batch size ({batch_size}) must be at least {min_size}"
        )
    elif batch_size > max_size:
        result.add_error(
            f"Batch size ({batch_size}) exceeds maximum ({max_size})"
        )
    
    # Check if power of 2 (recommended for GPU efficiency)
    if batch_size > 1 and (batch_size & (batch_size - 1)) != 0:
        result.add_warning(
            f"Batch size {batch_size} is not a power of 2. "
            f"Consider using {2 ** (batch_size - 1).bit_length()} for better GPU utilization"
        )
    
    return result


def validate_confidence_threshold(
    threshold: float,
) -> ValidationResult:
    """
    Validate confidence threshold parameter.
    
    Args:
        threshold: Confidence threshold (0.0 to 1.0).
    
    Returns:
        ValidationResult with detailed status.
    """
    result = ValidationResult()
    
    if not isinstance(threshold, (int, float)):
        return result.add_error(
            f"Threshold must be a number, got {type(threshold).__name__}"
        )
    
    if threshold < 0.0 or threshold > 1.0:
        result.add_error(
            f"Threshold ({threshold}) must be between 0.0 and 1.0"
        )
    elif threshold < 0.3:
        result.add_warning(
            f"Low threshold ({threshold}) may result in many uncertain predictions"
        )
    elif threshold > 0.9:
        result.add_warning(
            f"High threshold ({threshold}) may result in many uncertain predictions"
        )
    
    return result


# =============================================================================
# COMPOSITE VALIDATORS
# =============================================================================

def validate_analysis_request(
    video_file: BinaryIO | Path | str,
    sequence_length: int,
    batch_size: int = 8,
) -> ValidationResult:
    """
    Validate a complete analysis request.
    
    Combines multiple validators for comprehensive request validation.
    
    Args:
        video_file: Video file to analyze.
        sequence_length: Number of frames to analyze.
        batch_size: Processing batch size.
    
    Returns:
        ValidationResult with all validation outcomes merged.
    """
    result = ValidationResult()
    
    # Validate video file
    file_result = validate_video_file(video_file)
    result.merge(file_result)
    
    # Validate sequence length
    seq_result = validate_sequence_length(sequence_length)
    result.merge(seq_result)
    
    # Validate batch size
    batch_result = validate_batch_size(batch_size)
    result.merge(batch_result)
    
    return result
