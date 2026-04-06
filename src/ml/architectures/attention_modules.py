"""
Attention Mechanism Modules

Advanced attention mechanisms for deepfake detection:
    - CBAM: Convolutional Block Attention Module
    - Self-Attention: Scaled dot-product attention
    - Temporal Attention: Attention across video frames
    - Cross-Attention: Multi-modal attention fusion

These modules enhance the model's ability to focus on
discriminative regions and temporal artifacts in deepfake videos.

Research References:
    - CBAM: https://arxiv.org/abs/1807.06521
    - Attention is All You Need: https://arxiv.org/abs/1706.03762
"""

from __future__ import annotations

import math
from typing import Final, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class ChannelAttention(nn.Module):
    """
    Channel attention module from CBAM.
    
    Learns channel-wise feature importance using global
    average and max pooling followed by shared MLP.
    
    Args:
        channels: Number of input channels.
        reduction: Channel reduction ratio for MLP.
    """
    
    def __init__(
        self,
        channels: int,
        reduction: int = 16,
    ) -> None:
        super().__init__()
        
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        
        # Shared MLP
        reduced_channels = max(channels // reduction, 8)
        self.mlp = nn.Sequential(
            nn.Conv2d(channels, reduced_channels, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(reduced_channels, channels, kernel_size=1, bias=False),
        )
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor (B, C, H, W)
        
        Returns:
            Channel attention weights (B, C, 1, 1)
        """
        # Global average pooling path
        avg_out = self.mlp(self.avg_pool(x))
        
        # Global max pooling path
        max_out = self.mlp(self.max_pool(x))
        
        # Combine and apply sigmoid
        return torch.sigmoid(avg_out + max_out)


class SpatialAttention(nn.Module):
    """
    Spatial attention module from CBAM.
    
    Learns spatial feature importance using channel-wise
    statistics followed by convolution.
    
    Args:
        kernel_size: Convolution kernel size (default: 7).
    """
    
    def __init__(
        self,
        kernel_size: int = 7,
    ) -> None:
        super().__init__()
        
        padding = kernel_size // 2
        self.conv = nn.Conv2d(
            2, 1,
            kernel_size=kernel_size,
            padding=padding,
            bias=False,
        )
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor (B, C, H, W)
        
        Returns:
            Spatial attention weights (B, 1, H, W)
        """
        # Channel-wise statistics
        avg_out = x.mean(dim=1, keepdim=True)
        max_out, _ = x.max(dim=1, keepdim=True)
        
        # Concatenate and convolve
        combined = torch.cat([avg_out, max_out], dim=1)
        
        return torch.sigmoid(self.conv(combined))


class CBAM(nn.Module):
    """
    Convolutional Block Attention Module.
    
    Combines channel and spatial attention for comprehensive
    feature refinement. Originally proposed for image classification
    and detection tasks.
    
    The attention is applied sequentially:
        1. Channel attention refines "what" to focus on
        2. Spatial attention refines "where" to focus
    
    Args:
        channels: Number of input channels.
        reduction: Reduction ratio for channel attention.
        spatial_kernel: Kernel size for spatial attention.
    
    Example:
        >>> cbam = CBAM(channels=2048)
        >>> x = torch.randn(8, 2048, 7, 7)
        >>> out = cbam(x)  # Same shape as input
    """
    
    def __init__(
        self,
        channels: int,
        reduction: int = 16,
        spatial_kernel: int = 7,
    ) -> None:
        super().__init__()
        
        self.channel_attention = ChannelAttention(channels, reduction)
        self.spatial_attention = SpatialAttention(spatial_kernel)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass with sequential attention.
        
        Args:
            x: Input tensor (B, C, H, W)
        
        Returns:
            Attention-refined tensor (B, C, H, W)
        """
        # Channel attention
        x = x * self.channel_attention(x)
        
        # Spatial attention
        x = x * self.spatial_attention(x)
        
        return x


class SelfAttention(nn.Module):
    """
    Multi-head self-attention module.
    
    Implements scaled dot-product attention with multiple heads
    for capturing long-range dependencies.
    
    Args:
        dim: Input/output dimension.
        num_heads: Number of attention heads.
        dropout: Dropout rate for attention weights.
        bias: Whether to use bias in projections.
    
    Example:
        >>> attention = SelfAttention(dim=512, num_heads=8)
        >>> x = torch.randn(8, 60, 512)  # (B, T, D)
        >>> out, weights = attention(x)
    """
    
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        dropout: float = 0.0,
        bias: bool = True,
    ) -> None:
        super().__init__()
        
        assert dim % num_heads == 0, f"dim ({dim}) must be divisible by num_heads ({num_heads})"
        
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        # Combined QKV projection for efficiency
        self.qkv = nn.Linear(dim, dim * 3, bias=bias)
        self.attn_dropout = nn.Dropout(dropout)
        self.proj = nn.Linear(dim, dim, bias=bias)
        self.proj_dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: Tensor,
        mask: Tensor | None = None,
        return_attention: bool = True,
    ) -> tuple[Tensor, Tensor | None]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (B, T, D)
            mask: Optional attention mask (B, T, T)
            return_attention: Whether to return attention weights
        
        Returns:
            Tuple of (output, attention_weights)
            attention_weights is None if return_attention=False
        """
        B, T, D = x.shape
        
        # Compute Q, K, V
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, heads, T, head_dim)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # Scaled dot-product attention
        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))
        
        attn = F.softmax(attn, dim=-1)
        attn = self.attn_dropout(attn)
        
        # Apply attention to values
        out = (attn @ v).transpose(1, 2).reshape(B, T, D)
        out = self.proj(out)
        out = self.proj_dropout(out)
        
        if return_attention:
            # Average attention across heads for visualization
            attn_weights = attn.mean(dim=1)  # (B, T, T)
            return out, attn_weights
        
        return out, None


class TemporalAttention(nn.Module):
    """
    Temporal attention for video frame sequences.
    
    Learns to weight different frames based on their
    relevance for the final prediction. Particularly useful
    for detecting temporal inconsistencies in deepfakes.
    
    Architecture:
        1. Self-attention across temporal dimension
        2. Optional positional encoding
        3. Layer normalization
    
    Args:
        dim: Feature dimension per frame.
        num_heads: Number of attention heads.
        num_layers: Number of attention layers.
        dropout: Dropout rate.
        max_seq_len: Maximum sequence length for positional encoding.
    
    Example:
        >>> temporal_attn = TemporalAttention(dim=2048, num_heads=8, num_layers=2)
        >>> frame_features = torch.randn(8, 60, 2048)  # 60 frames
        >>> attended, weights = temporal_attn(frame_features)
    """
    
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        num_layers: int = 2,
        dropout: float = 0.1,
        max_seq_len: int = 300,
    ) -> None:
        super().__init__()
        
        self.dim = dim
        self.num_layers = num_layers
        
        # Positional encoding
        self.register_buffer(
            "positional_encoding",
            self._create_positional_encoding(max_seq_len, dim),
        )
        
        # Attention layers
        self.attention_layers = nn.ModuleList([
            SelfAttention(dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        # Layer norms
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(dim) for _ in range(num_layers)
        ])
        
        # Feed-forward layers
        self.ffn_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(dim, dim * 4),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(dim * 4, dim),
                nn.Dropout(dropout),
            )
            for _ in range(num_layers)
        ])
        
        self.ffn_norms = nn.ModuleList([
            nn.LayerNorm(dim) for _ in range(num_layers)
        ])
    
    def _create_positional_encoding(
        self,
        max_len: int,
        dim: int,
    ) -> Tensor:
        """Create sinusoidal positional encoding."""
        position = torch.arange(max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, dim, 2).float() * (-math.log(10000.0) / dim)
        )
        
        pe = torch.zeros(max_len, dim)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)  # (1, max_len, dim)
    
    def forward(
        self,
        x: Tensor,
        mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input tensor (B, T, D)
            mask: Optional attention mask
        
        Returns:
            Tuple of (attended_features, attention_weights)
        """
        B, T, D = x.shape
        
        # Add positional encoding
        x = x + self.positional_encoding[:, :T, :]
        
        # Store attention weights from last layer
        attention_weights = None
        
        # Apply transformer layers
        for i in range(self.num_layers):
            # Self-attention with residual
            attended, attn = self.attention_layers[i](
                self.layer_norms[i](x),
                mask=mask,
            )
            x = x + attended
            
            # Feed-forward with residual
            x = x + self.ffn_layers[i](self.ffn_norms[i](x))
            
            if i == self.num_layers - 1:
                attention_weights = attn
        
        return x, attention_weights


class CrossAttention(nn.Module):
    """
    Cross-attention module for multi-modal fusion.
    
    Attends from one modality (query) to another (key/value).
    Useful for:
        - Audio-visual synchronization analysis
        - Multi-scale feature fusion
        - Frame-to-global context attention
    
    Args:
        query_dim: Dimension of query input.
        key_dim: Dimension of key/value input.
        num_heads: Number of attention heads.
        dropout: Dropout rate.
    
    Example:
        >>> cross_attn = CrossAttention(query_dim=512, key_dim=2048)
        >>> local_features = torch.randn(8, 60, 512)
        >>> global_context = torch.randn(8, 1, 2048)
        >>> fused, weights = cross_attn(local_features, global_context)
    """
    
    def __init__(
        self,
        query_dim: int,
        key_dim: int,
        num_heads: int = 8,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        
        self.num_heads = num_heads
        self.head_dim = query_dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        # Projections
        self.q_proj = nn.Linear(query_dim, query_dim)
        self.k_proj = nn.Linear(key_dim, query_dim)
        self.v_proj = nn.Linear(key_dim, query_dim)
        self.out_proj = nn.Linear(query_dim, query_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        query: Tensor,
        key_value: Tensor,
        mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        """
        Forward pass.
        
        Args:
            query: Query tensor (B, Tq, Dq)
            key_value: Key/value tensor (B, Tkv, Dkv)
            mask: Optional attention mask
        
        Returns:
            Tuple of (output, attention_weights)
        """
        B, Tq, _ = query.shape
        _, Tkv, _ = key_value.shape
        
        # Project to Q, K, V
        q = self.q_proj(query).reshape(B, Tq, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(key_value).reshape(B, Tkv, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(key_value).reshape(B, Tkv, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))
        
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        
        # Apply to values
        out = (attn @ v).transpose(1, 2).reshape(B, Tq, -1)
        out = self.out_proj(out)
        
        # Average attention for visualization
        attn_weights = attn.mean(dim=1)
        
        return out, attn_weights


class SqueezeExcitation(nn.Module):
    """
    Squeeze-and-Excitation attention block.
    
    Adaptively recalibrates channel-wise feature responses
    by modeling channel interdependencies.
    
    Args:
        channels: Number of input channels.
        reduction: Reduction ratio for bottleneck.
    """
    
    def __init__(
        self,
        channels: int,
        reduction: int = 16,
    ) -> None:
        super().__init__()
        
        reduced = max(channels // reduction, 8)
        
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels, reduced, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(reduced, channels, bias=False),
            nn.Sigmoid(),
        )
    
    def forward(self, x: Tensor) -> Tensor:
        """Apply squeeze-excitation attention."""
        B, C, H, W = x.shape
        attention = self.fc(x).view(B, C, 1, 1)
        return x * attention


class EfficientChannelAttention(nn.Module):
    """
    Efficient Channel Attention (ECA) module.
    
    A lightweight alternative to SE blocks using 1D convolution
    for local cross-channel interaction.
    
    Args:
        channels: Number of input channels.
        kernel_size: Size of the 1D conv kernel (auto if None).
    """
    
    def __init__(
        self,
        channels: int,
        kernel_size: int | None = None,
    ) -> None:
        super().__init__()
        
        if kernel_size is None:
            # Adaptive kernel size based on channel count
            t = int(abs(math.log2(channels) + 1) / 2)
            kernel_size = t if t % 2 else t + 1
        
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(
            1, 1,
            kernel_size=kernel_size,
            padding=kernel_size // 2,
            bias=False,
        )
    
    def forward(self, x: Tensor) -> Tensor:
        """Apply ECA attention."""
        B, C, H, W = x.shape
        
        # Global average pooling
        y = self.avg_pool(x).view(B, 1, C)
        
        # 1D convolution for channel interaction
        y = self.conv(y).view(B, C, 1, 1)
        
        return x * torch.sigmoid(y)
