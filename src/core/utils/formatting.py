"""
Output Formatting Utilities

Functions for formatting values for display and API responses:
    - Human-readable durations
    - File size formatting
    - Confidence score formatting
    - Result formatting

All formatting functions support both human-readable output
and structured output for programmatic use.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Final, Literal

from core.constants import (
    LABEL_REAL,
    LABEL_FAKE,
    LABEL_UNCERTAIN,
    CONFIDENCE_LOW_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    CONFIDENCE_HIGH_THRESHOLD,
)


# =============================================================================
# TIME FORMATTING
# =============================================================================

def format_duration(
    seconds: float,
    precision: int = 2,
    verbose: bool = False,
) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds.
        precision: Decimal places for sub-second precision.
        verbose: Use verbose format (e.g., "2 hours, 30 minutes").
    
    Returns:
        Formatted duration string.
    
    Examples:
        >>> format_duration(3661.5)
        '1:01:01'
        >>> format_duration(3661.5, verbose=True)
        '1 hour, 1 minute, 1 second'
        >>> format_duration(0.5)
        '0.50s'
    """
    if seconds < 0:
        return "Invalid duration"
    
    if seconds < 1:
        return f"{seconds:.{precision}f}s"
    
    # Calculate time components
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if verbose:
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:
            if secs == int(secs):
                parts.append(f"{int(secs)} second{'s' if secs != 1 else ''}")
            else:
                parts.append(f"{secs:.{precision}f} seconds")
        return ", ".join(parts)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:05.{precision}f}"
    elif minutes > 0:
        return f"{minutes}:{secs:05.{precision}f}"
    else:
        return f"{secs:.{precision}f}s"


def format_timestamp(
    dt: datetime | None = None,
    format_str: str = "%Y-%m-%d %H:%M:%S UTC",
) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object (defaults to now).
        format_str: strftime format string.
    
    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime(format_str)


def format_relative_time(
    dt: datetime,
    now: datetime | None = None,
) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        dt: Datetime to format.
        now: Reference datetime (defaults to now).
    
    Returns:
        Relative time string.
    
    Examples:
        >>> format_relative_time(datetime.now() - timedelta(hours=2))
        '2 hours ago'
        >>> format_relative_time(datetime.now() - timedelta(days=1))
        'yesterday'
    """
    if now is None:
        now = datetime.utcnow()
    
    diff = now - dt
    
    if diff.total_seconds() < 0:
        return "in the future"
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 172800:
        return "yesterday"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} days ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")


# =============================================================================
# SIZE FORMATTING
# =============================================================================

def format_file_size(
    size_bytes: int,
    binary: bool = True,
    precision: int = 1,
) -> str:
    """
    Format file size to human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        binary: Use binary units (KiB, MiB) vs decimal (KB, MB).
        precision: Decimal places.
    
    Returns:
        Formatted size string.
    
    Examples:
        >>> format_file_size(1536)
        '1.5 KiB'
        >>> format_file_size(1536, binary=False)
        '1.5 KB'
        >>> format_file_size(1073741824)
        '1.0 GiB'
    """
    if size_bytes < 0:
        return "Invalid size"
    
    if binary:
        units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
        divisor = 1024
    else:
        units = ("B", "KB", "MB", "GB", "TB", "PB")
        divisor = 1000
    
    size = float(size_bytes)
    unit_index = 0
    
    while size >= divisor and unit_index < len(units) - 1:
        size /= divisor
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    
    return f"{size:.{precision}f} {units[unit_index]}"


def format_number(
    value: int | float,
    precision: int = 2,
    thousands_separator: str = ",",
) -> str:
    """
    Format number with thousands separator.
    
    Args:
        value: Number to format.
        precision: Decimal places for floats.
        thousands_separator: Separator for thousands.
    
    Returns:
        Formatted number string.
    
    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.5678, precision=2)
        '1,234.57'
    """
    if isinstance(value, int):
        return f"{value:,}".replace(",", thousands_separator)
    else:
        formatted = f"{value:,.{precision}f}"
        return formatted.replace(",", thousands_separator)


# =============================================================================
# CONFIDENCE FORMATTING
# =============================================================================

def format_confidence(
    confidence: float,
    as_percentage: bool = True,
    include_level: bool = False,
) -> str:
    """
    Format confidence score for display.
    
    Args:
        confidence: Confidence value (0.0-1.0 or 0-100).
        as_percentage: Format as percentage.
        include_level: Include confidence level label.
    
    Returns:
        Formatted confidence string.
    
    Examples:
        >>> format_confidence(0.95)
        '95.0%'
        >>> format_confidence(0.95, include_level=True)
        '95.0% (Very High)'
        >>> format_confidence(0.65)
        '65.0%'
    """
    # Normalize to percentage if needed
    if confidence <= 1.0:
        percentage = confidence * 100
    else:
        percentage = confidence
    
    if as_percentage:
        formatted = f"{percentage:.1f}%"
    else:
        formatted = f"{confidence:.4f}"
    
    if include_level:
        level = get_confidence_level(percentage)
        formatted = f"{formatted} ({level})"
    
    return formatted


def get_confidence_level(
    confidence: float,
) -> Literal["Very High", "High", "Medium", "Low"]:
    """
    Get confidence level category.
    
    Args:
        confidence: Confidence percentage (0-100).
    
    Returns:
        Confidence level string.
    """
    if confidence >= CONFIDENCE_HIGH_THRESHOLD:
        return "Very High"
    elif confidence >= CONFIDENCE_MEDIUM_THRESHOLD:
        return "High"
    elif confidence >= CONFIDENCE_LOW_THRESHOLD:
        return "Medium"
    else:
        return "Low"


def get_confidence_color(
    confidence: float,
) -> str:
    """
    Get color code for confidence level (for UI).
    
    Args:
        confidence: Confidence percentage (0-100).
    
    Returns:
        Hex color code.
    """
    COLORS: Final[dict[str, str]] = {
        "Very High": "#22c55e",  # Green
        "High": "#84cc16",       # Lime
        "Medium": "#eab308",     # Yellow
        "Low": "#ef4444",        # Red
    }
    
    level = get_confidence_level(confidence)
    return COLORS[level]


# =============================================================================
# RESULT FORMATTING
# =============================================================================

def format_detection_result(
    result: str,
    confidence: float,
    include_emoji: bool = True,
) -> str:
    """
    Format detection result for display.
    
    Args:
        result: Detection result (REAL/FAKE/UNCERTAIN).
        confidence: Confidence percentage.
        include_emoji: Include result emoji.
    
    Returns:
        Formatted result string.
    
    Examples:
        >>> format_detection_result("REAL", 95.5)
        '✅ REAL (95.5%)'
        >>> format_detection_result("FAKE", 88.2)
        '❌ FAKE (88.2%)'
    """
    EMOJIS: Final[dict[str, str]] = {
        LABEL_REAL: "✅",
        LABEL_FAKE: "❌",
        LABEL_UNCERTAIN: "⚠️",
    }
    
    result_upper = result.upper()
    
    if include_emoji:
        emoji = EMOJIS.get(result_upper, "❓")
        return f"{emoji} {result_upper} ({confidence:.1f}%)"
    else:
        return f"{result_upper} ({confidence:.1f}%)"


def format_result_summary(
    result: str,
    confidence: float,
    frames_analyzed: int,
    processing_time: float,
) -> dict[str, Any]:
    """
    Format complete result summary as dictionary.
    
    Args:
        result: Detection result.
        confidence: Confidence percentage.
        frames_analyzed: Number of frames processed.
        processing_time: Processing time in seconds.
    
    Returns:
        Structured result summary.
    """
    return {
        "result": {
            "label": result.upper(),
            "confidence": round(confidence, 2),
            "confidence_level": get_confidence_level(confidence),
            "formatted": format_detection_result(result, confidence),
        },
        "analysis": {
            "frames_analyzed": frames_analyzed,
            "processing_time_seconds": round(processing_time, 3),
            "processing_time_formatted": format_duration(processing_time),
        },
    }


# =============================================================================
# ERROR FORMATTING
# =============================================================================

def format_error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    error_id: str | None = None,
) -> dict[str, Any]:
    """
    Format error for API response.
    
    Args:
        code: Error code.
        message: Error message.
        details: Additional error details.
        error_id: Unique error identifier.
    
    Returns:
        Structured error response.
    """
    response = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if error_id:
        response["error"]["error_id"] = error_id
    
    return response


def format_validation_errors(
    errors: list[str],
) -> dict[str, Any]:
    """
    Format validation errors for API response.
    
    Args:
        errors: List of error messages.
    
    Returns:
        Structured validation error response.
    """
    return {
        "error": {
            "code": "E1000",
            "message": "Validation failed",
            "details": {
                "errors": errors,
                "error_count": len(errors),
            },
        }
    }
