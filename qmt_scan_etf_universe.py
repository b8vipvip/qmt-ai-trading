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
DEFAULT_FIXED_POOL = ["510300.SH", "510500.SH", "512100.SH", "159915.SZ", "588000.SH"]
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
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


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


def discover_etfs(cfg, xtdata=None):
    """Return metadata rows from QMT when available, otherwise local config rows."""
    configured = cfg.get("etf_universe_scan", {}) if isinstance(cfg.get("etf_universe_scan"), dict) else {}
    local = configured.get("local_etfs") or configured.get("etf_pool") or cfg.get("allowed_stocks") or DEFAULT_FIXED_POOL
    rows = []
    if xtdata is not None:
        for sector in ["沪深ETF", "ETF", "全部ETF"]:
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


def dedupe_records(records, mode="tracking_index", max_per_group=1):
    eligible = sorted([r for r in records if r.get("eligible")], key=lambda x: x.get("score", 0), reverse=True)
    counts, result = {}, []
    for row in eligible:
        key = row.get("tracking_index") if mode == "tracking_index" else row.get("stock_name")
        key = key or row.get("stock_code")
        if counts.get(key, 0) < int(max_per_group or 1):
            result.append(row); counts[key] = counts.get(key, 0) + 1
    return result


def run_scan(cfg=None, xtdata=None, output_dir=OUTPUT_DIR):
    cfg = cfg or load_raw_config()
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("ETF 候选池扫描要求 live_trading_enabled=false，且不会修改该配置。")
    settings = cfg.get("etf_universe_scan", {}) if isinstance(cfg.get("etf_universe_scan"), dict) else {}
    rows = discover_etfs(cfg, xtdata)
    codes = [r["stock_code"] for r in rows]
    start = settings.get("lookback_start_date") or _default_start()
    end = settings.get("lookback_end_date") or datetime.date.today().strftime("%Y-%m-%d")
    data, unused_dates = replay_data.load_history(codes, start, end, xtdata=xtdata) if codes else ({"close": {}, "amount": {}}, [])
    records = []
    by_code = dict((r["stock_code"], r) for r in rows)
    for code in codes:
        try:
            records.append(evaluate_etf(by_code[code], _series(data["close"], code), _series(data["amount"], code), settings))
        except Exception as exc:
            row = by_code[code]
            records.append({"stock_code": code, "stock_name": row.get("stock_name") or code, "category": row.get("category") or "未知",
                            "tracking_index": row.get("tracking_index") or "", "listed_days": 0, "avg_amount_20d": 0.0,
                            "return_20d": 0.0, "return_60d": 0.0, "max_drawdown_60d": 0.0,
                            "annualized_volatility_60d": 0.0, "score": 0.0, "eligible": False,
                            "skip_reason": "行情读取失败: {0}".format(exc)})
    expanded = dedupe_records(records, settings.get("dedupe_by", "tracking_index"), settings.get("max_per_group", 1))
    payload = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "mode": "READ_ONLY_RESEARCH",
               "safety": {"trading_functions_called": False, "config_modified": False, "live_trading_enabled_modified": False},
               "settings": settings, "total_count": len(records), "eligible_count": len([r for r in records if r.get("eligible")]),
               "expanded_count": len(expanded), "records": records}
    expanded_payload = {"generated_at": payload["generated_at"], "mode": "READ_ONLY_RESEARCH", "expanded_etf_pool": [r["stock_code"] for r in expanded], "records": expanded}
    _mkdir(output_dir)
    _json(os.path.join(output_dir, "etf_universe_scan_latest.json"), payload)
    _json(os.path.join(output_dir, "expanded_etf_pool_latest.json"), expanded_payload)
    with open(os.path.join(output_dir, "expanded_etf_pool_latest.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(expanded_payload["expanded_etf_pool"]) + ("\n" if expanded_payload["expanded_etf_pool"] else ""))
    write_markdown(os.path.join(output_dir, "etf_universe_scan_latest.md"), payload, expanded_payload)
    return payload, expanded_payload


def write_markdown(path, payload, expanded):
    lines = ["# 全市场 ETF 候选池扫描（只读研究）", "", "- 模式：{0}".format(payload.get("mode")),
             "- 扫描数量：{0}".format(payload.get("total_count")), "- 合格数量：{0}".format(payload.get("eligible_count")),
             "- 扩展池数量：{0}".format(payload.get("expanded_count")), "- 不修改 config.json / allowed_stocks / live_trading_enabled。", "",
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
    args = parser.parse_args(argv)
    from xtquant import xtdata
    payload, expanded = run_scan(xtdata=xtdata, output_dir=args.output_dir)
    print("[OK] ETF 候选池扫描完成: eligible={0}, expanded={1}".format(payload.get("eligible_count"), expanded.get("expanded_etf_pool")))


if __name__ == "__main__":
    main()
