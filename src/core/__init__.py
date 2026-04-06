"""
Aletheia Core Module

Shared utilities, base classes, and common functionality used across
all Aletheia applications. This module provides:

    - Custom exception hierarchy
    - Type definitions and protocols
    - Application constants
    - Utility decorators
    - Common mixins
    - Helper functions

Design Philosophy:
    - Zero business logic - purely infrastructure
    - Framework-agnostic where possible
    - Comprehensive type hints
    - Thorough documentation
"""

from __future__ import annotations

__all__ = [
    "exceptions",
    "constants",
    "types",
    "decorators",
    "mixins",
]
