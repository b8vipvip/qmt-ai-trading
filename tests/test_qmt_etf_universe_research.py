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
            self.assertTrue(os.path.exists(os.path.join(tmp, "latest_status.json")))
            with open(os.path.join(tmp, "latest_status.json"), "r", encoding="utf-8") as h:
                self.assertEqual("done", json.load(h)["status"])
            self.assertTrue(os.path.exists(os.path.join(scan.ROOT, "logs", "etf_universe_scan_latest.log")))
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
        def fake_run(periods, output_dir, cfg=None, rotation=None, xtdata=None, progress=None):
            self.assertFalse(cfg["live_trading_enabled"])
            return {"non_overlapping_summary": {"average_return_pct": 3, "average_win_rate": 0.5, "average_turnover": 1},
                    "rolling_summary": {"average_return_pct": 2}, "max_drawdown_worst_pct": 6,
                    "overfit_warning": "无明显过拟合警告", "underfit_warning": "无明显欠拟合警告",
                    "continue_shadow_replay_recommended": True, "robustness_score": 80,
                    "stability_score": 80, "period_results": [{"tradable_selected_etf_counts": {cfg["allowed_stocks"][0]: 2}}]}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(compare.batch, "run_batch", side_effect=fake_run):
            result = compare.run_compare(cfg=cfg, expanded_pool=["510500.SH", "512100.SH"], output_dir=tmp, periods=[{"period_name":"p","start_date":"2025-01-01","end_date":"2025-12-31"}], max_expanded_etfs=1)
            self.assertTrue(os.path.exists(os.path.join(tmp, "pool_compare_latest.md")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "latest_status.json")))
            with open(os.path.join(tmp, "latest_status.json"), "r", encoding="utf-8") as h:
                self.assertEqual("done", json.load(h)["status"])
            self.assertTrue(os.path.exists(os.path.join(compare.ROOT, "logs", "etf_pool_compare_latest.log")))
        self.assertEqual(["510300.SH"], cfg["allowed_stocks"])
        metrics = result["expanded_pool"]["metrics"]
        self.assertIn("max_drawdown", metrics)
        self.assertIn("annual_non_overlapping_average_return", metrics)
        self.assertIn("overfit_risk", metrics)
        self.assertIn("underfit_risk", metrics)
        self.assertEqual(["510500.SH"], result["expanded_pool"]["pool"])

    def test_scan_supports_max_etfs_and_local_only_status_running(self):
        cfg = {"live_trading_enabled": False, "allowed_stocks": ["510300.SH", "510500.SH"]}
        data, dates = make_data(["510300.SH"], 260)
        with tempfile.TemporaryDirectory() as tmp:
            def fake_load(codes, start, end, xtdata=None):
                status_path = os.path.join(tmp, "latest_status.json")
                with open(status_path, "r", encoding="utf-8") as h:
                    self.assertEqual("running", json.load(h)["status"])
                self.assertEqual(["510300.SH"], codes)
                return data, dates
            with mock.patch.object(scan.replay_data, "load_history", side_effect=fake_load):
                payload, expanded = scan.run_scan(cfg=cfg, output_dir=tmp, max_etfs=1, local_only=True, quiet=True)
                self.assertEqual(1, payload["total_count"])

    def test_diagnostics_collects_research_outputs(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostics, "ROOT", root):
            os.makedirs(os.path.join(root, "research", "etf_universe_scan"))
            os.makedirs(os.path.join(root, "research", "etf_pool_compare"))
            with open(os.path.join(root, "research", "etf_universe_scan", "etf_universe_scan_latest.json"), "w") as h:
                json.dump({"total_count": 2, "eligible_count": 1, "expanded_count": 1, "records": []}, h)
            with open(os.path.join(root, "research", "etf_pool_compare", "pool_compare_latest.json"), "w") as h:
                json.dump({"comparison": {"suitable_for_continued_shadow": False, "live_trading_not_recommended": True}}, h)
            with open(os.path.join(root, "research", "etf_universe_scan", "latest_status.json"), "w") as h:
                json.dump({"status": "running", "latest_message": "x"}, h)
            with open(os.path.join(root, "research", "etf_pool_compare", "latest_status.json"), "w") as h:
                json.dump({"status": "done", "latest_message": "y"}, h)
            os.makedirs(os.path.join(root, "logs"))
            with open(os.path.join(root, "logs", "etf_universe_scan_latest.log"), "w") as h:
                h.write("x")
            with open(os.path.join(root, "logs", "etf_pool_compare_latest.log"), "w") as h:
                h.write("y")
            scan_state = diagnostics.collect_etf_universe_scan()
            compare_state = diagnostics.collect_etf_pool_compare()
            self.assertTrue(scan_state["exists"])
            self.assertTrue(compare_state["exists"])
            self.assertEqual("running", scan_state["runtime_status"]["status"])
            self.assertEqual("done", compare_state["runtime_status"]["status"])

    def test_scan_default_caps_expanded_pool_and_excludes_non_positive_scores(self):
        records = []
        for idx in range(35):
            records.append({"stock_code": "5%05d.SH" % idx, "category": "cat%d" % idx,
                            "tracking_index": "idx%d" % idx, "eligible": True, "score": 10 - idx * 0.1})
        records.append({"stock_code": "599999.SH", "category": "zero", "tracking_index": "zero", "eligible": True, "score": 0})
        expanded, stats = scan.build_expanded_records(records)
        self.assertEqual(30, len(expanded))
        self.assertNotIn("599999.SH", [r["stock_code"] for r in expanded])
        self.assertEqual(1, stats["filtered_out_by_score"])

    def test_scan_max_expanded_and_min_score_options(self):
        records = [{"stock_code": "5%05d.SH" % idx, "category": "cat%d" % idx,
                    "tracking_index": "idx%d" % idx, "eligible": True, "score": idx} for idx in range(10)]
        expanded, stats = scan.build_expanded_records(records, min_score=7, max_expanded_etfs=2)
        self.assertEqual(["500009.SH", "500008.SH"], [r["stock_code"] for r in expanded])
        self.assertEqual(8, stats["filtered_out_by_score"])

    def test_compare_default_caps_expanded_pool_and_logs_period_progress(self):
        cfg = {"live_trading_enabled": False, "allowed_stocks": ["510300.SH"], "etf_rotation": {}, "shadow_trading": {"initial_cash": 100000}}
        periods = [{"period_name":"p1","start_date":"2025-01-01","end_date":"2025-01-31"}, {"period_name":"p2","start_date":"2025-02-01","end_date":"2025-02-28"}]
        def fake_run(periods_arg, output_dir, cfg=None, rotation=None, xtdata=None, progress=None):
            if progress:
                progress.emit("[INFO] 本次共 %d 个区间" % len(periods_arg), force_status=True)
                for idx, period in enumerate(periods_arg):
                    progress.current_index = idx + 1
                    progress.current_period = period
                    progress.emit("[%d/%d] 开始: %s 至 %s" % (idx + 1, len(periods_arg), period["start_date"], period["end_date"]), force_status=True)
                    progress.completed_periods += 1
                    progress.emit("[%d/%d] 回放完成" % (idx + 1, len(periods_arg)), force_status=True)
            return {"non_overlapping_summary": {"average_return_pct": 1, "average_win_rate": 1, "average_turnover": 1},
                    "rolling_summary": {"average_return_pct": 1}, "max_drawdown_worst_pct": 1,
                    "robustness_score": 80, "stability_score": 80, "period_results": []}
        expanded_pool = ["5%05d.SH" % idx for idx in range(60)]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(compare.batch, "run_batch", side_effect=fake_run):
            result = compare.run_compare(cfg=cfg, expanded_pool=expanded_pool, output_dir=tmp, periods=periods, quiet=True)
            self.assertEqual(30, len(result["expanded_pool"]["pool"]))
            with open(os.path.join(compare.ROOT, "logs", "etf_pool_compare_latest.log"), "r", encoding="utf-8") as h:
                log = h.read()
        self.assertIn("[expanded_pool][1/2] 开始 p1", log)
        self.assertIn("[expanded_pool][2/2] 完成", log)

    def test_compare_warns_when_explicit_expanded_pool_over_50(self):
        cfg = {"live_trading_enabled": False, "allowed_stocks": ["510300.SH"], "etf_rotation": {}, "shadow_trading": {"initial_cash": 100000}}
        def fake_run(periods_arg, output_dir, cfg=None, rotation=None, xtdata=None, progress=None):
            return {"non_overlapping_summary": {"average_return_pct": 1, "average_win_rate": 1, "average_turnover": 1},
                    "rolling_summary": {"average_return_pct": 1}, "max_drawdown_worst_pct": 1,
                    "robustness_score": 80, "stability_score": 80, "period_results": []}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(compare.batch, "run_batch", side_effect=fake_run):
            result = compare.run_compare(cfg=cfg, expanded_pool=["5%05d.SH" % idx for idx in range(60)], output_dir=tmp,
                                         periods=[{"period_name":"p","start_date":"2025-01-01","end_date":"2025-01-31"}],
                                         max_expanded_etfs=60, quiet=True)
            self.assertEqual(60, len(result["expanded_pool"]["pool"]))
            with open(os.path.join(tmp, "latest_status.json"), "r", encoding="utf-8") as h:
                status = json.load(h)
        self.assertTrue(any("扩展池超过 50" in item for item in status.get("warnings", [])))

    def test_research_is_gitignored_and_diagnostics_hints_when_unignored(self):
        with open(os.path.join(scan.ROOT, ".gitignore"), "r", encoding="utf-8") as h:
            self.assertIn("research/", h.read().splitlines())
        with mock.patch.object(diagnostics, "_git", side_effect=lambda *args: "?? research/" if args == ("status", "--short") else ""):
            state = diagnostics.collect_git()
        self.assertIn("研究产物目录 research/ 未被忽略，建议加入 .gitignore", state["warnings"])


if __name__ == "__main__":
    unittest.main()
