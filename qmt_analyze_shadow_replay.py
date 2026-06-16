# -*- coding: utf-8 -*-
"""Read-only AI-style analyzer for historical shadow replay outputs.

The analyzer only reads files under a shadow_replay/run_* directory and writes
ai_replay_analysis.json / ai_replay_analysis.md beside them. It never imports or
calls QMT trading APIs, never changes strategy code, and never modifies config.
"""
from __future__ import print_function

import argparse
import csv
import datetime
import glob
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATE_FMT = "%Y-%m-%d"
API_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
ACCOUNT_RE = re.compile(r"(?i)(account[_-]?id|account)\s*[:=]\s*([A-Za-z0-9_-]{4,})")


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        result = float(value)
        return result if math.isfinite(result) else default
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else ({} if default is None else default)
    except (IOError, OSError, ValueError, TypeError):
        return {} if default is None else default


def _read_csv(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (IOError, OSError, csv.Error):
        return []


def _redact_text(text):
    text = API_KEY_RE.sub("***", text)
    return ACCOUNT_RE.sub(lambda m: m.group(1) + "=***" + m.group(2)[-2:], text)


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return _redact_text(handle.read())
    except (IOError, OSError):
        return ""


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def _parse_date(value):
    try:
        return datetime.datetime.strptime(str(value)[:10], DATE_FMT).date()
    except Exception:
        return None


def latest_run_dir(root=None):
    base = root or ROOT
    paths = [p for p in glob.glob(os.path.join(base, "shadow_replay", "run_*")) if os.path.isdir(p)]
    return max(paths, key=os.path.getmtime) if paths else None


def _assess_performance(summary):
    total_return = _safe_float(summary.get("total_return_pct"))
    annualized = _safe_float(summary.get("annualized_return_pct"))
    drawdown = _safe_float(summary.get("max_drawdown_pct"))
    acceptable = total_return > 0 and annualized > 0 and drawdown <= 20
    notes = []
    notes.append("总收益为正" if total_return > 0 else "总收益不为正")
    notes.append("年化收益为正" if annualized > 0 else "年化收益不为正")
    notes.append("最大回撤在 20% 以内" if drawdown <= 20 else "最大回撤超过 20%")
    return {"acceptable": acceptable, "total_return_pct": total_return, "annualized_return_pct": annualized,
            "max_drawdown_pct": drawdown, "notes": notes}


def find_drawdown_periods(equity, limit=5):
    peak_value, peak_date, current = None, None, None
    periods = []
    for row in equity:
        date = row.get("date")
        value = _safe_float(row.get("total_asset"))
        if value <= 0:
            continue
        if peak_value is None or value >= peak_value:
            if current:
                current["end_date"] = date
                periods.append(current)
                current = None
            peak_value, peak_date = value, date
            continue
        drawdown_pct = (peak_value - value) / peak_value * 100.0 if peak_value else 0.0
        if current is None:
            current = {"start_date": peak_date, "trough_date": date, "end_date": None,
                       "max_drawdown_pct": round(drawdown_pct, 4)}
        elif drawdown_pct > current["max_drawdown_pct"]:
            current["trough_date"] = date
            current["max_drawdown_pct"] = round(drawdown_pct, 4)
    if current:
        current["end_date"] = None
        periods.append(current)
    periods.sort(key=lambda item: item.get("max_drawdown_pct", 0), reverse=True)
    return periods[:limit]


def calculate_etf_contributions(trades):
    lots, pnl_by_code, volume_by_code = {}, {}, {}
    for trade in trades:
        code = trade.get("stock_code") or trade.get("code")
        side = trade.get("side")
        volume = _safe_int(trade.get("volume"))
        price = _safe_float(trade.get("fill_price") or trade.get("plan_price"))
        commission = _safe_float(trade.get("commission"))
        if not code or volume <= 0 or price <= 0:
            continue
        volume_by_code[code] = volume_by_code.get(code, 0) + volume
        if side == "BUY":
            lots.setdefault(code, []).append({"volume": volume, "price": price, "commission_left": commission})
        elif side == "SELL":
            remaining, sell_fee_left = volume, commission
            while remaining > 0 and lots.get(code):
                lot = lots[code][0]
                matched = min(remaining, _safe_int(lot.get("volume")))
                buy_fee = _safe_float(lot.get("commission_left")) * matched / float(_safe_int(lot.get("volume")) or matched)
                sell_fee = sell_fee_left * matched / float(remaining or matched)
                pnl = (price - _safe_float(lot.get("price"))) * matched - buy_fee - sell_fee
                pnl_by_code[code] = pnl_by_code.get(code, 0.0) + pnl
                lot["volume"] = _safe_int(lot.get("volume")) - matched
                lot["commission_left"] = _safe_float(lot.get("commission_left")) - buy_fee
                remaining -= matched
                sell_fee_left -= sell_fee
                if lot["volume"] <= 0:
                    lots[code].pop(0)
    rows = []
    for code in sorted(set(list(pnl_by_code.keys()) + list(volume_by_code.keys()))):
        rows.append({"stock_code": code, "realized_pnl": round(pnl_by_code.get(code, 0.0), 2),
                     "traded_volume": volume_by_code.get(code, 0)})
    rows.sort(key=lambda item: item["realized_pnl"], reverse=True)
    return rows


def find_cash_periods(equity, min_days=5):
    periods, current = [], None
    for row in equity:
        date = row.get("date")
        market_value = _safe_float(row.get("market_value"))
        if market_value <= 0:
            if current is None:
                current = {"start_date": date, "end_date": date, "days": 1}
            else:
                current["end_date"] = date
                current["days"] += 1
        elif current:
            if current["days"] >= min_days:
                periods.append(current)
            current = None
    if current and current["days"] >= min_days:
        periods.append(current)
    periods.sort(key=lambda item: item["days"], reverse=True)
    return periods[:5]


def build_recommendations(summary, equity, trades, concentration, overtrade, long_cash, overfit_risk):
    recommendations = []
    if concentration.get("is_over_concentrated"):
        recommendations.append({"title": "降低单一 ETF 选择集中度", "modify_location": "config.json -> etf_rotation.top_n / score_weights / risk_limits",
            "reason": "历史回放中单一 ETF 占选择天数比例过高，组合可能对单一风格暴露过重。",
            "expected_metric_improvement": "降低最大回撤和单一 ETF 风格风险", "potential_side_effect": "分散后可能降低强趋势行情中的收益弹性。",
            "change_now": False})
    if overtrade.get("is_over_trading"):
        recommendations.append({"title": "降低换手和交易频率", "modify_location": "config.json -> etf_rotation.rebalance_mode / risk_limits.min_score_to_buy",
            "reason": "交易次数或换手率偏高，手续费、滑点和噪声交易影响可能被低估。",
            "expected_metric_improvement": "降低 turnover、交易次数和滑点敏感性", "potential_side_effect": "调仓变慢可能错过快速风格切换。",
            "change_now": False})
    if long_cash.get("has_long_cash_periods"):
        recommendations.append({"title": "复核长时间空仓规则", "modify_location": "config.json -> etf_rotation.risk_limits / market_regime_indexes",
            "reason": "回放中存在连续空仓区间，可能来自风控阈值过严或市场状态过滤过强。",
            "expected_metric_improvement": "提升资金利用率和潜在总收益", "potential_side_effect": "放宽空仓条件可能提高回撤和震荡期亏损。",
            "change_now": False})
    if overfit_risk.get("risk_level") in ("medium", "high"):
        recommendations.append({"title": "增加样本外与分阶段验证", "modify_location": "tests/ 或 backtest/replay 验证流程；不要直接修改策略参数",
            "reason": "样本周期、交易闭合数量或参数依赖可能不足以证明策略稳健。",
            "expected_metric_improvement": "降低样本内过拟合风险，提高样本外稳定性", "potential_side_effect": "验证周期更长，短期不会直接提升收益。",
            "change_now": False})
    if _safe_float(summary.get("max_drawdown_pct")) > 15:
        recommendations.append({"title": "加强回撤约束", "modify_location": "config.json -> etf_rotation.risk_limits.max_drawdown_60d / min_score_to_buy",
            "reason": "最大回撤接近或超过保守阈值，需要先确认风险承受能力。",
            "expected_metric_improvement": "降低最大回撤", "potential_side_effect": "可能减少交易机会并降低年化收益。",
            "change_now": False})
    if not recommendations:
        recommendations.append({"title": "继续观察，不立即改策略", "modify_location": "无；保持当前策略代码不变",
            "reason": "当前只基于历史影子盘产物，尚不足以支持自动改策略。",
            "expected_metric_improvement": "避免因单次回放过度调参导致样本内过拟合", "potential_side_effect": "可能延后发现可优化参数。",
            "change_now": False})
    return recommendations[:5]


def analyze_run(run_dir):
    summary_path = os.path.join(run_dir, "replay_summary.json")
    trades_path = os.path.join(run_dir, "trades.csv")
    equity_path = os.path.join(run_dir, "equity_curve.csv")
    report_path = os.path.join(run_dir, "replay_report.md")
    summary, trades, equity = _read_json(summary_path, {}), _read_csv(trades_path), _read_csv(equity_path)
    report_excerpt = _read_text(report_path)[:1000]
    counts = summary.get("tradable_selected_etf_counts") or summary.get("selected_etf_counts") or {}
    total_selected = sum([_safe_int(v) for v in counts.values()])
    top_code, top_count = None, 0
    if counts:
        top_code, top_count = max(counts.items(), key=lambda item: _safe_int(item[1]))
    concentration_ratio = round(float(top_count) / total_selected, 4) if total_selected else None
    turnover = _safe_float(summary.get("turnover"))
    trading_days = _safe_int(summary.get("trading_days")) or len(equity)
    total_trades = _safe_int(summary.get("total_trades")) or len(trades)
    trade_frequency = round(float(total_trades) / trading_days, 4) if trading_days else None
    concentration = {"top_etf": top_code, "top_etf_days": top_count, "top_etf_ratio": concentration_ratio,
                     "is_over_concentrated": bool(concentration_ratio is not None and concentration_ratio >= 0.7)}
    overtrade = {"turnover": turnover, "trade_frequency_per_day": trade_frequency,
                 "is_over_trading": bool(turnover > 5 or (trade_frequency is not None and trade_frequency > 0.25))}
    cash_periods = find_cash_periods(equity)
    long_cash = {"has_long_cash_periods": bool(cash_periods), "periods": cash_periods}
    closed_trades = _safe_int(summary.get("closed_trades"))
    overfit_flags = []
    if trading_days < 252:
        overfit_flags.append("回放交易日少于约 1 年")
    if closed_trades < 10:
        overfit_flags.append("闭合交易少于 10 笔")
    if concentration.get("is_over_concentrated"):
        overfit_flags.append("选择结果高度集中于单一 ETF")
    overfit_risk = {"risk_level": "high" if len(overfit_flags) >= 2 else ("medium" if overfit_flags else "low"), "flags": overfit_flags}
    drawdown_periods = find_drawdown_periods(equity)
    contributions = calculate_etf_contributions(trades)
    result = {"analysis_type": "shadow_replay_readonly_ai_analysis", "run_dir": os.path.relpath(run_dir, ROOT).replace(os.sep, "/"),
              "inputs": {"replay_summary": os.path.basename(summary_path), "trades": os.path.basename(trades_path),
                         "equity_curve": os.path.basename(equity_path), "replay_report": os.path.basename(report_path)},
              "safety": {"strategy_code_modified": False, "trading_functions_called": False, "live_trading_enabled_modified": False,
                         "api_key_output": False, "full_account_id_output": False},
              "performance_acceptability": _assess_performance(summary), "drawdown_periods": drawdown_periods,
              "etf_contributions": contributions, "concentration": concentration, "overtrading": overtrade,
              "long_cash_periods": long_cash, "overfit_risk": overfit_risk, "source_report_excerpt": report_excerpt,
              "recommendations": build_recommendations(summary, equity, trades, concentration, overtrade, long_cash, overfit_risk)}
    return result


def render_markdown(analysis):
    lines = ["# AI 历史影子盘回放分析", "", "## 安全声明",
             "- 仅分析 shadow_replay 产物，不自动修改策略代码。", "- 不调用 order_stock / cancel_order_stock。", "- 不修改 live_trading_enabled。", "",
             "## 核心结论",
             "- 总收益：{0}%".format(analysis["performance_acceptability"].get("total_return_pct")),
             "- 年化收益：{0}%".format(analysis["performance_acceptability"].get("annualized_return_pct")),
             "- 最大回撤：{0}%".format(analysis["performance_acceptability"].get("max_drawdown_pct")),
             "- 是否可接受：{0}".format("是" if analysis["performance_acceptability"].get("acceptable") else "否"), "",
             "## 回撤日期", json.dumps(analysis.get("drawdown_periods", []), ensure_ascii=False, indent=2), "",
             "## ETF 贡献", json.dumps(analysis.get("etf_contributions", []), ensure_ascii=False, indent=2), "",
             "## 集中度 / 交易频率 / 空仓 / 过拟合", json.dumps({"concentration": analysis.get("concentration"), "overtrading": analysis.get("overtrading"), "long_cash_periods": analysis.get("long_cash_periods"), "overfit_risk": analysis.get("overfit_risk")}, ensure_ascii=False, indent=2), "",
             "## 优化建议（最多 5 条）"]
    for i, rec in enumerate(analysis.get("recommendations", []), 1):
        lines.extend(["", "### {0}. {1}".format(i, rec.get("title")),
                      "- 修改位置：{0}".format(rec.get("modify_location")),
                      "- 修改原因：{0}".format(rec.get("reason")),
                      "- 预期改善指标：{0}".format(rec.get("expected_metric_improvement")),
                      "- 潜在副作用：{0}".format(rec.get("potential_side_effect")),
                      "- 是否建议立刻修改：{0}".format("是" if rec.get("change_now") else "否")])
    return "\n".join(lines) + "\n"


def write_analysis(run_dir, analysis):
    json_path = os.path.join(run_dir, "ai_replay_analysis.json")
    md_path = os.path.join(run_dir, "ai_replay_analysis.md")
    _write_json(json_path, analysis)
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(analysis))
    return json_path, md_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="只读 AI 历史影子盘回放分析器")
    parser.add_argument("--run-dir", help="shadow_replay/run_xxx 目录；默认使用最近一次回放")
    args = parser.parse_args(argv)
    run_dir = args.run_dir or latest_run_dir()
    if not run_dir:
        raise RuntimeError("未找到 shadow_replay/run_* 回放目录")
    analysis = analyze_run(os.path.abspath(run_dir))
    json_path, md_path = write_analysis(os.path.abspath(run_dir), analysis)
    print("[OK] AI 历史回放分析已生成: {0} {1}".format(json_path, md_path))
    return analysis


if __name__ == "__main__":
    main()
