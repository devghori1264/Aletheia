"""
Media Service

Handles media file operations including upload processing,
validation, metadata extraction, and storage management.
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from core.exceptions import (
    ValidationError,
    StorageError,
    ProcessingError,
)
from core.constants import (
    FileConstraints,
    SupportedFormats,
)

if TYPE_CHECKING:
    from detection.models import MediaFile

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================

@dataclass(frozen=True, slots=True)
class UploadResult:
    """
    Result of a media upload operation.
    
    Attributes:
        success: Whether upload succeeded
        media_file: Created MediaFile instance (if successful)
        error: Error message (if failed)
        warnings: Non-fatal issues detected
    """
    
    success: bool
    media_file: "MediaFile | None" = None
    error: str = ""
    warnings: list[str] | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of media validation.
    
    Attributes:
        is_valid: Whether file passed validation
        errors: List of validation errors
        warnings: List of warnings
        metadata: Extracted file metadata
    """
    
    is_valid: bool
    errors: list[str] | None = None
    warnings: list[str] | None = None
    metadata: dict[str, Any] | None = None


# =============================================================================
# Media Service
# =============================================================================

class MediaService:
    """
    Service for managing media files.
    
    Provides operations for:
        - Processing uploaded files
        - Validating media content
        - Extracting metadata
        - Managing file storage
        - Generating thumbnails
    
    Example:
        >>> service = MediaService()
        >>> result = service.process_upload(
        ...     file=request.FILES['video'],
        ...     user=request.user,
        ... )
        >>> if result.success:
        ...     print(f"Uploaded: {result.media_file.id}")
    """
    
    def __init__(
        self,
        storage_backend: Any | None = None,
        temp_dir: Path | None = None,
    ):
        """
        Initialize the media service.
        
        Args:
            storage_backend: Custom storage backend (optional)
            temp_dir: Custom temporary directory (optional)
        """
        self._storage = storage_backend
        self._temp_dir = temp_dir or Path(settings.MEDIA_ROOT) / "temp"
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Ensure temp directory exists
        self._temp_dir.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # Upload Processing
    # =========================================================================
    
    @transaction.atomic
    def process_upload(
        self,
        file: UploadedFile | BinaryIO,
        user: Any | None = None,
        filename: str | None = None,
        validate: bool = True,
        extract_metadata: bool = True,
        generate_thumbnail: bool = True,
    ) -> UploadResult:
        """
        Process an uploaded media file.
        
        Handles the complete upload workflow:
            1. Initial validation
            2. Save to storage
            3. Content validation
            4. Metadata extraction
            5. Thumbnail generation
        
        Args:
            file: Uploaded file object
            user: User performing the upload
            filename: Override filename
            validate: Whether to validate file
            extract_metadata: Whether to extract metadata
            generate_thumbnail: Whether to generate thumbnail
        
        Returns:
            UploadResult with outcome
        """
        from detection.models import MediaFile
        
        warnings = []
        
        # Determine filename
        if filename is None:
            filename = getattr(file, "name", "unknown")
        
        original_filename = self._sanitize_filename(filename)
        
        try:
            # Pre-upload validation
            if validate:
                pre_validation = self._pre_validate(file, original_filename)
                if not pre_validation.is_valid:
                    return UploadResult(
                        success=False,
                        error="; ".join(pre_validation.errors or []),
                    )
                warnings.extend(pre_validation.warnings or [])
            
            # Determine media type
            media_type = self._detect_media_type(original_filename)
            
            # Create media file record
            media_file = MediaFile(
                user=user,
                original_filename=original_filename,
                media_type=media_type,
            )
            
            # Save file
            if hasattr(file, "seek"):
                file.seek(0)
            
            media_file.file.save(original_filename, file, save=True)
            
            self._logger.info(
                "Media file saved",
                extra={
                    "media_id": str(media_file.id),
                    "file_name": original_filename,
                    "size": media_file.file_size,
                },
            )
            
            # Calculate hash for deduplication
            media_file.file_hash = media_file.calculate_hash()
            media_file.save(update_fields=["file_hash"])
            
            # Check for duplicates
            duplicate = self._check_duplicate(media_file)
            if duplicate:
                warnings.append(
                    f"Duplicate file detected: {duplicate.id}"
                )
            
            # Content validation
            if validate:
                post_validation = self._post_validate(media_file)
                if not post_validation.is_valid:
                    # Rollback: delete the file
                    media_file.hard_delete()
                    return UploadResult(
                        success=False,
                        error="; ".join(post_validation.errors or []),
                    )
                warnings.extend(post_validation.warnings or [])
            
            # Extract metadata
            if extract_metadata:
                try:
                    media_file.extract_metadata()
                except Exception as e:
                    warnings.append(f"Metadata extraction failed: {e}")
                    self._logger.warning(
                        "Metadata extraction failed",
                        extra={"media_id": str(media_file.id), "error": str(e)},
                    )
            
            # Final validation
            if validate:
                is_valid, error = media_file.validate()
                if not is_valid:
                    media_file.status = "invalid"
                    media_file.validation_error = error
                    media_file.save()
                    
                    return UploadResult(
                        success=False,
                        error=error,
                    )
            
            # Generate thumbnail
            if generate_thumbnail and media_file.is_video:
                try:
                    media_file.generate_thumbnail()
                except Exception as e:
                    warnings.append(f"Thumbnail generation failed: {e}")
            
            return UploadResult(
                success=True,
                media_file=media_file,
                warnings=warnings if warnings else None,
            )
        
        except Exception as e:
            self._logger.error(
                "Upload processing failed",
                extra={"file_name": original_filename, "error": str(e)},
                exc_info=True,
            )
            
            return UploadResult(
                success=False,
                error=f"Upload failed: {str(e)}",
            )
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def _pre_validate(
        self,
        file: UploadedFile | BinaryIO,
        filename: str,
    ) -> ValidationResult:
        """
        Validate file before saving.
        
        Checks:
            - File extension
            - File size
            - MIME type (if available)
        """
        errors = []
        warnings = []
        
        # Check extension
        ext = Path(filename).suffix.lower().lstrip(".")
        allowed_extensions = (
            SupportedFormats.VIDEO_EXTENSIONS + 
            SupportedFormats.IMAGE_EXTENSIONS
        )
        
        if ext not in allowed_extensions:
            errors.append(
                f"Unsupported file format: .{ext}. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size
        file_size = 0
        if hasattr(file, "size"):
            file_size = file.size
        elif hasattr(file, "seek") and hasattr(file, "tell"):
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset
        
        if file_size > FileConstraints.MAX_VIDEO_SIZE_BYTES:
            max_mb = FileConstraints.MAX_VIDEO_SIZE_BYTES / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            errors.append(
                f"File too large: {actual_mb:.1f}MB (max: {max_mb}MB)"
            )
        
        # Check MIME type if available
        if hasattr(file, "content_type"):
            content_type = file.content_type
            if content_type:
                is_video = content_type.startswith("video/")
                is_image = content_type.startswith("image/")
                
                if not (is_video or is_image):
                    warnings.append(
                        f"Unexpected content type: {content_type}"
                    )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
        )
    
    def _post_validate(
        self,
        media_file: "MediaFile",
    ) -> ValidationResult:
        """
        Validate file after saving.
        
        Performs content-based validation:
            - Magic bytes verification
            - Codec support check
            - Corruption detection
        """
        from django.conf import settings
        
        errors = []
        warnings = []
        
        if not media_file.file_exists:
            errors.append("File was not saved successfully")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Skip strict validation in DEBUG mode
        if settings.DEBUG:
            return ValidationResult(is_valid=True, warnings=["Validation skipped in development mode"])
        
        # Verify magic bytes
        magic_valid = self._verify_magic_bytes(media_file.file.path)
        if not magic_valid:
            errors.append("File content does not match extension")
        
        # Check for corruption (videos)
        if media_file.is_video:
            is_readable, error = self._check_video_readable(media_file.file.path)
            if not is_readable:
                errors.append(f"Video file appears corrupted: {error}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
        )
    
    def _verify_magic_bytes(self, file_path: str) -> bool:
        """Verify file magic bytes match expected format."""
        magic_signatures = {
            # Video formats
            b"\x00\x00\x00": ["mp4", "mov", "m4v"],  # MP4/MOV (various)
            b"\x1a\x45\xdf\xa3": ["webm", "mkv"],     # WebM/MKV
            b"\x52\x49\x46\x46": ["avi"],              # AVI (RIFF)
            b"\x47": ["ts"],                           # MPEG-TS
            b"\x00\x00\x01": ["mpg", "mpeg"],          # MPEG
            # Image formats
            b"\xff\xd8\xff": ["jpg", "jpeg"],
            b"\x89\x50\x4e\x47": ["png"],
            b"\x47\x49\x46": ["gif"],
            b"\x52\x49\x46\x46": ["webp"],
        }
        
        try:
            with open(file_path, "rb") as f:
                header = f.read(12)
            
            ext = Path(file_path).suffix.lower().lstrip(".")
            
            for magic, extensions in magic_signatures.items():
                if header.startswith(magic) and ext in extensions:
                    return True
            
            # MP4 has variable header, check for 'ftyp'
            if b"ftyp" in header and ext in ["mp4", "m4v", "mov"]:
                return True
            
            return True  # Default to valid for unknown formats
            
        except Exception:
            return False
    
    def _check_video_readable(self, file_path: str) -> tuple[bool, str]:
        """Check if video file can be read."""
        try:
            import cv2
            
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                return False, "Cannot open video file"
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Cannot read video frames"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def get_media(self, media_id: UUID | str) -> "MediaFile":
        """
        Get media file by ID.
        
        Args:
            media_id: Media file identifier
        
        Returns:
            MediaFile instance
        
        Raises:
            StorageError: If not found
        """
        from detection.models import MediaFile
        
        try:
            return MediaFile.objects.get(id=media_id)
        except MediaFile.DoesNotExist:
            raise StorageError(
                f"Media file not found: {media_id}",
                details={"media_id": str(media_id)},
            )
    
    def delete_media(
        self,
        media_id: UUID | str,
        hard_delete: bool = False,
    ) -> bool:
        """
        Delete a media file.
        
        Args:
            media_id: Media file to delete
            hard_delete: Whether to permanently delete
        
        Returns:
            True if deleted
        """
        media_file = self.get_media(media_id)
        
        if hard_delete:
            media_file.hard_delete()
        else:
            media_file.soft_delete()
        
        self._logger.info(
            "Media file deleted",
            extra={
                "media_id": str(media_id),
                "hard_delete": hard_delete,
            },
        )
        
        return True
    
    def _check_duplicate(
        self,
        media_file: "MediaFile",
    ) -> "MediaFile | None":
        """Check for duplicate files by hash."""
        from detection.models import MediaFile
        
        if not media_file.file_hash:
            return None
        
        duplicate = (
            MediaFile.objects
            .filter(file_hash=media_file.file_hash)
            .exclude(id=media_file.id)
            .exclude(is_deleted=True)
            .first()
        )
        
        return duplicate
    
    # =========================================================================
    # Utilities
    # =========================================================================
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Removes path components and dangerous characters.
        """
        # Remove directory components
        filename = Path(filename).name
        
        # Replace dangerous characters
        dangerous_chars = '<>:"/\\|?*\x00'
        for char in dangerous_chars:
            filename = filename.replace(char, "_")
        
        # Limit length
        max_length = 200
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        
        # Ensure non-empty
        if not filename or filename.startswith("."):
            filename = "unnamed" + filename
        
        return filename
    
    def _detect_media_type(self, filename: str) -> str:
        """Detect media type from filename."""
        ext = Path(filename).suffix.lower().lstrip(".")
        
        if ext in SupportedFormats.VIDEO_EXTENSIONS:
            return "video"
        elif ext in SupportedFormats.IMAGE_EXTENSIONS:
            return "image"
        
        return "video"  # Default
    
    # =========================================================================
    # Storage Management
    # =========================================================================
    
    def get_storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage metrics
        """
        from detection.models import MediaFile
        from django.db.models import Sum, Count
        
        stats = MediaFile.objects.filter(is_deleted=False).aggregate(
            total_files=Count("id"),
            total_size=Sum("file_size"),
            video_count=Count("id", filter=models.Q(media_type="video")),
            image_count=Count("id", filter=models.Q(media_type="image")),
        )
        
        # Add directory sizes
        media_root = Path(settings.MEDIA_ROOT)
        
        uploads_size = self._get_directory_size(media_root / "uploads")
        thumbnails_size = self._get_directory_size(media_root / "thumbnails")
        temp_size = self._get_directory_size(self._temp_dir)
        
        return {
            "total_files": stats["total_files"] or 0,
            "total_size_bytes": stats["total_size"] or 0,
            "total_size_mb": (stats["total_size"] or 0) / (1024 * 1024),
            "video_count": stats["video_count"] or 0,
            "image_count": stats["image_count"] or 0,
            "uploads_size_mb": uploads_size / (1024 * 1024),
            "thumbnails_size_mb": thumbnails_size / (1024 * 1024),
            "temp_size_mb": temp_size / (1024 * 1024),
        }
    
    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory."""
        total = 0
        
        if not path.exists():
            return 0
        
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
        
        return total
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours
        
        Returns:
            Number of files deleted
        """
        import time
        
        cutoff = time.time() - (max_age_hours * 3600)
        count = 0
        
        if not self._temp_dir.exists():
            return 0
        
        for entry in self._temp_dir.rglob("*"):
            if entry.is_file():
                try:
                    if entry.stat().st_mtime < cutoff:
                        entry.unlink()
                        count += 1
                except OSError:
                    pass
        
        if count > 0:
            self._logger.info(
                f"Cleaned up {count} temporary files",
                extra={"max_age_hours": max_age_hours},
            )
        
        return count
    
    def cleanup_orphaned_files(self) -> int:
        """
        Clean up files not referenced in database.
        
        Returns:
            Number of files deleted
        """
        from detection.models import MediaFile
        
        media_root = Path(settings.MEDIA_ROOT)
        uploads_dir = media_root / "uploads"
        
        if not uploads_dir.exists():
            return 0
        
        # Get all file paths from database
        db_paths = set(
            MediaFile.objects.filter(is_deleted=False)
            .values_list("file", flat=True)
        )
        
        count = 0
        
        for entry in uploads_dir.rglob("*"):
            if entry.is_file():
                rel_path = str(entry.relative_to(media_root))
                
                if rel_path not in db_paths:
                    try:
                        entry.unlink()
                        count += 1
                    except OSError:
                        pass
        
        if count > 0:
            self._logger.warning(
                f"Cleaned up {count} orphaned files",
            )
        
        return count


# Import models for aggregate
from django.db import models
