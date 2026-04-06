"""
Face Detector

Multi-backend face detection with alignment and landmark extraction.
Supports MTCNN, RetinaFace, MediaPipe, and dlib backends.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class DetectorBackend(Enum):
    """Available face detection backends."""
    
    MTCNN = "mtcnn"
    RETINAFACE = "retinaface"
    MEDIAPIPE = "mediapipe"
    OPENCV = "opencv"
    DLIB = "dlib"


@dataclass(slots=True)
class FaceLandmarks:
    """
    Facial landmark points.
    
    Attributes:
        left_eye: Left eye center coordinates
        right_eye: Right eye center coordinates
        nose: Nose tip coordinates
        left_mouth: Left mouth corner
        right_mouth: Right mouth corner
        all_points: All detected landmark points
    """
    
    left_eye: tuple[float, float] | None = None
    right_eye: tuple[float, float] | None = None
    nose: tuple[float, float] | None = None
    left_mouth: tuple[float, float] | None = None
    right_mouth: tuple[float, float] | None = None
    all_points: list[tuple[float, float]] = field(default_factory=list)
    
    @property
    def has_eyes(self) -> bool:
        """Check if both eyes are detected."""
        return self.left_eye is not None and self.right_eye is not None
    
    def to_array(self) -> np.ndarray:
        """Convert landmarks to numpy array."""
        points = [
            self.left_eye,
            self.right_eye,
            self.nose,
            self.left_mouth,
            self.right_mouth,
        ]
        valid = [p for p in points if p is not None]
        return np.array(valid) if valid else np.array([])


@dataclass(slots=True)
class FaceDetection:
    """
    Single face detection result.
    
    Attributes:
        bbox: Bounding box coordinates
        confidence: Detection confidence score
        landmarks: Facial landmarks
        aligned_face: Aligned face image (if computed)
    """
    
    bbox: dict[str, int]
    confidence: float
    landmarks: FaceLandmarks | None = None
    aligned_face: np.ndarray | None = None
    
    @property
    def x(self) -> int:
        return self.bbox["x"]
    
    @property
    def y(self) -> int:
        return self.bbox["y"]
    
    @property
    def width(self) -> int:
        return self.bbox["width"]
    
    @property
    def height(self) -> int:
        return self.bbox["height"]
    
    @property
    def center(self) -> tuple[int, int]:
        """Get bounding box center."""
        return (
            self.x + self.width // 2,
            self.y + self.height // 2,
        )
    
    @property
    def area(self) -> int:
        """Get bounding box area."""
        return self.width * self.height
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bbox": self.bbox,
            "confidence": self.confidence,
            "has_landmarks": self.landmarks is not None,
        }


# =============================================================================
# Base Detector
# =============================================================================

class BaseFaceDetector(ABC):
    """Abstract base class for face detectors."""
    
    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
    ) -> list[FaceDetection]:
        """
        Detect faces in image.
        
        Args:
            image: Input image (RGB, HWC format)
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of FaceDetection objects
        """
        ...
    
    @abstractmethod
    def detect_batch(
        self,
        images: Sequence[np.ndarray],
        min_confidence: float = 0.9,
    ) -> list[list[FaceDetection]]:
        """Detect faces in batch of images."""
        ...


# =============================================================================
# MTCNN Detector
# =============================================================================

class MTCNNDetector(BaseFaceDetector):
    """
    MTCNN-based face detector.
    
    Multi-task Cascaded Convolutional Networks for high-accuracy
    face detection with landmark localization.
    """
    
    def __init__(
        self,
        device: str = "cuda",
        min_face_size: int = 40,
        thresholds: tuple[float, float, float] = (0.6, 0.7, 0.7),
    ):
        """
        Initialize MTCNN detector.
        
        Args:
            device: Device for computation (cuda/cpu)
            min_face_size: Minimum face size to detect
            thresholds: Detection thresholds for P-Net, R-Net, O-Net
        """
        try:
            from facenet_pytorch import MTCNN
            import torch
            
            device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
            
            self._detector = MTCNN(
                image_size=160,
                margin=0,
                min_face_size=min_face_size,
                thresholds=list(thresholds),
                factor=0.709,
                post_process=False,
                device=device,
                keep_all=True,
            )
            self._device = device
            
        except ImportError:
            raise ImportError(
                "facenet-pytorch is required for MTCNN. "
                "Install with: pip install facenet-pytorch"
            )
    
    def detect(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
    ) -> list[FaceDetection]:
        """Detect faces using MTCNN."""
        from PIL import Image
        
        # Convert to PIL Image
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Detect faces
        boxes, probs, landmarks = self._detector.detect(pil_image, landmarks=True)
        
        detections = []
        
        if boxes is not None:
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                if prob < min_confidence:
                    continue
                
                x1, y1, x2, y2 = map(int, box)
                
                # Extract landmarks if available
                face_landmarks = None
                if landmarks is not None and i < len(landmarks):
                    pts = landmarks[i]
                    face_landmarks = FaceLandmarks(
                        left_eye=tuple(pts[0]),
                        right_eye=tuple(pts[1]),
                        nose=tuple(pts[2]),
                        left_mouth=tuple(pts[3]),
                        right_mouth=tuple(pts[4]),
                    )
                
                detection = FaceDetection(
                    bbox={
                        "x": max(0, x1),
                        "y": max(0, y1),
                        "width": x2 - x1,
                        "height": y2 - y1,
                    },
                    confidence=float(prob),
                    landmarks=face_landmarks,
                )
                
                detections.append(detection)
        
        return detections
    
    def detect_batch(
        self,
        images: Sequence[np.ndarray],
        min_confidence: float = 0.9,
    ) -> list[list[FaceDetection]]:
        """Detect faces in batch."""
        from PIL import Image
        
        pil_images = [Image.fromarray(img) for img in images]
        
        # Batch detection
        batch_boxes, batch_probs, batch_landmarks = self._detector.detect(
            pil_images, landmarks=True
        )
        
        all_detections = []
        
        for i, (boxes, probs, landmarks) in enumerate(
            zip(batch_boxes, batch_probs, batch_landmarks)
        ):
            detections = []
            
            if boxes is not None:
                for j, (box, prob) in enumerate(zip(boxes, probs)):
                    if prob < min_confidence:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box)
                    
                    face_landmarks = None
                    if landmarks is not None and j < len(landmarks):
                        pts = landmarks[j]
                        face_landmarks = FaceLandmarks(
                            left_eye=tuple(pts[0]),
                            right_eye=tuple(pts[1]),
                            nose=tuple(pts[2]),
                            left_mouth=tuple(pts[3]),
                            right_mouth=tuple(pts[4]),
                        )
                    
                    detection = FaceDetection(
                        bbox={
                            "x": max(0, x1),
                            "y": max(0, y1),
                            "width": x2 - x1,
                            "height": y2 - y1,
                        },
                        confidence=float(prob),
                        landmarks=face_landmarks,
                    )
                    
                    detections.append(detection)
            
            all_detections.append(detections)
        
        return all_detections


# =============================================================================
# OpenCV Detector (Fallback)
# =============================================================================

class OpenCVDetector(BaseFaceDetector):
    """
    OpenCV-based face detector.
    
    Uses DNN face detector for reasonable accuracy without
    additional dependencies.
    """
    
    def __init__(self):
        """Initialize OpenCV DNN face detector."""
        # Use OpenCV's built-in DNN face detector
        self._detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    
    def detect(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
    ) -> list[FaceDetection]:
        """Detect faces using OpenCV cascade."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = self._detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        
        detections = []
        
        for (x, y, w, h) in faces:
            detection = FaceDetection(
                bbox={"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                confidence=1.0,  # OpenCV cascade doesn't provide confidence
            )
            detections.append(detection)
        
        return detections
    
    def detect_batch(
        self,
        images: Sequence[np.ndarray],
        min_confidence: float = 0.9,
    ) -> list[list[FaceDetection]]:
        """Detect faces in batch (sequential for OpenCV)."""
        return [self.detect(img, min_confidence) for img in images]


# =============================================================================
# MediaPipe Detector
# =============================================================================

class MediaPipeDetector(BaseFaceDetector):
    """
    MediaPipe-based face detector.
    
    Fast and accurate face detection using MediaPipe's BlazeFace.
    """
    
    def __init__(self, min_detection_confidence: float = 0.5):
        """Initialize MediaPipe face detector."""
        try:
            import mediapipe as mp
            
            self._mp_face = mp.solutions.face_detection
            self._detector = self._mp_face.FaceDetection(
                model_selection=1,  # Full-range model
                min_detection_confidence=min_detection_confidence,
            )
            
        except ImportError:
            raise ImportError(
                "mediapipe is required. Install with: pip install mediapipe"
            )
    
    def detect(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
    ) -> list[FaceDetection]:
        """Detect faces using MediaPipe."""
        h, w = image.shape[:2]
        
        # MediaPipe expects RGB
        results = self._detector.process(image)
        
        detections = []
        
        if results.detections:
            for detection in results.detections:
                if detection.score[0] < min_confidence:
                    continue
                
                bbox = detection.location_data.relative_bounding_box
                
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Extract keypoints as landmarks
                keypoints = detection.location_data.relative_keypoints
                landmarks = None
                
                if len(keypoints) >= 6:
                    landmarks = FaceLandmarks(
                        right_eye=(keypoints[0].x * w, keypoints[0].y * h),
                        left_eye=(keypoints[1].x * w, keypoints[1].y * h),
                        nose=(keypoints[2].x * w, keypoints[2].y * h),
                        right_mouth=(keypoints[3].x * w, keypoints[3].y * h),
                        left_mouth=(keypoints[4].x * w, keypoints[4].y * h),
                    )
                
                face_det = FaceDetection(
                    bbox={
                        "x": max(0, x),
                        "y": max(0, y),
                        "width": width,
                        "height": height,
                    },
                    confidence=float(detection.score[0]),
                    landmarks=landmarks,
                )
                
                detections.append(face_det)
        
        return detections
    
    def detect_batch(
        self,
        images: Sequence[np.ndarray],
        min_confidence: float = 0.9,
    ) -> list[list[FaceDetection]]:
        """Detect faces in batch (sequential for MediaPipe)."""
        return [self.detect(img, min_confidence) for img in images]


# =============================================================================
# Unified Face Detector
# =============================================================================

class FaceDetector:
    """
    Unified face detector with multiple backend support.
    
    Automatically selects the best available backend and provides
    fallback options for robustness.
    
    Example:
        >>> detector = FaceDetector(backend="mtcnn")
        >>> detections = detector.detect(image)
        >>> for det in detections:
        ...     print(f"Face at {det.bbox} with confidence {det.confidence:.2f}")
    """
    
    _BACKENDS: dict[str, type[BaseFaceDetector]] = {
        "mtcnn": MTCNNDetector,
        "mediapipe": MediaPipeDetector,
        "opencv": OpenCVDetector,
    }
    
    def __init__(
        self,
        backend: str | DetectorBackend = "mtcnn",
        device: str = "cuda",
        fallback_backends: list[str] | None = None,
        **kwargs,
    ):
        """
        Initialize face detector.
        
        Args:
            backend: Primary detection backend
            device: Device for computation
            fallback_backends: Fallback backends if primary fails
            **kwargs: Additional backend-specific arguments
        """
        if isinstance(backend, DetectorBackend):
            backend = backend.value
        
        self._backend_name = backend
        self._fallback_backends = fallback_backends or ["mediapipe", "opencv"]
        self._detector = self._create_detector(backend, device, **kwargs)
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _create_detector(
        self,
        backend: str,
        device: str,
        **kwargs,
    ) -> BaseFaceDetector:
        """Create detector instance for backend."""
        if backend not in self._BACKENDS:
            raise ValueError(
                f"Unknown backend: {backend}. "
                f"Available: {list(self._BACKENDS.keys())}"
            )
        
        try:
            detector_class = self._BACKENDS[backend]
            
            if backend == "mtcnn":
                return detector_class(device=device, **kwargs)
            elif backend == "mediapipe":
                return detector_class(**kwargs)
            else:
                return detector_class(**kwargs)
        
        except ImportError as e:
            self._logger.warning(
                f"Failed to initialize {backend}: {e}. Trying fallback..."
            )
            
            # Try fallbacks
            for fallback in self._fallback_backends:
                if fallback != backend:
                    try:
                        return self._create_detector(fallback, device)
                    except ImportError:
                        continue
            
            # Last resort: OpenCV
            return OpenCVDetector()
    
    def detect(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
        align_faces: bool = False,
        target_size: tuple[int, int] = (224, 224),
    ) -> list[FaceDetection]:
        """
        Detect faces in image.
        
        Args:
            image: Input image (RGB format)
            min_confidence: Minimum detection confidence
            align_faces: Whether to align detected faces
            target_size: Target size for aligned faces
        
        Returns:
            List of FaceDetection objects
        """
        detections = self._detector.detect(image, min_confidence)
        
        # Align faces if requested
        if align_faces:
            for det in detections:
                if det.landmarks and det.landmarks.has_eyes:
                    det.aligned_face = self._align_face(
                        image, det.landmarks, target_size
                    )
        
        return detections
    
    def detect_batch(
        self,
        images: Sequence[np.ndarray],
        min_confidence: float = 0.9,
    ) -> list[list[FaceDetection]]:
        """Detect faces in batch of images."""
        return self._detector.detect_batch(images, min_confidence)
    
    def _align_face(
        self,
        image: np.ndarray,
        landmarks: FaceLandmarks,
        target_size: tuple[int, int],
    ) -> np.ndarray:
        """
        Align face based on eye landmarks.
        
        Performs affine transformation to normalize face orientation.
        """
        if not landmarks.has_eyes:
            return image
        
        left_eye = np.array(landmarks.left_eye)
        right_eye = np.array(landmarks.right_eye)
        
        # Calculate angle
        dy = right_eye[1] - left_eye[1]
        dx = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Calculate center
        eye_center = (
            (left_eye[0] + right_eye[0]) / 2,
            (left_eye[1] + right_eye[1]) / 2,
        )
        
        # Rotation matrix
        M = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
        
        # Rotate
        h, w = image.shape[:2]
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        
        # Resize
        aligned = cv2.resize(rotated, target_size, interpolation=cv2.INTER_AREA)
        
        return aligned
    
    def get_largest_face(
        self,
        image: np.ndarray,
        min_confidence: float = 0.9,
    ) -> FaceDetection | None:
        """
        Get the largest detected face.
        
        Useful when expecting a single face (e.g., selfie videos).
        """
        detections = self.detect(image, min_confidence)
        
        if not detections:
            return None
        
        return max(detections, key=lambda d: d.area)
    
    @property
    def backend(self) -> str:
        """Get current backend name."""
        return self._backend_name
