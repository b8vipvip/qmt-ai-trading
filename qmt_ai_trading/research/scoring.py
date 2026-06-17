"""Stage 6 research scoring helpers.

Scoring consumes caller-provided MarketBar data and returns structured analysis
results only. It never submits orders or bypasses the Risk Gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol
from qmt_ai_trading.research.factors import (
    FactorResult,
    compute_momentum_factor,
    compute_volatility_factor,
    compute_volume_factor,
)


@dataclass(slots=True)
class ResearchScore:
    symbol: str
    score: float | None = None
    eligible: bool = True
    reason: str = ""
    factor_results: list[FactorResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def normalize_score(value: float | None, *, lower: float = -0.2, upper: float = 0.2) -> float | None:
    """Normalize a numeric value to a 0-100 score with clipping."""

    if value is None:
        return None
    if upper <= lower:
        raise ValueError("upper must be greater than lower")
    clipped = max(lower, min(upper, float(value)))
    return ((clipped - lower) / (upper - lower)) * 100.0


def combine_factor_scores(scores: Mapping[str, float | None], weights: Mapping[str, float] | None = None) -> float | None:
    """Combine normalized factor scores into one weighted score."""

    weights = weights or {}
    total = 0.0
    total_weight = 0.0
    for name, value in scores.items():
        if value is None:
            continue
        weight = float(weights.get(name, 1.0))
        total += float(value) * weight
        total_weight += abs(weight)
    if total_weight <= 0:
        return None
    return total / total_weight


def score_symbol_from_bars(
    symbol: str,
    bars: Iterable[MarketBar] | None,
    *,
    momentum_window: int = 20,
    volatility_window: int = 20,
    volume_window: int = 20,
) -> ResearchScore:
    """Create a structured research score for one symbol from local bars."""

    normalized = normalize_symbol(symbol)
    materialized = list(bars or [])
    if not materialized:
        return ResearchScore(symbol=normalized, score=None, eligible=False, reason="no bars supplied")

    momentum = compute_momentum_factor(materialized, window=momentum_window, symbol=normalized)
    volatility = compute_volatility_factor(materialized, window=volatility_window, symbol=normalized)
    volume = compute_volume_factor(materialized, window=volume_window, symbol=normalized)

    momentum_score = normalize_score(momentum.score, lower=-0.2, upper=0.2)
    raw_volatility_score = normalize_score(volatility.score, lower=0.0, upper=0.8)
    volatility_score = None if raw_volatility_score is None else 100.0 - raw_volatility_score
    volume_score = 50.0 if volume.score is not None else None
    combined = combine_factor_scores(
        {"momentum": momentum_score, "volatility": volatility_score, "volume": volume_score},
        {"momentum": 0.5, "volatility": 0.3, "volume": 0.2},
    )
    reasons = [item.reason for item in [momentum, volatility, volume] if item.reason]
    return ResearchScore(
        symbol=normalized,
        score=combined,
        eligible=combined is not None,
        reason="; ".join(reasons),
        factor_results=[momentum, volatility, volume],
        metrics={"momentum_score": momentum_score, "volatility_score": volatility_score, "volume_score": volume_score},
    )


def score_etf_universe(bars_by_symbol: Mapping[str, Iterable[MarketBar] | None]) -> list[ResearchScore]:
    """Score multiple ETF symbols from caller-provided bars."""

    return [score_symbol_from_bars(symbol, bars) for symbol, bars in (bars_by_symbol or {}).items()]
