"""Lightweight gateway models for normalizing QMT query payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _read_value(raw: Any, *names: str, default: Any = None) -> Any:
    """Read a value from a dict-like or object-like QMT payload."""

    if isinstance(raw, Mapping):
        for name in names:
            if name in raw:
                return raw[name]
    for name in names:
        if hasattr(raw, name):
            return getattr(raw, name)
    return default


def _raw_dict(raw: Any) -> dict[str, Any]:
    """Best-effort conversion of a QMT object to a serializable-ish dict."""

    if raw is None:
        return {}
    if isinstance(raw, Mapping):
        return dict(raw)
    if hasattr(raw, "__dict__"):
        return dict(vars(raw))
    return {"value": raw}


@dataclass(slots=True)
class QmtAsset:
    cash: float = 0.0
    market_value: float = 0.0
    total_asset: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QmtPosition:
    symbol: str = ""
    volume: int = 0
    available_volume: int = 0
    market_value: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QmtOrder:
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    volume: int = 0
    price: float = 0.0
    status: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QmtTrade:
    trade_id: str = ""
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    volume: int = 0
    price: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


def asset_from_raw(raw: Any) -> QmtAsset:
    """Convert a QMT asset payload into a lightweight model."""

    return QmtAsset(
        cash=float(_read_value(raw, "cash", "cash_available", "available_cash", default=0.0) or 0.0),
        market_value=float(_read_value(raw, "market_value", "stock_market_value", default=0.0) or 0.0),
        total_asset=float(_read_value(raw, "total_asset", "total_asset_value", default=0.0) or 0.0),
        raw=_raw_dict(raw),
    )


def position_from_raw(raw: Any) -> QmtPosition:
    """Convert a QMT position payload into a lightweight model."""

    return QmtPosition(
        symbol=str(_read_value(raw, "stock_code", "symbol", "code", default="") or ""),
        volume=int(_read_value(raw, "volume", "m_nVolume", default=0) or 0),
        available_volume=int(_read_value(raw, "available_volume", "can_use_volume", default=0) or 0),
        market_value=float(_read_value(raw, "market_value", default=0.0) or 0.0),
        raw=_raw_dict(raw),
    )


def order_from_raw(raw: Any) -> QmtOrder:
    """Convert a QMT order payload into a lightweight model."""

    return QmtOrder(
        order_id=str(_read_value(raw, "order_id", "order_sysid", default="") or ""),
        symbol=str(_read_value(raw, "stock_code", "symbol", "code", default="") or ""),
        side=str(_read_value(raw, "order_type", "side", default="") or ""),
        volume=int(_read_value(raw, "order_volume", "volume", default=0) or 0),
        price=float(_read_value(raw, "price", "order_price", default=0.0) or 0.0),
        status=str(_read_value(raw, "order_status", "status", default="") or ""),
        raw=_raw_dict(raw),
    )


def trade_from_raw(raw: Any) -> QmtTrade:
    """Convert a QMT trade payload into a lightweight model."""

    return QmtTrade(
        trade_id=str(_read_value(raw, "trade_id", "traded_id", default="") or ""),
        order_id=str(_read_value(raw, "order_id", "order_sysid", default="") or ""),
        symbol=str(_read_value(raw, "stock_code", "symbol", "code", default="") or ""),
        side=str(_read_value(raw, "order_type", "side", default="") or ""),
        volume=int(_read_value(raw, "traded_volume", "volume", default=0) or 0),
        price=float(_read_value(raw, "traded_price", "price", default=0.0) or 0.0),
        raw=_raw_dict(raw),
    )
