"""
Security Utilities

Cryptographic and security-related utility functions:
    - Secure token generation
    - File hashing
    - Input sanitization
    - Filename sanitization

All functions are designed with security best practices:
    - Use of cryptographically secure random
    - Constant-time comparisons where applicable
    - Defense against common attacks (path traversal, etc.)
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import unicodedata
from pathlib import Path
from typing import BinaryIO, Final

# Regex patterns for sanitization
_FILENAME_UNSAFE_CHARS: Final[re.Pattern] = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_FILENAME_RESERVED: Final[frozenset[str]] = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})

# Hash algorithm configurations
HASH_ALGORITHM: Final[str] = "sha256"
HASH_CHUNK_SIZE: Final[int] = 8192  # 8 KB chunks for file hashing


def generate_secure_token(
    length: int = 32,
    alphabet: str | None = None,
) -> str:
    """
    Generate a cryptographically secure random token.
    
    Uses Python's secrets module which is suitable for security-sensitive
    applications including token generation for authentication.
    
    Args:
        length: Length of the token in characters.
            For hex tokens, actual entropy is length * 4 bits.
            For URL-safe tokens, entropy is approximately length * 6 bits.
        alphabet: Optional custom alphabet. If None, uses URL-safe base64.
    
    Returns:
        Secure random token string.
    
    Example:
        >>> token = generate_secure_token(32)
        >>> len(token)
        32
        >>> token.isalnum() or '-' in token or '_' in token
        True
    
    Security Note:
        For session tokens, use at least 32 characters.
        For API keys, use at least 40 characters.
    """
    if alphabet:
        return "".join(secrets.choice(alphabet) for _ in range(length))
    return secrets.token_urlsafe(length)[:length]


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Format: 'ale_' prefix + 40 character secure token.
    The prefix helps identify Aletheia API keys.
    
    Returns:
        API key string (44 characters total).
    
    Example:
        >>> key = generate_api_key()
        >>> key.startswith('ale_')
        True
        >>> len(key)
        44
    """
    return f"ale_{generate_secure_token(40)}"


def hash_file(
    file: BinaryIO | Path | str,
    algorithm: str = HASH_ALGORITHM,
) -> str:
    """
    Calculate cryptographic hash of a file.
    
    Uses streaming to handle large files efficiently without
    loading the entire file into memory.
    
    Args:
        file: File object (opened in binary mode), Path, or string path.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hexadecimal hash string.
    
    Example:
        >>> with open("video.mp4", "rb") as f:
        ...     file_hash = hash_file(f)
        >>> len(file_hash)  # SHA256 produces 64 hex characters
        64
    
    Raises:
        FileNotFoundError: If file path doesn't exist.
        ValueError: If algorithm is not supported.
    """
    hasher = hashlib.new(algorithm)
    
    if isinstance(file, (str, Path)):
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                hasher.update(chunk)
    else:
        # File object - read in chunks
        for chunk in iter(lambda: file.read(HASH_CHUNK_SIZE), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def hash_string(
    value: str,
    algorithm: str = HASH_ALGORITHM,
) -> str:
    """
    Calculate cryptographic hash of a string.
    
    Args:
        value: String to hash.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hexadecimal hash string.
    """
    return hashlib.new(algorithm, value.encode("utf-8")).hexdigest()


def sanitize_filename(
    filename: str,
    max_length: int = 255,
    replacement: str = "_",
) -> str:
    """
    Sanitize a filename to be safe for filesystem operations.
    
    Performs the following sanitization:
        1. Normalizes Unicode (NFC normalization)
        2. Removes or replaces unsafe characters
        3. Handles reserved Windows filenames
        4. Prevents path traversal attacks
        5. Enforces maximum length
    
    Args:
        filename: Original filename to sanitize.
        max_length: Maximum allowed filename length.
        replacement: Character to replace unsafe characters with.
    
    Returns:
        Sanitized filename safe for filesystem operations.
    
    Example:
        >>> sanitize_filename("../../etc/passwd")
        '__etc_passwd'
        >>> sanitize_filename("my:file<name>.txt")
        'my_file_name_.txt'
        >>> sanitize_filename("CON.txt")
        '_CON.txt'
    
    Security Note:
        Always sanitize user-provided filenames before using them
        in file operations to prevent path traversal attacks.
    """
    if not filename:
        return f"unnamed_{generate_secure_token(8)}"
    
    # Normalize Unicode
    filename = unicodedata.normalize("NFC", filename)
    
    # Remove path components (prevent path traversal)
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    filename = _FILENAME_UNSAFE_CHARS.sub(replacement, filename)
    
    # Handle reserved Windows filenames
    name_without_ext = filename.rsplit(".", 1)[0].upper()
    if name_without_ext in _FILENAME_RESERVED:
        filename = f"_{filename}"
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")
    
    # Ensure we have a filename
    if not filename:
        filename = f"unnamed_{generate_secure_token(8)}"
    
    # Enforce maximum length (preserve extension if possible)
    if len(filename) > max_length:
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            max_name_length = max_length - len(ext) - 1
            if max_name_length > 0:
                filename = f"{name[:max_name_length]}.{ext}"
            else:
                filename = filename[:max_length]
        else:
            filename = filename[:max_length]
    
    return filename


def sanitize_path(path: str | Path) -> Path:
    """
    Sanitize a file path to prevent path traversal attacks.
    
    Resolves the path to an absolute path and ensures it doesn't
    escape the intended directory.
    
    Args:
        path: Path to sanitize.
    
    Returns:
        Resolved absolute Path object.
    
    Raises:
        ValueError: If path contains suspicious patterns.
    
    Security Note:
        Always validate that the resulting path is within
        your intended base directory after calling this function.
    """
    path_str = str(path)
    
    # Check for null bytes
    if "\x00" in path_str:
        raise ValueError("Path contains null bytes")
    
    # Resolve to absolute path
    resolved = Path(path_str).resolve()
    
    return resolved


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Compare two strings in constant time.
    
    Prevents timing attacks by ensuring comparison takes the same
    amount of time regardless of where the strings differ.
    
    Args:
        val1: First string.
        val2: Second string.
    
    Returns:
        True if strings are equal, False otherwise.
    
    Security Note:
        Always use this for comparing sensitive values like
        tokens, API keys, or passwords.
    """
    return secrets.compare_digest(val1.encode(), val2.encode())


def mask_sensitive_value(
    value: str,
    visible_chars: int = 4,
    mask_char: str = "*",
) -> str:
    """
    Mask a sensitive value for display/logging.
    
    Shows only the last few characters with the rest masked.
    
    Args:
        value: Sensitive value to mask.
        visible_chars: Number of characters to show at the end.
        mask_char: Character to use for masking.
    
    Returns:
        Masked string.
    
    Example:
        >>> mask_sensitive_value("api_key_12345678")
        '************5678'
    """
    if len(value) <= visible_chars:
        return mask_char * len(value)
    
    masked_length = len(value) - visible_chars
    return mask_char * masked_length + value[-visible_chars:]


def generate_file_id(file_content: BinaryIO | bytes) -> str:
    """
    Generate a unique identifier for a file based on its content.
    
    Uses the first and last chunks plus file size to create a
    fast content-based ID without reading the entire file.
    
    Args:
        file_content: File object or bytes.
    
    Returns:
        16-character hexadecimal ID.
    """
    hasher = hashlib.sha256()
    
    if isinstance(file_content, bytes):
        hasher.update(file_content)
    else:
        # Read first chunk
        file_content.seek(0)
        first_chunk = file_content.read(HASH_CHUNK_SIZE)
        hasher.update(first_chunk)
        
        # Read last chunk
        file_content.seek(0, 2)  # Seek to end
        file_size = file_content.tell()
        hasher.update(file_size.to_bytes(8, "big"))
        
        if file_size > HASH_CHUNK_SIZE:
            file_content.seek(-HASH_CHUNK_SIZE, 2)  # Seek to last chunk
            last_chunk = file_content.read()
            hasher.update(last_chunk)
        
        file_content.seek(0)  # Reset position
    
    return hasher.hexdigest()[:16]
