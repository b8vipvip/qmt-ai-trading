"""Dependency-light research factor utilities for Stage 6.

The functions in this module operate on already supplied Data Hub ``MarketBar``
objects. They do not fetch data, connect to QMT, or create orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import mean, pstdev
from typing import Any, Iterable

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class FactorValue:
    """Single factor observation for one symbol."""

    symbol: str
    name: str
    value: float | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactorResult:
    """Structured factor calculation result for one symbol."""

    symbol: str
    factors: list[FactorValue] = field(default_factory=list)
    score: float | None = None
    eligible: bool = True
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_bars(bars: Iterable[MarketBar] | None) -> list[MarketBar]:
    return [bar for bar in (bars or []) if bar is not None]


def _close_values(bars: Iterable[MarketBar] | None) -> list[float]:
    values: list[float] = []
    for bar in _clean_bars(bars):
        if bar.close is None:
            continue
        close = float(bar.close)
        if close > 0:
            values.append(close)
    return values


def _volume_values(bars: Iterable[MarketBar] | None) -> list[float]:
    values: list[float] = []
    for bar in _clean_bars(bars):
        if bar.volume is None:
            continue
        volume = float(bar.volume)
        if volume >= 0:
            values.append(volume)
    return values


def _symbol_from_bars(bars: Iterable[MarketBar] | None, fallback: str = "") -> str:
    for bar in _clean_bars(bars):
        if bar.symbol:
            return normalize_symbol(bar.symbol)
    return normalize_symbol(fallback) if fallback else ""


def compute_momentum_factor(
    bars: Iterable[MarketBar] | None,
    *,
    window: int = 20,
    symbol: str = "",
    factor_name: str = "momentum",
) -> FactorResult:
    """Compute close-to-close momentum over ``window`` bars."""

    closes = _close_values(bars)
    result_symbol = _symbol_from_bars(bars, symbol)
    if window <= 0:
        return FactorResult(result_symbol, eligible=False, reason="window must be positive")
    if len(closes) < window + 1:
        return FactorResult(result_symbol, eligible=False, reason=f"not enough close data for {window} bar momentum")
    start = closes[-window - 1]
    end = closes[-1]
    value = (end / start) - 1.0 if start > 0 else None
    factor = FactorValue(result_symbol, factor_name, value, metadata={"window": window, "start_close": start, "end_close": end})
    return FactorResult(result_symbol, factors=[factor], score=value, eligible=value is not None)


def compute_volatility_factor(
    bars: Iterable[MarketBar] | None,
    *,
    window: int = 20,
    annualization: float = 252.0,
    symbol: str = "",
    factor_name: str = "volatility",
) -> FactorResult:
    """Compute annualized close-return volatility."""

    closes = _close_values(bars)
    result_symbol = _symbol_from_bars(bars, symbol)
    if window <= 1:
        return FactorResult(result_symbol, eligible=False, reason="window must be greater than 1")
    if len(closes) < window + 1:
        return FactorResult(result_symbol, eligible=False, reason=f"not enough close data for {window} bar volatility")
    sample = closes[-window - 1 :]
    returns = [(sample[i] / sample[i - 1]) - 1.0 for i in range(1, len(sample)) if sample[i - 1] > 0]
    if len(returns) < 2:
        return FactorResult(result_symbol, eligible=False, reason="not enough return data for volatility")
    value = pstdev(returns) * sqrt(float(annualization))
    factor = FactorValue(result_symbol, factor_name, value, metadata={"window": window, "annualization": annualization})
    return FactorResult(result_symbol, factors=[factor], score=value, eligible=True)


def compute_volume_factor(
    bars: Iterable[MarketBar] | None,
    *,
    window: int = 20,
    symbol: str = "",
    factor_name: str = "volume",
) -> FactorResult:
    """Compute average volume over ``window`` bars."""

    volumes = _volume_values(bars)
    result_symbol = _symbol_from_bars(bars, symbol)
    if window <= 0:
        return FactorResult(result_symbol, eligible=False, reason="window must be positive")
    if len(volumes) < window:
        return FactorResult(result_symbol, eligible=False, reason=f"not enough volume data for {window} bar volume factor")
    value = mean(volumes[-window:])
    factor = FactorValue(result_symbol, factor_name, value, metadata={"window": window})
    return FactorResult(result_symbol, factors=[factor], score=value, eligible=True)


def compute_simple_score(
    factor_results: Iterable[FactorResult],
    *,
    weights: dict[str, float] | None = None,
) -> FactorResult:
    """Combine factor values into a simple weighted score."""

    results = list(factor_results or [])
    symbol = next((item.symbol for item in results if item.symbol), "")
    factors: list[FactorValue] = []
    total = 0.0
    total_weight = 0.0
    reasons: list[str] = []
    weights = weights or {}
    for result in results:
        factors.extend(result.factors)
        if result.reason:
            reasons.append(result.reason)
        for factor in result.factors:
            if factor.value is None:
                continue
            weight = float(weights.get(factor.name, 1.0))
            total += float(factor.value) * weight
            total_weight += abs(weight)
    if total_weight <= 0:
        return FactorResult(symbol, factors=factors, score=None, eligible=False, reason="no numeric factor values to score")
    return FactorResult(symbol, factors=factors, score=total / total_weight, eligible=True, reason="; ".join(reasons))


def rank_factor_results(results: Iterable[FactorResult], *, reverse: bool = True) -> list[FactorResult]:
    """Rank factor results by score, keeping missing scores last."""

    return sorted(list(results or []), key=lambda item: (item.score is not None, item.score if item.score is not None else 0.0), reverse=reverse)


def list_placeholder_factors() -> list[str]:
    """Return available lightweight factor names."""

    return ["momentum", "volatility", "volume"]


def calculate_factor_snapshot(symbols: Iterable[str]) -> dict[str, dict[str, float | None]]:
    """Return an empty factor snapshot shape without importing research engines."""

    return {symbol: {"score": None} for symbol in symbols}
