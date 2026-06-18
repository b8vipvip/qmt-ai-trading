"""Pipeline data source policy and read-only cache decision helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.symbols import normalize_symbol
from qmt_ai_trading.research.cache_reader import CachedResearchDataset, CachedResearchRequest, load_cached_research_dataset
from qmt_ai_trading.research.cache_scoring import score_symbols_from_cache
from qmt_ai_trading.strategies.cached_etf_rotation import CachedETFSignalConfig, generate_cached_etf_rotation_signal

MODES = {"legacy", "cached", "auto", "mock"}
CONFIDENCE_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
MOCK_FALLBACK_WARNING = "mock/fallback data is for dry-run validation only and should not be used for live trading decisions."


@dataclass
class PipelineDataSourcePolicy:
    mode: str = "legacy"
    preferred_source: str = "cached_research"
    allow_mock_fallback: bool = False
    min_coverage_ratio: float = 0.8
    min_loaded_symbols: int = 1
    require_cached_research: bool = False
    warmup_before_research: bool = False
    provider: str = "mock"
    cache_root: str | Path = "market_data"
    start_date: str | None = None
    end_date: str | None = None
    frequency: str = "1d"
    min_bars: int = 20
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineDataSourceDecision:
    selected_source: str = "legacy_default"
    requested_source: str = "legacy_default"
    fallback_used: bool = False
    fallback_reason: str = ""
    coverage_ratio: float = 0.0
    loaded_symbols: int = 0
    total_symbols: int = 0
    hit_count: int = 0
    miss_count: int = 0
    fetched_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    confidence: str = "LOW"
    allow_trade_intents: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineDataSourceResult:
    policy: PipelineDataSourcePolicy
    decision: PipelineDataSourceDecision
    warmup_result: Any = None
    cached_dataset: CachedResearchDataset | None = None
    research_scores: list[Any] = field(default_factory=list)
    candidates: list[Any] = field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _symbols(symbols: Iterable[str] | None = None) -> list[str]:
    if symbols is None:
        symbols = [item.symbol for item in get_default_etf_universe()]
    return [normalize_symbol(str(item)) for item in symbols if str(item).strip()]


def _dates(policy: PipelineDataSourcePolicy) -> tuple[str, str]:
    end = policy.end_date or date.today().isoformat()
    start = policy.start_date or (date.fromisoformat(str(end)) - timedelta(days=max(30, int(policy.min_bars or 20) * 2))).isoformat()
    return start, end


def build_data_source_policy(**kwargs: Any) -> PipelineDataSourcePolicy:
    mode = str(kwargs.pop("mode", kwargs.pop("data_source_mode", "legacy")) or "legacy").lower()
    if mode not in MODES:
        raise ValueError(f"unsupported data_source_mode: {mode}")
    policy = PipelineDataSourcePolicy(mode=mode, **kwargs)
    policy.min_coverage_ratio = max(0.0, min(1.0, float(policy.min_coverage_ratio)))
    policy.min_loaded_symbols = max(0, int(policy.min_loaded_symbols or 0))
    policy.min_bars = max(0, int(policy.min_bars or 0))
    return policy


def evaluate_cache_coverage(policy: PipelineDataSourcePolicy, symbols: Iterable[str] | None = None) -> tuple[PipelineDataSourceDecision, CachedResearchDataset]:
    start, end = _dates(policy)
    requested = _symbols(symbols)
    request = CachedResearchRequest(requested, start, end, frequency=policy.frequency, cache_root=policy.cache_root, min_bars=policy.min_bars, allow_partial=True, metadata={"stage": "stage19_data_source", **policy.metadata})
    dataset = load_cached_research_dataset(request)
    total = dataset.total_symbols
    loaded = dataset.loaded_symbols
    coverage = (loaded / total) if total else 1.0
    hit = loaded
    failed = dataset.failed_symbols
    decision = PipelineDataSourceDecision(
        selected_source="unavailable",
        requested_source=policy.preferred_source,
        coverage_ratio=coverage,
        loaded_symbols=loaded,
        total_symbols=total,
        hit_count=hit,
        miss_count=failed,
        failed_count=failed,
        confidence="HIGH" if total and coverage >= policy.min_coverage_ratio and loaded >= policy.min_loaded_symbols else ("MEDIUM" if loaded > 0 else "LOW"),
        allow_trade_intents=False,
        message=dataset.message,
        metadata={"cache_root": str(policy.cache_root), "start_date": start, "end_date": end, "frequency": policy.frequency, "min_bars": policy.min_bars},
    )
    return decision, dataset


def choose_pipeline_data_source(policy: PipelineDataSourcePolicy, symbols: Iterable[str] | None = None) -> PipelineDataSourceDecision:
    policy = build_data_source_policy(**policy.__dict__)
    if policy.mode == "legacy":
        return PipelineDataSourceDecision("legacy_default", "legacy_default", confidence="MEDIUM", allow_trade_intents=True, message="legacy default dry-run data source selected", metadata={"mode": "legacy"})
    if policy.mode == "mock":
        return PipelineDataSourceDecision("mock_fallback", "mock_fallback", True, "explicit mock mode", confidence="LOW", allow_trade_intents=True, message=f"explicit mock/default dry-run data source selected; {MOCK_FALLBACK_WARNING}", metadata={"mode": "mock"})
    coverage, _dataset = evaluate_cache_coverage(policy, symbols)
    enough = coverage.coverage_ratio >= policy.min_coverage_ratio and coverage.loaded_symbols >= policy.min_loaded_symbols
    if enough:
        coverage.selected_source = "cached_research"
        coverage.allow_trade_intents = True
        coverage.message = f"cached_research selected: coverage={coverage.coverage_ratio:.2%}, loaded={coverage.loaded_symbols}/{coverage.total_symbols}"
        return coverage
    if policy.mode == "auto" and policy.allow_mock_fallback:
        coverage.selected_source = "mock_fallback"
        coverage.fallback_used = True
        coverage.fallback_reason = f"cache coverage below threshold: {coverage.coverage_ratio:.2%} < {policy.min_coverage_ratio:.2%} or loaded {coverage.loaded_symbols} < {policy.min_loaded_symbols}"
        coverage.confidence = "LOW"
        coverage.allow_trade_intents = True
        coverage.message = f"mock fallback selected because cached research is insufficient; {MOCK_FALLBACK_WARNING}"
        return coverage
    coverage.selected_source = "unavailable"
    coverage.confidence = "LOW"
    coverage.allow_trade_intents = False
    coverage.message = f"cached research unavailable or insufficient: coverage={coverage.coverage_ratio:.2%}, loaded={coverage.loaded_symbols}/{coverage.total_symbols}; no fallback enabled"
    return coverage


def load_pipeline_research_data(policy: PipelineDataSourcePolicy, symbols: Iterable[str] | None = None, *, top_n: int = 1, min_score: float | None = None, cached_strategy_min_bars: int | None = None, capital: float | None = None) -> PipelineDataSourceResult:
    decision = choose_pipeline_data_source(policy, symbols)
    dataset = None
    scores: list[Any] = []
    candidates: list[Any] = []
    if decision.selected_source == "cached_research":
        start, end = _dates(policy)
        scores, dataset = score_symbols_from_cache(_symbols(symbols), start, end, frequency=policy.frequency, cache_root=policy.cache_root, min_bars=policy.min_bars, allow_partial=True)
        signal = generate_cached_etf_rotation_signal(scores, CachedETFSignalConfig(top_n=top_n, min_score=min_score, min_bars=cached_strategy_min_bars or policy.min_bars), capital=capital)
        candidates = signal.candidates
        decision.metadata.update({"selected_candidates": len(signal.selected_candidates), "skipped": signal.skipped_symbols, "signal_message": signal.message})
    return PipelineDataSourceResult(policy, decision, None, dataset, scores, candidates, decision.message, {"source": decision.selected_source})


def format_data_source_decision(decision: PipelineDataSourceDecision) -> str:
    lines = [
        "Data Source Decision",
        f"selected_source={decision.selected_source}",
        f"coverage_ratio={decision.coverage_ratio:.4f}",
        f"loaded_symbols={decision.loaded_symbols}/{decision.total_symbols}",
        f"hit={decision.hit_count} miss={decision.miss_count} fetched={decision.fetched_count} skipped={decision.skipped_count} failed={decision.failed_count}",
        f"confidence={decision.confidence}",
        f"fallback_used={decision.fallback_used}",
        f"allow_trade_intents={decision.allow_trade_intents}",
        f"message={decision.message}",
    ]
    if decision.fallback_used or decision.selected_source == "mock_fallback":
        lines.append(MOCK_FALLBACK_WARNING)
    return "\n".join(lines)
