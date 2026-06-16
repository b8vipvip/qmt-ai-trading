# -*- coding: utf-8 -*-
"""Read-only full-market ETF universe scanner for research.

This module only reads ETF metadata/history and writes research artifacts under
research/etf_universe_scan/. It never imports or exposes real trading functions.
"""
from __future__ import print_function

import argparse
import datetime
import json
import math
import os
import re

from data_tools.etf_rotation_selector import calculate_max_drawdown, calculate_volatility
from data_tools.etf_universe import load_raw_config
import qmt_shadow_replay as replay_data

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT, "research", "etf_universe_scan")
LOG_DIR = os.path.join(ROOT, "logs")
STATUS_PATH = os.path.join(OUTPUT_DIR, "latest_status.json")
DEFAULT_FIXED_POOL = ["510300.SH", "510500.SH", "512100.SH", "159915.SZ", "588000.SH"]
DEFAULT_MIN_SCORE = 0.0
DEFAULT_MAX_EXPANDED_ETFS = 30
DEFAULT_MAX_PER_TRACKING_INDEX = 1
DEFAULT_MAX_PER_CATEGORY = 3
EXCLUDE_KEYWORDS = [
    ("货币", "货币ETF"), ("现金", "货币ETF"), ("债", "债券ETF"), ("国债", "债券ETF"),
    ("黄金", "商品ETF"), ("商品", "商品ETF"), ("豆粕", "商品ETF"), ("有色", "商品ETF"),
    ("QDII", "跨境QDII ETF"), ("标普", "跨境QDII ETF"), ("纳指", "跨境QDII ETF"),
    ("日经", "跨境QDII ETF"), ("恒生", "跨境QDII ETF"), ("港股", "跨境QDII ETF"),
    ("杠杆", "杠杆/特殊结构ETF"), ("反向", "杠杆/特殊结构ETF"), ("增强", "特殊结构ETF"),
]


def _mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _json(path, value):
    parent = os.path.dirname(path)
    if parent:
        _mkdir(parent)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()


class ProgressReporter(object):
    def __init__(self, log_prefix, status_path, quiet=False):
        self.quiet = quiet
        self.started_at = datetime.datetime.now()
        self.status_path = status_path
        _mkdir(LOG_DIR)
        stamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        self.latest_log = os.path.join(LOG_DIR, log_prefix + "_latest.log")
        self.stamped_log = os.path.join(LOG_DIR, log_prefix + "_" + stamp + ".log")
        self.handles = [open(self.latest_log, "w", encoding="utf-8"), open(self.stamped_log, "w", encoding="utf-8")]
        self.status = {"status": "running", "started_at": self.started_at.strftime("%Y-%m-%dT%H:%M:%S"), "updated_at": None,
                       "elapsed_seconds": 0, "total_etfs": 0, "current_index": 0, "current_code": "", "completed_etfs": 0,
                       "eligible_count": 0, "expanded_count": 0, "latest_message": "", "errors": [], "warnings": []}

    def close(self):
        for handle in self.handles:
            try: handle.close()
            except Exception: pass

    def emit(self, message):
        if not self.quiet:
            print(message, flush=True)
        for handle in self.handles:
            handle.write(message + "\n")
            handle.flush()

    def update(self, latest_message=None, **kwargs):
        if latest_message is not None:
            self.status["latest_message"] = latest_message
        self.status.update(kwargs)
        now = datetime.datetime.now()
        self.status["updated_at"] = now.strftime("%Y-%m-%dT%H:%M:%S")
        self.status["elapsed_seconds"] = int((now - self.started_at).total_seconds())
        _json(self.status_path, self.status)

    def fail(self, error):
        errors = list(self.status.get("errors") or [])
        errors.append(str(error))
        self.update(status="failed", errors=errors, latest_message="运行失败")
        self.emit("[FAILED] {0}".format(error))

    def done(self, total_etfs=0, eligible_count=0, expanded_count=0):
        self.update(status="done", total_etfs=total_etfs, completed_etfs=total_etfs, eligible_count=eligible_count, expanded_count=expanded_count, latest_message="扫描完成")


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


def _mean(values):
    return sum(values) / float(len(values)) if values else 0.0


def _return(values, days):
    return values[-1] / values[-1 - days] - 1.0 if len(values) > days and values[-1 - days] > 0 else 0.0


def _compact_date(value):
    return value.replace("-", "")


def _default_start(days=520):
    return (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")


def _normalize_code(code):
    text = str(code or "").strip().upper()
    if re.match(r"^\d{6}\.(SH|SZ)$", text):
        return text
    return ""


def _instrument_name(xtdata, code):
    try:
        detail = xtdata.get_instrument_detail(code) or {}
        return detail.get("InstrumentName") or detail.get("ProductName") or detail.get("name") or code
    except Exception:
        return code


def discover_etfs(cfg, xtdata=None, sectors=None, local_only=False):
    """Return metadata rows from QMT when available, otherwise local config rows."""
    configured = cfg.get("etf_universe_scan", {}) if isinstance(cfg.get("etf_universe_scan"), dict) else {}
    local = configured.get("local_etfs") or configured.get("etf_pool") or cfg.get("allowed_stocks") or DEFAULT_FIXED_POOL
    rows = []
    if xtdata is not None and not local_only:
        for sector in (sectors or ["沪深ETF", "ETF", "全部ETF"]):
            try:
                for code in xtdata.get_stock_list_in_sector(sector) or []:
                    code = _normalize_code(code)
                    if code:
                        rows.append({"stock_code": code, "stock_name": _instrument_name(xtdata, code)})
            except Exception:
                pass
    if not rows:
        for item in local:
            if isinstance(item, dict):
                code = _normalize_code(item.get("stock_code") or item.get("code"))
                if code:
                    rows.append({"stock_code": code, "stock_name": item.get("stock_name") or item.get("name") or code,
                                 "category": item.get("category"), "tracking_index": item.get("tracking_index")})
            else:
                code = _normalize_code(item)
                if code:
                    rows.append({"stock_code": code, "stock_name": code})
    dedup, seen = [], set()
    for row in rows:
        code = row.get("stock_code")
        if code not in seen:
            dedup.append(row); seen.add(code)
    return dedup


def classify_etf(row):
    name = str(row.get("stock_name") or row.get("stock_code") or "").upper()
    category = row.get("category") or "权益ETF"
    for keyword, reason in EXCLUDE_KEYWORDS:
        if keyword.upper() in name:
            return category, reason
    return category, ""


def _series(frame, code):
    
    values = []
    for col in list(frame.columns):
        try:
            values.append(_safe_float(frame.loc[code, col]))
        except Exception:
            values.append(0.0)
    return values


def evaluate_etf(row, closes, amounts, settings):
    code = row.get("stock_code")
    category, excluded = classify_etf(row)
    record = {"stock_code": code, "stock_name": row.get("stock_name") or code, "category": category,
              "tracking_index": row.get("tracking_index") or "", "listed_days": len([x for x in closes if x > 0]),
              "avg_amount_20d": 0.0, "return_20d": 0.0, "return_60d": 0.0,
              "max_drawdown_60d": 0.0, "annualized_volatility_60d": 0.0,
              "score": 0.0, "eligible": False, "skip_reason": ""}
    if excluded:
        record["skip_reason"] = excluded; return record
    if record["listed_days"] < int(settings.get("min_listed_days", 252)) or len(closes) < 253:
        record["skip_reason"] = "历史数据不足"; return record
    if closes[-1] <= 0 or amounts[-1] <= 0:
        record["skip_reason"] = "最近交易日无有效价格或成交额"; return record
    recent60 = closes[-60:]
    record.update({"avg_amount_20d": _mean(amounts[-20:]), "return_20d": _return(closes, 20),
                   "return_60d": _return(closes, 60), "max_drawdown_60d": calculate_max_drawdown(recent60),
                   "annualized_volatility_60d": calculate_volatility(recent60)})
    if record["avg_amount_20d"] < float(settings.get("min_avg_amount_20d", 50000000)):
        record["skip_reason"] = "近20日平均成交额低于阈值"; return record
    if record["max_drawdown_60d"] > float(settings.get("max_drawdown_60d", 0.20)):
        record["skip_reason"] = "近60日最大回撤超过阈值"; return record
    if record["annualized_volatility_60d"] > float(settings.get("max_annualized_volatility_60d", 0.45)):
        record["skip_reason"] = "近60日年化波动超过阈值"; return record
    record["score"] = round(record["return_20d"] * 35 + record["return_60d"] * 35 + min(record["avg_amount_20d"] / 100000000.0, 20) - record["max_drawdown_60d"] * 25 - record["annualized_volatility_60d"] * 10, 4)
    record["eligible"] = True
    return record


def build_expanded_records(records, min_score=DEFAULT_MIN_SCORE, max_expanded_etfs=DEFAULT_MAX_EXPANDED_ETFS,
                           max_per_category=DEFAULT_MAX_PER_CATEGORY,
                           max_per_tracking_index=DEFAULT_MAX_PER_TRACKING_INDEX):
    """Filter eligible ETF records into a bounded expanded research pool."""
    min_score = _safe_float(min_score, DEFAULT_MIN_SCORE)
    max_expanded_etfs = int(max_expanded_etfs if max_expanded_etfs is not None else DEFAULT_MAX_EXPANDED_ETFS)
    max_per_category = int(max_per_category if max_per_category is not None else DEFAULT_MAX_PER_CATEGORY)
    max_per_tracking_index = int(max_per_tracking_index if max_per_tracking_index is not None else DEFAULT_MAX_PER_TRACKING_INDEX)
    eligible = sorted([r for r in records if r.get("eligible")], key=lambda x: x.get("score", 0), reverse=True)
    score_filtered = [r for r in eligible if _safe_float(r.get("score")) > min_score]
    filtered_out_by_score = len(eligible) - len(score_filtered)
    category_counts, index_counts, result, group_filtered = {}, {}, [], 0
    for row in score_filtered:
        category = row.get("category") or "未知"
        tracking_index = row.get("tracking_index") or row.get("stock_code")
        if max_per_category > 0 and category_counts.get(category, 0) >= max_per_category:
            group_filtered += 1; continue
        if max_per_tracking_index > 0 and index_counts.get(tracking_index, 0) >= max_per_tracking_index:
            group_filtered += 1; continue
        if max_expanded_etfs > 0 and len(result) >= max_expanded_etfs:
            group_filtered += 1; continue
        result.append(row)
        category_counts[category] = category_counts.get(category, 0) + 1
        index_counts[tracking_index] = index_counts.get(tracking_index, 0) + 1
    return result, {"filtered_out_by_score": filtered_out_by_score, "filtered_out_by_group_limit": group_filtered}


def dedupe_records(records, mode="tracking_index", max_per_group=1):
    # Backward-compatible helper retained for older callers/tests.
    eligible = sorted([r for r in records if r.get("eligible")], key=lambda x: x.get("score", 0), reverse=True)
    counts, result = {}, []
    for row in eligible:
        key = row.get("tracking_index") if mode == "tracking_index" else row.get("stock_name")
        key = key or row.get("stock_code")
        if counts.get(key, 0) < int(max_per_group or 1):
            result.append(row); counts[key] = counts.get(key, 0) + 1
    return result


def run_scan(cfg=None, xtdata=None, output_dir=OUTPUT_DIR, max_etfs=None, sectors=None, local_only=False, status_interval=1, verbose=True, quiet=False, min_score=None, max_expanded_etfs=None, min_avg_amount_20d=None, max_per_category=None, max_per_tracking_index=None):
    cfg = cfg or load_raw_config()
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("ETF 候选池扫描要求 live_trading_enabled=false，且不会修改该配置。")
    settings = dict(cfg.get("etf_universe_scan", {}) if isinstance(cfg.get("etf_universe_scan"), dict) else {})
    if min_avg_amount_20d is not None:
        settings["min_avg_amount_20d"] = float(min_avg_amount_20d)
    settings["min_score"] = DEFAULT_MIN_SCORE if min_score is None else float(min_score)
    settings["max_expanded_etfs"] = DEFAULT_MAX_EXPANDED_ETFS if max_expanded_etfs is None else int(max_expanded_etfs)
    settings["max_per_category"] = DEFAULT_MAX_PER_CATEGORY if max_per_category is None else int(max_per_category)
    settings["max_per_tracking_index"] = DEFAULT_MAX_PER_TRACKING_INDEX if max_per_tracking_index is None else int(max_per_tracking_index)
    reporter = ProgressReporter("etf_universe_scan", os.path.join(output_dir, "latest_status.json"), quiet=(quiet or not verbose))
    try:
        reporter.emit("[START] 全市场 ETF 候选池扫描开始")
        reporter.emit("[INFO] 正在读取 ETF 列表...")
        reporter.update(latest_message="正在读取 ETF 列表")
        rows = discover_etfs(cfg, xtdata, sectors=sectors, local_only=local_only)
        if max_etfs is not None:
            rows = rows[:int(max_etfs)]
        codes = [r["stock_code"] for r in rows]
        reporter.emit("[INFO] ETF 列表读取完成，共 {0} 只".format(len(codes)))
        reporter.update(total_etfs=len(codes), latest_message="ETF 列表读取完成")
        start = settings.get("lookback_start_date") or _default_start()
        end = settings.get("lookback_end_date") or datetime.date.today().strftime("%Y-%m-%d")
        reporter.emit("[INFO] 正在下载/读取历史行情: {0} 至 {1}".format(start, end))
        reporter.update(latest_message="正在下载/读取历史行情")
        data, unused_dates = replay_data.load_history(codes, start, end, xtdata=xtdata) if codes else ({"close": {}, "amount": {}}, [])
        reporter.emit("[INFO] 历史行情读取完成")
        reporter.update(latest_message="历史行情读取完成")
        records = []
        by_code = dict((r["stock_code"], r) for r in rows)
        status_interval = max(1, int(status_interval or 1))
        for idx, code in enumerate(codes, 1):
            reporter.emit("[{0}/{1}] 评分 ETF: {2} ...".format(idx, len(codes), code))
            reporter.update(current_index=idx, current_code=code, completed_etfs=idx - 1, latest_message="正在评分 ETF")
            try:
                record = evaluate_etf(by_code[code], _series(data["close"], code), _series(data["amount"], code), settings)
                records.append(record)
            except Exception as exc:
                row = by_code[code]
                record = {"stock_code": code, "stock_name": row.get("stock_name") or code, "category": row.get("category") or "未知",
                                "tracking_index": row.get("tracking_index") or "", "listed_days": 0, "avg_amount_20d": 0.0,
                                "return_20d": 0.0, "return_60d": 0.0, "max_drawdown_60d": 0.0,
                                "annualized_volatility_60d": 0.0, "score": 0.0, "eligible": False,
                                "skip_reason": "行情读取失败: {0}".format(exc)}
                records.append(record)
            reporter.emit("[{0}/{1}] 完成: eligible={2} score={3}".format(idx, len(codes), record.get("eligible"), record.get("score")))
            if idx % status_interval == 0 or idx == len(codes):
                reporter.update(completed_etfs=idx, eligible_count=len([r for r in records if r.get("eligible")]), latest_message="ETF 评分进度更新")
        expanded, filter_stats = build_expanded_records(records, settings.get("min_score"), settings.get("max_expanded_etfs"), settings.get("max_per_category"), settings.get("max_per_tracking_index"))
        payload = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "mode": "READ_ONLY_RESEARCH",
        "safety": {"trading_functions_called": False, "config_modified": False, "live_trading_enabled_modified": False},
        "settings": settings, "total_count": len(records), "eligible_count": len([r for r in records if r.get("eligible")]),
        "expanded_count": len(expanded), "filtered_out_by_score": filter_stats.get("filtered_out_by_score"),
        "filtered_out_by_group_limit": filter_stats.get("filtered_out_by_group_limit"), "records": records}
        expanded_payload = {"generated_at": payload["generated_at"], "mode": "READ_ONLY_RESEARCH", "expanded_etf_pool": [r["stock_code"] for r in expanded], "records": expanded}
        _mkdir(output_dir)
        _json(os.path.join(output_dir, "etf_universe_scan_latest.json"), payload)
        _json(os.path.join(output_dir, "expanded_etf_pool_latest.json"), expanded_payload)
        with open(os.path.join(output_dir, "expanded_etf_pool_latest.txt"), "w", encoding="utf-8") as handle:
            handle.write("\n".join(expanded_payload["expanded_etf_pool"]) + ("\n" if expanded_payload["expanded_etf_pool"] else ""))
            handle.flush()
        write_markdown(os.path.join(output_dir, "etf_universe_scan_latest.md"), payload, expanded_payload)
        reporter.done(total_etfs=len(records), eligible_count=payload.get("eligible_count"), expanded_count=payload.get("expanded_count"))
        reporter.emit("[DONE] ETF 候选池扫描完成: total={0} eligible={1} expanded={2}".format(len(records), payload.get("eligible_count"), payload.get("expanded_count")))
        return payload, expanded_payload
    except Exception as exc:
        reporter.fail(exc)
        raise
    finally:
        reporter.close()


def write_markdown(path, payload, expanded):
    lines = ["# 全市场 ETF 候选池扫描（只读研究）", "", "- 模式：{0}".format(payload.get("mode")),
             "- 扫描数量：{0}".format(payload.get("total_count")), "- 合格数量：{0}".format(payload.get("eligible_count")),
             "- 扩展池数量：{0}".format(payload.get("expanded_count")), "- 因分数过滤数量：{0}".format(payload.get("filtered_out_by_score")),
             "- 因分组/数量限制过滤数量：{0}".format(payload.get("filtered_out_by_group_limit")), "- 不修改 config.json / allowed_stocks / live_trading_enabled。", "",
             "## Expanded ETF Pool", "```", "\n".join(expanded.get("expanded_etf_pool") or []), "```", "",
             "## 明细", "| 代码 | 名称 | 合格 | 20日成交额 | 60日回撤 | 60日波动 | 分数 | 跳过原因 |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for r in payload.get("records") or []:
        lines.append("| {0} | {1} | {2} | {3:.2f} | {4:.4f} | {5:.4f} | {6} | {7} |".format(r.get("stock_code"), r.get("stock_name"), r.get("eligible"), _safe_float(r.get("avg_amount_20d")), _safe_float(r.get("max_drawdown_60d")), _safe_float(r.get("annualized_volatility_60d")), r.get("score"), r.get("skip_reason")))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="只读全市场 ETF 候选池扫描")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--max-etfs", type=int, default=None)
    parser.add_argument("--sectors", default=None)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--status-interval", type=int, default=1)
    parser.add_argument("--verbose", dest="verbose", action="store_true", default=True)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--max-expanded-etfs", type=int, default=DEFAULT_MAX_EXPANDED_ETFS)
    parser.add_argument("--min-avg-amount-20d", type=float, default=None)
    parser.add_argument("--max-per-category", type=int, default=DEFAULT_MAX_PER_CATEGORY)
    parser.add_argument("--max-per-tracking-index", type=int, default=DEFAULT_MAX_PER_TRACKING_INDEX)
    args = parser.parse_args(argv)
    xtdata = None
    if not args.local_only:
        from qmt_gateway.gateway import QmtGateway
        xtdata = QmtGateway({"live_trading_enabled": False}).data._client()
    sectors = [x.strip() for x in args.sectors.split(",") if x.strip()] if args.sectors else None
    run_scan(xtdata=xtdata, output_dir=args.output_dir, max_etfs=args.max_etfs, sectors=sectors, local_only=args.local_only, status_interval=args.status_interval, verbose=args.verbose, quiet=args.quiet, min_score=args.min_score, max_expanded_etfs=args.max_expanded_etfs, min_avg_amount_20d=args.min_avg_amount_20d, max_per_category=args.max_per_category, max_per_tracking_index=args.max_per_tracking_index)


if __name__ == "__main__":
    main()
