# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest

from data_tools.etf_rotation_selector import score_etf
from qmt_generate_signal_rotation import build_rotation_signal


class FakeAsset(object):
    total_asset = 100000.0
    cash = 100000.0


def rising_prices():
    return [100.0 + i for i in range(70)]


class ETFRotationScoringTest(unittest.TestCase):
    def test_scoring_contains_required_metrics(self):
        row = score_etf("510300.SH", rising_prices(), [100000000.0] * 70,
                        risk_limits={"min_avg_amount_20d": 50000000, "max_drawdown_60d": 0.15})
        self.assertTrue(row["eligible"])
        self.assertGreater(row["score"], 60)
        for key in ["return_5d", "return_20d", "return_60d", "above_ma20", "above_ma60",
                    "avg_amount_20d", "max_drawdown_60d", "annualized_volatility_60d"]:
            self.assertIn(key, row)

    def test_liquidity_filter(self):
        row = score_etf("510300.SH", rising_prices(), [1000.0] * 70,
                        risk_limits={"min_avg_amount_20d": 50000000})
        self.assertFalse(row["eligible"])
        self.assertIn("成交额", row["skip_reason"])

    def test_drawdown_filter(self):
        prices = [100.0] * 61 + [80.0] * 9
        row = score_etf("510300.SH", prices, [100000000.0] * 70,
                        risk_limits={"max_drawdown_60d": 0.15})
        self.assertFalse(row["eligible"])
        self.assertIn("最大回撤", row["skip_reason"])

    def test_bearish_market_never_buys(self):
        selected = {"selected": [{"stock_code": "510300.SH", "last_close": 4.0, "score": 90.0}]}
        signal = build_rotation_signal(selected, {"market_regime": "bearish"}, 60)
        self.assertNotEqual(signal["signal"], "BUY_SIGNAL")
        self.assertEqual(signal["signal"], "SELL_SIGNAL")

    def test_signal_is_compatible_with_dryrun_planner(self):
        selected = {"selected": [{"stock_code": "510300.SH", "last_close": 4.0, "score": 90.0}]}
        signal = build_rotation_signal(selected, {"market_regime": "bullish"}, 60)
        for required_key in ["stock_code", "signal", "target_position_pct", "last_close", "reason"]:
            self.assertIn(required_key, signal)
        self.assertEqual(signal["stock_code"], "510300.SH")
        self.assertEqual(signal["signal"], "BUY_SIGNAL")
        self.assertIsInstance(signal["last_close"], float)


if __name__ == "__main__":
    unittest.main()
