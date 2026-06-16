# -*- coding: utf-8 -*-
"""Batch historical ETF shadow replay validation; read-only and never trades."""
from __future__ import print_function

import argparse
import csv
import datetime
import json
import math
import os
import time
import traceback

import qmt_shadow_replay as single
from data_tools.etf_universe import load_raw_config

ROOT = os.path.dirname(os.path.abspath(__file__))
DATE_FMT = "%Y-%m-%d"


def _now_text():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _safe_message(value):
    text = str(value)
    # Avoid accidentally leaking common secret/account key-value pairs in logs/status.
    import re
    text = re.sub(r"(?i)(api[_-]?key|token|secret|authorization)\s*[:=]\s*([^\s,;}]+)", r"\1=***", text)
    text = re.sub(r"(?i)(account[_-]?id|account)\s*[:=]\s*([A-Za-z0-9_-]{4,})", r"\1=***", text)
    return text


class BatchProgress(object):
    def __init__(self, periods, output_dir, verbose=True, quiet=False, status_interval=10):
        self.periods = periods
        self.output_dir = output_dir
        self.verbose = bool(verbose) and not bool(quiet)
        self.quiet = bool(quiet)
        self.status_interval = max(1, int(status_interval or 10))
        self.started_at = _now_text()
        self.start_time = time.time()
        self.completed_periods = 0
        self.failed_periods = 0
        self.errors = []
        self.warnings = []
        self.current_index = 0
        self.current_period = None
        self.latest_message = ""
        self.last_status_write = 0
        self.logs_dir = os.path.join(ROOT, "logs")
        _mkdir(self.logs_dir)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(self.logs_dir, "shadow_replay_batch_{0}.log".format(stamp))
        self.latest_log_path = os.path.join(self.logs_dir, "shadow_replay_batch_latest.log")
        self.log_handles = [open(self.log_path, "w", encoding="utf-8"), open(self.latest_log_path, "w", encoding="utf-8")]
        self.status_path = os.path.join(ROOT, "shadow_replay_batch", "latest_status.json")
        _mkdir(os.path.dirname(self.status_path))

    def close(self):
        for handle in self.log_handles:
            try:
                handle.close()
            except Exception:
                pass

    def emit(self, message, force_status=False):
        message = _safe_message(message)
        self.latest_message = message
        if self.verbose:
            print(message, flush=True)
        for handle in self.log_handles:
            handle.write(message + "\n")
            handle.flush()
        now = time.time()
        if force_status or now - self.last_status_write >= self.status_interval:
            self.write_status("running")

    def period_payload(self, period):
        if not period:
            return None
        return {"name": period.get("period_name"), "start_date": period.get("start_date"), "end_date": period.get("end_date")}

    def write_status(self, status):
        self.last_status_write = time.time()
        payload = {"status": status, "generated_at": _now_text(), "started_at": self.started_at, "updated_at": _now_text(),
                   "elapsed_seconds": round(time.time() - self.start_time, 3), "total_periods": len(self.periods),
                   "current_index": self.current_index, "current_period": self.period_payload(self.current_period),
                   "completed_periods": self.completed_periods, "failed_periods": self.failed_periods,
                   "latest_message": self.latest_message, "output_dir": _rel_output(self.output_dir),
                   "errors": self.errors, "warnings": self.warnings}
        _json(self.status_path, payload)


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
        handle.write("\n")
        handle.flush()


def _rel_output(path):
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except Exception:
        return path


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
        ("2026年至今", "2026-01-01", _date_text(this_year_end)),
        ("2023年至今", "2023-01-01", _date_text(this_year_end)),
        ("最近3个月", _date_text(this_year_end - datetime.timedelta(days=91)), _date_text(this_year_end)),
        ("最近6个月", _date_text(this_year_end - datetime.timedelta(days=183)), _date_text(this_year_end)),
        ("最近12个月", _date_text(this_year_end - datetime.timedelta(days=365)), _date_text(this_year_end)),
        ("最近18个月", _date_text(this_year_end - datetime.timedelta(days=548)), _date_text(this_year_end)),
        ("最近24个月", _date_text(this_year_end - datetime.timedelta(days=730)), _date_text(this_year_end)),
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


def _period_year_bounds(result):
    try:
        start = _parse_date(result.get("start_date")); end = _parse_date(result.get("end_date"))
        return start, end
    except Exception:
        return None, None


def _period_category(result):
    name = str(result.get("period_name") or "")
    start, end = _period_year_bounds(result)
    if "2023年至今" in name or name in ("full_period", "全周期", "长期全周期"):
        return "full_period"
    if "最近" in name or "rolling" in name.lower():
        return "rolling"
    if start and end and start.month == 1 and start.day == 1 and start.year == end.year:
        if (end.month == 12 and end.day == 31) or end == _today():
            return "non_overlapping"
    return "non_overlapping"


def _split_period_results(results):
    groups = {"non_overlapping": [], "rolling": [], "full_period": []}
    for result in results:
        groups[_period_category(result)].append(result)
    return groups


def _basic_period_summary(results):
    valid_returns = [_safe_float(r.get("total_return_pct")) for r in results if r.get("total_return_pct") is not None]
    ann = [_safe_float(r.get("annualized_return_pct")) for r in results if r.get("annualized_return_pct") is not None]
    dds = [_safe_float(r.get("max_drawdown_pct")) for r in results if r.get("max_drawdown_pct") is not None]
    win_rates = [_safe_float(r.get("win_rate")) for r in results if r.get("win_rate") is not None]
    turnovers = [_safe_float(r.get("turnover")) for r in results if r.get("turnover") is not None]
    best = max(results, key=lambda r: _safe_float(r.get("total_return_pct"))) if results else None
    worst = min(results, key=lambda r: _safe_float(r.get("total_return_pct"))) if results else None
    worst_dd = max(results, key=lambda r: _safe_float(r.get("max_drawdown_pct"))) if results else None
    pos = len([r for r in results if _safe_float(r.get("total_return_pct")) > 0])
    neg = len([r for r in results if _safe_float(r.get("total_return_pct")) < 0])
    return {"period_count": len(results), "period_names": [r.get("period_name") for r in results],
            "best_period": best.get("period_name") if best else None, "worst_period": worst.get("period_name") if worst else None,
            "average_return_pct": round(sum(valid_returns) / float(len(valid_returns)), 4) if valid_returns else 0.0,
            "median_return_pct": round(_median(valid_returns), 4),
            "average_annualized_return_pct": round(sum(ann) / float(len(ann)), 4) if ann else 0.0,
            "max_drawdown_worst_pct": round(max(dds), 4) if dds else 0.0,
            "max_drawdown_worst_period": worst_dd.get("period_name") if worst_dd else None,
            "max_drawdown_average_pct": round(sum(dds) / float(len(dds)), 4) if dds else 0.0,
            "average_win_rate": round(sum(win_rates) / float(len(win_rates)), 4) if win_rates else None,
            "average_turnover": round(sum(turnovers) / float(len(turnovers)), 4) if turnovers else 0.0,
            "positive_period_count": pos, "negative_period_count": neg}


def build_batch_summary(periods, results):
    groups = _split_period_results(results)
    core_results = groups["non_overlapping"] or results
    non_overlapping_summary = _basic_period_summary(core_results)
    rolling_summary = _basic_period_summary(groups["rolling"])
    full_period_summary = _basic_period_summary(groups["full_period"])
    warnings = []
    overfit_flags = []
    underfit_flags = []
    risk_flags = []
    if any(r.get("candidate_pool_valid") is False for r in results): warnings.append("候选池存在无效区间，稳定性不合格")
    if any(_safe_float(r.get("max_drawdown_pct")) > 15 for r in core_results): risk_flags.append("任一年度最大回撤超过15%，高风险")
    full_max_dd = full_period_summary.get("max_drawdown_worst_pct") or 0.0
    if full_max_dd > 20: risk_flags.append("长周期最大回撤超过20%，不适合实盘")
    if any(_safe_float(r.get("turnover")) > 5 for r in results): risk_flags.append("turnover 偏高，存在过度交易风险")
    if non_overlapping_summary.get("negative_period_count", 0) > len(core_results) / 2.0:
        warnings.append("多数区间亏损（年度非重叠口径），策略不稳"); underfit_flags.append("多数年度收益低或亏损")
    positives = [max(0.0, _safe_float(r.get("total_return_pct"))) for r in core_results]
    total_positive = sum(positives)
    if total_positive > 0 and max(positives or [0]) / total_positive >= 0.7:
        overfit_flags.append("收益主要来自单一年度区间，可能过拟合")
    core_returns = [_safe_float(r.get("total_return_pct")) for r in core_results if r.get("total_return_pct") is not None]
    if full_period_summary.get("average_return_pct", 0) > 0 and core_returns and (max(core_returns) - min(core_returns) >= 15 or non_overlapping_summary.get("negative_period_count", 0) > 0):
        overfit_flags.append("full_period 表现较好但年度区间分化严重，可能过拟合")
    rolling_returns = [_safe_float(r.get("total_return_pct")) for r in groups["rolling"] if r.get("total_return_pct") is not None]
    early_losses = [r for r in core_results if str(r.get("period_name") or "")[:4] in ("2023", "2024") and _safe_float(r.get("total_return_pct")) < 0]
    if rolling_returns and sum(rolling_returns) / float(len(rolling_returns)) > 5 and early_losses:
        overfit_flags.append("最近滚动区间较好但早期年份亏损，存在近期行情依赖风险")
    if len(core_results) >= 2 and _safe_float(core_results[0].get("total_return_pct")) > 0 and _safe_float(core_results[-1].get("total_return_pct")) < 0:
        overfit_flags.append("样本内较好、样本外较差，存在参数或策略版本过拟合风险")
    win_rates = [_safe_float(r.get("win_rate")) for r in core_results if r.get("win_rate") is not None]
    if win_rates and sum(win_rates) / float(len(win_rates)) < 0.35:
        underfit_flags.append("长期胜率很低")
    if non_overlapping_summary.get("positive_period_count", 0) <= len(core_results) / 3.0 and core_results:
        underfit_flags.append("大部分市场环境无法盈利")
    if non_overlapping_summary.get("average_return_pct", 0) < 3 and non_overlapping_summary.get("max_drawdown_average_pct", 0) > 10:
        underfit_flags.append("收益低但回撤仍高，规则可能无效")
    for r in results:
        counts = r.get("tradable_selected_etf_counts") or {}; total = sum([_safe_float(v) for v in counts.values()])
        if total > 0 and _safe_float(counts.get("159915.SZ")) / total >= 0.6: risk_flags.append("159915.SZ 选择占比过高，存在风格集中风险"); break
    warnings.extend(overfit_flags + underfit_flags + risk_flags)
    overfitting_score = max(0, 100 - len(overfit_flags) * 25)
    underfitting_score = max(0, 100 - len(underfit_flags) * 25)
    risk_penalty = len(risk_flags) * 20 + non_overlapping_summary.get("negative_period_count", 0) * 5
    regime_fit_score = max(0, 100 - len(underfit_flags) * 15 - len(overfit_flags) * 10 - non_overlapping_summary.get("negative_period_count", 0) * 8)
    robustness_score = max(0, min(overfitting_score, underfitting_score, regime_fit_score) - risk_penalty)
    stability_score = robustness_score
    recommendation = []
    if overfit_flags: recommendation.append("降低近期样本权重，使用年度非重叠区间做主评分，并增加样本外验证")
    if underfit_flags: recommendation.append("复核入场/出场规则、候选池和市场状态过滤，避免规则整体无效")
    if risk_flags: recommendation.append("优先降低回撤、换手率和单一 ETF 集中度")
    if not recommendation: recommendation.append("可继续影子盘观察，但仍不构成实盘建议")
    overfit_warning = "；".join(overfit_flags) if overfit_flags else "无明显过拟合警告"
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "periods": periods,
            "non_overlapping_summary": non_overlapping_summary, "rolling_summary": rolling_summary, "full_period_summary": full_period_summary,
            "overfitting_score": overfitting_score, "underfitting_score": underfitting_score, "regime_fit_score": regime_fit_score,
            "robustness_score": robustness_score, "optimization_recommendation": "；".join(recommendation),
            "best_period": non_overlapping_summary.get("best_period"), "worst_period": non_overlapping_summary.get("worst_period"),
            "average_return_pct": non_overlapping_summary.get("average_return_pct"), "median_return_pct": non_overlapping_summary.get("median_return_pct"),
            "average_annualized_return_pct": non_overlapping_summary.get("average_annualized_return_pct"),
            "max_drawdown_worst_pct": non_overlapping_summary.get("max_drawdown_worst_pct"), "max_drawdown_worst_period": non_overlapping_summary.get("max_drawdown_worst_period"),
            "max_drawdown_average_pct": non_overlapping_summary.get("max_drawdown_average_pct"),
            "positive_period_count": non_overlapping_summary.get("positive_period_count"), "negative_period_count": non_overlapping_summary.get("negative_period_count"),
            "stability_score": stability_score, "overfit_warning": overfit_warning,
            "underfit_warning": "；".join(underfit_flags) if underfit_flags else "无明显欠拟合警告",
            "risk_warning": "；".join(risk_flags) if risk_flags else "无明显风控警告",
            "continue_shadow_replay_recommended": robustness_score >= 60 and full_max_dd <= 20,
            "live_trading_not_recommended": True, "warnings": warnings, "period_results": results}

def _period_table(results):
    if not results:
        return "- 无"
    lines = ["| 区间 | 起止 | 收益% | 年化% | 最大回撤% | 胜率 | 换手率 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in results:
        lines.append("| {0} | {1} 至 {2} | {3} | {4} | {5} | {6} | {7} |".format(r.get("period_name"), r.get("start_date"), r.get("end_date"), r.get("total_return_pct"), r.get("annualized_return_pct"), r.get("max_drawdown_pct"), r.get("win_rate"), r.get("turnover")))
    return "\n".join(lines)


def write_report(path, summary):
    groups = _split_period_results(summary.get("period_results") or [])
    lines = ["# 历史多时段区间验证报告", "",
             "## 1. 总体结论", "- 核心评分仅使用年度非重叠区间，滚动区间只观察近期状态，2023年至今只展示长周期表现。",
             "- 稳定性评分：{0}".format(summary.get("stability_score")),
             "- 鲁棒性评分：{0}".format(summary.get("robustness_score")),
             "- 市场环境适配评分：{0}".format(summary.get("regime_fit_score")),
             "- 风险警告：{0}".format("；".join(summary.get("warnings") or ["无"])), "",
             "## 2. 年度非重叠表现", _period_table(groups.get("non_overlapping") or []), "",
             "## 3. 滚动区间表现", _period_table(groups.get("rolling") or []), "",
             "## 4. 长周期表现", _period_table(groups.get("full_period") or []), "",
             "## 5. 过拟合风险", "- 评分：{0}".format(summary.get("overfitting_score")), "- 诊断：{0}".format(summary.get("overfit_warning")), "",
             "## 6. 欠拟合风险", "- 评分：{0}".format(summary.get("underfitting_score")), "- 诊断：{0}".format(summary.get("underfit_warning")), "",
             "## 7. 风控风险", "- {0}".format(summary.get("risk_warning")), "",
             "## 8. 是否建议继续影子盘", "- {0}".format("建议继续真实影子盘观察。" if summary.get("continue_shadow_replay_recommended") else "暂不建议继续扩大验证前提下的真实影子盘。"), "",
             "## 9. 是否不建议实盘", "- {0}".format("不建议实盘；本模块只读历史行情和本地产物，不构成交易建议。" if summary.get("live_trading_not_recommended") else "仍需人工复核。"), "",
             "## 10. 下一步优化方向", "- {0}".format(summary.get("optimization_recommendation")), ""]
    with open(path, "w", encoding="utf-8") as handle: handle.write("\n".join(lines))

def write_summary_csv(path, results):
    fields = ["period_name", "start_date", "end_date", "trading_days", "initial_cash", "final_asset", "total_return_pct", "annualized_return_pct", "max_drawdown_pct", "total_trades", "closed_trades", "win_rate", "average_holding_days", "turnover", "open_positions", "realized_pnl", "unrealized_pnl", "candidate_pool_valid"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(results)


def run_batch(periods, output_dir, cfg=None, rotation=None, xtdata=None, progress=None):
    cfg = cfg or load_raw_config(); rotation = rotation or cfg.get("etf_rotation", {})
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("批量历史回放要求 live_trading_enabled=false，且不会修改该配置。")
    tradable = single._unique_symbols(cfg.get("allowed_stocks") or rotation.get("etf_pool") or [])
    benchmarks = single._unique_symbols(rotation.get("market_regime_indexes") or [])
    symbols = single._unique_symbols(tradable + benchmarks)
    min_start, max_end = min(p["start_date"] for p in periods), max(p["end_date"] for p in periods)
    if progress:
        progress.emit("[INFO] 本次共 {0} 个区间".format(len(periods)), force_status=True)
        progress.emit("[INFO] 下载/读取历史行情: {0} 至 {1}".format(min_start, max_end), force_status=True)
    data, dates = single.load_history(symbols, min_start, max_end, xtdata=xtdata)
    if progress:
        progress.emit("[INFO] 历史行情准备完成", force_status=True)
    results = []
    for idx, period in enumerate(periods):
        if progress:
            progress.current_index = idx + 1
            progress.current_period = period
            progress.emit("\n[{0}/{1}] 开始: {2} 至 {3}".format(idx + 1, len(periods), period.get("start_date"), period.get("end_date")), force_status=True)
            progress.emit("[{0}/{1}] 下载/读取历史行情...".format(idx + 1, len(periods)), force_status=True)
        period_start = time.time()
        out = os.path.join(output_dir, "period_{0:03d}".format(idx + 1)); _mkdir(out)
        try:
            single.replay(cfg, rotation, tradable, benchmarks, data, dates, period["start_date"], period["end_date"], out)
            with open(os.path.join(out, "replay_summary.json"), "r", encoding="utf-8") as handle: summary = json.load(handle)
            result = normalize_period_result(period, summary)
            results.append(result)
            if progress:
                progress.completed_periods += 1
                progress.emit("[{0}/{1}] 回放完成: 收益 {2}%, 最大回撤 {3}%, 交易 {4} 次, 用时 {5:.1f} 秒".format(idx + 1, len(periods), result.get("total_return_pct"), result.get("max_drawdown_pct"), result.get("total_trades"), time.time() - period_start), force_status=True)
        except Exception as exc:
            warning = "区间回放失败: {0}".format(_safe_message(exc))
            if progress:
                progress.failed_periods += 1
                progress.errors.append({"period": progress.period_payload(period), "error": warning})
                progress.emit("[{0}/{1}] 回放失败: {2}; 继续下一个区间".format(idx + 1, len(periods), warning), force_status=True)
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
    failed_count = len([r for r in results if r.get("candidate_pool_valid") is False and any("区间回放失败" in str(w) for w in r.get("metric_warnings", []))])
    if failed_count:
        summary.setdefault("warnings", []).append("{0} 个区间回放失败，已跳过并继续".format(failed_count))
    _json(os.path.join(output_dir, "batch_summary.json"), summary)
    write_report(os.path.join(output_dir, "batch_report.md"), summary)
    write_summary_csv(os.path.join(output_dir, "batch_summary.csv"), results)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="历史多时段区间验证（只模拟，不交易）")
    parser.add_argument("--start"); parser.add_argument("--end"); parser.add_argument("--initial-cash", type=float)
    parser.add_argument("--periods-file"); parser.add_argument("--output-dir", default=os.path.join(ROOT, "shadow_replay_batch"))
    parser.add_argument("--verbose", action="store_true", default=True)
    parser.add_argument("--quiet", action="store_true", default=False)
    parser.add_argument("--status-interval", type=int, default=10)
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
    progress = BatchProgress(periods, out, verbose=args.verbose, quiet=args.quiet, status_interval=args.status_interval)
    try:
        progress.emit("[START] 历史多时段回放开始", force_status=True)
        progress.emit("[INFO] 输出目录: {0}".format(_rel_output(out)), force_status=True)
        run_batch(periods, out, cfg=cfg, progress=progress)
        progress.emit("[DONE] 历史多时段回放完成，总用时 {0:.1f} 秒".format(time.time() - progress.start_time), force_status=True)
        progress.write_status("done")
    except Exception as exc:
        message = "批量回放失败: {0}".format(_safe_message(exc))
        progress.errors.append({"error": message})
        progress.emit("[ERROR] " + message, force_status=True)
        progress.emit(traceback.format_exc(), force_status=True)
        progress.write_status("failed")
        raise
    finally:
        progress.close()


if __name__ == "__main__":
    main()
