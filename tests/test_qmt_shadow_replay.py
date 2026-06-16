# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
import tempfile
import unittest

import qmt_shadow_replay as replay


class Loc(object):
    def __init__(self, data): self.data = data
    def __getitem__(self, key): return self.data[key[0]][key[1]]


class Frame(object):
    def __init__(self, columns, data):
        self.columns = columns
        self.loc = Loc(data)


def make_data(days=90, missing_last=False):
    cols = ["2024-01-%02d" % ((i % 30) + 1) if i < 30 else "2024-02-%02d" % ((i % 29) + 1) if i < 59 else "2024-03-%02d" % (i - 58) for i in range(days)]
    close, amount = {}, {}
    for code, base, step in [("AAA", 1.0, 0.02), ("BBB", 2.0, -0.005), ("IDX", 3.0, 0.01)]:
        close[code] = {}; amount[code] = {}
        for i, col in enumerate(cols):
            close[code][col] = base + step * i
            amount[code][col] = 1000000
    if missing_last:
        close["AAA"][cols[-1]] = 0
        amount["AAA"][cols[-1]] = 0
    return {"close": Frame(cols, close), "amount": Frame(cols, amount)}, cols


class ShadowReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = {"lot_size": 100, "max_single_order_value": 1000000, "min_order_value": 0,
                    "shadow_trading": {"initial_cash": 100000, "slippage_rate": 0, "commission_rate": 0, "min_commission": 0}}
        self.rotation = {"top_n": 1, "market_regime_indexes": ["IDX"], "risk_limits": {"min_score_to_buy": 1}}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_replay_uses_only_past_data(self):
        data, dates = make_data()
        out1, out2 = os.path.join(self.tmp, "r1"), os.path.join(self.tmp, "r2")
        replay.replay(self.cfg, self.rotation, ["AAA", "BBB", "IDX"], data, dates[:70], dates[65], dates[69], out1)
        data2, dates2 = make_data()
        for col in dates2[70:]:
            data2["close"].loc.data["AAA"][col] = 999.0
        replay.replay(self.cfg, self.rotation, ["AAA", "BBB", "IDX"], data2, dates2, dates[65], dates[69], out2)
        with open(os.path.join(out1, "replay_summary.json"), "r", encoding="utf-8") as handle:
            a = json.load(handle)
        with open(os.path.join(out2, "replay_summary.json"), "r", encoding="utf-8") as handle:
            b = json.load(handle)
        self.assertEqual(a["final_asset"], b["final_asset"])

    def test_replay_outputs_and_does_not_write_real_shadow(self):
        data, dates = make_data()
        cwd_shadow = os.path.join(os.getcwd(), "shadow")
        before = set(os.listdir(cwd_shadow)) if os.path.isdir(cwd_shadow) else set()
        replay.replay(self.cfg, self.rotation, ["AAA", "BBB", "IDX"], data, dates, dates[65], dates[70], self.tmp)
        for name in ["portfolio.json", "trades.csv", "equity_curve.csv", "daily_snapshots.csv", "replay_summary.json", "replay_report.md"]:
            self.assertTrue(os.path.exists(os.path.join(self.tmp, name)))
        after = set(os.listdir(cwd_shadow)) if os.path.isdir(cwd_shadow) else set()
        self.assertEqual(before, after)

    def test_replay_does_not_expose_real_trading_functions(self):
        self.assertFalse(hasattr(replay, "order_stock"))
        self.assertFalse(hasattr(replay, "cancel_order_stock"))

    def test_missing_quote_records_warning(self):
        data, dates = make_data(missing_last=True)
        replay.replay(self.cfg, self.rotation, ["AAA", "BBB", "IDX"], data, dates, dates[-2], dates[-1], self.tmp)
        summary_path = os.path.join(self.tmp, "replay_summary.json")
        with open(summary_path, "r", encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertTrue(summary["warnings"])
        self.assertTrue(any("行情缺失或无效" in warning for warning in summary["warnings"]))

    def test_max_drawdown_calculation(self):
        self.assertAlmostEqual(replay.calculate_max_drawdown([100, 120, 90, 150]), 0.25)


if __name__ == "__main__":
    unittest.main()
