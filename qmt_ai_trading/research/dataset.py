"""Stage 7 Research Model Lab dataset helpers.

The helpers in this module are offline/read-only. They transform caller-supplied
Data Hub ``MarketBar`` objects into research samples and labels only; they never
connect to QMT, access the network, or place orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class FeatureRow:
    symbol: str
    datetime: Any
    features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LabelRow:
    symbol: str
    datetime: Any
    forward_return: float
    horizon: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchDataset:
    features: list[FeatureRow] = field(default_factory=list)
    labels: list[LabelRow] = field(default_factory=list)
    name: str = "research_dataset"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainTestSplit:
    train: ResearchDataset
    test: ResearchDataset
    split_datetime: Any = None
    split_ratio: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct_change(current: float | None, previous: float | None) -> float:
    if current is None or previous is None or previous == 0:
        return 0.0
    return (current - previous) / previous


def build_feature_rows_from_bars(symbol: str, bars: list[MarketBar] | Iterable[MarketBar] | None) -> list[FeatureRow]:
    """Build dependency-light feature rows from local MarketBar objects."""

    normalized = normalize_symbol(symbol)
    materialized = list(bars or [])
    rows: list[FeatureRow] = []
    previous_close: float | None = None
    previous_volume: float | None = None
    for index, bar in enumerate(materialized):
        close = _safe_float(bar.close)
        open_ = _safe_float(bar.open)
        high = _safe_float(bar.high)
        low = _safe_float(bar.low)
        volume = _safe_float(bar.volume)
        features = {
            "close": close or 0.0,
            "open_close_return": _pct_change(close, open_),
            "high_low_range": 0.0 if close in (None, 0) or high is None or low is None else (high - low) / close,
            "prev_close_return": _pct_change(close, previous_close),
            "volume_change": _pct_change(volume, previous_volume),
        }
        rows.append(
            FeatureRow(
                symbol=normalized or normalize_symbol(getattr(bar, "symbol", "")),
                datetime=bar.datetime,
                features=features,
                metadata={"bar_index": index, "source": getattr(bar, "source", "")},
            )
        )
        previous_close = close
        previous_volume = volume
    return rows


def build_forward_return_labels(symbol: str, bars: list[MarketBar] | Iterable[MarketBar] | None, horizon: int = 1) -> list[LabelRow]:
    """Build forward-return labels aligned to the source bar datetime."""

    normalized = normalize_symbol(symbol)
    materialized = list(bars or [])
    horizon = max(1, int(horizon or 1))
    labels: list[LabelRow] = []
    for index, bar in enumerate(materialized):
        target_index = index + horizon
        if target_index >= len(materialized):
            break
        close = _safe_float(bar.close)
        future_close = _safe_float(materialized[target_index].close)
        if close is None or close == 0 or future_close is None:
            continue
        labels.append(
            LabelRow(
                symbol=normalized or normalize_symbol(getattr(bar, "symbol", "")),
                datetime=bar.datetime,
                forward_return=(future_close - close) / close,
                horizon=horizon,
                metadata={"bar_index": index, "target_index": target_index},
            )
        )
    return labels


def build_research_dataset(symbol: str, bars: list[MarketBar] | Iterable[MarketBar] | None, horizon: int = 1) -> ResearchDataset:
    """Build a feature/label research dataset for one ETF or index symbol."""

    materialized = list(bars or [])
    metadata: dict[str, Any] = {"symbol": normalize_symbol(symbol), "horizon": max(1, int(horizon or 1)), "bar_count": len(materialized)}
    features = build_feature_rows_from_bars(symbol, materialized)
    labels = build_forward_return_labels(symbol, materialized, horizon=metadata["horizon"])
    if not materialized:
        metadata["reason"] = "no bars supplied"
    elif not labels:
        metadata["reason"] = "not enough bars to build forward-return labels"
    return ResearchDataset(features=features[: len(labels)], labels=labels, name=f"{normalize_symbol(symbol)}_h{metadata['horizon']}", metadata=metadata)


def split_dataset_by_ratio(dataset: ResearchDataset, train_ratio: float = 0.7) -> TrainTestSplit:
    """Split a ResearchDataset chronologically by row ratio."""

    ratio = max(0.0, min(1.0, float(train_ratio)))
    pair_count = min(len(dataset.features), len(dataset.labels))
    split_index = int(pair_count * ratio)
    base_meta = dict(dataset.metadata or {})
    train = ResearchDataset(dataset.features[:split_index], dataset.labels[:split_index], name=f"{dataset.name}_train", metadata={**base_meta, "split": "train"})
    test = ResearchDataset(dataset.features[split_index:pair_count], dataset.labels[split_index:pair_count], name=f"{dataset.name}_test", metadata={**base_meta, "split": "test"})
    split_datetime = dataset.features[split_index].datetime if split_index < pair_count and dataset.features else None
    return TrainTestSplit(train=train, test=test, split_datetime=split_datetime, split_ratio=ratio, metadata={"pair_count": pair_count})
