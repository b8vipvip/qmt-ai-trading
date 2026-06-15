# -*- coding: utf-8 -*-
"""Persistent virtual ETF portfolio. This module never imports trading APIs."""
from __future__ import print_function
import csv
import datetime
import json
import os


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle: return json.load(handle)
    except (IOError, OSError, ValueError, TypeError): return {} if default is None else default


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle: json.dump(value, handle, ensure_ascii=False, indent=2)


def _commission(value, cfg):
    return max(float(cfg.get("min_commission", 5.0)), value * float(cfg.get("commission_rate", 0.0003)))


def calculate_max_drawdown(values):
    peak, result = 0.0, 0.0
    for value in values:
        value = float(value)
        peak = max(peak, value)
        if peak > 0: result = max(result, (peak - value) / peak)
    return result


def update_shadow_portfolio(config, order_plan, target_signal=None, shadow_dir="shadow", now=None):
    """Apply at most one virtual fill per symbol/side/day and write ledger files."""
    now = now or datetime.datetime.now(); day = now.strftime("%Y-%m-%d"); stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    settings = config.get("shadow_trading", {}); os.makedirs(shadow_dir, exist_ok=True)
    portfolio_path = os.path.join(shadow_dir, "portfolio.json"); trades_path = os.path.join(shadow_dir, "trades.csv"); curve_path = os.path.join(shadow_dir, "equity_curve.csv")
    initial = float(settings.get("initial_cash", 100000.0))
    portfolio = _read_json(portfolio_path, {"initial_cash": initial, "cash": initial, "positions": {}, "trades": [], "total_asset": initial, "floating_pnl": 0.0, "max_drawdown": 0.0})
    positions = portfolio.setdefault("positions", {}); trades = portfolio.setdefault("trades", [])
    code = order_plan.get("stock_code") or (target_signal or {}).get("stock_code"); action = order_plan.get("action", "NO_ACTION")
    price = float(order_plan.get("plan_price_ref") or (target_signal or {}).get("last_close") or 0); volume = int(order_plan.get("plan_volume", 0) or 0)
    duplicate = any(t.get("trade_date") == day and t.get("stock_code") == code and t.get("side") == action.replace("PLAN_", "") for t in trades)
    if settings.get("enabled", True) and action in ("PLAN_BUY", "PLAN_SELL") and code and price > 0 and volume > 0 and not duplicate:
        side = action.replace("PLAN_", ""); slip = float(settings.get("slippage_rate", 0.001)); fill_price = price * (1 + slip if side == "BUY" else 1 - slip); gross = fill_price * volume; fee = _commission(gross, settings)
        pos = positions.get(code, {"volume": 0, "average_cost": 0.0, "last_price": price})
        if side == "BUY" and portfolio["cash"] >= gross + fee:
            old_cost = float(pos["average_cost"]) * int(pos["volume"]); pos["volume"] = int(pos["volume"]) + volume; pos["average_cost"] = (old_cost + gross + fee) / pos["volume"]; portfolio["cash"] -= gross + fee
        elif side == "SELL" and int(pos.get("volume", 0)) > 0:
            volume = min(volume, int(pos["volume"])); gross = fill_price * volume; fee = _commission(gross, settings); pos["volume"] -= volume; portfolio["cash"] += gross - fee
            if pos["volume"] == 0: pos["average_cost"] = 0.0
        else: side = None
        if side:
            pos["last_price"] = price; positions[code] = pos; trades.append({"trade_date": day, "timestamp": stamp, "stock_code": code, "side": side, "volume": volume, "plan_price": price, "fill_price": round(fill_price, 6), "gross_amount": round(gross, 2), "commission": round(fee, 2)})
    if code and code in positions and price > 0: positions[code]["last_price"] = price
    market_value = sum(int(p.get("volume", 0)) * float(p.get("last_price", 0)) for p in positions.values())
    cost_value = sum(int(p.get("volume", 0)) * float(p.get("average_cost", 0)) for p in positions.values())
    portfolio.update({"updated_at": stamp, "initial_cash": initial, "total_asset": round(float(portfolio["cash"]) + market_value, 2), "market_value": round(market_value, 2), "floating_pnl": round(market_value - cost_value, 2)})
    rows = []
    if os.path.exists(curve_path):
        with open(curve_path, "r", encoding="utf-8") as handle: rows = list(csv.DictReader(handle))
    row = {"date": day, "total_asset": portfolio["total_asset"], "cash": round(float(portfolio["cash"]), 2), "market_value": portfolio["market_value"], "floating_pnl": portfolio["floating_pnl"]}
    rows = [r for r in rows if r.get("date") != day] + [row]; portfolio["max_drawdown"] = round(calculate_max_drawdown([r["total_asset"] for r in rows]), 8)
    _write_json(portfolio_path, portfolio); _write_json(os.path.join(shadow_dir, "daily_snapshot.json"), dict(row, positions=positions, max_drawdown=portfolio["max_drawdown"], today_trades=[t for t in trades if t["trade_date"] == day]))
    for path, records, fields in [(trades_path, trades, ["trade_date","timestamp","stock_code","side","volume","plan_price","fill_price","gross_amount","commission"]), (curve_path, rows, ["date","total_asset","cash","market_value","floating_pnl"])]:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(records)
    return portfolio
