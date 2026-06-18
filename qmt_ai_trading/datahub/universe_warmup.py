"""ETF universe historical cache warmup helpers.

This module expands the stage 15 cache warmup flow from explicit symbols to a
resolved ETF universe. It only touches historical bar cache/provider APIs and
never imports xttrader or trading/account/order interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from qmt_ai_trading.datahub.cache_warmup import CacheWarmupResult, build_default_warmup_request, warmup_history_cache
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class UniverseWarmupRequest:
    universe_name: str = "default_etf"
    symbols: list[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    lookback_days: int | None = None
    lookback_years: int | None = None
    frequency: str = "1d"
    provider: str = "mock"
    cache_root: str | Path = "market_data"
    adjust: str | None = None
    fail_fast: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UniverseWarmupResult:
    success: bool
    universe_name: str
    symbol_count: int
    start_date: str
    end_date: str
    frequency: str
    provider: str
    cache_root: str
    warmup_result: CacheWarmupResult
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _split_symbols(symbols: Iterable[str] | str | None) -> list[str]:
    if symbols is None:
        return []
    if isinstance(symbols, str):
        raw = symbols.split(",")
    else:
        raw = list(symbols)
    result: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            result.append(normalize_symbol(text))
    return list(dict.fromkeys(result))


def _parse_day(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).split("T", 1)[0].split(" ", 1)[0])


def resolve_universe_symbols(universe_name: str = "default_etf", symbols: Iterable[str] | str | None = None) -> list[str]:
    """Resolve ETF universe symbols, with explicit symbols taking precedence."""

    explicit = _split_symbols(symbols)
    if explicit:
        return explicit
    normalized_name = str(universe_name or "default_etf").strip().lower()
    if normalized_name != "default_etf":
        raise ValueError(f"unsupported universe_name: {universe_name}")
    return [item.symbol for item in get_default_etf_universe()]


def resolve_warmup_date_range(
    start_date: str | date | datetime | None = None,
    end_date: str | date | datetime | None = None,
    lookback_days: int | None = None,
    lookback_years: int | None = None,
    today: str | date | datetime | None = None,
) -> tuple[str, str]:
    """Resolve start/end dates from explicit dates or lookback settings."""

    end = _parse_day(end_date or today or date.today())
    if start_date:
        start = _parse_day(start_date)
    elif lookback_days is not None:
        start = end - timedelta(days=max(int(lookback_days), 0))
    elif lookback_years is not None:
        start = end - timedelta(days=max(int(lookback_years), 0) * 365)
    else:
        start = end
    if start > end:
        raise ValueError(f"start_date {start.isoformat()} cannot be after end_date {end.isoformat()}")
    return start.isoformat(), end.isoformat()


def build_universe_warmup_request(
    *,
    universe_name: str = "default_etf",
    symbols: Iterable[str] | str | None = None,
    start_date: str | date | datetime | None = None,
    end_date: str | date | datetime | None = None,
    lookback_days: int | None = None,
    lookback_years: int | None = None,
    frequency: str = "1d",
    provider: str = "mock",
    cache_root: str | Path = "market_data",
    adjust: str | None = None,
    fail_fast: bool = False,
    metadata: dict[str, Any] | None = None,
) -> UniverseWarmupRequest:
    resolved_start, resolved_end = resolve_warmup_date_range(start_date, end_date, lookback_days, lookback_years)
    resolved_symbols = resolve_universe_symbols(universe_name=universe_name, symbols=symbols)
    return UniverseWarmupRequest(
        universe_name=str(universe_name or "default_etf"),
        symbols=resolved_symbols,
        start_date=resolved_start,
        end_date=resolved_end,
        lookback_days=lookback_days,
        lookback_years=lookback_years,
        frequency=str(frequency or "1d"),
        provider=str(provider or "mock").lower().strip(),
        cache_root=cache_root,
        adjust=adjust,
        fail_fast=fail_fast,
        metadata=dict(metadata or {}),
    )


def warmup_etf_universe_history(request: UniverseWarmupRequest | None = None, **kwargs: Any) -> UniverseWarmupResult:
    """Warm local historical cache for an ETF universe.

    Per-symbol isolation and QMT/xtquant graceful behavior are delegated to the
    stage 15 ``warmup_history_cache`` implementation.
    """

    req = request or build_universe_warmup_request(**kwargs)
    cache_req = build_default_warmup_request(
        symbols=req.symbols,
        start_date=req.start_date,
        end_date=req.end_date,
        frequency=req.frequency,
        provider=req.provider,
        cache_root=req.cache_root,
        adjust=req.adjust,
        fail_fast=req.fail_fast,
        metadata={**req.metadata, "universe_name": req.universe_name},
    )
    warmup = warmup_history_cache(cache_req)
    message = f"universe warmup completed: universe={req.universe_name}, symbols={len(req.symbols)}, {warmup.message}"
    return UniverseWarmupResult(
        success=warmup.success,
        universe_name=req.universe_name,
        symbol_count=len(req.symbols),
        start_date=req.start_date,
        end_date=req.end_date,
        frequency=req.frequency,
        provider=req.provider,
        cache_root=str(req.cache_root),
        warmup_result=warmup,
        message=message,
        metadata={"lookback_days": req.lookback_days, "lookback_years": req.lookback_years, **req.metadata},
    )


def format_universe_warmup_result(result: UniverseWarmupResult) -> str:
    warmup = result.warmup_result
    lines = [
        "Universe warmup summary",
        f"universe={result.universe_name} provider={result.provider} cache_root={result.cache_root} range={result.start_date}..{result.end_date} frequency={result.frequency}",
        f"symbol_count={result.symbol_count} hits={warmup.hit_count} misses={warmup.miss_count} fetched={warmup.fetched_count} failed={warmup.failed_count} skipped={warmup.skipped_count} success={result.success}",
        result.message,
    ]
    for item in warmup.items:
        status = "hit" if item.hit else "fetched" if item.success else "skipped" if item.metadata.get("skipped") else "failed"
        lines.append(f"- {item.symbol}: {status}; rows={item.row_count}; message={item.message}")
    return "\n".join(lines)
