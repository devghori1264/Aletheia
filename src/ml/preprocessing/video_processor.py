"""
Video Processor

High-performance video processing pipeline for frame extraction,
face detection, and sequence preparation for deepfake detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence
import threading
from queue import Queue

import cv2
import numpy as np

from core.exceptions import ProcessingError, ValidationError
from core.constants import FileConstraints, AnalysisSettings

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """
    Video file metadata.
    
    Attributes:
        path: Path to video file
        width: Frame width in pixels
        height: Frame height in pixels
        fps: Frames per second
        frame_count: Total number of frames
        duration: Video duration in seconds
        codec: Video codec identifier
        has_audio: Whether video has audio track
    """
    
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float
    codec: str
    has_audio: bool = False
    
    @property
    def resolution(self) -> str:
        """Get resolution string."""
        return f"{self.width}x{self.height}"
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.width / self.height if self.height > 0 else 0.0
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (HH:MM:SS)."""
        total = int(self.duration)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class FrameSequence:
    """
    Extracted frame sequence with metadata.
    
    Attributes:
        frames: Numpy array of frames (N, H, W, C)
        indices: Original frame indices
        timestamps: Frame timestamps in milliseconds
        faces: Extracted face regions (if available)
        face_boxes: Face bounding boxes per frame
    """
    
    frames: np.ndarray
    indices: list[int] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)
    faces: np.ndarray | None = None
    face_boxes: list[list[dict[str, int]]] = field(default_factory=list)
    
    def __len__(self) -> int:
        return len(self.frames)
    
    @property
    def shape(self) -> tuple[int, ...]:
        """Get frame array shape."""
        return self.frames.shape
    
    @property
    def has_faces(self) -> bool:
        """Check if face data is available."""
        return self.faces is not None and len(self.faces) > 0


@dataclass
class ExtractionConfig:
    """
    Configuration for frame extraction.
    
    Attributes:
        num_frames: Target number of frames to extract
        sampling_strategy: Strategy for frame selection
        target_size: Target frame size (height, width)
        face_margin: Margin around detected faces (percentage)
        skip_frames: Number of initial frames to skip
        max_frames: Maximum frames to consider
    """
    
    num_frames: int = AnalysisSettings.DEFAULT_SEQUENCE_LENGTH
    sampling_strategy: str = "uniform"  # uniform, random, keyframe
    target_size: tuple[int, int] = (224, 224)
    face_margin: float = 0.3
    skip_frames: int = 0
    max_frames: int | None = None
    extract_faces: bool = True
    min_face_size: int = 64
    batch_size: int = 32


# =============================================================================
# Video Processor
# =============================================================================

class VideoProcessor:
    """
    High-performance video processing for deepfake detection.
    
    Provides:
        - Efficient frame extraction with multiple strategies
        - Parallel face detection and alignment
        - Memory-optimized batch processing
        - Video metadata extraction
    
    Example:
        >>> processor = VideoProcessor()
        >>> metadata = processor.get_metadata("video.mp4")
        >>> sequence = processor.extract_frames(
        ...     "video.mp4",
        ...     config=ExtractionConfig(num_frames=60),
        ... )
        >>> print(f"Extracted {len(sequence)} frames")
    """
    
    def __init__(
        self,
        face_detector: Any | None = None,
        num_workers: int = 4,
    ):
        """
        Initialize video processor.
        
        Args:
            face_detector: Face detector instance (lazy loaded if None)
            num_workers: Number of parallel workers for processing
        """
        self._face_detector = face_detector
        self._num_workers = num_workers
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    def face_detector(self):
        """Lazy-load face detector."""
        if self._face_detector is None:
            from ml.preprocessing.face_detector import FaceDetector
            self._face_detector = FaceDetector()
        return self._face_detector
    
    # =========================================================================
    # Metadata Extraction
    # =========================================================================
    
    def get_metadata(self, video_path: str | Path) -> VideoMetadata:
        """
        Extract video metadata.
        
        Args:
            video_path: Path to video file
        
        Returns:
            VideoMetadata with video properties
        
        Raises:
            ValidationError: If video cannot be opened
        """
        path = Path(video_path)
        
        if not path.exists():
            raise ValidationError(
                f"Video file not found: {path}",
                details={"path": str(path)},
            )
        
        cap = cv2.VideoCapture(str(path))
        
        if not cap.isOpened():
            raise ValidationError(
                f"Cannot open video file: {path}",
                details={"path": str(path)},
            )
        
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate duration
            duration = frame_count / fps if fps > 0 else 0.0
            
            # Get codec
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            return VideoMetadata(
                path=str(path),
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                duration=duration,
                codec=codec.strip(),
            )
        
        finally:
            cap.release()
    
    def validate_video(self, video_path: str | Path) -> tuple[bool, str]:
        """
        Validate video file meets requirements.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            metadata = self.get_metadata(video_path)
            
            # Check minimum dimensions
            min_dim = min(metadata.width, metadata.height)
            if min_dim < FileConstraints.MIN_VIDEO_DIMENSION:
                return False, (
                    f"Video resolution too low: {metadata.resolution}. "
                    f"Minimum dimension: {FileConstraints.MIN_VIDEO_DIMENSION}px"
                )
            
            # Check duration
            if metadata.duration < 1.0:
                return False, "Video too short: minimum 1 second"
            
            if metadata.duration > FileConstraints.MAX_VIDEO_DURATION_SECONDS:
                return False, (
                    f"Video too long: {metadata.duration:.1f}s. "
                    f"Maximum: {FileConstraints.MAX_VIDEO_DURATION_SECONDS}s"
                )
            
            # Check frame count
            if metadata.frame_count < 10:
                return False, "Video has too few frames (minimum 10)"
            
            return True, ""
        
        except Exception as e:
            return False, str(e)
    
    # =========================================================================
    # Frame Extraction
    # =========================================================================
    
    def extract_frames(
        self,
        video_path: str | Path,
        config: ExtractionConfig | None = None,
        progress_callback: Any | None = None,
    ) -> FrameSequence:
        """
        Extract frames from video.
        
        Args:
            video_path: Path to video file
            config: Extraction configuration
            progress_callback: Optional callback for progress updates
        
        Returns:
            FrameSequence with extracted frames
        
        Raises:
            ProcessingError: If extraction fails
        """
        config = config or ExtractionConfig()
        
        metadata = self.get_metadata(video_path)
        
        self._logger.info(
            f"Extracting frames from video",
            extra={
                "path": str(video_path),
                "resolution": metadata.resolution,
                "fps": metadata.fps,
                "frame_count": metadata.frame_count,
                "target_frames": config.num_frames,
            },
        )
        
        # Calculate frame indices to extract
        indices = self._calculate_frame_indices(metadata, config)
        
        # Extract frames
        frames, timestamps = self._extract_frames_at_indices(
            video_path, indices, progress_callback
        )
        
        if len(frames) == 0:
            raise ProcessingError(
                "No frames could be extracted from video",
                details={"path": str(video_path)},
            )
        
        # Create initial sequence
        sequence = FrameSequence(
            frames=np.array(frames),
            indices=indices[:len(frames)],
            timestamps=timestamps,
        )
        
        # Extract faces if configured
        if config.extract_faces:
            sequence = self._extract_faces_from_sequence(sequence, config)
        
        self._logger.info(
            f"Frame extraction complete",
            extra={
                "extracted": len(sequence),
                "has_faces": sequence.has_faces,
            },
        )
        
        return sequence
    
    def _calculate_frame_indices(
        self,
        metadata: VideoMetadata,
        config: ExtractionConfig,
    ) -> list[int]:
        """Calculate which frame indices to extract."""
        total_frames = metadata.frame_count
        
        # Apply skip and max constraints
        start_frame = config.skip_frames
        end_frame = config.max_frames or total_frames
        end_frame = min(end_frame, total_frames)
        
        available_frames = end_frame - start_frame
        num_to_extract = min(config.num_frames, available_frames)
        
        if config.sampling_strategy == "uniform":
            # Uniformly sample frames
            if num_to_extract >= available_frames:
                indices = list(range(start_frame, end_frame))
            else:
                step = available_frames / num_to_extract
                indices = [int(start_frame + i * step) for i in range(num_to_extract)]
        
        elif config.sampling_strategy == "random":
            # Randomly sample frames
            import random
            all_indices = list(range(start_frame, end_frame))
            indices = sorted(random.sample(all_indices, num_to_extract))
        
        elif config.sampling_strategy == "keyframe":
            # Sample around detected scene changes (simplified)
            # In practice, use actual scene detection
            indices = self._detect_keyframe_indices(
                metadata.path, start_frame, end_frame, num_to_extract
            )
        
        else:
            raise ValueError(f"Unknown sampling strategy: {config.sampling_strategy}")
        
        return indices
    
    def _detect_keyframe_indices(
        self,
        video_path: str,
        start: int,
        end: int,
        num_frames: int,
    ) -> list[int]:
        """Detect keyframes based on scene changes."""
        # Simplified keyframe detection using frame differences
        cap = cv2.VideoCapture(video_path)
        
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            
            prev_frame = None
            differences = []
            
            for i in range(start, min(end, start + 500)):  # Sample first 500 frames
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (64, 64))
                
                if prev_frame is not None:
                    diff = np.mean(np.abs(gray.astype(float) - prev_frame.astype(float)))
                    differences.append((i, diff))
                
                prev_frame = gray
            
            if not differences:
                # Fallback to uniform sampling
                step = (end - start) / num_frames
                return [int(start + i * step) for i in range(num_frames)]
            
            # Sort by difference and take top frames
            differences.sort(key=lambda x: x[1], reverse=True)
            keyframes = sorted([d[0] for d in differences[:num_frames * 2]])
            
            # Select evenly spaced keyframes
            if len(keyframes) >= num_frames:
                step = len(keyframes) / num_frames
                indices = [keyframes[int(i * step)] for i in range(num_frames)]
            else:
                indices = keyframes
            
            return indices
        
        finally:
            cap.release()
    
    def _extract_frames_at_indices(
        self,
        video_path: str | Path,
        indices: list[int],
        progress_callback: Any | None = None,
    ) -> tuple[list[np.ndarray], list[float]]:
        """Extract frames at specified indices."""
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        frames = []
        timestamps = []
        
        try:
            for i, idx in enumerate(indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                    timestamps.append(idx / fps * 1000)  # ms
                
                if progress_callback and i % 10 == 0:
                    progress = (i / len(indices)) * 100
                    progress_callback(progress, f"Extracting frame {i+1}/{len(indices)}")
        
        finally:
            cap.release()
        
        return frames, timestamps
    
    def _extract_faces_from_sequence(
        self,
        sequence: FrameSequence,
        config: ExtractionConfig,
    ) -> FrameSequence:
        """Extract and align faces from frame sequence."""
        faces_per_frame = []
        boxes_per_frame = []
        aligned_faces = []
        
        for frame in sequence.frames:
            # Detect faces in frame
            detections = self.face_detector.detect(frame)
            
            frame_faces = []
            frame_boxes = []
            
            for det in detections:
                # Skip small faces
                if det.width < config.min_face_size or det.height < config.min_face_size:
                    continue
                
                # Extract face with margin
                face = self._extract_face_region(
                    frame, det.bbox, config.face_margin, config.target_size
                )
                
                if face is not None:
                    frame_faces.append(face)
                    frame_boxes.append(det.bbox)
            
            faces_per_frame.append(frame_faces)
            boxes_per_frame.append(frame_boxes)
            
            # Use first face for primary sequence
            if frame_faces:
                aligned_faces.append(frame_faces[0])
        
        # Update sequence with face data
        if aligned_faces:
            sequence.faces = np.array(aligned_faces)
        sequence.face_boxes = boxes_per_frame
        
        return sequence
    
    def _extract_face_region(
        self,
        frame: np.ndarray,
        bbox: dict[str, int],
        margin: float,
        target_size: tuple[int, int],
    ) -> np.ndarray | None:
        """Extract and resize face region with margin."""
        h, w = frame.shape[:2]
        
        x1, y1 = bbox["x"], bbox["y"]
        x2, y2 = x1 + bbox["width"], y1 + bbox["height"]
        
        # Add margin
        margin_w = int(bbox["width"] * margin)
        margin_h = int(bbox["height"] * margin)
        
        x1 = max(0, x1 - margin_w)
        y1 = max(0, y1 - margin_h)
        x2 = min(w, x2 + margin_w)
        y2 = min(h, y2 + margin_h)
        
        # Extract region
        face = frame[y1:y2, x1:x2]
        
        if face.size == 0:
            return None
        
        # Resize to target size
        face = cv2.resize(face, target_size, interpolation=cv2.INTER_AREA)
        
        return face
    
    # =========================================================================
    # Streaming Interface
    # =========================================================================
    
    def stream_frames(
        self,
        video_path: str | Path,
        batch_size: int = 32,
        skip_frames: int = 0,
    ) -> Iterator[tuple[list[np.ndarray], list[int]]]:
        """
        Stream frames from video in batches.
        
        Memory-efficient iterator for processing large videos.
        
        Args:
            video_path: Path to video file
            batch_size: Number of frames per batch
            skip_frames: Frames to skip between extractions
        
        Yields:
            Tuple of (frames, indices) for each batch
        """
        cap = cv2.VideoCapture(str(video_path))
        
        try:
            frame_idx = 0
            batch_frames = []
            batch_indices = []
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                if frame_idx % (skip_frames + 1) == 0:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    batch_frames.append(frame_rgb)
                    batch_indices.append(frame_idx)
                    
                    if len(batch_frames) >= batch_size:
                        yield batch_frames, batch_indices
                        batch_frames = []
                        batch_indices = []
                
                frame_idx += 1
            
            # Yield remaining frames
            if batch_frames:
                yield batch_frames, batch_indices
        
        finally:
            cap.release()
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def extract_thumbnail(
        self,
        video_path: str | Path,
        output_path: str | Path | None = None,
        frame_index: int = 0,
        size: tuple[int, int] = (320, 240),
    ) -> np.ndarray:
        """
        Extract thumbnail from video.
        
        Args:
            video_path: Path to video file
            output_path: Optional path to save thumbnail
            frame_index: Frame to use for thumbnail
            size: Thumbnail dimensions
        
        Returns:
            Thumbnail image as numpy array
        """
        cap = cv2.VideoCapture(str(video_path))
        
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            
            if not ret:
                raise ProcessingError(f"Cannot read frame {frame_index}")
            
            # Resize
            thumbnail = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            
            # Save if path provided
            if output_path:
                cv2.imwrite(str(output_path), thumbnail)
            
            return cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
        
        finally:
            cap.release()
    
    def get_frame_at_time(
        self,
        video_path: str | Path,
        time_ms: float,
    ) -> np.ndarray:
        """
        Get frame at specific timestamp.
        
        Args:
            video_path: Path to video file
            time_ms: Timestamp in milliseconds
        
        Returns:
            Frame as numpy array (RGB)
        """
        cap = cv2.VideoCapture(str(video_path))
        
        try:
            cap.set(cv2.CAP_PROP_POS_MSEC, time_ms)
            ret, frame = cap.read()
            
            if not ret:
                raise ProcessingError(f"Cannot read frame at {time_ms}ms")
            
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        finally:
            cap.release()
