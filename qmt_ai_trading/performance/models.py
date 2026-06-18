"""Performance and long-backtest data contracts.

All models are dataclasses with JSON-serializable fields only. This package is
read-only with respect to market cache data and never calls QMT or xttrader.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class BacktestPeriod:
    start_date: str
    end_date: str
    frequency: str = "1d"
    rebalance_frequency: str = "5d"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioEquityPoint:
    date: str
    equity: float
    cash: float = 0.0
    market_value: float = 0.0
    daily_return: float = 0.0
    drawdown: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioBacktestTrade:
    date: str
    symbol: str
    side: str
    quantity: int
    price: float
    value: float
    target_weight: float = 0.0
    allowed_by_risk: bool = True
    blocked_reason: str = ""
    source: str = "long_portfolio_backtest"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioPerformanceSummary:
    start_date: str
    end_date: str
    initial_cash: float
    final_equity: float
    total_return: float = 0.0
    annualized_return: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    rebalance_count: int = 0
    turnover: float = 0.0
    risk_blocked_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactorAttribution:
    factor_name: str
    contribution: float = 0.0
    average_exposure: float = 0.0
    average_score: float = 0.0
    win_rate: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LongBacktestResult:
    run_id: str
    created_at: str
    period: BacktestPeriod
    data_source: str
    cache_quality: str
    equity_curve: list[PortfolioEquityPoint] = field(default_factory=list)
    trades: list[PortfolioBacktestTrade] = field(default_factory=list)
    summary: PortfolioPerformanceSummary | None = None
    factor_attribution: list[FactorAttribution] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    return value
