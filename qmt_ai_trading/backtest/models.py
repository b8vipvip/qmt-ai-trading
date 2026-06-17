"""Lightweight backtest data contracts for simulated trading only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BacktestOrder:
    symbol: str
    side: str
    quantity: int
    price: float
    datetime: Any = None
    source: str = ""
    reason: str = ""


@dataclass(slots=True)
class BacktestTrade:
    symbol: str
    side: str
    quantity: int
    price: float
    datetime: Any = None
    fee: float = 0.0
    amount: float = 0.0
    pnl: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BacktestPosition:
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BacktestAccount:
    cash: float
    total_asset: float | None = None
    positions: dict[str, BacktestPosition] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BacktestResult:
    initial_cash: float
    final_cash: float
    final_asset: float
    total_return: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
