# -*- coding: utf-8 -*-
"""Read-only comparison between fixed ETF pool and scanned expanded ETF pool."""
from __future__ import print_function

import argparse
import copy
import datetime
import json
import os

from data_tools.etf_universe import load_raw_config
import qmt_shadow_replay_batch as batch

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT, "research", "etf_pool_compare")
SCAN_POOL_PATH = os.path.join(ROOT, "research", "etf_universe_scan", "expanded_etf_pool_latest.json")
FIXED_POOL = ["510300.SH", "510500.SH", "512100.SH", "159915.SZ", "588000.SH"]


def _mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {} if default is None else default


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _pool_cfg(cfg, pool):
    research_cfg = copy.deepcopy(cfg)
    research_cfg["live_trading_enabled"] = bool(cfg.get("live_trading_enabled", False))
    research_cfg["allowed_stocks"] = list(pool)
    research_cfg.setdefault("etf_rotation", {})["etf_pool"] = list(pool)
    return research_cfg


def load_expanded_pool(path=SCAN_POOL_PATH):
    data = _read_json(path, {})
    pool = data.get("expanded_etf_pool") or []
    return [str(x).strip().upper() for x in pool if str(x).strip()]


def concentration(summary):
    counts = {}
    for result in summary.get("period_results") or []:
        for code, value in (result.get("tradable_selected_etf_counts") or {}).items():
            counts[code] = counts.get(code, 0.0) + _safe_float(value)
    total = sum(counts.values())
    if total <= 0:
        return {"top_code": None, "top_ratio": 0.0, "counts": counts}
    top_code = max(counts, key=lambda k: counts[k])
    return {"top_code": top_code, "top_ratio": round(counts[top_code] / total, 4), "counts": counts}


def extract_metrics(summary):
    conc = concentration(summary)
    return {"annual_non_overlapping_average_return": (summary.get("non_overlapping_summary") or {}).get("average_return_pct"),
            "rolling_average_return": (summary.get("rolling_summary") or {}).get("average_return_pct"),
            "max_drawdown": summary.get("max_drawdown_worst_pct"),
            "win_rate": (summary.get("non_overlapping_summary") or {}).get("average_win_rate"),
            "turnover": (summary.get("non_overlapping_summary") or {}).get("average_turnover"),
            "overfit_risk": summary.get("overfit_warning"), "underfit_risk": summary.get("underfit_warning"),
            "single_etf_concentration": conc, "continue_shadow_replay_recommended": summary.get("continue_shadow_replay_recommended"),
            "live_trading_not_recommended": True, "robustness_score": summary.get("robustness_score"),
            "stability_score": summary.get("stability_score")}


def run_one_pool(name, cfg, pool, periods, output_dir, xtdata=None):
    pool_dir = os.path.join(output_dir, name)
    _mkdir(pool_dir)
    research_cfg = _pool_cfg(cfg, pool)
    if bool(research_cfg.get("live_trading_enabled", False)):
        raise RuntimeError("研究回放要求 live_trading_enabled=false，且不会修改原配置。")
    summary = batch.run_batch(periods, pool_dir, cfg=research_cfg, rotation=research_cfg.get("etf_rotation", {}), xtdata=xtdata)
    return {"pool_name": name, "pool": list(pool), "summary": summary, "metrics": extract_metrics(summary)}


def build_compare(fixed_result, expanded_result):
    fixed, expanded = fixed_result["metrics"], expanded_result["metrics"]
    better_return = _safe_float(expanded.get("annual_non_overlapping_average_return")) > _safe_float(fixed.get("annual_non_overlapping_average_return"))
    lower_dd = _safe_float(expanded.get("max_drawdown")) <= _safe_float(fixed.get("max_drawdown"))
    enough_robust = _safe_float(expanded.get("robustness_score")) >= 60
    continue_shadow = bool(better_return and lower_dd and enough_robust)
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "mode": "READ_ONLY_RESEARCH",
            "safety": {"config_modified": False, "allowed_stocks_modified": False, "live_trading_enabled_modified": False, "trading_functions_called": False},
            "fixed_pool": fixed_result, "expanded_pool": expanded_result,
            "comparison": {"expanded_return_better": better_return, "expanded_drawdown_not_worse": lower_dd,
                           "expanded_robust_enough": enough_robust, "suitable_for_continued_shadow": continue_shadow,
                           "live_trading_not_recommended": True,
                           "conclusion": "扩展池可进入继续影子盘观察" if continue_shadow else "扩展池暂不建议替换当前固定池，仅保留研究观察"}}


def write_markdown(path, payload):
    f, e, c = payload["fixed_pool"]["metrics"], payload["expanded_pool"]["metrics"], payload["comparison"]
    lines = ["# ETF 固定池 vs 扩展池 对比研究（只读）", "", "- 不修改 config.json 的 allowed_stocks。", "- 不修改 live_trading_enabled。", "- 不建议实盘：{0}".format(c.get("live_trading_not_recommended")), "",
             "| 指标 | 固定5 ETF池 | 扩展ETF池 |", "| --- | ---: | ---: |",
             "| 年度非重叠平均收益 | {0} | {1} |".format(f.get("annual_non_overlapping_average_return"), e.get("annual_non_overlapping_average_return")),
             "| 滚动区间平均收益 | {0} | {1} |".format(f.get("rolling_average_return"), e.get("rolling_average_return")),
             "| 最大回撤 | {0} | {1} |".format(f.get("max_drawdown"), e.get("max_drawdown")),
             "| 胜率 | {0} | {1} |".format(f.get("win_rate"), e.get("win_rate")),
             "| 换手率 | {0} | {1} |".format(f.get("turnover"), e.get("turnover")),
             "| 过拟合风险 | {0} | {1} |".format(f.get("overfit_risk"), e.get("overfit_risk")),
             "| 欠拟合风险 | {0} | {1} |".format(f.get("underfit_risk"), e.get("underfit_risk")),
             "| 单一ETF集中度 | {0} | {1} |".format(f.get("single_etf_concentration"), e.get("single_etf_concentration")), "",
             "## 结论", "- 是否适合继续影子盘：{0}".format("是" if c.get("suitable_for_continued_shadow") else "否"),
             "- 是否不建议实盘：是", "- {0}".format(c.get("conclusion"))]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run_compare(cfg=None, expanded_pool=None, output_dir=OUTPUT_DIR, periods=None, xtdata=None):
    cfg = cfg or load_raw_config()
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("ETF 池对比要求 live_trading_enabled=false，且不会修改该配置。")
    fixed_pool = cfg.get("allowed_stocks") or FIXED_POOL
    expanded_pool = expanded_pool or load_expanded_pool()
    if not expanded_pool:
        raise RuntimeError("未找到 expanded ETF pool，请先运行 qmt_scan_etf_universe.py")
    periods = periods or batch.default_periods()
    _mkdir(output_dir)
    fixed_result = run_one_pool("fixed_pool", cfg, fixed_pool, periods, output_dir, xtdata=xtdata)
    expanded_result = run_one_pool("expanded_pool", cfg, expanded_pool, periods, output_dir, xtdata=xtdata)
    payload = build_compare(fixed_result, expanded_result)
    _json(os.path.join(output_dir, "pool_compare_latest.json"), payload)
    write_markdown(os.path.join(output_dir, "pool_compare_latest.md"), payload)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="只读 ETF 候选池对比研究")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--expanded-pool-file", default=SCAN_POOL_PATH)
    args = parser.parse_args(argv)
    from xtquant import xtdata
    result = run_compare(expanded_pool=load_expanded_pool(args.expanded_pool_file), output_dir=args.output_dir, xtdata=xtdata)
    print("[OK] ETF 池对比完成: {0}".format(result.get("comparison", {}).get("conclusion")))


if __name__ == "__main__":
    main()
