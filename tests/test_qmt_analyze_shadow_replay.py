# -*- coding: utf-8 -*-
import csv
import json
import os
import shutil
import tempfile
import unittest

import qmt_analyze_shadow_replay as analyzer


class ShadowReplayAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.run_dir = os.path.join(self.tmp, "shadow_replay", "run_20260616_120000")
        os.makedirs(self.run_dir)
        with open(os.path.join(self.run_dir, "replay_summary.json"), "w", encoding="utf-8") as handle:
            json.dump({"start_date": "2025-01-01", "end_date": "2025-01-10", "trading_days": 10,
                       "total_return_pct": 2.0, "annualized_return_pct": 50.0, "max_drawdown_pct": 6.0,
                       "total_trades": 4, "closed_trades": 2, "turnover": 0.8,
                       "tradable_selected_etf_counts": {"510300.SH": 8, "159915.SZ": 2}}, handle)
        with open(os.path.join(self.run_dir, "trades.csv"), "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["trade_date", "stock_code", "side", "volume", "fill_price", "gross_amount", "commission"])
            writer.writeheader()
            writer.writerows([
                {"trade_date": "2025-01-01", "stock_code": "510300.SH", "side": "BUY", "volume": 100, "fill_price": 10, "gross_amount": 1000, "commission": 0},
                {"trade_date": "2025-01-03", "stock_code": "510300.SH", "side": "SELL", "volume": 100, "fill_price": 11, "gross_amount": 1100, "commission": 0},
                {"trade_date": "2025-01-04", "stock_code": "159915.SZ", "side": "BUY", "volume": 100, "fill_price": 10, "gross_amount": 1000, "commission": 0},
                {"trade_date": "2025-01-05", "stock_code": "159915.SZ", "side": "SELL", "volume": 100, "fill_price": 9, "gross_amount": 900, "commission": 0},
            ])
        with open(os.path.join(self.run_dir, "equity_curve.csv"), "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "total_asset", "cash", "market_value", "floating_pnl"])
            writer.writeheader()
            writer.writerows([
                {"date": "2025-01-01", "total_asset": 100000, "cash": 99000, "market_value": 1000, "floating_pnl": 0},
                {"date": "2025-01-02", "total_asset": 98000, "cash": 97000, "market_value": 1000, "floating_pnl": -2000},
                {"date": "2025-01-03", "total_asset": 102000, "cash": 102000, "market_value": 0, "floating_pnl": 0},
                {"date": "2025-01-04", "total_asset": 101000, "cash": 101000, "market_value": 0, "floating_pnl": 0},
                {"date": "2025-01-05", "total_asset": 100000, "cash": 100000, "market_value": 0, "floating_pnl": 0},
                {"date": "2025-01-06", "total_asset": 100000, "cash": 100000, "market_value": 0, "floating_pnl": 0},
                {"date": "2025-01-07", "total_asset": 100000, "cash": 100000, "market_value": 0, "floating_pnl": 0},
            ])
        with open(os.path.join(self.run_dir, "replay_report.md"), "w", encoding="utf-8") as handle:
            handle.write("# report\napi_key: sk-supersecret123456\naccount_id: 1234567890\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_analyzes_shadow_replay_outputs_and_writes_files(self):
        analysis = analyzer.analyze_run(self.run_dir)
        json_path, md_path = analyzer.write_analysis(self.run_dir, analysis)
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(md_path))
        self.assertEqual("shadow_replay_readonly_ai_analysis", analysis["analysis_type"])
        self.assertTrue(analysis["performance_acceptability"]["acceptable"])
        self.assertTrue(analysis["drawdown_periods"])
        self.assertEqual("510300.SH", analysis["etf_contributions"][0]["stock_code"])
        self.assertTrue(analysis["concentration"]["is_over_concentrated"])
        self.assertTrue(analysis["long_cash_periods"]["has_long_cash_periods"])
        self.assertLessEqual(len(analysis["recommendations"]), 5)
        for rec in analysis["recommendations"]:
            for key in ["modify_location", "reason", "expected_metric_improvement", "potential_side_effect", "change_now"]:
                self.assertIn(key, rec)

    def test_latest_run_dir_finds_newest(self):
        newer = os.path.join(self.tmp, "shadow_replay", "run_20260616_130000")
        os.makedirs(newer)
        os.utime(self.run_dir, (100, 100))
        os.utime(newer, (200, 200))
        self.assertEqual(newer, analyzer.latest_run_dir(self.tmp))

    def test_safety_flags_and_source_do_not_expose_secrets(self):
        analysis = analyzer.analyze_run(self.run_dir)
        self.assertFalse(analysis["safety"]["trading_functions_called"])
        self.assertFalse(analysis["safety"]["strategy_code_modified"])
        self.assertFalse(analysis["safety"]["live_trading_enabled_modified"])
        text = json.dumps(analysis, ensure_ascii=False)
        self.assertNotIn("sk-", text)
        self.assertNotIn("sk-supersecret123456", text)
        self.assertNotIn("1234567890", text)

    def test_module_does_not_expose_real_trading_functions(self):
        self.assertFalse(hasattr(analyzer, "order_stock"))
        self.assertFalse(hasattr(analyzer, "cancel_order_stock"))


if __name__ == "__main__":
    unittest.main()
