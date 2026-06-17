"""Stage 7 lightweight Research Model Lab.

Model Lab is research-only: it evaluates caller-provided datasets and returns
predictions/metrics without placing orders or connecting to QMT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qmt_ai_trading.research.dataset import ResearchDataset, split_dataset_by_ratio
from qmt_ai_trading.research.metrics import ModelEvaluationResult, evaluate_predictions


@dataclass
class ModelPrediction:
    symbol: str
    datetime: Any
    prediction: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelLabResult:
    success: bool
    reason: str = ""
    predictions: list[ModelPrediction] = field(default_factory=list)
    evaluation: ModelEvaluationResult | None = None
    model: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def train_simple_linear_model(dataset: ResearchDataset) -> dict[str, Any]:
    """Train a tiny pure-Python weighted baseline over feature/label rows."""

    pair_count = min(len(dataset.features), len(dataset.labels))
    if pair_count < 2:
        return {"success": False, "reason": "not enough samples to train simple model", "weights": {}, "intercept": 0.0}
    feature_names = sorted({name for row in dataset.features[:pair_count] for name in row.features})
    label_values = [float(row.forward_return) for row in dataset.labels[:pair_count]]
    mean_label = sum(label_values) / len(label_values)
    weights: dict[str, float] = {}
    for name in feature_names:
        values = [float(row.features.get(name, 0.0)) for row in dataset.features[:pair_count]]
        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values)
        if variance == 0:
            weights[name] = 0.0
            continue
        covariance = sum((value - mean_value) * (label - mean_label) for value, label in zip(values, label_values))
        weights[name] = covariance / variance
    intercept = mean_label - sum(weights[name] * (sum(float(row.features.get(name, 0.0)) for row in dataset.features[:pair_count]) / pair_count) for name in feature_names)
    return {"success": True, "reason": "simple pure-Python linear baseline", "weights": weights, "intercept": intercept, "feature_names": feature_names}


def predict_with_simple_linear_model(model, dataset: ResearchDataset) -> list[ModelPrediction]:
    """Generate ModelPrediction rows from the lightweight baseline model."""

    if not model or not model.get("success"):
        return []
    weights = dict(model.get("weights", {}) or {})
    intercept = float(model.get("intercept", 0.0) or 0.0)
    predictions: list[ModelPrediction] = []
    for row in dataset.features[: min(len(dataset.features), len(dataset.labels) or len(dataset.features))]:
        value = intercept + sum(float(row.features.get(name, 0.0)) * float(weight) for name, weight in weights.items())
        predictions.append(ModelPrediction(symbol=row.symbol, datetime=row.datetime, prediction=value, metadata={"model": "simple_linear_baseline"}))
    return predictions


def run_model_lab(dataset: ResearchDataset) -> ModelLabResult:
    """Train, predict, and evaluate the Stage 7 lightweight baseline."""

    pair_count = min(len(dataset.features), len(dataset.labels))
    if pair_count < 3:
        return ModelLabResult(success=False, reason="not enough samples for train/test model lab", metadata={"pair_count": pair_count})
    split = split_dataset_by_ratio(dataset, train_ratio=0.7)
    model = train_simple_linear_model(split.train)
    if not model.get("success"):
        return ModelLabResult(success=False, reason=str(model.get("reason", "model training failed")), model=model, metadata={"pair_count": pair_count})
    evaluation_dataset = split.test if split.test.features and split.test.labels else split.train
    predictions = predict_with_simple_linear_model(model, evaluation_dataset)
    labels = [row.forward_return for row in evaluation_dataset.labels[: len(predictions)]]
    evaluation = evaluate_predictions([row.prediction for row in predictions], labels)
    return ModelLabResult(
        success=bool(predictions) and evaluation.success,
        reason=evaluation.reason,
        predictions=predictions,
        evaluation=evaluation,
        model=model,
        metadata={"pair_count": pair_count, "train_count": len(split.train.labels), "test_count": len(split.test.labels)},
    )
