"""
Explainability Module

GradCAM++ and attention visualization for deepfake detection.
Provides interpretable explanations of model predictions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ExplainabilityResult:
    """
    Result of explainability analysis.
    
    Attributes:
        heatmap: Attention/activation heatmap (H, W)
        overlay: Heatmap overlaid on original image (H, W, 3)
        target_class: Class for which explanation was generated
        confidence: Confidence for target class
        method: Explainability method used
    """
    
    heatmap: np.ndarray
    overlay: np.ndarray
    target_class: str
    confidence: float
    method: str = "gradcam++"
    layer_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (without arrays)."""
        return {
            "target_class": self.target_class,
            "confidence": self.confidence,
            "method": self.method,
            "layer_name": self.layer_name,
            "heatmap_shape": self.heatmap.shape,
            "overlay_shape": self.overlay.shape,
            "metadata": self.metadata,
        }


# =============================================================================
# GradCAM++
# =============================================================================

class GradCAMPlusPlus:
    """
    GradCAM++ implementation for visual explanations.
    
    Computes class activation maps using gradients and activations
    from a target convolutional layer.
    
    Reference:
        "Grad-CAM++: Improved Visual Explanations for Deep Network Predictions"
        Chattopadhyay et al., 2018
    
    Example:
        >>> gradcam = GradCAMPlusPlus(model, target_layer="backbone.layer4")
        >>> result = gradcam.explain(image, target_class=1)
        >>> cv2.imwrite("heatmap.jpg", result.overlay)
    """
    
    def __init__(
        self,
        model: nn.Module,
        target_layer: str | nn.Module,
        use_cuda: bool = True,
    ):
        """
        Initialize GradCAM++.
        
        Args:
            model: PyTorch model
            target_layer: Target layer name or module
            use_cuda: Use CUDA if available
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for GradCAM++")
        
        self._model = model
        self._model.eval()
        
        # Get target layer
        if isinstance(target_layer, str):
            self._target_layer = self._get_layer_by_name(target_layer)
            self._layer_name = target_layer
        else:
            self._target_layer = target_layer
            self._layer_name = target_layer.__class__.__name__
        
        # Device setup
        self._device = torch.device(
            "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        )
        self._model = self._model.to(self._device)
        
        # Storage for activations and gradients
        self._activations: torch.Tensor | None = None
        self._gradients: torch.Tensor | None = None
        
        # Register hooks
        self._forward_hook = self._target_layer.register_forward_hook(
            self._activation_hook
        )
        self._backward_hook = self._target_layer.register_full_backward_hook(
            self._gradient_hook
        )
        
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _get_layer_by_name(self, layer_name: str) -> nn.Module:
        """Get layer by dot-separated name."""
        module = self._model
        
        for part in layer_name.split("."):
            if part.isdigit():
                module = module[int(part)]
            else:
                module = getattr(module, part)
        
        return module
    
    def _activation_hook(
        self,
        module: nn.Module,
        input: tuple[torch.Tensor, ...],
        output: torch.Tensor,
    ) -> None:
        """Hook to capture activations."""
        self._activations = output.detach()
    
    def _gradient_hook(
        self,
        module: nn.Module,
        grad_input: tuple[torch.Tensor, ...],
        grad_output: tuple[torch.Tensor, ...],
    ) -> None:
        """Hook to capture gradients."""
        self._gradients = grad_output[0].detach()
    
    def explain(
        self,
        image: np.ndarray | torch.Tensor,
        target_class: int | None = None,
    ) -> ExplainabilityResult:
        """
        Generate GradCAM++ explanation.
        
        Args:
            image: Input image (RGB, HWC or CHW)
            target_class: Class to explain (None = predicted class)
        
        Returns:
            ExplainabilityResult with heatmap and overlay
        """
        # Prepare input
        if isinstance(image, np.ndarray):
            original_image = image.copy()
            
            # Normalize and convert to tensor
            if image.ndim == 3 and image.shape[2] == 3:
                # HWC to CHW
                tensor = torch.from_numpy(image.transpose(2, 0, 1)).float()
            else:
                tensor = torch.from_numpy(image).float()
            
            # Normalize to [0, 1]
            if tensor.max() > 1.0:
                tensor = tensor / 255.0
            
            # ImageNet normalization
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            tensor = (tensor - mean) / std
            
            tensor = tensor.unsqueeze(0)  # Add batch dim
        else:
            tensor = image
            if tensor.dim() == 3:
                tensor = tensor.unsqueeze(0)
            
            # Denormalize for overlay
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            denorm = tensor[0] * std + mean
            original_image = (denorm.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        
        tensor = tensor.to(self._device)
        tensor.requires_grad_(True)
        
        # Forward pass
        output = self._model(tensor)
        
        if hasattr(output, "logits"):
            output = output.logits
        
        # Get predicted class if not specified
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Get class score
        class_score = output[0, target_class]
        confidence = F.softmax(output, dim=1)[0, target_class].item()
        
        # Backward pass
        self._model.zero_grad()
        class_score.backward(retain_graph=True)
        
        # Compute GradCAM++
        heatmap = self._compute_gradcam_pp()
        
        # Resize to input size
        heatmap = cv2.resize(
            heatmap,
            (original_image.shape[1], original_image.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )
        
        # Create overlay
        overlay = self._create_overlay(original_image, heatmap)
        
        class_name = "fake" if target_class == 1 else "real"
        
        return ExplainabilityResult(
            heatmap=heatmap,
            overlay=overlay,
            target_class=class_name,
            confidence=confidence,
            method="gradcam++",
            layer_name=self._layer_name,
        )
    
    def _compute_gradcam_pp(self) -> np.ndarray:
        """Compute GradCAM++ heatmap."""
        if self._activations is None or self._gradients is None:
            raise RuntimeError("No activations/gradients captured")
        
        activations = self._activations[0]  # Remove batch dim
        gradients = self._gradients[0]
        
        # GradCAM++ weights
        # alpha = grad^2 / (2 * grad^2 + sum(A * grad^3))
        
        grad_2 = gradients ** 2
        grad_3 = gradients ** 3
        
        # Sum over spatial dimensions
        spatial_sum = activations * grad_3
        spatial_sum = spatial_sum.sum(dim=(1, 2), keepdim=True)
        
        alpha = grad_2 / (2 * grad_2 + spatial_sum + 1e-8)
        
        # Zero out alpha where gradient is negative
        alpha = alpha * torch.relu(gradients)
        
        # Weights for each channel
        weights = alpha.sum(dim=(1, 2))
        
        # Weighted combination of activations
        heatmap = torch.zeros(activations.shape[1:], device=self._device)
        
        for i, w in enumerate(weights):
            heatmap += w * activations[i]
        
        # ReLU and normalize
        heatmap = torch.relu(heatmap)
        heatmap = heatmap - heatmap.min()
        heatmap = heatmap / (heatmap.max() + 1e-8)
        
        return heatmap.cpu().numpy()
    
    def _create_overlay(
        self,
        image: np.ndarray,
        heatmap: np.ndarray,
        colormap: int = cv2.COLORMAP_JET,
        alpha: float = 0.5,
    ) -> np.ndarray:
        """Create heatmap overlay on image."""
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV is required for overlay")
        
        # Convert heatmap to colormap
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
        
        # Convert from BGR to RGB
        colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)
        
        # Blend with original image
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        overlay = cv2.addWeighted(image, 1 - alpha, colored_heatmap, alpha, 0)
        
        return overlay
    
    def explain_sequence(
        self,
        frames: np.ndarray,
        target_class: int | None = None,
    ) -> list[ExplainabilityResult]:
        """
        Generate explanations for frame sequence.
        
        Args:
            frames: Frame sequence (T, H, W, C)
            target_class: Class to explain
        
        Returns:
            List of ExplainabilityResult
        """
        results = []
        
        for i, frame in enumerate(frames):
            try:
                result = self.explain(frame, target_class)
                result.metadata["frame_index"] = i
                results.append(result)
            except Exception as e:
                self._logger.warning(f"Failed to explain frame {i}: {e}")
        
        return results
    
    def __del__(self):
        """Clean up hooks."""
        if hasattr(self, "_forward_hook"):
            self._forward_hook.remove()
        if hasattr(self, "_backward_hook"):
            self._backward_hook.remove()


# =============================================================================
# Attention Visualization
# =============================================================================

def visualize_attention(
    image: np.ndarray,
    attention_weights: np.ndarray,
    colormap: int = cv2.COLORMAP_JET,
    alpha: float = 0.5,
) -> np.ndarray:
    """
    Visualize attention weights on image.
    
    Args:
        image: Input image (RGB, HWC)
        attention_weights: Attention weights (H, W) or (N, H, W)
        colormap: OpenCV colormap
        alpha: Blend alpha
    
    Returns:
        Image with attention overlay
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV is required for attention visualization")
    
    # Average attention if multiple heads
    if attention_weights.ndim == 3:
        attention_weights = attention_weights.mean(axis=0)
    
    # Normalize
    attention = attention_weights.astype(np.float32)
    attention = (attention - attention.min()) / (attention.max() - attention.min() + 1e-8)
    
    # Resize to image size
    attention = cv2.resize(
        attention,
        (image.shape[1], image.shape[0]),
        interpolation=cv2.INTER_LINEAR,
    )
    
    # Apply colormap
    attention_uint8 = (attention * 255).astype(np.uint8)
    colored_attention = cv2.applyColorMap(attention_uint8, colormap)
    colored_attention = cv2.cvtColor(colored_attention, cv2.COLOR_BGR2RGB)
    
    # Blend
    if image.max() <= 1.0:
        image = (image * 255).astype(np.uint8)
    
    overlay = cv2.addWeighted(image, 1 - alpha, colored_attention, alpha, 0)
    
    return overlay


# =============================================================================
# LayerCAM (Simpler Alternative)
# =============================================================================

class LayerCAM:
    """
    LayerCAM implementation.
    
    Simpler than GradCAM++ but still produces good visualizations.
    Uses positive gradients and activations directly.
    
    Reference:
        "LayerCAM: Exploring Hierarchical Class Activation Maps"
        Jiang et al., 2021
    """
    
    def __init__(
        self,
        model: nn.Module,
        target_layer: str | nn.Module,
        use_cuda: bool = True,
    ):
        """Initialize LayerCAM."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for LayerCAM")
        
        self._model = model
        self._model.eval()
        
        if isinstance(target_layer, str):
            self._target_layer = self._get_layer_by_name(target_layer)
            self._layer_name = target_layer
        else:
            self._target_layer = target_layer
            self._layer_name = target_layer.__class__.__name__
        
        self._device = torch.device(
            "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        )
        self._model = self._model.to(self._device)
        
        self._activations: torch.Tensor | None = None
        self._gradients: torch.Tensor | None = None
        
        self._forward_hook = self._target_layer.register_forward_hook(
            self._activation_hook
        )
        self._backward_hook = self._target_layer.register_full_backward_hook(
            self._gradient_hook
        )
    
    def _get_layer_by_name(self, layer_name: str) -> nn.Module:
        """Get layer by dot-separated name."""
        module = self._model
        for part in layer_name.split("."):
            if part.isdigit():
                module = module[int(part)]
            else:
                module = getattr(module, part)
        return module
    
    def _activation_hook(self, module, input, output):
        self._activations = output.detach()
    
    def _gradient_hook(self, module, grad_input, grad_output):
        self._gradients = grad_output[0].detach()
    
    def explain(
        self,
        image: np.ndarray | torch.Tensor,
        target_class: int | None = None,
    ) -> np.ndarray:
        """Generate LayerCAM heatmap."""
        # Prepare input
        if isinstance(image, np.ndarray):
            if image.ndim == 3 and image.shape[2] == 3:
                tensor = torch.from_numpy(image.transpose(2, 0, 1)).float()
            else:
                tensor = torch.from_numpy(image).float()
            
            if tensor.max() > 1.0:
                tensor = tensor / 255.0
            
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            tensor = (tensor - mean) / std
            tensor = tensor.unsqueeze(0)
        else:
            tensor = image
            if tensor.dim() == 3:
                tensor = tensor.unsqueeze(0)
        
        tensor = tensor.to(self._device)
        tensor.requires_grad_(True)
        
        # Forward pass
        output = self._model(tensor)
        
        if hasattr(output, "logits"):
            output = output.logits
        
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Backward pass
        self._model.zero_grad()
        output[0, target_class].backward(retain_graph=True)
        
        # LayerCAM: element-wise product of ReLU(activations) and ReLU(gradients)
        activations = self._activations[0]
        gradients = self._gradients[0]
        
        # Element-wise multiplication
        cam = torch.relu(activations) * torch.relu(gradients)
        
        # Sum over channels
        cam = cam.sum(dim=0)
        
        # Normalize
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        
        return cam.cpu().numpy()
    
    def __del__(self):
        if hasattr(self, "_forward_hook"):
            self._forward_hook.remove()
        if hasattr(self, "_backward_hook"):
            self._backward_hook.remove()


# =============================================================================
# Score-CAM (Gradient-Free)
# =============================================================================

class ScoreCAM:
    """
    Score-CAM implementation.
    
    Gradient-free method that uses forward passes with masked inputs.
    More stable but slower than gradient-based methods.
    
    Reference:
        "Score-CAM: Score-Weighted Visual Explanations for CNNs"
        Wang et al., 2020
    """
    
    def __init__(
        self,
        model: nn.Module,
        target_layer: str | nn.Module,
        use_cuda: bool = True,
        batch_size: int = 16,
    ):
        """Initialize Score-CAM."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for Score-CAM")
        
        self._model = model
        self._model.eval()
        
        if isinstance(target_layer, str):
            self._target_layer = self._get_layer_by_name(target_layer)
        else:
            self._target_layer = target_layer
        
        self._device = torch.device(
            "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        )
        self._model = self._model.to(self._device)
        
        self._batch_size = batch_size
        self._activations: torch.Tensor | None = None
        
        self._hook = self._target_layer.register_forward_hook(self._activation_hook)
    
    def _get_layer_by_name(self, layer_name: str) -> nn.Module:
        module = self._model
        for part in layer_name.split("."):
            if part.isdigit():
                module = module[int(part)]
            else:
                module = getattr(module, part)
        return module
    
    def _activation_hook(self, module, input, output):
        self._activations = output.detach()
    
    @torch.no_grad()
    def explain(
        self,
        image: np.ndarray | torch.Tensor,
        target_class: int | None = None,
    ) -> np.ndarray:
        """Generate Score-CAM heatmap."""
        # Prepare input
        if isinstance(image, np.ndarray):
            if image.ndim == 3 and image.shape[2] == 3:
                tensor = torch.from_numpy(image.transpose(2, 0, 1)).float()
            else:
                tensor = torch.from_numpy(image).float()
            
            if tensor.max() > 1.0:
                tensor = tensor / 255.0
            
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            tensor = (tensor - mean) / std
            tensor = tensor.unsqueeze(0)
        else:
            tensor = image
            if tensor.dim() == 3:
                tensor = tensor.unsqueeze(0)
        
        tensor = tensor.to(self._device)
        
        # Get baseline output
        output = self._model(tensor)
        if hasattr(output, "logits"):
            output = output.logits
        
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Get activations
        activations = self._activations[0]  # (C, H, W)
        num_channels = activations.shape[0]
        
        # Upsample activations to input size
        upsampled = F.interpolate(
            activations.unsqueeze(0),
            size=tensor.shape[2:],
            mode="bilinear",
            align_corners=False,
        )[0]  # (C, H, W)
        
        # Normalize each channel
        maxs = upsampled.view(num_channels, -1).max(dim=1)[0]
        mins = upsampled.view(num_channels, -1).min(dim=1)[0]
        ranges = maxs - mins + 1e-8
        
        upsampled = (upsampled - mins.view(-1, 1, 1)) / ranges.view(-1, 1, 1)
        
        # Score each channel
        scores = torch.zeros(num_channels, device=self._device)
        
        for i in range(0, num_channels, self._batch_size):
            batch_end = min(i + self._batch_size, num_channels)
            batch_masks = upsampled[i:batch_end]  # (B, H, W)
            
            # Apply masks
            masked_inputs = tensor * batch_masks.unsqueeze(1)  # (B, C, H, W)
            
            # Get outputs
            outputs = self._model(masked_inputs)
            if hasattr(outputs, "logits"):
                outputs = outputs.logits
            
            # Softmax scores for target class
            batch_scores = F.softmax(outputs, dim=1)[:, target_class]
            scores[i:batch_end] = batch_scores
        
        # Weighted combination
        scores = F.relu(scores)
        cam = (scores.view(-1, 1, 1) * upsampled).sum(dim=0)
        
        # Normalize
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        
        return cam.cpu().numpy()
    
    def __del__(self):
        if hasattr(self, "_hook"):
            self._hook.remove()


# =============================================================================
# Utility Functions
# =============================================================================

def get_explainer(
    method: str,
    model: nn.Module,
    target_layer: str,
    **kwargs,
) -> GradCAMPlusPlus | LayerCAM | ScoreCAM:
    """
    Factory function to create explainer.
    
    Args:
        method: Explainability method (gradcam++, layercam, scorecam)
        model: PyTorch model
        target_layer: Target layer name
        **kwargs: Additional arguments
    
    Returns:
        Explainer instance
    """
    methods = {
        "gradcam++": GradCAMPlusPlus,
        "gradcampp": GradCAMPlusPlus,
        "layercam": LayerCAM,
        "scorecam": ScoreCAM,
    }
    
    method_lower = method.lower()
    
    if method_lower not in methods:
        raise ValueError(
            f"Unknown method: {method}. Available: {list(methods.keys())}"
        )
    
    return methods[method_lower](model, target_layer, **kwargs)


def create_heatmap_grid(
    heatmaps: list[np.ndarray],
    images: list[np.ndarray],
    grid_size: tuple[int, int] | None = None,
    spacing: int = 2,
) -> np.ndarray:
    """
    Create a grid of heatmap overlays.
    
    Args:
        heatmaps: List of heatmaps
        images: List of images
        grid_size: (rows, cols) or None for auto
        spacing: Spacing between images
    
    Returns:
        Grid image
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV is required for heatmap grid")
    
    n = len(heatmaps)
    
    if grid_size is None:
        cols = int(np.ceil(np.sqrt(n)))
        rows = int(np.ceil(n / cols))
    else:
        rows, cols = grid_size
    
    # Create overlays
    overlays = []
    for heatmap, image in zip(heatmaps, images):
        heatmap_resized = cv2.resize(
            heatmap,
            (image.shape[1], image.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )
        overlays.append(visualize_attention(image, heatmap_resized))
    
    # Pad to fill grid
    h, w = overlays[0].shape[:2]
    while len(overlays) < rows * cols:
        overlays.append(np.zeros((h, w, 3), dtype=np.uint8))
    
    # Create grid
    grid_rows = []
    for i in range(rows):
        row_images = overlays[i * cols:(i + 1) * cols]
        
        # Add horizontal spacing
        row = row_images[0]
        for img in row_images[1:]:
            spacer = np.zeros((h, spacing, 3), dtype=np.uint8)
            row = np.hstack([row, spacer, img])
        
        grid_rows.append(row)
    
    # Stack rows with vertical spacing
    grid = grid_rows[0]
    for row in grid_rows[1:]:
        spacer = np.zeros((spacing, grid.shape[1], 3), dtype=np.uint8)
        grid = np.vstack([grid, spacer, row])
    
    return grid
