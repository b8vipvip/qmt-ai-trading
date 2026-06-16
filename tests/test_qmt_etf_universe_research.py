# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import tempfile
import unittest
from unittest import mock

import qmt_scan_etf_universe as scan
import qmt_compare_etf_pools as compare
import qmt_collect_diagnostics as diagnostics


class Loc(object):
    def __init__(self, rows): self.rows = rows
    def __getitem__(self, key): return self.rows[key[0]][key[1]]


class Frame(object):
    def __init__(self, rows):
        self.rows = rows
        self.columns = list(next(iter(rows.values())).keys()) if rows else []
        self.loc = Loc(rows)


def make_data(codes, days=260, low_amount=None):
    low_amount = low_amount or set()
    cols = ["D%04d" % i for i in range(days)]
    close, amount = {}, {}
    for code in codes:
        close[code] = dict((c, 1.0 + i * 0.001) for i, c in enumerate(cols))
        amount[code] = dict((c, 1000.0 if code in low_amount else 80000000.0) for c in cols)
    return {"close": Frame(close), "amount": Frame(amount)}, cols


class EtfUniverseResearchTests(unittest.TestCase):
    def test_scan_filters_and_does_not_modify_config(self):
        cfg = {"live_trading_enabled": False, "allowed_stocks": ["510300.SH"], "etf_universe_scan": {"local_etfs": [
            {"stock_code": "510300.SH", "stock_name": "沪深300ETF", "tracking_index": "沪深300"},
            {"stock_code": "511880.SH", "stock_name": "货币ETF"},
            {"stock_code": "511010.SH", "stock_name": "国债ETF"},
            {"stock_code": "518880.SH", "stock_name": "黄金ETF"},
            {"stock_code": "513100.SH", "stock_name": "纳指ETF QDII"},
            {"stock_code": "159999.SZ", "stock_name": "低流动ETF"},
            {"stock_code": "159998.SZ", "stock_name": "新ETF"}], "min_avg_amount_20d": 50000000}}
        original = json.dumps(cfg, sort_keys=True, ensure_ascii=False)
        codes = ["510300.SH", "511880.SH", "511010.SH", "518880.SH", "513100.SH", "159999.SZ"]
        data, dates = make_data(codes, 260, set(["159999.SZ"]))
        short, sdates = make_data(["159998.SZ"], 100)
        for key in ["close", "amount"]:
            data[key].rows.update(short[key].rows)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(scan.replay_data, "load_history", return_value=(data, dates)):
            payload, expanded = scan.run_scan(cfg=cfg, output_dir=tmp)
            self.assertTrue(os.path.exists(os.path.join(tmp, "etf_universe_scan_latest.json")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "expanded_etf_pool_latest.txt")))
        self.assertEqual(original, json.dumps(cfg, sort_keys=True, ensure_ascii=False))
        self.assertEqual(["510300.SH"], expanded["expanded_etf_pool"])
        reasons = dict((r["stock_code"], r["skip_reason"]) for r in payload["records"])
        self.assertIn("货币", reasons["511880.SH"])
        self.assertIn("债券", reasons["511010.SH"])
        self.assertIn("商品", reasons["518880.SH"])
        self.assertIn("QDII", reasons["513100.SH"])
        self.assertIn("成交额", reasons["159999.SZ"])
        self.assertIn("历史数据不足", reasons["159998.SZ"])

    def test_compare_uses_research_config_and_reports_required_metrics(self):
        cfg = {"live_trading_enabled": False, "allowed_stocks": ["510300.SH"], "etf_rotation": {}, "shadow_trading": {"initial_cash": 100000}}
        def fake_run(periods, output_dir, cfg=None, rotation=None, xtdata=None):
            self.assertFalse(cfg["live_trading_enabled"])
            return {"non_overlapping_summary": {"average_return_pct": 3, "average_win_rate": 0.5, "average_turnover": 1},
                    "rolling_summary": {"average_return_pct": 2}, "max_drawdown_worst_pct": 6,
                    "overfit_warning": "无明显过拟合警告", "underfit_warning": "无明显欠拟合警告",
                    "continue_shadow_replay_recommended": True, "robustness_score": 80,
                    "stability_score": 80, "period_results": [{"tradable_selected_etf_counts": {cfg["allowed_stocks"][0]: 2}}]}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(compare.batch, "run_batch", side_effect=fake_run):
            result = compare.run_compare(cfg=cfg, expanded_pool=["510500.SH"], output_dir=tmp, periods=[{"period_name":"p","start_date":"2025-01-01","end_date":"2025-12-31"}])
            self.assertTrue(os.path.exists(os.path.join(tmp, "pool_compare_latest.md")))
        self.assertEqual(["510300.SH"], cfg["allowed_stocks"])
        metrics = result["expanded_pool"]["metrics"]
        self.assertIn("max_drawdown", metrics)
        self.assertIn("annual_non_overlapping_average_return", metrics)
        self.assertIn("overfit_risk", metrics)
        self.assertIn("underfit_risk", metrics)

    def test_diagnostics_collects_research_outputs(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostics, "ROOT", root):
            os.makedirs(os.path.join(root, "research", "etf_universe_scan"))
            os.makedirs(os.path.join(root, "research", "etf_pool_compare"))
            with open(os.path.join(root, "research", "etf_universe_scan", "etf_universe_scan_latest.json"), "w") as h:
                json.dump({"total_count": 2, "eligible_count": 1, "expanded_count": 1, "records": []}, h)
            with open(os.path.join(root, "research", "etf_pool_compare", "pool_compare_latest.json"), "w") as h:
                json.dump({"comparison": {"suitable_for_continued_shadow": False, "live_trading_not_recommended": True}}, h)
            self.assertTrue(diagnostics.collect_etf_universe_scan()["exists"])
            self.assertTrue(diagnostics.collect_etf_pool_compare()["exists"])


if __name__ == "__main__":
    unittest.main()
