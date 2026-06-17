"""Historical cache warmup helpers for the scheduled dry-run pipeline.

This module only works with historical bar cache/provider APIs. It does not
import or call xttrader, order, account, position, or trade interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.providers import fetch_historical_bars
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class CacheWarmupRequest:
    symbols: list[str]
    start_date: str
    end_date: str
    frequency: str = "1d"
    provider: str = "mock"
    cache_root: str | Path = "market_data"
    adjust: str | None = None
    fail_fast: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheWarmupItemResult:
    symbol: str
    hit: bool
    success: bool
    row_count: int
    missing_ranges: list[tuple[str, str]] = field(default_factory=list)
    cache_paths: list[str] = field(default_factory=list)
    provider: str = "mock"
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheWarmupResult:
    success: bool
    provider: str
    cache_root: str
    start_date: str
    end_date: str
    frequency: str
    total_symbols: int
    hit_count: int
    miss_count: int
    fetched_count: int
    failed_count: int
    skipped_count: int
    items: list[CacheWarmupItemResult] = field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def build_default_warmup_request(
    *,
    symbols: list[str] | tuple[str, ...] | None = None,
    start_date: str,
    end_date: str,
    frequency: str = "1d",
    provider: str = "mock",
    cache_root: str | Path = "market_data",
    adjust: str | None = None,
    fail_fast: bool = False,
    metadata: dict[str, Any] | None = None,
) -> CacheWarmupRequest:
    normalized_symbols = [normalize_symbol(item) for item in (symbols or []) if str(item).strip()]
    return CacheWarmupRequest(
        symbols=normalized_symbols,
        start_date=str(start_date),
        end_date=str(end_date),
        frequency=str(frequency),
        provider=str(provider or "mock").lower().strip(),
        cache_root=cache_root,
        adjust=adjust,
        fail_fast=fail_fast,
        metadata=dict(metadata or {}),
    )


def warmup_history_cache(request: CacheWarmupRequest) -> CacheWarmupResult:
    """Warm historical bar cache one symbol at a time.

    Cache hits are not fetched again. Cache misses call ``fetch_historical_bars``,
    which writes through ``LocalBarStore``. Per-symbol failures are isolated
    unless ``request.fail_fast`` is true.
    """

    store = LocalBarStore(request.cache_root)
    items: list[CacheWarmupItemResult] = []
    aborted = False
    for symbol in request.symbols:
        normalized = normalize_symbol(symbol)
        query = BarQuery(
            symbols=[normalized],
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            adjust=request.adjust,
            provider=request.provider,
            metadata=dict(request.metadata),
        )
        cached = store.query_bars(query)
        if cached.hit:
            items.append(
                CacheWarmupItemResult(
                    symbol=normalized,
                    hit=True,
                    success=True,
                    row_count=len(cached.bars),
                    missing_ranges=[],
                    cache_paths=[m.path for m in cached.metadata if m.path],
                    provider=request.provider,
                    message="cache hit",
                )
            )
            continue
        try:
            fetched = fetch_historical_bars(query, store=store, provider=request.provider)
            paths = [m.path for m in fetched.metadata if m.path]
            row_count = len([bar for bar in fetched.bars if normalize_symbol(bar.symbol) == normalized])
            success = row_count > 0 or store.has_coverage(query)
            items.append(
                CacheWarmupItemResult(
                    symbol=normalized,
                    hit=False,
                    success=success,
                    row_count=row_count,
                    missing_ranges=list(fetched.missing_ranges),
                    cache_paths=paths,
                    provider=request.provider,
                    message=fetched.message or ("fetched" if success else "no bars fetched"),
                )
            )
        except Exception as exc:  # noqa: BLE001 - convert provider errors into scheduler-safe result items
            message = str(exc)
            skipped = request.provider.lower() == "qmt" and "xtquant" in message.lower()
            items.append(
                CacheWarmupItemResult(
                    symbol=normalized,
                    hit=False,
                    success=False,
                    row_count=0,
                    missing_ranges=list(cached.missing_ranges),
                    provider=request.provider,
                    message=("skipped: " if skipped else "failed: ") + message,
                    metadata={"skipped": skipped, "exception_type": type(exc).__name__},
                )
            )
            if request.fail_fast:
                aborted = True
                break

    hit_count = sum(1 for item in items if item.hit)
    failed_count = sum(1 for item in items if not item.success and not item.metadata.get("skipped"))
    skipped_count = sum(1 for item in items if item.metadata.get("skipped"))
    fetched_count = sum(1 for item in items if not item.hit and item.success)
    miss_count = sum(1 for item in items if not item.hit)
    success = failed_count == 0 and (not request.fail_fast or not aborted)
    if skipped_count and request.provider.lower() == "qmt":
        success = success and failed_count == 0
    message = f"cache warmup completed: hits={hit_count}, fetched={fetched_count}, failed={failed_count}, skipped={skipped_count}"
    if aborted:
        message += "; aborted by fail_fast"
    return CacheWarmupResult(
        success=success,
        provider=request.provider,
        cache_root=str(request.cache_root),
        start_date=request.start_date,
        end_date=request.end_date,
        frequency=request.frequency,
        total_symbols=len(request.symbols),
        hit_count=hit_count,
        miss_count=miss_count,
        fetched_count=fetched_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        items=items,
        message=message,
        metadata={"aborted": aborted},
    )


def format_cache_warmup_result(result: CacheWarmupResult) -> str:
    lines = [
        "Cache warmup summary",
        f"provider={result.provider} cache_root={result.cache_root} range={result.start_date}..{result.end_date} frequency={result.frequency}",
        f"symbols={result.total_symbols} hits={result.hit_count} misses={result.miss_count} fetched={result.fetched_count} failed={result.failed_count} skipped={result.skipped_count} success={result.success}",
        result.message,
    ]
    for item in result.items:
        status = "hit" if item.hit else "fetched" if item.success else "skipped" if item.metadata.get("skipped") else "failed"
        lines.append(f"- {item.symbol}: {status}; rows={item.row_count}; message={item.message}")
    return "\n".join(lines)
