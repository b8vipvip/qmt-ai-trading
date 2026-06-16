# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import qmt_shadow_replay_batch as batch
from tests.test_qmt_shadow_replay import make_data


class BatchReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = {"lot_size": 100, "max_single_order_value": 1000000, "min_order_value": 0,
                    "live_trading_enabled": False, "allowed_stocks": ["AAA", "BBB"],
                    "shadow_trading": {"initial_cash": 100000, "slippage_rate": 0, "commission_rate": 0, "min_commission": 0}}
        self.rotation = {"top_n": 1, "market_regime_indexes": ["IDX"], "risk_limits": {"min_score_to_buy": 1}}
        self.periods = [{"period_name": "p1", "start_date": "2024-03-07", "end_date": "2024-03-10"},
                        {"period_name": "p2", "start_date": "2024-03-11", "end_date": "2024-03-15"}]

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_batch_outputs_summary_report_and_independent_periods(self):
        data, dates = make_data()
        with mock.patch.object(batch.single, "load_history", return_value=(data, dates)):
            summary = batch.run_batch(self.periods, self.tmp, cfg=self.cfg, rotation=self.rotation)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "batch_summary.json")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "batch_report.md")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "batch_summary.csv")))
        self.assertEqual(2, len(summary["period_results"]))
        for name in ["period_001", "period_002"]:
            for artifact in ["replay_summary.json", "replay_report.md", "trades.csv", "equity_curve.csv"]:
                self.assertTrue(os.path.exists(os.path.join(self.tmp, name, artifact)))

    def test_failed_period_records_warning_without_crashing(self):
        data, dates = make_data()
        real_replay = batch.single.replay
        calls = {"count": 0}
        def flaky(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("boom")
            return real_replay(*args, **kwargs)
        with mock.patch.object(batch.single, "load_history", return_value=(data, dates)), mock.patch.object(batch.single, "replay", side_effect=flaky):
            summary = batch.run_batch(self.periods, self.tmp, cfg=self.cfg, rotation=self.rotation)
        self.assertEqual(2, len(summary["period_results"]))
        self.assertFalse(summary["period_results"][1]["candidate_pool_valid"])
        self.assertTrue(any("区间回放失败" in w for w in summary["period_results"][1]["metric_warnings"]))

    def test_batch_directory_is_gitignored(self):
        with open(os.path.join(os.path.dirname(__file__), "..", ".gitignore"), "r", encoding="utf-8") as handle:
            self.assertIn("shadow_replay_batch/", handle.read())

    def test_does_not_expose_real_trading_functions_or_modify_live_flag(self):
        self.assertFalse(hasattr(batch, "order_stock"))
        self.assertFalse(hasattr(batch, "cancel_order_stock"))
        data, dates = make_data()
        with mock.patch.object(batch.single, "load_history", return_value=(data, dates)):
            batch.run_batch(self.periods[:1], self.tmp, cfg=self.cfg, rotation=self.rotation)
        self.assertFalse(self.cfg["live_trading_enabled"])

    def test_candidate_pool_invalid_marks_batch_unqualified(self):
        periods = [{"period_name": "bad", "start_date": "2024-01-01", "end_date": "2024-01-02"}]
        results = [batch.normalize_period_result(periods[0], {"candidate_pool_valid": False, "total_return_pct": 1, "max_drawdown_pct": 1})]
        summary = batch.build_batch_summary(periods, results)
        self.assertTrue(any("候选池" in w for w in summary["warnings"]))
        self.assertLess(summary["stability_score"], 100)

    def test_majority_losses_marks_unstable(self):
        periods = [{"period_name": "a"}, {"period_name": "b"}, {"period_name": "c"}]
        results = [{"period_name": "a", "total_return_pct": -1, "max_drawdown_pct": 1, "candidate_pool_valid": True},
                   {"period_name": "b", "total_return_pct": -2, "max_drawdown_pct": 1, "candidate_pool_valid": True},
                   {"period_name": "c", "total_return_pct": 3, "max_drawdown_pct": 1, "candidate_pool_valid": True}]
        summary = batch.build_batch_summary(periods, results)
        self.assertTrue(any("多数区间亏损" in w for w in summary["warnings"]))

    def test_concentrated_profit_marks_overfit(self):
        periods = [{"period_name": "a"}, {"period_name": "b"}]
        results = [{"period_name": "a", "total_return_pct": 10, "max_drawdown_pct": 1, "candidate_pool_valid": True},
                   {"period_name": "b", "total_return_pct": 1, "max_drawdown_pct": 1, "candidate_pool_valid": True}]
        summary = batch.build_batch_summary(periods, results)
        self.assertIn("过拟合", summary["overfit_warning"])


if __name__ == "__main__":
    unittest.main()
