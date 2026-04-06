"""
Ensemble Model Orchestrator

Multi-model ensemble for robust deepfake detection:
    - Combines predictions from multiple architectures
    - Supports weighted voting and averaging
    - Handles uncertainty quantification
    - Provides model agreement metrics

Ensemble Strategy:
    1. Each model produces independent predictions
    2. Predictions are weighted by model confidence/performance
    3. Final prediction combines evidence from all models
    4. Disagreement triggers uncertainty flag

Benefits:
    - Higher accuracy than single models
    - More robust to adversarial attacks
    - Better generalization across datasets
    - Uncertainty quantification
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .base import BaseDetectionModel, ModelOutput

logger = logging.getLogger(__name__)


@dataclass
class EnsemblePrediction:
    """
    Structured output from ensemble prediction.
    
    Contains combined predictions and individual model outputs
    for analysis and debugging.
    """
    
    # Final ensemble prediction
    prediction: Tensor
    confidence: Tensor
    probabilities: Tensor
    
    # Uncertainty metrics
    uncertainty: Tensor
    agreement_score: float
    
    # Per-model results
    model_predictions: dict[str, ModelOutput] = field(default_factory=dict)
    model_weights: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prediction": self.prediction.cpu().numpy().tolist(),
            "confidence": self.confidence.cpu().numpy().tolist(),
            "probabilities": self.probabilities.cpu().numpy().tolist(),
            "uncertainty": self.uncertainty.cpu().numpy().tolist(),
            "agreement_score": self.agreement_score,
            "model_weights": self.model_weights,
            "model_predictions": {
                name: output.to_dict()
                for name, output in self.model_predictions.items()
            },
        }


class EnsembleModel(nn.Module):
    """
    Multi-model ensemble for deepfake detection.
    
    Combines predictions from multiple detection models using
    various aggregation strategies for improved accuracy and
    robustness.
    
    Supported Strategies:
        - "voting": Majority voting (discrete)
        - "averaging": Probability averaging (soft)
        - "weighted": Weighted probability averaging
        - "stacking": Learned meta-classifier
    
    Args:
        models: Dictionary of model_name -> model instance.
        weights: Optional dictionary of model weights.
        strategy: Ensemble aggregation strategy.
        uncertainty_threshold: Threshold for uncertain predictions.
    
    Example:
        >>> from ml.architectures import EfficientNetLSTM
        >>> models = {
        ...     "efficientnet": EfficientNetLSTM(),
        ...     "resnext": ResNeXtTransformer(),
        ... }
        >>> ensemble = EnsembleModel(models, strategy="weighted")
        >>> video = torch.randn(1, 60, 3, 224, 224)
        >>> result = ensemble.predict(video)
        >>> print(f"Prediction: {result.prediction}, Agreement: {result.agreement_score}")
    """
    
    STRATEGIES: Final[tuple[str, ...]] = ("voting", "averaging", "weighted", "stacking")
    
    def __init__(
        self,
        models: dict[str, BaseDetectionModel],
        weights: dict[str, float] | None = None,
        strategy: Literal["voting", "averaging", "weighted", "stacking"] = "weighted",
        uncertainty_threshold: float = 0.15,
        num_classes: int = 2,
    ) -> None:
        super().__init__()
        
        if not models:
            raise ValueError("At least one model is required for ensemble")
        
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Strategy must be one of {self.STRATEGIES}")
        
        self.strategy = strategy
        self.uncertainty_threshold = uncertainty_threshold
        self.num_classes = num_classes
        
        # Store models as ModuleDict for proper parameter tracking
        self.models = nn.ModuleDict(models)
        
        # Initialize or validate weights
        if weights is None:
            # Equal weights
            self.weights = {name: 1.0 / len(models) for name in models}
        else:
            # Normalize provided weights
            total = sum(weights.values())
            self.weights = {name: w / total for name, w in weights.items()}
        
        # Validate weights match models
        if set(self.weights.keys()) != set(models.keys()):
            raise ValueError("Weights must match model names")
        
        # Stacking meta-classifier (if strategy is stacking)
        if strategy == "stacking":
            self.meta_classifier = nn.Sequential(
                nn.Linear(len(models) * num_classes, 64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, num_classes),
            )
        else:
            self.meta_classifier = None
        
        logger.info(
            f"Initialized ensemble with {len(models)} models: "
            f"{list(models.keys())}, strategy={strategy}"
        )
    
    @property
    def device(self) -> torch.device:
        """Get ensemble device (from first model)."""
        first_model = next(iter(self.models.values()))
        return first_model.device
    
    def forward(
        self,
        x: Tensor,
    ) -> tuple[Tensor, dict[str, ModelOutput]]:
        """
        Forward pass through all ensemble models.
        
        Args:
            x: Input tensor (B, T, C, H, W)
        
        Returns:
            Tuple of (ensemble_logits, model_outputs)
        """
        model_outputs: dict[str, ModelOutput] = {}
        
        # Get predictions from each model
        for name, model in self.models.items():
            model_outputs[name] = model.predict(x)
        
        # Aggregate predictions
        if self.strategy == "voting":
            logits = self._voting_aggregation(model_outputs)
        elif self.strategy == "averaging":
            logits = self._averaging_aggregation(model_outputs)
        elif self.strategy == "weighted":
            logits = self._weighted_aggregation(model_outputs)
        else:  # stacking
            logits = self._stacking_aggregation(model_outputs)
        
        return logits, model_outputs
    
    def _voting_aggregation(
        self,
        outputs: dict[str, ModelOutput],
    ) -> Tensor:
        """
        Majority voting aggregation.
        
        Each model votes for a class, majority wins.
        """
        batch_size = next(iter(outputs.values())).prediction.size(0)
        device = next(iter(outputs.values())).prediction.device
        
        # Collect votes
        votes = torch.zeros(batch_size, self.num_classes, device=device)
        
        for name, output in outputs.items():
            weight = self.weights[name]
            for i in range(batch_size):
                pred_class = output.prediction[i].item()
                votes[i, pred_class] += weight
        
        return votes  # Treat votes as logits
    
    def _averaging_aggregation(
        self,
        outputs: dict[str, ModelOutput],
    ) -> Tensor:
        """
        Simple probability averaging.
        
        Average probabilities across all models.
        """
        all_probs = torch.stack([
            output.probabilities for output in outputs.values()
        ], dim=0)  # (num_models, B, num_classes)
        
        avg_probs = all_probs.mean(dim=0)  # (B, num_classes)
        
        # Convert back to logits for consistency
        return torch.log(avg_probs + 1e-8)
    
    def _weighted_aggregation(
        self,
        outputs: dict[str, ModelOutput],
    ) -> Tensor:
        """
        Weighted probability averaging.
        
        Weight each model's probabilities by its assigned weight.
        """
        batch_size = next(iter(outputs.values())).probabilities.size(0)
        device = next(iter(outputs.values())).probabilities.device
        
        weighted_probs = torch.zeros(
            batch_size, self.num_classes,
            device=device,
        )
        
        for name, output in outputs.items():
            weight = self.weights[name]
            weighted_probs += weight * output.probabilities
        
        # Convert back to logits
        return torch.log(weighted_probs + 1e-8)
    
    def _stacking_aggregation(
        self,
        outputs: dict[str, ModelOutput],
    ) -> Tensor:
        """
        Learned stacking aggregation.
        
        Concatenate model outputs and pass through meta-classifier.
        """
        # Concatenate all model probabilities
        all_probs = torch.cat([
            output.probabilities for output in outputs.values()
        ], dim=1)  # (B, num_models * num_classes)
        
        # Pass through meta-classifier
        return self.meta_classifier(all_probs)
    
    def predict(self, x: Tensor) -> EnsemblePrediction:
        """
        Make ensemble prediction with uncertainty quantification.
        
        Args:
            x: Input tensor (B, T, C, H, W)
        
        Returns:
            EnsemblePrediction with combined results and metrics.
        """
        self.eval()
        
        with torch.no_grad():
            logits, model_outputs = self.forward(x)
            
            # Compute final probabilities and predictions
            probabilities = F.softmax(logits, dim=1)
            confidence, prediction = torch.max(probabilities, dim=1)
            
            # Compute uncertainty (entropy-based)
            uncertainty = self._compute_uncertainty(probabilities)
            
            # Compute model agreement
            agreement_score = self._compute_agreement(model_outputs)
        
        return EnsemblePrediction(
            prediction=prediction,
            confidence=confidence,
            probabilities=probabilities,
            uncertainty=uncertainty,
            agreement_score=agreement_score,
            model_predictions=model_outputs,
            model_weights=self.weights.copy(),
        )
    
    def _compute_uncertainty(self, probabilities: Tensor) -> Tensor:
        """
        Compute prediction uncertainty using entropy.
        
        High entropy = high uncertainty.
        
        Args:
            probabilities: Predicted probabilities (B, num_classes)
        
        Returns:
            Uncertainty scores (B,) in range [0, 1]
        """
        # Shannon entropy
        entropy = -torch.sum(
            probabilities * torch.log(probabilities + 1e-8),
            dim=1,
        )
        
        # Normalize by maximum entropy
        max_entropy = torch.log(torch.tensor(self.num_classes, dtype=torch.float))
        normalized_entropy = entropy / max_entropy
        
        return normalized_entropy
    
    def _compute_agreement(self, outputs: dict[str, ModelOutput]) -> float:
        """
        Compute agreement score between models.
        
        Agreement = percentage of samples where all models agree.
        
        Args:
            outputs: Dictionary of model outputs
        
        Returns:
            Agreement score in range [0, 1]
        """
        predictions = [output.prediction for output in outputs.values()]
        
        if len(predictions) < 2:
            return 1.0
        
        # Stack predictions
        stacked = torch.stack(predictions, dim=0)  # (num_models, B)
        
        # Check if all models agree for each sample
        agreement = torch.all(stacked == stacked[0:1], dim=0)  # (B,)
        
        return agreement.float().mean().item()
    
    def get_disagreement_analysis(
        self,
        outputs: dict[str, ModelOutput],
    ) -> dict[str, Any]:
        """
        Analyze disagreements between models.
        
        Useful for understanding where models differ and why.
        
        Args:
            outputs: Dictionary of model outputs
        
        Returns:
            Analysis dictionary with disagreement statistics
        """
        predictions = {name: output.prediction for name, output in outputs.items()}
        confidences = {name: output.confidence for name, output in outputs.items()}
        
        batch_size = next(iter(predictions.values())).size(0)
        
        analysis = {
            "total_samples": batch_size,
            "disagreements": [],
        }
        
        for i in range(batch_size):
            preds = {name: pred[i].item() for name, pred in predictions.items()}
            confs = {name: conf[i].item() for name, conf in confidences.items()}
            
            # Check for disagreement
            unique_preds = set(preds.values())
            if len(unique_preds) > 1:
                analysis["disagreements"].append({
                    "sample_index": i,
                    "predictions": preds,
                    "confidences": confs,
                })
        
        analysis["disagreement_rate"] = len(analysis["disagreements"]) / batch_size
        
        return analysis
    
    def update_weights(self, new_weights: dict[str, float]) -> None:
        """
        Update model weights.
        
        Args:
            new_weights: New weight dictionary (will be normalized)
        """
        # Validate keys
        if set(new_weights.keys()) != set(self.models.keys()):
            raise ValueError("New weights must match model names")
        
        # Normalize
        total = sum(new_weights.values())
        self.weights = {name: w / total for name, w in new_weights.items()}
        
        logger.info(f"Updated ensemble weights: {self.weights}")
    
    def add_model(
        self,
        name: str,
        model: BaseDetectionModel,
        weight: float = 1.0,
    ) -> None:
        """
        Add a new model to the ensemble.
        
        Args:
            name: Model name/identifier
            model: Model instance
            weight: Initial weight for the model
        """
        if name in self.models:
            raise ValueError(f"Model '{name}' already exists in ensemble")
        
        self.models[name] = model
        
        # Update weights
        total_weight = sum(self.weights.values()) + weight
        self.weights = {n: w / total_weight for n, w in self.weights.items()}
        self.weights[name] = weight / total_weight
        
        logger.info(f"Added model '{name}' to ensemble with weight {self.weights[name]:.3f}")
    
    def remove_model(self, name: str) -> None:
        """
        Remove a model from the ensemble.
        
        Args:
            name: Model name to remove
        """
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found in ensemble")
        
        if len(self.models) <= 1:
            raise ValueError("Cannot remove last model from ensemble")
        
        del self.models[name]
        del self.weights[name]
        
        # Renormalize weights
        total = sum(self.weights.values())
        self.weights = {n: w / total for n, w in self.weights.items()}
        
        logger.info(f"Removed model '{name}' from ensemble")
    
    @classmethod
    def from_checkpoints(
        cls,
        checkpoint_configs: list[dict[str, Any]],
        device: torch.device | str = "cpu",
        strategy: str = "weighted",
    ) -> "EnsembleModel":
        """
        Create ensemble from checkpoint files.
        
        Args:
            checkpoint_configs: List of dicts with 'path', 'name', 'class', 'weight'
            device: Device to load models on
            strategy: Ensemble strategy
        
        Returns:
            Initialized ensemble model
        
        Example:
            >>> configs = [
            ...     {"path": "model1.pt", "name": "m1", "class": EfficientNetLSTM, "weight": 0.4},
            ...     {"path": "model2.pt", "name": "m2", "class": ResNeXtTransformer, "weight": 0.6},
            ... ]
            >>> ensemble = EnsembleModel.from_checkpoints(configs)
        """
        models = {}
        weights = {}
        
        for config in checkpoint_configs:
            model_cls = config["class"]
            model = model_cls.from_checkpoint(config["path"], device=device)
            model.eval()
            
            models[config["name"]] = model
            weights[config["name"]] = config.get("weight", 1.0)
        
        return cls(models=models, weights=weights, strategy=strategy)
