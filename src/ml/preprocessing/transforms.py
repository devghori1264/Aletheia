"""
Image Transforms

Augmentation and normalization pipelines for training and inference.
Uses albumentations for high-performance augmentations.
"""

from __future__ import annotations

from typing import Any, Callable

import cv2
import numpy as np

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False

try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# =============================================================================
# ImageNet Normalization Constants
# =============================================================================

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# FaceForensics++ specific normalization (if different)
FF_MEAN = (0.5, 0.5, 0.5)
FF_STD = (0.5, 0.5, 0.5)


# =============================================================================
# Albumentations Transforms
# =============================================================================

def get_train_transforms(
    image_size: int = 224,
    augmentation_strength: str = "medium",
) -> Any:
    """
    Get training augmentation pipeline.
    
    Args:
        image_size: Target image size
        augmentation_strength: Augmentation intensity (light/medium/heavy)
    
    Returns:
        Albumentations Compose object
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("albumentations required. Install: pip install albumentations")
    
    # Base transforms
    base_transforms = [
        A.Resize(image_size, image_size),
    ]
    
    # Augmentation based on strength
    if augmentation_strength == "light":
        augmentations = [
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(
                brightness_limit=0.1,
                contrast_limit=0.1,
                p=0.3,
            ),
        ]
    
    elif augmentation_strength == "medium":
        augmentations = [
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.15,
                rotate_limit=15,
                border_mode=cv2.BORDER_REFLECT_101,
                p=0.5,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5,
            ),
            A.OneOf([
                A.GaussNoise(var_limit=(10.0, 50.0)),
                A.ISONoise(color_shift=(0.01, 0.05)),
            ], p=0.3),
            A.OneOf([
                A.MotionBlur(blur_limit=5),
                A.GaussianBlur(blur_limit=5),
            ], p=0.2),
            A.HueSaturationValue(
                hue_shift_limit=10,
                sat_shift_limit=20,
                val_shift_limit=10,
                p=0.3,
            ),
        ]
    
    elif augmentation_strength == "heavy":
        augmentations = [
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.15,
                scale_limit=0.2,
                rotate_limit=20,
                border_mode=cv2.BORDER_REFLECT_101,
                p=0.7,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=0.3,
                contrast_limit=0.3,
                p=0.7,
            ),
            A.OneOf([
                A.GaussNoise(var_limit=(10.0, 100.0)),
                A.ISONoise(color_shift=(0.01, 0.1)),
                A.MultiplicativeNoise(multiplier=(0.9, 1.1)),
            ], p=0.5),
            A.OneOf([
                A.MotionBlur(blur_limit=7),
                A.GaussianBlur(blur_limit=7),
                A.MedianBlur(blur_limit=5),
            ], p=0.4),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=0.5,
            ),
            A.CoarseDropout(
                max_holes=4,
                max_height=int(image_size * 0.1),
                max_width=int(image_size * 0.1),
                min_holes=1,
                fill_value=0,
                p=0.3,
            ),
            A.OneOf([
                A.ImageCompression(quality_lower=60, quality_upper=90),
                A.Downscale(scale_min=0.5, scale_max=0.9),
            ], p=0.3),
        ]
    
    else:
        raise ValueError(f"Unknown augmentation strength: {augmentation_strength}")
    
    # Normalization
    normalize = [
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ]
    
    return A.Compose(base_transforms + augmentations + normalize)


def get_inference_transforms(
    image_size: int = 224,
    normalize: bool = True,
) -> Any:
    """
    Get inference/validation transforms.
    
    Args:
        image_size: Target image size
        normalize: Whether to apply normalization
    
    Returns:
        Albumentations Compose object
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("albumentations required")
    
    transforms = [
        A.Resize(image_size, image_size),
    ]
    
    if normalize:
        transforms.extend([
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ])
    
    return A.Compose(transforms)


def get_augmentation_pipeline(
    config: dict[str, Any],
) -> Any:
    """
    Create augmentation pipeline from configuration.
    
    Args:
        config: Dictionary with augmentation settings
    
    Returns:
        Albumentations Compose object
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("albumentations required")
    
    transforms = []
    
    # Resize
    if "resize" in config:
        transforms.append(A.Resize(**config["resize"]))
    
    # Spatial transforms
    if config.get("horizontal_flip", False):
        transforms.append(A.HorizontalFlip(p=config.get("flip_p", 0.5)))
    
    if "rotation" in config:
        transforms.append(A.Rotate(limit=config["rotation"], p=0.5))
    
    if "shift_scale_rotate" in config:
        transforms.append(A.ShiftScaleRotate(**config["shift_scale_rotate"]))
    
    # Color transforms
    if "brightness_contrast" in config:
        transforms.append(A.RandomBrightnessContrast(**config["brightness_contrast"]))
    
    if "hsv" in config:
        transforms.append(A.HueSaturationValue(**config["hsv"]))
    
    # Noise and blur
    if config.get("gaussian_noise", False):
        transforms.append(A.GaussNoise(var_limit=(10.0, 50.0), p=0.3))
    
    if config.get("motion_blur", False):
        transforms.append(A.MotionBlur(blur_limit=5, p=0.2))
    
    # Compression artifacts
    if config.get("compression", False):
        transforms.append(A.ImageCompression(quality_lower=50, quality_upper=95, p=0.3))
    
    # Cutout/Dropout
    if "cutout" in config:
        transforms.append(A.CoarseDropout(**config["cutout"]))
    
    # Normalize
    if config.get("normalize", True):
        transforms.append(A.Normalize(
            mean=config.get("mean", IMAGENET_MEAN),
            std=config.get("std", IMAGENET_STD),
        ))
    
    if config.get("to_tensor", True):
        transforms.append(ToTensorV2())
    
    return A.Compose(transforms)


# =============================================================================
# Deepfake-Specific Augmentations
# =============================================================================

def get_deepfake_augmentations(
    image_size: int = 224,
    p: float = 0.5,
) -> Any:
    """
    Get augmentations designed for deepfake detection robustness.
    
    Includes augmentations that simulate common deepfake artifacts
    and social media compression.
    """
    if not ALBUMENTATIONS_AVAILABLE:
        raise ImportError("albumentations required")
    
    return A.Compose([
        A.Resize(image_size, image_size),
        
        # Simulate face blending artifacts
        A.OneOf([
            A.GaussianBlur(blur_limit=(1, 3)),
            A.MotionBlur(blur_limit=3),
        ], p=0.2),
        
        # Simulate color mismatches from face swaps
        A.OneOf([
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10),
            A.RGBShift(r_shift_limit=10, g_shift_limit=10, b_shift_limit=10),
            A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05),
        ], p=0.3),
        
        # Simulate compression (common in social media)
        A.OneOf([
            A.ImageCompression(quality_lower=30, quality_upper=70),
            A.ImageCompression(quality_lower=50, quality_upper=90),
        ], p=0.4),
        
        # Simulate resolution changes
        A.OneOf([
            A.Downscale(scale_min=0.5, scale_max=0.9, interpolation=cv2.INTER_AREA),
            A.Downscale(scale_min=0.7, scale_max=0.95, interpolation=cv2.INTER_LINEAR),
        ], p=0.3),
        
        # Noise (camera/sensor noise)
        A.OneOf([
            A.GaussNoise(var_limit=(5.0, 30.0)),
            A.ISONoise(color_shift=(0.01, 0.03), intensity=(0.1, 0.3)),
        ], p=0.2),
        
        # Basic augmentations
        A.HorizontalFlip(p=0.5),
        A.ShiftScaleRotate(
            shift_limit=0.05,
            scale_limit=0.1,
            rotate_limit=10,
            border_mode=cv2.BORDER_REFLECT_101,
            p=p,
        ),
        
        # Normalize
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])


# =============================================================================
# Face Normalization
# =============================================================================

def normalize_face(
    face: np.ndarray,
    target_size: tuple[int, int] = (224, 224),
    mean: tuple[float, ...] = IMAGENET_MEAN,
    std: tuple[float, ...] = IMAGENET_STD,
) -> np.ndarray:
    """
    Normalize face image for model input.
    
    Args:
        face: Face image (RGB, HWC format, uint8)
        target_size: Target size (H, W)
        mean: Normalization mean
        std: Normalization std
    
    Returns:
        Normalized face (float32, CHW format)
    """
    # Resize
    if face.shape[:2] != target_size:
        face = cv2.resize(face, target_size, interpolation=cv2.INTER_AREA)
    
    # Convert to float and normalize to [0, 1]
    face = face.astype(np.float32) / 255.0
    
    # Apply normalization
    mean = np.array(mean, dtype=np.float32).reshape(1, 1, 3)
    std = np.array(std, dtype=np.float32).reshape(1, 1, 3)
    face = (face - mean) / std
    
    # Convert HWC to CHW
    face = np.transpose(face, (2, 0, 1))
    
    return face


def denormalize_image(
    image: np.ndarray,
    mean: tuple[float, ...] = IMAGENET_MEAN,
    std: tuple[float, ...] = IMAGENET_STD,
) -> np.ndarray:
    """
    Denormalize image for visualization.
    
    Args:
        image: Normalized image (CHW format)
        mean: Normalization mean
        std: Normalization std
    
    Returns:
        Denormalized image (HWC format, uint8)
    """
    # Handle tensor
    if TORCH_AVAILABLE and isinstance(image, torch.Tensor):
        image = image.cpu().numpy()
    
    # Convert CHW to HWC if needed
    if image.shape[0] in [1, 3]:
        image = np.transpose(image, (1, 2, 0))
    
    # Denormalize
    mean = np.array(mean, dtype=np.float32)
    std = np.array(std, dtype=np.float32)
    image = image * std + mean
    
    # Clip and convert to uint8
    image = np.clip(image * 255, 0, 255).astype(np.uint8)
    
    return image


# =============================================================================
# Batch Processing
# =============================================================================

def prepare_batch(
    images: list[np.ndarray],
    transform: Callable | None = None,
    target_size: tuple[int, int] = (224, 224),
) -> np.ndarray:
    """
    Prepare batch of images for model input.
    
    Args:
        images: List of images (RGB, HWC)
        transform: Optional transform to apply
        target_size: Target size for images
    
    Returns:
        Batch array (N, C, H, W)
    """
    batch = []
    
    for img in images:
        if transform is not None:
            # Albumentations format
            result = transform(image=img)
            img = result["image"]
        else:
            img = normalize_face(img, target_size)
        
        batch.append(img)
    
    # Stack into batch
    if TORCH_AVAILABLE and isinstance(batch[0], torch.Tensor):
        return torch.stack(batch)
    else:
        return np.stack(batch)


def prepare_sequence(
    frames: np.ndarray,
    transform: Callable | None = None,
    target_size: tuple[int, int] = (224, 224),
) -> np.ndarray:
    """
    Prepare frame sequence for model input.
    
    Args:
        frames: Frame sequence (T, H, W, C)
        transform: Optional transform to apply
        target_size: Target size for frames
    
    Returns:
        Processed sequence (T, C, H, W)
    """
    processed = []
    
    for frame in frames:
        if transform is not None:
            result = transform(image=frame)
            frame = result["image"]
        else:
            frame = normalize_face(frame, target_size)
        
        processed.append(frame)
    
    if TORCH_AVAILABLE and isinstance(processed[0], torch.Tensor):
        return torch.stack(processed)
    else:
        return np.stack(processed)


# =============================================================================
# TorchVision Fallback
# =============================================================================

def get_torchvision_transforms(
    image_size: int = 224,
    training: bool = False,
) -> Any:
    """
    Get transforms using torchvision (fallback if albumentations unavailable).
    
    Args:
        image_size: Target image size
        training: Whether to include training augmentations
    
    Returns:
        torchvision Compose object
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch required for torchvision transforms")
    
    if training:
        return T.Compose([
            T.ToPILImage(),
            T.Resize((image_size, image_size)),
            T.RandomHorizontalFlip(p=0.5),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            T.RandomRotation(degrees=10),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    else:
        return T.Compose([
            T.ToPILImage(),
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
