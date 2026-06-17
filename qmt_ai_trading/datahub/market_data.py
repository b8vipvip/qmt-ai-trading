"""Unified read-only market data entry points for Data Hub."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from qmt_ai_trading.datahub.models import LatestPrice, MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol

SOURCE_QMT = "qmt_market_adapter"


def _call_qmt_market(name: str, *args: Any, **kwargs: Any) -> Any:
    """Call the safe gateway adapter lazily and swallow unavailable-QMT errors."""

    try:
        from qmt_ai_trading.gateway import qmt_market

        func = getattr(qmt_market, name)
        return func(*args, **kwargs)
    except Exception:
        return None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_latest_price(raw: Any, symbol: str) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float, str)):
        return _to_float(raw)
    if isinstance(raw, Mapping):
        for key in ("price", "lastPrice", "last_price", "close"):
            value = raw.get(key)
            if isinstance(value, Mapping):
                value = value.get(symbol) or value.get(normalize_symbol(symbol))
            price = _to_float(value[-1] if isinstance(value, (list, tuple)) and value else value)
            if price is not None:
                return price
        if symbol in raw:
            return _extract_latest_price(raw[symbol], symbol)
    return None


def get_latest_price(symbol: str) -> LatestPrice | None:
    """Return latest price from the gateway adapter, or ``None`` when unavailable."""

    normalized = normalize_symbol(symbol)
    raw = _call_qmt_market("get_latest_price", normalized)
    price = _extract_latest_price(raw, normalized)
    if price is None:
        return None
    return LatestPrice(symbol=normalized, price=price, datetime=datetime.now(timezone.utc), source=SOURCE_QMT)


def _bar_from_mapping(symbol: str, row: Mapping[str, Any]) -> MarketBar:
    return MarketBar(
        symbol=symbol,
        datetime=row.get("datetime") or row.get("time") or row.get("date"),
        open=_to_float(row.get("open")),
        high=_to_float(row.get("high")),
        low=_to_float(row.get("low")),
        close=_to_float(row.get("close")),
        volume=_to_float(row.get("volume")),
        amount=_to_float(row.get("amount")),
        source=SOURCE_QMT,
    )


def _extract_bars(raw: Any, symbol: str) -> list[MarketBar]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [_bar_from_mapping(symbol, item) for item in raw if isinstance(item, Mapping)]
    if isinstance(raw, Mapping):
        rows = raw.get(symbol) or raw.get(normalize_symbol(symbol)) or raw.get("bars")
        if isinstance(rows, list):
            return [_bar_from_mapping(symbol, item) for item in rows if isinstance(item, Mapping)]
    return []


def get_bars(symbol: str, period: str = "1d", count: int = 100) -> list[MarketBar]:
    """Return recent bars via QMT gateway adapter; empty list when unavailable."""

    normalized = normalize_symbol(symbol)
    raw = _call_qmt_market("get_bars", normalized, period=period, count=count)
    return _extract_bars(raw, normalized)


def get_market_snapshot(symbol: str) -> dict[str, Any]:
    """Return a basic Data Hub snapshot dictionary for backward compatibility."""

    normalized = normalize_symbol(symbol)
    return {
        "symbol": normalized,
        "latest_price": get_latest_price(normalized),
        "bars": get_bars(normalized),
        "source": SOURCE_QMT,
    }
