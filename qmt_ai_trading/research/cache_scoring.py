"""Score ETF research signals from local cached bars only."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.symbols import normalize_symbol
from qmt_ai_trading.research.cache_reader import CachedResearchDataset, CachedResearchRequest, load_cached_research_dataset
from qmt_ai_trading.research.scoring import ResearchScore, score_symbol_from_bars
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate, build_candidates_from_research_scores


def score_symbols_from_cache(
    symbols: Iterable[str],
    start_date: str,
    end_date: str,
    *,
    frequency: str = "1d",
    cache_root: str | Path = "market_data",
    min_bars: int = 20,
    allow_partial: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[list[ResearchScore], CachedResearchDataset]:
    request = CachedResearchRequest(
        symbols=[normalize_symbol(str(item)) for item in symbols if str(item).strip()],
        start_date=str(start_date),
        end_date=str(end_date),
        frequency=frequency,
        cache_root=cache_root,
        min_bars=min_bars,
        allow_partial=allow_partial,
        metadata={"source": "cached_research", **dict(metadata or {})},
    )
    dataset = load_cached_research_dataset(request)
    scores: list[ResearchScore] = []
    for item in dataset.items:
        if item.success:
            score = score_symbol_from_bars(item.symbol, item.bars)
            score.metrics.update({"source": "cached_research", "bar_count": item.bar_count, "cache_message": item.message})
            scores.append(score)
        else:
            scores.append(ResearchScore(item.symbol, None, False, item.message, metrics={"source": "cached_research", "bar_count": item.bar_count}))
    return scores, dataset


def score_etf_universe_from_cache(
    *,
    universe_name: str = "default_etf",
    symbols: Iterable[str] | None = None,
    start_date: str,
    end_date: str,
    frequency: str = "1d",
    cache_root: str | Path = "market_data",
    min_bars: int = 20,
    allow_partial: bool = True,
) -> tuple[list[ResearchScore], CachedResearchDataset]:
    if symbols is None:
        if universe_name != "default_etf":
            # Stage 17 only has the built-in offline universe.
            symbols = []
        else:
            symbols = [item.symbol for item in get_default_etf_universe()]
    return score_symbols_from_cache(symbols, start_date, end_date, frequency=frequency, cache_root=cache_root, min_bars=min_bars, allow_partial=allow_partial, metadata={"universe_name": universe_name})


def build_candidates_from_cached_research(
    scores: Iterable[ResearchScore],
    *,
    dataset: CachedResearchDataset | None = None,
    target_percent: float | None = None,
    min_score: float | None = None,
) -> list[ETFCandidate]:
    candidates = build_candidates_from_research_scores(scores, target_percent=target_percent, min_score=min_score)
    bar_counts = {item.symbol: item.bar_count for item in (dataset.items if dataset else [])}
    for candidate in candidates:
        candidate.metrics["source"] = "cached_research"
        candidate.metrics["cached_research"] = True
        if candidate.symbol in bar_counts:
            candidate.metrics["bar_count"] = bar_counts[candidate.symbol]
    return candidates
