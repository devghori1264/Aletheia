"""
Media File Model

Handles uploaded video storage with comprehensive metadata tracking,
validation, and lifecycle management.
"""

from __future__ import annotations

import hashlib
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Final

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from core.constants import FileConstraints, SupportedFormats


def media_upload_path(instance: "MediaFile", filename: str) -> str:
    """
    Generate upload path for media files.
    
    Structure: uploads/{year}/{month}/{day}/{uuid}/{filename}
    
    Args:
        instance: MediaFile instance
        filename: Original filename
    
    Returns:
        Upload path string
    """
    now = timezone.now()
    sanitized_name = Path(filename).name  # Prevent directory traversal
    return f"uploads/{now.year}/{now.month:02d}/{now.day:02d}/{instance.id}/{sanitized_name}"


class MediaFileManager(models.Manager):
    """Custom manager for MediaFile model."""
    
    def videos(self):
        """Get video files only."""
        return self.filter(media_type="video")
    
    def images(self):
        """Get image files only."""
        return self.filter(media_type="image")
    
    def by_hash(self, file_hash: str):
        """Find files by SHA-256 hash (deduplication)."""
        return self.filter(file_hash=file_hash)
    
    def unprocessed(self):
        """Get files that haven't been analyzed."""
        return self.filter(analyses__isnull=True)


class MediaFile(models.Model):
    """
    Uploaded media file model.
    
    Stores video and image files for deepfake detection analysis.
    Includes comprehensive metadata tracking, deduplication support,
    and secure file handling.
    
    Attributes:
        id: Unique UUID identifier
        file: The uploaded file
        original_filename: Original user-provided filename
        file_hash: SHA-256 hash for deduplication
        media_type: video or image
        file_size: Size in bytes
        duration: Video duration in seconds
        frame_count: Total frames in video
    
    Example:
        >>> media = MediaFile.objects.create(
        ...     user=request.user,
        ...     file=uploaded_file,
        ...     original_filename=uploaded_file.name,
        ... )
        >>> media.extract_metadata()
    """
    
    # Media type choices
    MEDIA_TYPE_CHOICES: Final = [
        ("video", "Video"),
        ("image", "Image"),
    ]
    
    # Processing status choices
    STATUS_CHOICES: Final = [
        ("uploaded", "Uploaded"),
        ("validating", "Validating"),
        ("validated", "Validated"),
        ("invalid", "Invalid"),
        ("deleted", "Deleted"),
    ]
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique file identifier",
    )
    
    # User relationship
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_files",
        help_text="User who uploaded the file",
    )
    
    # File storage
    file = models.FileField(
        upload_to=media_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=SupportedFormats.VIDEO_EXTENSIONS 
                + SupportedFormats.IMAGE_EXTENSIONS
            ),
        ],
        help_text="Uploaded media file",
    )
    
    # File metadata
    original_filename = models.CharField(
        max_length=500,
        help_text="Original filename as uploaded",
    )
    
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of file contents",
    )
    
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        db_index=True,
        help_text="Type of media (video/image)",
    )
    
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="MIME type of the file",
    )
    
    file_size = models.BigIntegerField(
        default=0,
        help_text="File size in bytes",
    )
    
    # Validation status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded",
        db_index=True,
        help_text="File validation status",
    )
    
    validation_error = models.TextField(
        blank=True,
        help_text="Validation error message if invalid",
    )
    
    # Video-specific metadata
    duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Video duration in seconds",
    )
    
    frame_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of frames",
    )
    
    fps = models.FloatField(
        null=True,
        blank=True,
        help_text="Frames per second",
    )
    
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Video/image width in pixels",
    )
    
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Video/image height in pixels",
    )
    
    codec = models.CharField(
        max_length=50,
        blank=True,
        help_text="Video codec used",
    )
    
    has_audio = models.BooleanField(
        default=False,
        help_text="Whether video contains audio track",
    )
    
    # Derived files
    thumbnail_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated thumbnail",
    )
    
    preview_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to preview/compressed version",
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Upload timestamp",
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp",
    )
    
    # Storage tracking
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag",
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deletion timestamp",
    )
    
    # Extensible metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional file metadata",
    )
    
    # Custom manager
    objects = MediaFileManager()
    
    class Meta:
        verbose_name = "Media File"
        verbose_name_plural = "Media Files"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["media_type", "status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["file_hash"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.original_filename} ({self.media_type})"
    
    def __repr__(self) -> str:
        return f"<MediaFile(id={self.id}, name={self.original_filename})>"
    
    # ==========================================================================
    # Properties
    # ==========================================================================
    
    @property
    def is_video(self) -> bool:
        """Check if file is a video."""
        return self.media_type == "video"
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.media_type == "image"
    
    @property
    def is_valid(self) -> bool:
        """Check if file passed validation."""
        return self.status == "validated"
    
    @property
    def file_exists(self) -> bool:
        """Check if file exists on storage."""
        try:
            return self.file and self.file.storage.exists(self.file.name)
        except Exception:
            return False
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return Path(self.original_filename).suffix.lower()
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024) if self.file_size else 0.0
    
    @property
    def resolution(self) -> str:
        """Get resolution string (e.g., '1920x1080')."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"
    
    @property
    def aspect_ratio(self) -> float | None:
        """Calculate aspect ratio."""
        if self.width and self.height:
            return self.width / self.height
        return None
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string (HH:MM:SS)."""
        if not self.duration:
            return "00:00:00"
        
        total_seconds = int(self.duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # ==========================================================================
    # Methods
    # ==========================================================================
    
    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of file contents.
        
        Uses chunked reading to handle large files efficiently.
        
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        
        self.file.seek(0)
        for chunk in self.file.chunks(chunk_size=8192):
            sha256.update(chunk)
        self.file.seek(0)
        
        return sha256.hexdigest()
    
    def detect_media_type(self) -> str:
        """
        Detect media type from file extension and MIME type.
        
        Returns:
            'video' or 'image'
        """
        ext = self.extension.lstrip(".")
        
        if ext in SupportedFormats.VIDEO_EXTENSIONS:
            return "video"
        elif ext in SupportedFormats.IMAGE_EXTENSIONS:
            return "image"
        
        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(self.original_filename)
        if mime_type:
            if mime_type.startswith("video/"):
                return "video"
            elif mime_type.startswith("image/"):
                return "image"
        
        return "video"  # Default assumption
    
    def extract_metadata(self) -> dict[str, Any]:
        """
        Extract metadata from the uploaded file.
        
        Uses OpenCV/ffprobe for video metadata extraction.
        
        Returns:
            Dictionary of extracted metadata
        """
        import cv2
        
        metadata = {}
        
        if self.is_video and self.file:
            try:
                cap = cv2.VideoCapture(self.file.path)
                
                if cap.isOpened():
                    self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.fps = cap.get(cv2.CAP_PROP_FPS)
                    self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    
                    if self.fps and self.fps > 0:
                        self.duration = self.frame_count / self.fps
                    
                    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                    self.codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                    
                    metadata = {
                        "width": self.width,
                        "height": self.height,
                        "fps": self.fps,
                        "frame_count": self.frame_count,
                        "duration": self.duration,
                        "codec": self.codec,
                    }
                
                cap.release()
                
            except Exception as e:
                metadata["extraction_error"] = str(e)
        
        elif self.is_image and self.file:
            try:
                from PIL import Image
                
                with Image.open(self.file.path) as img:
                    self.width, self.height = img.size
                    metadata = {
                        "width": self.width,
                        "height": self.height,
                        "mode": img.mode,
                        "format": img.format,
                    }
                    
            except Exception as e:
                metadata["extraction_error"] = str(e)
        
        self.metadata.update(metadata)
        return metadata
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate file meets requirements.
        
        Checks:
            - File size within limits
            - Valid media type
            - Minimum resolution
            - Valid codec (for video)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        self.status = "validating"
        self.save(update_fields=["status"])
        
        errors = []
        
        # Check file size
        if self.file_size > FileConstraints.MAX_VIDEO_SIZE_BYTES:
            max_mb = FileConstraints.MAX_VIDEO_SIZE_BYTES / (1024 * 1024)
            errors.append(f"File size exceeds maximum of {max_mb}MB")
        
        # Check extension
        ext = self.extension.lstrip(".")
        allowed = SupportedFormats.VIDEO_EXTENSIONS + SupportedFormats.IMAGE_EXTENSIONS
        if ext not in allowed:
            errors.append(f"Unsupported file format: {ext}")
        
        # Check resolution (if metadata extracted)
        if self.width and self.height:
            min_dim = min(self.width, self.height)
            if min_dim < FileConstraints.MIN_VIDEO_DIMENSION:
                errors.append(
                    f"Resolution too low: {self.resolution}. "
                    f"Minimum dimension: {FileConstraints.MIN_VIDEO_DIMENSION}px"
                )
        
        # Check duration (for video)
        if self.is_video and self.duration:
            if self.duration < 1.0:
                errors.append("Video too short: minimum 1 second")
            if self.duration > FileConstraints.MAX_VIDEO_DURATION_SECONDS:
                errors.append(
                    f"Video too long: maximum {FileConstraints.MAX_VIDEO_DURATION_SECONDS} seconds"
                )
        
        # Update status
        if errors:
            self.status = "invalid"
            self.validation_error = "; ".join(errors)
            self.save(update_fields=["status", "validation_error"])
            return False, self.validation_error
        
        self.status = "validated"
        self.save(update_fields=["status"])
        return True, ""
    
    def soft_delete(self) -> None:
        """Soft delete the file (mark as deleted)."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.status = "deleted"
        self.save(update_fields=["is_deleted", "deleted_at", "status"])
    
    def hard_delete(self) -> None:
        """Permanently delete file and database record."""
        if self.file_exists:
            self.file.delete(save=False)
        self.delete()
    
    def generate_thumbnail(self, frame_index: int = 0) -> str | None:
        """
        Generate thumbnail image from video.
        
        Args:
            frame_index: Which frame to use for thumbnail
        
        Returns:
            Path to generated thumbnail or None
        """
        if not self.is_video or not self.file_exists:
            return None
        
        import cv2
        
        try:
            cap = cv2.VideoCapture(self.file.path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Generate thumbnail path
                thumb_dir = Path(settings.MEDIA_ROOT) / "thumbnails" / str(self.id)
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = thumb_dir / "thumbnail.jpg"
                
                # Resize to thumbnail dimensions
                thumb_width = 320
                thumb_height = int(320 * self.height / self.width) if self.width else 240
                thumbnail = cv2.resize(frame, (thumb_width, thumb_height))
                
                cv2.imwrite(str(thumb_path), thumbnail)
                
                self.thumbnail_path = str(thumb_path.relative_to(settings.MEDIA_ROOT))
                self.save(update_fields=["thumbnail_path"])
                
                return self.thumbnail_path
        
        except Exception:
            pass
        
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        # Build the file URL - use the actual file path
        file_url = None
        if self.file and self.file.name:
            file_url = f"/media/{self.file.name}"
        
        # Build thumbnail URL
        thumbnail_url = None
        if self.thumbnail_path:
            thumbnail_url = f"/media/{self.thumbnail_path}"
        
        return {
            "id": str(self.id),
            "original_filename": self.original_filename,
            "media_type": self.media_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "size_mb": round(self.size_mb, 2),
            "status": self.status,
            "resolution": self.resolution,
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "has_audio": self.has_audio,
            "file_url": file_url,
            "thumbnail_url": thumbnail_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def save(self, *args, **kwargs) -> None:
        """
        Override save to auto-populate fields.
        """
        # Set media type if not set
        if not self.media_type and self.original_filename:
            self.media_type = self.detect_media_type()
        
        # Set MIME type
        if not self.mime_type and self.original_filename:
            mime, _ = mimetypes.guess_type(self.original_filename)
            self.mime_type = mime or ""
        
        # Set file size
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        
        super().save(*args, **kwargs)
