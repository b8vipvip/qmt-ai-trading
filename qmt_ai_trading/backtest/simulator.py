"""Lightweight historical simulation for TradeIntent objects.

This module never connects to QMT and never calls real order placement APIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from qmt_ai_trading.backtest.metrics import compute_max_drawdown, compute_total_return, compute_win_rate
from qmt_ai_trading.backtest.models import BacktestAccount, BacktestOrder, BacktestPosition, BacktestResult, BacktestTrade
from qmt_ai_trading.common.types import TradeIntent

DEFAULT_FEE_RATE = 0.0003


def simulate_order_fill(order: BacktestOrder, *, fee_rate: float = DEFAULT_FEE_RATE) -> BacktestTrade:
    amount = float(order.quantity) * float(order.price)
    fee = abs(amount) * float(fee_rate)
    return BacktestTrade(
        symbol=order.symbol,
        side=order.side.upper(),
        quantity=int(order.quantity),
        price=float(order.price),
        datetime=order.datetime,
        fee=fee,
        amount=amount,
        pnl=0.0,
        metadata={"source": order.source, "reason": order.reason, "simulated": True},
    )


def update_backtest_account(account: BacktestAccount, trade: BacktestTrade, latest_prices: Mapping[str, float] | None = None) -> BacktestAccount:
    side = trade.side.upper()
    position = account.positions.get(trade.symbol, BacktestPosition(symbol=trade.symbol))
    if side == "BUY":
        total_cost = trade.amount + trade.fee
        if account.cash < total_cost:
            trade.metadata["filled"] = False
            trade.metadata["reason"] = "insufficient cash"
            return _mark_to_market(account, latest_prices)
        new_qty = position.quantity + trade.quantity
        position.avg_price = ((position.avg_price * position.quantity) + trade.amount) / new_qty if new_qty else 0.0
        position.quantity = new_qty
        account.cash -= total_cost
    elif side == "SELL":
        sell_qty = min(position.quantity, trade.quantity)
        if sell_qty <= 0:
            trade.metadata["filled"] = False
            trade.metadata["reason"] = "no position to sell"
            return _mark_to_market(account, latest_prices)
        trade.quantity = sell_qty
        trade.amount = sell_qty * trade.price
        trade.fee = abs(trade.amount) * DEFAULT_FEE_RATE
        trade.pnl = (trade.price - position.avg_price) * sell_qty - trade.fee
        position.quantity -= sell_qty
        account.cash += trade.amount - trade.fee
        if position.quantity <= 0:
            position.avg_price = 0.0
    else:
        trade.metadata["filled"] = False
        trade.metadata["reason"] = f"unsupported side {trade.side}"
    trade.metadata.setdefault("filled", True)
    account.positions[trade.symbol] = position
    return _mark_to_market(account, latest_prices)


def simulate_trade_intents(
    intents: Iterable[TradeIntent],
    prices: Mapping[str, float] | None = None,
    bars: Mapping[str, Iterable[Any]] | None = None,
    *,
    fee_rate: float = DEFAULT_FEE_RATE,
) -> list[BacktestTrade]:
    trades: list[BacktestTrade] = []
    for intent in intents or []:
        price = _resolve_price(intent.symbol, prices, bars)
        if price is None or price <= 0:
            trades.append(_rejected_trade(intent, "missing price data"))
            continue
        if intent.side.upper() not in {"BUY", "SELL"} or int(intent.quantity or 0) <= 0:
            trades.append(_rejected_trade(intent, "unsupported side or non-positive quantity"))
            continue
        order = BacktestOrder(intent.symbol, intent.side.upper(), int(intent.quantity), float(price), getattr(intent, "created_at", None), intent.source, intent.reason)
        trades.append(simulate_order_fill(order, fee_rate=fee_rate))
    return trades


def run_simple_backtest(
    intents: Iterable[TradeIntent] | None,
    prices: Mapping[str, float] | None = None,
    bars: Mapping[str, Iterable[Any]] | None = None,
    *,
    initial_cash: float = 1_000_000.0,
    fee_rate: float = DEFAULT_FEE_RATE,
) -> BacktestResult:
    account = BacktestAccount(cash=float(initial_cash), total_asset=float(initial_cash))
    trades = simulate_trade_intents(intents or [], prices, bars, fee_rate=fee_rate)
    executed: list[BacktestTrade] = []
    equity_curve = [{"datetime": None, "equity": float(initial_cash), "cash": float(initial_cash)}]
    for trade in trades:
        if trade.metadata.get("filled") is False:
            continue
        update_backtest_account(account, trade, prices)
        if trade.metadata.get("filled") is not False:
            executed.append(trade)
        equity_curve.append({"datetime": trade.datetime, "equity": account.total_asset or account.cash, "cash": account.cash})
    final_asset = float(account.total_asset if account.total_asset is not None else account.cash)
    metrics = {
        "total_return": compute_total_return(initial_cash, final_asset),
        "max_drawdown": compute_max_drawdown(equity_curve),
        "win_rate": compute_win_rate(executed),
        "trade_count": len(executed),
    }
    return BacktestResult(float(initial_cash), account.cash, final_asset, metrics["total_return"], metrics["max_drawdown"], metrics["win_rate"], len(executed), executed, equity_curve, metrics, {"rejected_count": len(trades) - len(executed), "simulated_only": True})


def _resolve_price(symbol: str, prices: Mapping[str, float] | None, bars: Mapping[str, Iterable[Any]] | None) -> float | None:
    if prices and symbol in prices:
        return float(prices[symbol])
    rows = list((bars or {}).get(symbol, []) or [])
    if rows:
        close = getattr(rows[-1], "close", rows[-1].get("close") if isinstance(rows[-1], dict) else None)
        return float(close) if close is not None else None
    return None


def _rejected_trade(intent: TradeIntent, reason: str) -> BacktestTrade:
    return BacktestTrade(intent.symbol, intent.side.upper(), int(intent.quantity or 0), 0.0, getattr(intent, "created_at", datetime.now(timezone.utc)), metadata={"filled": False, "reason": reason, "source": intent.source})


def _mark_to_market(account: BacktestAccount, latest_prices: Mapping[str, float] | None = None) -> BacktestAccount:
    total = account.cash
    for symbol, position in account.positions.items():
        price = float((latest_prices or {}).get(symbol, position.avg_price) or 0.0)
        position.market_value = position.quantity * price
        position.unrealized_pnl = (price - position.avg_price) * position.quantity
        total += position.market_value
    account.total_asset = total
    return account
