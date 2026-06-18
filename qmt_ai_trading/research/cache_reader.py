"""Read-only cached historical bars for Research.

Stage 17 keeps research data access local and safe: this module only reads
``LocalBarStore`` files, never calls providers, QMT trading APIs, or order APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class CachedResearchRequest:
    symbols: list[str]
    start_date: str
    end_date: str
    frequency: str = "1d"
    cache_root: str | Path = "market_data"
    min_bars: int = 20
    allow_partial: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CachedResearchItem:
    symbol: str
    success: bool
    bar_count: int = 0
    bars: list[MarketBar] = field(default_factory=list)
    source: str = "cached_research"
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CachedResearchDataset:
    request: CachedResearchRequest
    items: list[CachedResearchItem] = field(default_factory=list)
    success: bool = False
    total_symbols: int = 0
    loaded_symbols: int = 0
    failed_symbols: int = 0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _request_from_args(
    symbols: Iterable[str],
    start_date: str,
    end_date: str,
    frequency: str = "1d",
    cache_root: str | Path = "market_data",
    min_bars: int = 20,
    allow_partial: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> CachedResearchRequest:
    return CachedResearchRequest(
        symbols=[normalize_symbol(str(item)) for item in symbols if str(item).strip()],
        start_date=str(start_date),
        end_date=str(end_date),
        frequency=str(frequency or "1d"),
        cache_root=cache_root,
        min_bars=max(0, int(min_bars or 0)),
        allow_partial=bool(allow_partial),
        metadata=dict(metadata or {}),
    )


def load_cached_bars_for_symbol(
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    frequency: str = "1d",
    cache_root: str | Path = "market_data",
    min_bars: int = 20,
    store: LocalBarStore | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CachedResearchItem:
    """Load one symbol from ``LocalBarStore`` without provider fallback."""

    normalized = normalize_symbol(symbol)
    local_store = store or LocalBarStore(cache_root)
    query = BarQuery(
        symbols=[normalized],
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        provider="local_cache_research",
        metadata={"read_only": True, **dict(metadata or {})},
    )
    try:
        result = local_store.query_bars(query)
        bars = list(result.bars or [])
        bar_count = len(bars)
        item_metadata = {
            "cache_root": str(cache_root),
            "frequency": frequency,
            "cache_hit": result.hit,
            "missing_ranges": result.missing_ranges,
            "source": "cached_research",
        }
        if not result.hit:
            return CachedResearchItem(normalized, False, 0, [], "cached_research", "cache miss; no provider fallback attempted", item_metadata)
        if bar_count < max(0, int(min_bars or 0)):
            return CachedResearchItem(normalized, False, bar_count, bars, "cached_research", f"insufficient bars: {bar_count} < {int(min_bars or 0)}", item_metadata)
        return CachedResearchItem(normalized, True, bar_count, bars, "cached_research", "cache hit", item_metadata)
    except Exception as exc:  # read boundary: convert failures to explainable item
        return CachedResearchItem(normalized, False, 0, [], "cached_research", f"cache read failed: {exc!r}", {"cache_root": str(cache_root), "source": "cached_research"})


def load_cached_research_dataset(request: CachedResearchRequest | None = None, **kwargs: Any) -> CachedResearchDataset:
    """Load a multi-symbol cached research dataset, allowing partial success."""

    if request is None:
        request = _request_from_args(**kwargs)
    request.symbols = [normalize_symbol(str(item)) for item in request.symbols if str(item).strip()]
    store = LocalBarStore(request.cache_root)
    items = [
        load_cached_bars_for_symbol(
            symbol,
            request.start_date,
            request.end_date,
            frequency=request.frequency,
            cache_root=request.cache_root,
            min_bars=request.min_bars,
            store=store,
            metadata=request.metadata,
        )
        for symbol in request.symbols
    ]
    loaded = sum(1 for item in items if item.success)
    failed = len(items) - loaded
    success = loaded == len(items) if not request.allow_partial else loaded > 0 or len(items) == 0
    if loaded == len(items):
        message = "all symbols loaded from cache"
    elif loaded > 0 and request.allow_partial:
        message = f"partial cached research success: loaded {loaded}, failed {failed}"
    elif not items:
        message = "no symbols requested"
    else:
        message = f"cached research unavailable: loaded {loaded}, failed {failed}"
    return CachedResearchDataset(request, items, success, len(items), loaded, failed, message, {"source": "cached_research", "cache_root": str(request.cache_root)})


def format_cached_research_dataset(dataset: CachedResearchDataset) -> str:
    lines = [
        "Cached Research Dataset",
        f"success={dataset.success} total={dataset.total_symbols} loaded={dataset.loaded_symbols} failed={dataset.failed_symbols}",
        f"range={dataset.request.start_date}..{dataset.request.end_date} frequency={dataset.request.frequency} cache_root={dataset.request.cache_root}",
        f"message={dataset.message}",
    ]
    for item in dataset.items:
        status = "OK" if item.success else "WARN"
        lines.append(f"- {status} {item.symbol}: bars={item.bar_count} source={item.source} message={item.message}")
    return "\n".join(lines)
