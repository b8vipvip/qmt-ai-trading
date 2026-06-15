# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import tempfile
import unittest

from ai_tools.analyze_backtest import analyze
from ai_tools.common import validate_strategy_source
from ai_tools.optimize_strategy import optimize


SAFE_STRATEGY = '''
PARAM_GRID = {"window": [2, 3]}
def backtest(dates, closes, params):
    return {"profit_rate": 0.1 / params["window"], "max_drawdown": 0.02, "trade_count": 10}
def generate_signal(dates, closes, params):
    return {"signal": "HOLD"}
'''


class FakeStrategy(object):
    PARAM_GRID = {"window": [2, 3]}

    @staticmethod
    def backtest(dates, closes, params):
        return {"profit_rate": 0.1 / params["window"], "max_drawdown": 0.02, "trade_count": 10}


class AIToolsTest(unittest.TestCase):
    def test_analysis_flags_small_sample(self):
        report = analyze([{"profit_rate": 0.1, "max_drawdown": 0.1, "trade_count": 2}])
        self.assertEqual(report["sample_count"], 1)
        self.assertEqual(report["overfitting_risk"], "medium")
        self.assertTrue(report["risk_findings"])

    def test_strategy_safety_accepts_research_contract(self):
        self.assertTrue(validate_strategy_source(SAFE_STRATEGY))

    def test_strategy_safety_accepts_future_print_function(self):
        source = "from __future__ import print_function\n" + SAFE_STRATEGY
        self.assertTrue(validate_strategy_source(source))

    def test_strategy_safety_accepts_collections(self):
        source = "from collections import deque\n" + SAFE_STRATEGY
        self.assertTrue(validate_strategy_source(source))

    def test_strategy_safety_rejects_order_call(self):
        unsafe = SAFE_STRATEGY.replace('return {"signal": "HOLD"}', 'return ' + 'order_' + 'stock("x")')
        with self.assertRaises(ValueError):
            validate_strategy_source(unsafe)

    def test_strategy_safety_rejects_file_access(self):
        unsafe = SAFE_STRATEGY.replace('return {"signal": "HOLD"}', 'return open("secret")')
        with self.assertRaises(ValueError):
            validate_strategy_source(unsafe)

    def test_strategy_safety_rejects_network_access(self):
        for module in ("socket", "requests", "urllib"):
            with self.assertRaises(ValueError):
                validate_strategy_source("import " + module + "\n" + SAFE_STRATEGY)

    def test_strategy_safety_rejects_process_call(self):
        for source in (
            SAFE_STRATEGY.replace('return {"signal": "HOLD"}', 'return system("echo unsafe")'),
            "import subprocess\n" + SAFE_STRATEGY,
            "import multiprocessing\n" + SAFE_STRATEGY,
            "import os\n" + SAFE_STRATEGY,
        ):
            with self.assertRaises(ValueError):
                validate_strategy_source(source)

    def test_strategy_safety_rejects_live_trading_enablement(self):
        unsafe = "live_trading_enabled = True\n" + SAFE_STRATEGY
        with self.assertRaises(ValueError):
            validate_strategy_source(unsafe)

    def test_optimizer_uses_multiple_periods(self):
        datasets = [
            {"start_time": "20230101", "end_time": "20231231", "dates": [], "closes": []},
            {"start_time": "20240101", "end_time": "20241231", "dates": [], "closes": []}
        ]
        rows = optimize(FakeStrategy, datasets)
        self.assertEqual(rows[0]["params"]["window"], 2)
        self.assertEqual(len(rows[0]["period_results"]), 2)


if __name__ == "__main__":
    unittest.main()
