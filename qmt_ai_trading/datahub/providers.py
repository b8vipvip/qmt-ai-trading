"""Historical data provider abstractions for Data Hub."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Protocol

from qmt_ai_trading.datahub.local_store import BarCacheResult, BarQuery, LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


class HistoricalDataProvider(Protocol):
    name: str

    def get_bars(self, query: BarQuery) -> list[MarketBar]:
        """Return historical bars for the requested query."""


def _parse_day(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).split("T", 1)[0].split(" ", 1)[0])


class MockHistoricalDataProvider:
    """Deterministic mock provider for tests and local dry runs."""

    name = "mock"

    def get_bars(self, query: BarQuery) -> list[MarketBar]:
        start = _parse_day(query.start_date)
        end = _parse_day(query.end_date)
        bars: list[MarketBar] = []
        if end < start:
            return bars
        for symbol in query.symbols:
            normalized = normalize_symbol(symbol)
            seed = sum(ord(ch) for ch in normalized) % 100
            current = start
            index = 0
            while current <= end:
                price = round(10 + seed / 10 + index * 0.05, 4)
                bars.append(MarketBar(symbol=normalized, datetime=current.isoformat(), open=price, high=round(price + 0.2, 4), low=round(price - 0.2, 4), close=round(price + 0.05, 4), volume=1000 + index, amount=round((1000 + index) * price, 4), source=self.name))
                current += timedelta(days=1)
                index += 1
        return bars


def create_historical_provider(provider: str | HistoricalDataProvider = "mock", **kwargs: Any) -> HistoricalDataProvider:
    """Create a historical data provider by name without importing optional QMT eagerly."""

    if not isinstance(provider, str):
        return provider
    normalized = provider.lower().strip()
    if normalized == "mock":
        return MockHistoricalDataProvider()
    if normalized == "qmt":
        from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider

        return QmtHistoricalDataProvider(**kwargs)
    raise ValueError(f"unsupported historical provider: {provider}")


def fetch_historical_bars(query: BarQuery, store: LocalBarStore | None = None, provider: HistoricalDataProvider | str | None = None, **provider_kwargs: Any) -> BarCacheResult:
    """Fetch historical bars with local-cache-first behavior."""

    store = store or LocalBarStore()
    provider = create_historical_provider(provider or query.provider or "mock", **provider_kwargs)
    cached = store.query_bars(query)
    if cached.hit:
        cached.message = "cache hit"
        return cached

    fetch = getattr(provider, "fetch_bars", None) or getattr(provider, "get_bars")
    fetched = fetch(query)
    metadata = []
    for symbol in query.symbols:
        symbol_bars = [bar for bar in fetched if normalize_symbol(bar.symbol) == normalize_symbol(symbol)]
        metadata.append(store.save_bars(symbol, query.frequency, symbol_bars, provider=getattr(provider, "name", query.provider)))
    bars = store.load_bars(query)
    return BarCacheResult(query=query, hit=False, missing_ranges=cached.missing_ranges, bars=bars, metadata=metadata, message="cache miss; fetched from provider and saved")
