"""Pure-Python metrics for lightweight backtest results."""

from __future__ import annotations

from typing import Any, Iterable


def compute_total_return(initial_asset: float, final_asset: float) -> float:
    if not initial_asset or initial_asset <= 0:
        return 0.0
    return (float(final_asset) - float(initial_asset)) / float(initial_asset)


def compute_max_drawdown(equity_curve: Iterable[Any]) -> float:
    peak: float | None = None
    max_dd = 0.0
    for row in equity_curve or []:
        equity = _equity_value(row)
        if equity is None:
            continue
        peak = equity if peak is None else max(peak, equity)
        if peak and peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    return max_dd


def compute_win_rate(trades: Iterable[Any]) -> float:
    materialized = list(trades or [])
    if not materialized:
        return 0.0
    wins = sum(1 for trade in materialized if float(getattr(trade, "pnl", 0.0) or 0.0) > 0)
    return wins / len(materialized)


def compute_equity_curve(snapshots: Iterable[Any]) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    for index, row in enumerate(snapshots or []):
        equity = _equity_value(row)
        if equity is None:
            continue
        curve.append({"index": index, "datetime": getattr(row, "datetime", None) if not isinstance(row, dict) else row.get("datetime"), "equity": equity})
    return curve


def summarize_backtest_result(result: Any) -> dict[str, Any]:
    return {
        "initial_cash": float(getattr(result, "initial_cash", 0.0) or 0.0),
        "final_cash": float(getattr(result, "final_cash", 0.0) or 0.0),
        "final_asset": float(getattr(result, "final_asset", 0.0) or 0.0),
        "total_return": float(getattr(result, "total_return", 0.0) or 0.0),
        "max_drawdown": float(getattr(result, "max_drawdown", 0.0) or 0.0),
        "win_rate": float(getattr(result, "win_rate", 0.0) or 0.0),
        "trade_count": int(getattr(result, "trade_count", 0) or 0),
        "metadata": dict(getattr(result, "metadata", {}) or {}),
    }


def _equity_value(row: Any) -> float | None:
    if isinstance(row, dict):
        value = row.get("equity", row.get("total_asset", row.get("asset")))
    else:
        value = getattr(row, "equity", getattr(row, "total_asset", None))
    if value is None:
        return None
    return float(value)
