"""Cached Research driven ETF rotation signals.

Stage 18 connects read-only cached research factor scores to the ETF rotation
Strategy Engine. This module never downloads data, never calls QMT/xttrader, and
only emits dry-run TradeIntent objects for downstream Risk Gate validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.datahub.symbols import normalize_symbol
from qmt_ai_trading.research.cache_reader import CachedResearchDataset
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate, LOT_SIZE, _buy_quantity


@dataclass
class CachedETFSignalConfig:
    top_n: int = 1
    max_position_pct: float | None = None
    min_score: float | None = None
    min_bars: int = 20
    momentum_weight: float = 0.5
    volatility_weight: float = 0.3
    volume_weight: float = 0.2
    prefer_low_volatility: bool = True
    source: str = "cached_etf_rotation"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CachedETFSignalResult:
    candidates: list[ETFCandidate] = field(default_factory=list)
    selected_candidates: list[ETFCandidate] = field(default_factory=list)
    trade_intents: list[TradeIntent] = field(default_factory=list)
    skipped_symbols: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _config(config: CachedETFSignalConfig | None = None, **overrides: Any) -> CachedETFSignalConfig:
    cfg = config or CachedETFSignalConfig()
    for key, value in overrides.items():
        if value is not None and hasattr(cfg, key):
            setattr(cfg, key, value)
    if cfg.max_position_pct is None:
        cfg.max_position_pct = get_settings().max_position_pct
    return cfg


def _metric(metrics: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in metrics:
            return metrics[name]
    factors = metrics.get("factor_values")
    if isinstance(factors, Mapping):
        for name in names:
            if name in factors:
                return factors[name]
    return None


def _factor_adjusted_score(raw_score: float, metrics: Mapping[str, Any], cfg: CachedETFSignalConfig) -> float:
    momentum = _metric(metrics, "momentum_score", "momentum")
    volatility = _metric(metrics, "volatility_score", "volatility")
    volume = _metric(metrics, "volume_score", "volume_factor")
    parts: list[tuple[float, float]] = []
    if momentum is not None:
        parts.append((float(momentum), cfg.momentum_weight))
    if volatility is not None:
        vol_value = float(volatility)
        if cfg.prefer_low_volatility and "volatility_score" not in metrics:
            vol_value = max(0.0, 100.0 - min(100.0, vol_value * 100.0 if vol_value <= 1.0 else vol_value))
        parts.append((vol_value, cfg.volatility_weight))
    if volume is not None:
        parts.append((float(volume), cfg.volume_weight))
    total_weight = sum(abs(weight) for _, weight in parts)
    if total_weight <= 0:
        return float(raw_score)
    factor_score = sum(value * weight for value, weight in parts) / total_weight
    return (float(raw_score) + factor_score) / 2.0


def normalize_cached_research_scores(items: Iterable[Any] | CachedResearchDataset | None) -> list[Any]:
    if items is None:
        return []
    if isinstance(items, CachedResearchDataset):
        from qmt_ai_trading.research.cache_scoring import score_symbols_from_cache

        scores, _ = score_symbols_from_cache(
            items.request.symbols,
            items.request.start_date,
            items.request.end_date,
            frequency=items.request.frequency,
            cache_root=items.request.cache_root,
            min_bars=items.request.min_bars,
            allow_partial=items.request.allow_partial,
        )
        return scores
    return list(items or [])


def build_cached_etf_candidates(items: Iterable[Any] | CachedResearchDataset | None, config: CachedETFSignalConfig | None = None, **overrides: Any) -> tuple[list[ETFCandidate], list[dict[str, Any]]]:
    cfg = _config(config, **overrides)
    candidates: list[ETFCandidate] = []
    skipped: list[dict[str, Any]] = []
    for item in normalize_cached_research_scores(items):
        if isinstance(item, ETFCandidate):
            candidate = item
            metrics = candidate.metrics
            raw_score = candidate.score
        else:
            symbol = normalize_symbol(str(getattr(item, "symbol", "")))
            metrics = dict(getattr(item, "metrics", {}) or {})
            raw_score_obj = getattr(item, "score", None)
            raw_score = float(raw_score_obj) if raw_score_obj is not None else 0.0
            candidate = ETFCandidate(symbol=symbol, score=raw_score, eligible=bool(getattr(item, "eligible", True)), reason=str(getattr(item, "reason", "") or ""), metrics=metrics)
        candidate.symbol = normalize_symbol(candidate.symbol)
        bar_count = int(_metric(candidate.metrics, "bar_count") or 0)
        if bar_count < int(cfg.min_bars or 0):
            candidate.eligible = False
            missing = int(cfg.min_bars or 0) - bar_count
            candidate.reason = candidate.reason or f"insufficient cached bars: missing {missing} bars ({bar_count} < {cfg.min_bars})"
        candidate.score = _factor_adjusted_score(float(candidate.score or 0.0), candidate.metrics, cfg)
        candidate.target_percent = min(float(candidate.target_percent if candidate.target_percent is not None else cfg.max_position_pct or 0.0), float(cfg.max_position_pct or 0.0), get_settings().max_position_pct)
        candidate.metrics.update({"source": "cached_etf_rotation", "cached_research_source": candidate.metrics.get("source", "cached_research"), "bar_count": bar_count})
        if cfg.min_score is not None and candidate.score < float(cfg.min_score):
            candidate.eligible = False
            candidate.reason = candidate.reason or f"cached factor score below min_score {float(cfg.min_score):.2f}"
        if not candidate.eligible or not candidate.symbol:
            skipped.append({"symbol": candidate.symbol, "reason": candidate.reason or "not eligible", "bar_count": bar_count})
        candidates.append(candidate)
    return candidates, skipped


def select_cached_etf_candidates(candidates: Iterable[ETFCandidate], config: CachedETFSignalConfig | None = None, **overrides: Any) -> list[ETFCandidate]:
    cfg = _config(config, **overrides)
    eligible = [item for item in candidates if item.eligible and item.symbol and (cfg.min_score is None or item.score >= float(cfg.min_score))]
    eligible.sort(key=lambda item: item.score, reverse=True)
    return eligible[: max(1, int(cfg.top_n or 1))]


def generate_cached_etf_rotation_intents(candidates: Iterable[ETFCandidate], config: CachedETFSignalConfig | None = None, *, capital: float | None = None, **overrides: Any) -> list[TradeIntent]:
    cfg = _config(config, **overrides)
    intents: list[TradeIntent] = []
    for candidate in select_cached_etf_candidates(candidates, cfg):
        target = min(float(candidate.target_percent if candidate.target_percent is not None else cfg.max_position_pct or 0.0), float(cfg.max_position_pct or 0.0), get_settings().max_position_pct)
        qty = _buy_quantity(candidate, target, capital)
        qty = max(LOT_SIZE, (int(qty) // LOT_SIZE) * LOT_SIZE)
        intents.append(TradeIntent(candidate.symbol, "BUY", qty, target, reason=f"cached factor score selected; {candidate.symbol} score={candidate.score:.2f}", source=cfg.source, dry_run=True))
    return intents


def generate_cached_etf_rotation_signal(items: Iterable[Any] | CachedResearchDataset | None, config: CachedETFSignalConfig | None = None, *, capital: float | None = None, **overrides: Any) -> CachedETFSignalResult:
    cfg = _config(config, **overrides)
    candidates, skipped = build_cached_etf_candidates(items, cfg)
    selected = select_cached_etf_candidates(candidates, cfg)
    intents = generate_cached_etf_rotation_intents(selected, cfg, capital=capital)
    message = "selected cached ETF candidates by cached factor score" if intents else "no eligible candidates from cached research"
    return CachedETFSignalResult(candidates, selected, intents, skipped, message, {"source": cfg.source, "top_n": cfg.top_n, "min_bars": cfg.min_bars, "min_score": cfg.min_score})
