"""Dependency-light research evaluation metrics for Stage 7 Model Lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any, Sequence


@dataclass(slots=True)
class EvaluationMetric:
    name: str
    value: float
    reason: str = ""


@dataclass(slots=True)
class ModelEvaluationResult:
    metrics: list[EvaluationMetric] = field(default_factory=list)
    ic: float = 0.0
    rank_ic: float = 0.0
    directional_accuracy: float = 0.0
    sample_count: int = 0
    success: bool = True
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _pairs(xs: Sequence[float] | Any, ys: Sequence[float] | Any) -> list[tuple[float, float]]:
    try:
        left = list(xs or [])
        right = list(ys or [])
    except TypeError:
        return []
    if len(left) != len(right):
        return []
    pairs: list[tuple[float, float]] = []
    for x, y in zip(left, right):
        try:
            pairs.append((float(x), float(y)))
        except (TypeError, ValueError):
            continue
    return pairs


def pearson_corr(xs, ys) -> float:
    pairs = _pairs(xs, ys)
    if len(pairs) < 2:
        return 0.0
    x_values, y_values = zip(*pairs)
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denom_x = sqrt(sum((x - mean_x) ** 2 for x in x_values))
    denom_y = sqrt(sum((y - mean_y) ** 2 for y in y_values))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def _ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_corr(xs, ys) -> float:
    pairs = _pairs(xs, ys)
    if len(pairs) < 2:
        return 0.0
    x_values, y_values = zip(*pairs)
    return pearson_corr(_ranks(list(x_values)), _ranks(list(y_values)))


def compute_ic(predictions, labels) -> float:
    return pearson_corr(predictions, labels)


def compute_rank_ic(predictions, labels) -> float:
    return spearman_corr(predictions, labels)


def compute_directional_accuracy(predictions, labels) -> float:
    pairs = _pairs(predictions, labels)
    if not pairs:
        return 0.0
    hits = sum(1 for pred, label in pairs if (pred >= 0 and label >= 0) or (pred < 0 and label < 0))
    return hits / len(pairs)


def evaluate_predictions(predictions, labels) -> ModelEvaluationResult:
    pairs = _pairs(predictions, labels)
    if not pairs:
        return ModelEvaluationResult(success=False, reason="empty inputs or length mismatch", sample_count=0)
    pred_values, label_values = zip(*pairs)
    ic = compute_ic(pred_values, label_values)
    rank_ic = compute_rank_ic(pred_values, label_values)
    accuracy = compute_directional_accuracy(pred_values, label_values)
    metrics = [
        EvaluationMetric("ic", ic),
        EvaluationMetric("rank_ic", rank_ic),
        EvaluationMetric("directional_accuracy", accuracy),
    ]
    return ModelEvaluationResult(metrics=metrics, ic=ic, rank_ic=rank_ic, directional_accuracy=accuracy, sample_count=len(pairs))
