"""Adapters for future shadow/dry-run replay sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from qmt_ai_trading.backtest.models import BacktestResult
from qmt_ai_trading.backtest.simulator import run_simple_backtest
from qmt_ai_trading.common.types import TradeIntent


@dataclass(slots=True)
class ShadowReplayEvent:
    intent: TradeIntent | None = None
    datetime: Any = None
    status: str = "accepted"
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ShadowReplayResult:
    events: list[ShadowReplayEvent] = field(default_factory=list)
    backtest_result: BacktestResult | None = None
    report: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def replay_trade_intents(intents: Iterable[TradeIntent] | None, prices: Mapping[str, float] | None = None, bars: Mapping[str, Iterable[Any]] | None = None, *, initial_cash: float = 1_000_000.0) -> ShadowReplayResult:
    materialized = list(intents or [])
    events = [ShadowReplayEvent(intent=item, datetime=getattr(item, "created_at", None), metadata={"source": item.source, "dry_run": item.dry_run}) for item in materialized]
    backtest = run_simple_backtest(materialized, prices, bars, initial_cash=initial_cash)
    result = ShadowReplayResult(events=events, backtest_result=backtest, metadata={"simulated_only": True, "todo": "adapt existing shadow replay logs without reading sensitive paths"})
    result.report = build_shadow_replay_report(result)
    return result


def build_shadow_replay_report(result: ShadowReplayResult) -> dict[str, Any]:
    backtest = result.backtest_result
    return {
        "event_count": len(result.events),
        "trade_count": int(getattr(backtest, "trade_count", 0) or 0),
        "final_asset": float(getattr(backtest, "final_asset", 0.0) or 0.0),
        "total_return": float(getattr(backtest, "total_return", 0.0) or 0.0),
        "simulated_only": True,
    }
