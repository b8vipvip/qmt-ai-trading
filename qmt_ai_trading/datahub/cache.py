"""Data Hub cache extension points.

Stage 5 intentionally avoids writing market data by default. These placeholders
keep cache paths under a local, ignored ``data/cache`` tree and can later be
implemented with parquet, duckdb, sqlite, or postgres backends.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol

_DEFAULT_CACHE_ROOT = Path("data") / "cache" / "datahub"


def get_cache_path(symbol: str, period: str = "1d", cache_root: str | Path | None = None) -> Path:
    """Return a non-sensitive default cache path without creating or writing it."""

    root = Path(cache_root) if cache_root is not None else _DEFAULT_CACHE_ROOT
    safe_symbol = normalize_symbol(symbol).replace(".", "_")
    safe_period = str(period or "1d").replace("/", "_").replace("\\", "_")
    return root / safe_symbol / f"{safe_period}.placeholder"


def load_cached_bars(symbol: str, period: str = "1d", cache_root: str | Path | None = None) -> list[MarketBar]:
    """Placeholder cache reader; returns an empty list until a backend is added."""

    get_cache_path(symbol, period, cache_root)
    return []


def save_cached_bars(
    symbol: str,
    bars: Iterable[MarketBar],
    period: str = "1d",
    cache_root: str | Path | None = None,
) -> Path:
    """Placeholder cache writer; validates the path but does not write data."""

    path = get_cache_path(symbol, period, cache_root)
    list(bars or [])
    return path
