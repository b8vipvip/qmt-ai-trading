# -*- coding: utf-8 -*-
"""Batch historical ETF shadow replay validation; read-only and never trades."""
from __future__ import print_function

import argparse
import csv
import datetime
import json
import math
import os

import qmt_shadow_replay as single
from data_tools.etf_universe import load_raw_config

ROOT = os.path.dirname(os.path.abspath(__file__))
DATE_FMT = "%Y-%m-%d"


def _today():
    return datetime.date.today()


def _parse_date(value):
    return datetime.datetime.strptime(str(value), DATE_FMT).date()


def _date_text(value):
    if isinstance(value, datetime.date):
        return value.strftime(DATE_FMT)
    return str(value)


def _mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


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


def default_periods(today=None):
    today = today or _today()
    this_year_end = min(today, datetime.date(2026, 6, 16)) if today.year >= 2026 else today
    periods = [
        ("2023全年", "2023-01-01", "2023-12-31"),
        ("2024全年", "2024-01-01", "2024-12-31"),
        ("2025全年", "2025-01-01", "2025-12-31"),
        ("2025年至今", "2025-01-01", _date_text(this_year_end)),
        ("2023年至今", "2023-01-01", _date_text(this_year_end)),
        ("最近6个月", _date_text(this_year_end - datetime.timedelta(days=183)), _date_text(this_year_end)),
        ("最近12个月", _date_text(this_year_end - datetime.timedelta(days=365)), _date_text(this_year_end)),
        ("最近18个月", _date_text(this_year_end - datetime.timedelta(days=548)), _date_text(this_year_end)),
    ]
    return [{"period_name": name, "start_date": start, "end_date": end} for name, start, end in periods]


def load_periods(path):
    with open(path, "r", encoding="utf-8") as handle:
        if path.lower().endswith(".json"):
            raw = json.load(handle)
        else:
            raw = list(csv.DictReader(handle))
    periods = raw.get("periods", raw) if isinstance(raw, dict) else raw
    result = []
    for idx, item in enumerate(periods):
        if isinstance(item, dict):
            start, end = item.get("start_date") or item.get("start"), item.get("end_date") or item.get("end")
            name = item.get("period_name") or item.get("name") or "区间{0:03d}".format(idx + 1)
        else:
            name, start, end = "区间{0:03d}".format(idx + 1), item[0], item[1]
        if start and end:
            result.append({"period_name": name, "start_date": str(start), "end_date": str(end)})
    return result


def period_metric_warnings(summary):
    warnings = []
    if summary.get("candidate_pool_valid") is False:
        warnings.append("候选池无效")
    if _safe_float(summary.get("max_drawdown_pct")) > 15:
        warnings.append("最大回撤超过15%")
    if _safe_float(summary.get("turnover")) > 5:
        warnings.append("换手率偏高，可能过度交易")
    counts = summary.get("tradable_selected_etf_counts") or {}
    total = sum([_safe_float(v) for v in counts.values()])
    if total > 0 and _safe_float(counts.get("159915.SZ")) / total >= 0.6:
        warnings.append("159915.SZ 选择占比过高，存在风格集中风险")
    return warnings


def normalize_period_result(period, summary, warning=None):
    keys = ["trading_days", "initial_cash", "final_asset", "total_return_pct", "annualized_return_pct", "max_drawdown_pct", "total_trades", "closed_trades", "win_rate", "average_holding_days", "turnover", "open_positions", "realized_pnl", "unrealized_pnl", "tradable_selected_etf_counts", "benchmark_counts", "candidate_pool_valid"]
    result = {"period_name": period.get("period_name"), "start_date": period.get("start_date"), "end_date": period.get("end_date")}
    for key in keys:
        result[key] = summary.get(key)
    result["metric_warnings"] = period_metric_warnings(summary) + list(summary.get("warnings") or [])
    if warning:
        result["metric_warnings"].append(warning)
        result["candidate_pool_valid"] = False
    return result


def _median(values):
    if not values:
        return 0.0
    values = sorted(values); mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2.0


def build_batch_summary(periods, results):
    valid_returns = [_safe_float(r.get("total_return_pct")) for r in results if r.get("total_return_pct") is not None]
    ann = [_safe_float(r.get("annualized_return_pct")) for r in results if r.get("annualized_return_pct") is not None]
    dds = [_safe_float(r.get("max_drawdown_pct")) for r in results if r.get("max_drawdown_pct") is not None]
    best = max(results, key=lambda r: _safe_float(r.get("total_return_pct"))) if results else None
    worst = min(results, key=lambda r: _safe_float(r.get("total_return_pct"))) if results else None
    worst_dd = max(results, key=lambda r: _safe_float(r.get("max_drawdown_pct"))) if results else None
    pos = len([r for r in results if _safe_float(r.get("total_return_pct")) > 0])
    neg = len([r for r in results if _safe_float(r.get("total_return_pct")) < 0])
    warnings = []
    if any(r.get("candidate_pool_valid") is False for r in results): warnings.append("候选池存在无效区间，稳定性不合格")
    if any(_safe_float(r.get("max_drawdown_pct")) > 15 for r in results): warnings.append("存在最大回撤超过15%的高风险区间")
    if neg > len(results) / 2.0: warnings.append("多数区间亏损，策略不稳")
    total_positive = sum([max(0.0, _safe_float(r.get("total_return_pct"))) for r in results])
    if total_positive > 0 and max([max(0.0, _safe_float(r.get("total_return_pct"))) for r in results] or [0]) / total_positive >= 0.7:
        warnings.append("收益主要来自单一区间，可能过拟合")
    for r in results:
        counts = r.get("tradable_selected_etf_counts") or {}; total = sum([_safe_float(v) for v in counts.values()])
        if total > 0 and _safe_float(counts.get("159915.SZ")) / total >= 0.6: warnings.append("159915.SZ 选择占比过高，存在风格集中风险"); break
    if any(_safe_float(r.get("turnover")) > 5 for r in results): warnings.append("存在过度交易风险")
    score = max(0, 100 - len(warnings) * 15 - neg * 5)
    overfit = any("过拟合" in w for w in warnings)
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "periods": periods,
            "best_period": best.get("period_name") if best else None, "worst_period": worst.get("period_name") if worst else None,
            "average_return_pct": round(sum(valid_returns) / float(len(valid_returns)), 4) if valid_returns else 0.0,
            "median_return_pct": round(_median(valid_returns), 4),
            "average_annualized_return_pct": round(sum(ann) / float(len(ann)), 4) if ann else 0.0,
            "max_drawdown_worst_pct": round(max(dds), 4) if dds else 0.0, "max_drawdown_worst_period": worst_dd.get("period_name") if worst_dd else None,
            "max_drawdown_average_pct": round(sum(dds) / float(len(dds)), 4) if dds else 0.0,
            "positive_period_count": pos, "negative_period_count": neg, "stability_score": score,
            "overfit_warning": "；".join([w for w in warnings if "过拟合" in w]) if overfit else "无明显过拟合警告",
            "continue_shadow_replay_recommended": score >= 60, "live_trading_not_recommended": True,
            "warnings": warnings, "period_results": results}


def write_report(path, summary):
    profitable = [r["period_name"] for r in summary["period_results"] if _safe_float(r.get("total_return_pct")) > 0]
    losing = [r["period_name"] for r in summary["period_results"] if _safe_float(r.get("total_return_pct")) < 0]
    lines = ["# 历史多时段区间验证报告", "", "## 1. 总体结论", "- 稳定性评分：{0}".format(summary["stability_score"]), "- 风险警告：{0}".format("；".join(summary.get("warnings") or ["无"])), "", "## 2. 哪些区间赚钱", "- {0}".format("、".join(profitable) if profitable else "无"), "", "## 3. 哪些区间亏损", "- {0}".format("、".join(losing) if losing else "无"), "", "## 4. 最差区间", "- {0}".format(summary.get("worst_period")), "", "## 5. 最大回撤最严重区间", "- {0}（{1}%）".format(summary.get("max_drawdown_worst_period"), summary.get("max_drawdown_worst_pct")), "", "## 6. 是否依赖单一 ETF", "- {0}".format("是，请关注选择分布。" if any("159915" in w for w in summary.get("warnings", [])) else "未发现 159915.SZ 过度集中。"), "", "## 7. 是否过度交易", "- {0}".format("是" if any("过度交易" in w for w in summary.get("warnings", [])) else "否"), "", "## 8. 是否可能过拟合", "- {0}".format(summary.get("overfit_warning")), "", "## 9. 是否建议继续真实影子盘", "- {0}".format("建议继续真实影子盘观察。" if summary.get("continue_shadow_replay_recommended") else "暂不建议继续扩大验证前提下的真实影子盘。"), "", "## 10. 是否不建议实盘", "- 不建议实盘；本模块只读历史行情和本地产物，不构成交易建议。", "", "## 11. 下一步建议", "- 优先复核亏损区间、最大回撤、候选池有效性和 ETF 选择集中度。", ""]
    with open(path, "w", encoding="utf-8") as handle: handle.write("\n".join(lines))


def write_summary_csv(path, results):
    fields = ["period_name", "start_date", "end_date", "trading_days", "initial_cash", "final_asset", "total_return_pct", "annualized_return_pct", "max_drawdown_pct", "total_trades", "closed_trades", "win_rate", "average_holding_days", "turnover", "open_positions", "realized_pnl", "unrealized_pnl", "candidate_pool_valid"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(results)


def run_batch(periods, output_dir, cfg=None, rotation=None, xtdata=None):
    cfg = cfg or load_raw_config(); rotation = rotation or cfg.get("etf_rotation", {})
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("批量历史回放要求 live_trading_enabled=false，且不会修改该配置。")
    tradable = single._unique_symbols(cfg.get("allowed_stocks") or rotation.get("etf_pool") or [])
    benchmarks = single._unique_symbols(rotation.get("market_regime_indexes") or [])
    symbols = single._unique_symbols(tradable + benchmarks)
    min_start, max_end = min(p["start_date"] for p in periods), max(p["end_date"] for p in periods)
    data, dates = single.load_history(symbols, min_start, max_end, xtdata=xtdata)
    results = []
    for idx, period in enumerate(periods):
        out = os.path.join(output_dir, "period_{0:03d}".format(idx + 1)); _mkdir(out)
        try:
            single.replay(cfg, rotation, tradable, benchmarks, data, dates, period["start_date"], period["end_date"], out)
            with open(os.path.join(out, "replay_summary.json"), "r", encoding="utf-8") as handle: summary = json.load(handle)
            results.append(normalize_period_result(period, summary))
        except Exception as exc:
            warning = "区间回放失败: {0}".format(exc)
            failed = {"trading_days": 0, "initial_cash": cfg.get("shadow_trading", {}).get("initial_cash"), "final_asset": None, "total_return_pct": None, "annualized_return_pct": None, "max_drawdown_pct": None, "total_trades": 0, "closed_trades": 0, "win_rate": None, "average_holding_days": None, "turnover": 0, "open_positions": False, "realized_pnl": 0, "unrealized_pnl": 0, "tradable_selected_etf_counts": {}, "benchmark_counts": {}, "candidate_pool_valid": False, "warnings": [warning]}
            _json(os.path.join(out, "replay_summary.json"), failed)
            with open(os.path.join(out, "trades.csv"), "w", encoding="utf-8") as handle:
                handle.write("trade_date,stock_code,side,volume,plan_price,fill_price,gross_amount,commission\n")
            with open(os.path.join(out, "equity_curve.csv"), "w", encoding="utf-8") as handle:
                handle.write("date,total_asset,cash,market_value,floating_pnl\n")
            with open(os.path.join(out, "replay_report.md"), "w", encoding="utf-8") as handle:
                handle.write("# 区间回放失败\n\n- {0}\n".format(warning))
            results.append(normalize_period_result(period, failed, warning))
    summary = build_batch_summary(periods, results)
    _json(os.path.join(output_dir, "batch_summary.json"), summary)
    write_report(os.path.join(output_dir, "batch_report.md"), summary)
    write_summary_csv(os.path.join(output_dir, "batch_summary.csv"), results)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="历史多时段区间验证（只模拟，不交易）")
    parser.add_argument("--start"); parser.add_argument("--end"); parser.add_argument("--initial-cash", type=float)
    parser.add_argument("--periods-file"); parser.add_argument("--output-dir", default=os.path.join(ROOT, "shadow_replay_batch"))
    args = parser.parse_args(argv)
    cfg = load_raw_config()
    if args.initial_cash is not None:
        cfg.setdefault("shadow_trading", {})["initial_cash"] = args.initial_cash
    periods = load_periods(args.periods_file) if args.periods_file else default_periods()
    if args.start or args.end:
        if not (args.start and args.end): raise RuntimeError("--start 与 --end 必须同时提供")
        periods = [{"period_name": "自定义区间", "start_date": args.start, "end_date": args.end}]
    stamp = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    out = args.output_dir if os.path.basename(args.output_dir).startswith("run_") else os.path.join(args.output_dir, stamp)
    _mkdir(out)
    run_batch(periods, out, cfg=cfg)
    print("[OK] 历史多时段区间验证完成: {0}".format(out))


if __name__ == "__main__":
    main()
