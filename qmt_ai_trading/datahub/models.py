"""Dependency-light Data Hub data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MarketBar:
    symbol: str
    datetime: datetime | str | None
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None = None
    amount: float | None = None
    source: str = ""


@dataclass(slots=True)
class LatestPrice:
    symbol: str
    price: float
    datetime: datetime | str | None = None
    source: str = ""


@dataclass(slots=True)
class ETFUniverseItem:
    symbol: str
    name: str = ""
    category: str = "ETF"
    enabled: bool = True
    weight: float = 1.0
    source: str = "datahub_default"


@dataclass(slots=True)
class DataSnapshot:
    symbol: str
    latest_price: LatestPrice | None = None
    bars: list[MarketBar] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
