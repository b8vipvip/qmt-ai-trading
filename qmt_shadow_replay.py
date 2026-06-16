# -*- coding: utf-8 -*-
"""Historical ETF shadow replay; writes only to shadow_replay/ and never trades."""
from __future__ import print_function

import argparse
import csv
import datetime
import glob
import json
import math
import os

from data_tools.etf_universe import load_raw_config
from data_tools.etf_rotation_selector import score_etf
from data_tools.market_regime import classify_index, classify_market
from qmt_generate_signal_rotation import build_rotation_signal
from risk.risk_engine import RiskEngine
from shadow_trading.shadow_portfolio import calculate_max_drawdown

ROOT = os.path.dirname(os.path.abspath(__file__))
DATE_FMT = "%Y-%m-%d"


def _parse_date(value):
    return datetime.datetime.strptime(value, DATE_FMT).date()


def _compact_date(value):
    return value.replace("-", "")


def _json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def _mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        result = float(value)
        if not math.isfinite(result):
            return default
        return result
    except Exception:
        return default


def _frame_series(frame, code):
    return [_safe_float(frame.loc[code, col]) for col in list(frame.columns)]


def fetch_history(xtdata, codes, start_time, end_time):
    for code in codes:
        xtdata.download_history_data(code, "1d", start_time, end_time)
    return xtdata.get_market_data(field_list=["close", "amount"], stock_list=codes, period="1d",
                                  start_time=start_time, end_time=end_time, count=-1,
                                  dividend_type="front", fill_data=False)


def load_history(codes, start_date, end_date, xtdata=None):
    if xtdata is None:
        from qmt_gateway.gateway import QmtGateway
        xtdata = QmtGateway({"live_trading_enabled": False}).data._client()
    data = fetch_history(xtdata, codes, _compact_date(start_date), _compact_date(end_date))
    dates = []
    close_frame = data["close"]
    for col in list(close_frame.columns):
        text = str(col)
        if len(text) == 8 and text.isdigit():
            text = text[:4] + "-" + text[4:6] + "-" + text[6:]
        dates.append(text[:10])
    return data, dates


def _series_until(data, field, code, end_index):
    frame = data[field]
    cols = list(frame.columns)[:end_index + 1]
    return [_safe_float(frame.loc[code, col]) for col in cols]


def _latest_price(data, code, end_index):
    values = _series_until(data, "close", code, end_index)
    return values[-1] if values else 0.0


def _unique_symbols(values):
    result, seen = [], set()
    for value in values or []:
        code = str(value).strip().upper()
        if code and code not in seen:
            result.append(code); seen.add(code)
    return result


def build_order_plan(cfg, signal, portfolio, risk_result=None, context=None):
    code = signal.get("stock_code", "")
    price = _safe_float(signal.get("last_close"))
    lot = int(cfg.get("lot_size", 100))
    max_value = _safe_float(cfg.get("max_single_order_value", portfolio.get("total_asset", 0)), portfolio.get("total_asset", 0))
    min_value = _safe_float(cfg.get("min_order_value", 0))
    current = int(portfolio.get("positions", {}).get(code, {}).get("volume", 0))
    current_value = current * price
    total = _safe_float(portfolio.get("total_asset"), _safe_float(portfolio.get("cash")))
    cash = _safe_float(portfolio.get("cash"))
    if risk_result is None:
        risk_result = RiskEngine(cfg, mode="shadow").evaluate(signal, portfolio=portfolio, context=context or {})
    target_pct = risk_result.get("approved_target_position_pct")
    plan = {"stock_code": code, "signal": signal.get("signal"), "action": "NO_ACTION", "plan_side": "NONE",
            "plan_volume": 0, "plan_price_ref": price, "plan_amount": 0.0, "warnings": [], "risk": risk_result}
    if not risk_result.get("approved", False):
        plan["warnings"].append("Risk Engine拒绝交易：" + ";".join(risk_result.get("risk_rejections") or [])); return plan
    if not code or price <= 0 or target_pct is None or signal.get("signal") == "HOLD":
        return plan
    if signal.get("signal") == "SELL_SIGNAL":
        volume = int(current / lot) * lot
        if volume > 0:
            plan.update({"action": "PLAN_SELL", "plan_side": "SELL", "plan_volume": volume, "plan_amount": volume * price})
        return plan
    if signal.get("signal") == "BUY_SIGNAL":
        diff = total * _safe_float(target_pct) - current_value
        diff = min(diff, max_value, cash)
        volume = int((diff / price) / lot) * lot
        if volume > 0 and volume * price >= min_value:
            plan.update({"action": "PLAN_BUY", "plan_side": "BUY", "plan_volume": volume, "plan_amount": volume * price})
        return plan
    return plan


def apply_virtual_fill(cfg, portfolio, plan, day):
    settings = cfg.get("shadow_trading", {})
    trades = []
    code, action = plan.get("stock_code"), plan.get("action")
    price, volume = _safe_float(plan.get("plan_price_ref")), int(plan.get("plan_volume", 0) or 0)
    if action not in ("PLAN_BUY", "PLAN_SELL") or not code or price <= 0 or volume <= 0:
        return trades
    side = action.replace("PLAN_", "")
    slip = _safe_float(settings.get("slippage_rate", 0.001))
    fill = price * (1 + slip if side == "BUY" else 1 - slip)
    gross = fill * volume
    fee = max(_safe_float(settings.get("min_commission", 5.0)), gross * _safe_float(settings.get("commission_rate", 0.0003)))
    positions = portfolio.setdefault("positions", {})
    pos = positions.get(code, {"volume": 0, "average_cost": 0.0, "last_price": price})
    if side == "BUY" and portfolio["cash"] >= gross + fee:
        old = int(pos.get("volume", 0)) * _safe_float(pos.get("average_cost"))
        pos["volume"] = int(pos.get("volume", 0)) + volume
        pos["average_cost"] = (old + gross + fee) / float(pos["volume"])
        portfolio["cash"] -= gross + fee
    elif side == "SELL" and int(pos.get("volume", 0)) > 0:
        volume = min(volume, int(pos.get("volume", 0)))
        gross = fill * volume; fee = max(_safe_float(settings.get("min_commission", 5.0)), gross * _safe_float(settings.get("commission_rate", 0.0003)))
        pos["volume"] = int(pos.get("volume", 0)) - volume
        portfolio["cash"] += gross - fee
        if pos["volume"] == 0:
            pos["average_cost"] = 0.0
    else:
        return trades
    pos["last_price"] = price; positions[code] = pos
    trade = {"trade_date": day, "stock_code": code, "side": side, "volume": volume, "plan_price": price,
             "fill_price": round(fill, 6), "gross_amount": round(gross, 2), "commission": round(fee, 2)}
    portfolio.setdefault("trades", []).append(trade); trades.append(trade)
    return trades


def replay(cfg, rotation, tradable_symbols, benchmark_symbols, data, dates, start_date, end_date, output_dir):
    tradable_symbols = _unique_symbols(tradable_symbols)
    benchmark_symbols = _unique_symbols(benchmark_symbols)
    tradable_set = set(tradable_symbols)
    initial = _safe_float(cfg.get("shadow_trading", {}).get("initial_cash", cfg.get("initial_cash", 100000.0)))
    portfolio = {"initial_cash": initial, "cash": initial, "positions": {}, "trades": [], "total_asset": initial,
                 "market_value": 0.0, "floating_pnl": 0.0, "max_drawdown": 0.0}
    warnings, candidate_warnings, equity, snaps, counts, benchmark_counts = [], [], [], [], {}, {}
    for i, day in enumerate(dates):
        if day < start_date or day > end_date:
            continue
        rows = []
        for code in benchmark_symbols:
            closes = _series_until(data, "close", code, i)
            rows.append(classify_index(code, closes))
            benchmark_counts[code] = benchmark_counts.get(code, 0) + 1
        regime = {"market_regime": classify_market(rows), "indexes": rows}
        scores = []
        for code in tradable_symbols:
            closes, amounts = _series_until(data, "close", code, i), _series_until(data, "amount", code, i)
            rec = score_etf(code, closes, amounts, rotation.get("score_weights"), rotation.get("risk_limits"), code)
            if not rec.get("eligible") and len(closes) >= 61 and (not closes[-1] or not amounts[-1]):
                warnings.append("{0} {1} 行情缺失或无效".format(day, code))
            scores.append(rec)
        selected = sorted([r for r in scores if r.get("eligible")], key=lambda r: r["score"], reverse=True)[:max(1, int(rotation.get("top_n", 1)))]
        if selected:
            selected_code = selected[0].get("stock_code")
            if selected_code in tradable_set:
                counts[selected_code] = counts.get(selected_code, 0) + 1
            else:
                warning = "非可交易代码被选中，已忽略: {0}".format(selected_code)
                warnings.append(warning); candidate_warnings.append(warning)
        signal = build_rotation_signal({"selected": selected}, regime, rotation.get("risk_limits", {}).get("min_score_to_buy", 60))
        if signal.get("stock_code") and signal.get("stock_code") not in tradable_set:
            warning = "信号代码不是可交易 ETF，已强制 NO_ACTION: {0}".format(signal.get("stock_code"))
            warnings.append(warning); candidate_warnings.append(warning)
            signal["signal"] = "HOLD"; signal["raw_target_position_pct"] = None; signal["target_position_pct"] = None
        context = {"trades_today": len([t for t in portfolio.get("trades", []) if t.get("trade_date") == day]), "sold_today": any(t.get("trade_date") == day and t.get("side") == "SELL" for t in portfolio.get("trades", [])), "max_drawdown_pct": portfolio.get("max_drawdown", 0)}
        risk_result = RiskEngine(cfg, mode="shadow").evaluate(signal, portfolio=portfolio, context=context)
        plan = build_order_plan(cfg, signal, portfolio, risk_result, context)
        if plan.get("stock_code") and plan.get("stock_code") not in tradable_set:
            warning = "计划代码不是可交易 ETF，已强制 NO_ACTION: {0}".format(plan.get("stock_code"))
            warnings.append(warning); candidate_warnings.append(warning)
            plan.update({"action": "NO_ACTION", "plan_side": "NONE", "plan_volume": 0, "plan_amount": 0.0})
        day_trades = apply_virtual_fill(cfg, portfolio, plan, day)
        for code, pos in portfolio.get("positions", {}).items():
            price = _latest_price(data, code, i)
            if price > 0: pos["last_price"] = price
        mv = sum(int(p.get("volume", 0)) * _safe_float(p.get("last_price")) for p in portfolio.get("positions", {}).values())
        cost = sum(int(p.get("volume", 0)) * _safe_float(p.get("average_cost")) for p in portfolio.get("positions", {}).values())
        portfolio.update({"cash": round(portfolio["cash"], 2), "market_value": round(mv, 2), "total_asset": round(portfolio["cash"] + mv, 2), "floating_pnl": round(mv - cost, 2)})
        equity.append({"date": day, "total_asset": portfolio["total_asset"], "cash": portfolio["cash"], "market_value": portfolio["market_value"], "floating_pnl": portfolio["floating_pnl"]})
        portfolio["max_drawdown"] = round(calculate_max_drawdown([r["total_asset"] for r in equity]), 8)
        snaps.append({"date": day, "market_regime": regime["market_regime"], "selected_etf": selected[0]["stock_code"] if selected else "", "signal": signal.get("signal"), "action": plan.get("action"), "total_asset": portfolio["total_asset"], "max_drawdown": portfolio["max_drawdown"], "warnings": ";".join((warnings + plan.get("risk", {}).get("risk_rejections", []))[-3:])})
    write_outputs(output_dir, portfolio, equity, snaps, summary(start_date, end_date, initial, portfolio, equity, counts, warnings, benchmark_counts, benchmark_symbols, tradable_symbols, candidate_warnings))
    return portfolio


def _trade_date(value):
    try:
        return _parse_date(str(value)[:10])
    except Exception:
        return None


def calculate_closed_trade_metrics(trades):
    lots, closed = {}, []
    for trade in trades:
        code = trade.get("stock_code")
        side = trade.get("side")
        volume = int(trade.get("volume", 0) or 0)
        price = _safe_float(trade.get("fill_price") or trade.get("plan_price"))
        commission = _safe_float(trade.get("commission"))
        day = _trade_date(trade.get("trade_date"))
        if not code or volume <= 0 or price <= 0:
            continue
        if side == "BUY":
            lots.setdefault(code, []).append({"date": day, "volume": volume, "price": price, "commission_left": commission})
        elif side == "SELL":
            remaining, proceeds_commission_left = volume, commission
            while remaining > 0 and lots.get(code):
                lot = lots[code][0]
                matched = min(remaining, int(lot.get("volume", 0)))
                buy_commission = _safe_float(lot.get("commission_left")) * matched / float(lot.get("volume", matched) or matched)
                sell_commission = proceeds_commission_left * matched / float(remaining or matched)
                pnl = (price - _safe_float(lot.get("price"))) * matched - buy_commission - sell_commission
                holding_days = (day - lot["date"]).days if day and lot.get("date") else None
                closed.append({"stock_code": code, "buy_date": lot.get("date").strftime(DATE_FMT) if lot.get("date") else None,
                               "sell_date": trade.get("trade_date"), "volume": matched, "buy_price": round(_safe_float(lot.get("price")), 6),
                               "sell_price": round(price, 6), "pnl": round(pnl, 2), "return_pct": round((price / _safe_float(lot.get("price")) - 1) * 100, 4) if lot.get("price") else None,
                               "holding_days": holding_days})
                lot["commission_left"] = _safe_float(lot.get("commission_left")) - buy_commission
                lot["volume"] = int(lot.get("volume", 0)) - matched
                remaining -= matched
                proceeds_commission_left -= sell_commission
                if lot["volume"] <= 0:
                    lots[code].pop(0)
    realized = round(sum(_safe_float(t.get("pnl")) for t in closed), 2)
    if not closed:
        return {"closed_trades": 0, "win_rate": None, "average_holding_days": None, "best_trade": None, "worst_trade": None, "realized_pnl": realized}
    wins = [t for t in closed if _safe_float(t.get("pnl")) > 0]
    holding = [t.get("holding_days") for t in closed if t.get("holding_days") is not None]
    return {"closed_trades": len(closed), "win_rate": round(len(wins) / float(len(closed)), 6),
            "average_holding_days": round(sum(holding) / float(len(holding)), 4) if holding else None,
            "best_trade": max(closed, key=lambda t: _safe_float(t.get("pnl"))),
            "worst_trade": min(closed, key=lambda t: _safe_float(t.get("pnl"))), "realized_pnl": realized}


def summary(start, end, initial, portfolio, equity, counts, warnings, benchmark_counts=None, regime_reference_symbols=None, tradable_symbols=None, candidate_pool_warnings=None):
    trades = portfolio.get("trades", [])
    final = portfolio.get("total_asset", initial)
    years = max(1.0 / 252.0, len(equity) / 252.0)
    total_return = (final / initial - 1.0) if initial else 0.0
    positions = {code: pos for code, pos in portfolio.get("positions", {}).items() if int(pos.get("volume", 0) or 0) > 0}
    trade_metrics = calculate_closed_trade_metrics(trades)
    open_positions = bool(positions)
    warnings_out = list(warnings[:200])
    if trade_metrics["closed_trades"] == 0 and trades:
        warnings_out.append("暂无完整买入到卖出的闭合交易，胜率和持仓天数不计算。")
    return {"start_date": start, "end_date": end, "trading_days": len(equity), "initial_cash": initial, "final_asset": final,
            "total_return_pct": round(total_return * 100, 4), "annualized_return_pct": round(((1 + total_return) ** (1 / years) - 1) * 100, 4),
            "max_drawdown_pct": round(portfolio.get("max_drawdown", 0) * 100, 4), "total_trades": len(trades), "win_rate": trade_metrics["win_rate"],
            "average_holding_days": trade_metrics["average_holding_days"], "turnover": round(sum(_safe_float(t.get("gross_amount")) for t in trades) / initial, 6) if initial else 0.0,
            "best_trade": trade_metrics["best_trade"], "worst_trade": trade_metrics["worst_trade"], "selected_etf_counts": dict(counts),
            "tradable_selected_etf_counts": dict(counts), "benchmark_counts": benchmark_counts or {}, "regime_reference_symbols": regime_reference_symbols or [],
            "tradable_symbols": tradable_symbols or [], "benchmark_symbols": regime_reference_symbols or [],
            "candidate_pool_valid": not bool(candidate_pool_warnings), "candidate_pool_warnings": candidate_pool_warnings or [],
            "closed_trades": trade_metrics["closed_trades"], "open_positions": open_positions, "realized_pnl": trade_metrics["realized_pnl"],
            "unrealized_pnl": round(_safe_float(portfolio.get("floating_pnl")), 2), "final_positions": positions,
            "no_action_days": len([r for r in equity]) - len(trades), "warnings": warnings_out}


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(rows)


def write_outputs(out, portfolio, equity, snaps, summ):
    _mkdir(out)
    _json(os.path.join(out, "portfolio.json"), portfolio)
    write_csv(os.path.join(out, "trades.csv"), portfolio.get("trades", []), ["trade_date", "stock_code", "side", "volume", "plan_price", "fill_price", "gross_amount", "commission"])
    write_csv(os.path.join(out, "equity_curve.csv"), equity, ["date", "total_asset", "cash", "market_value", "floating_pnl"])
    write_csv(os.path.join(out, "daily_snapshots.csv"), snaps, ["date", "market_regime", "selected_etf", "signal", "action", "total_asset", "max_drawdown", "warnings"])
    _json(os.path.join(out, "replay_summary.json"), summ)
    report = "# ETF 历史影子盘回放报告\n\n- 总体收益：{0}%\n- 最大回撤：{1}%\n- 交易次数：{2}\n- 可交易 ETF 选择分布：{3}\n- 亏损区间：请结合 equity_curve.csv 查看净值低于前高的区间。\n- 是否过度交易：{4}\n- 是否建议继续影子盘：建议继续，仅作为观察验证。\n- 是否不建议实盘：不建议仅凭本次历史回放直接实盘。\n\n风险提示：历史回放不代表未来收益。\n".format(summ["total_return_pct"], summ["max_drawdown_pct"], summ["total_trades"], json.dumps(summ["selected_etf_counts"], ensure_ascii=False), "是" if summ["turnover"] > 5 else "否")
    with open(os.path.join(out, "replay_report.md"), "w", encoding="utf-8") as handle:
        handle.write(report)


def main(argv=None):
    parser = argparse.ArgumentParser(description="历史影子盘回放（只模拟，不交易）")
    parser.add_argument("--start", required=True); parser.add_argument("--end", required=True)
    parser.add_argument("--initial-cash", type=float); parser.add_argument("--symbols")
    parser.add_argument("--output-dir", default=os.path.join(ROOT, "shadow_replay"))
    args = parser.parse_args(argv)
    cfg = load_raw_config(); rotation = cfg.get("etf_rotation", {})
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("历史回放要求 live_trading_enabled=false，且不会修改该配置。")
    if args.initial_cash is not None:
        cfg.setdefault("shadow_trading", {})["initial_cash"] = args.initial_cash
    tradable_symbols = _unique_symbols(args.symbols.split(",") if args.symbols else (cfg.get("allowed_stocks") or rotation.get("etf_pool") or []))
    benchmark_symbols = _unique_symbols(rotation.get("market_regime_indexes") or [])
    history_symbols = _unique_symbols(tradable_symbols + benchmark_symbols)
    stamp = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    out = args.output_dir if os.path.basename(args.output_dir).startswith("run_") else os.path.join(args.output_dir, stamp)
    data, dates = load_history(history_symbols, args.start, args.end)
    replay(cfg, rotation, tradable_symbols, benchmark_symbols, data, dates, args.start, args.end, out)
    print("[OK] 历史影子盘回放完成: {0}".format(out))


if __name__ == "__main__":
    main()
