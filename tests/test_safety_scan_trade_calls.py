# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import unittest

from qmt_gateway.safety import scan_source_text_for_trade_call_violations
from qmt_gateway.trade_executor_disabled import DisabledTradeExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SafetyScanTradeCallsTest(unittest.TestCase):
    def _read(self, rel):
        with open(os.path.join(ROOT, rel), encoding="utf-8-sig") as handle:
            return handle.read()

    def test_disabled_executor_rejecting_definitions_are_allowed(self):
        text = self._read("qmt_gateway/trade_executor_disabled.py")
        self.assertEqual([], scan_source_text_for_trade_call_violations("qmt_gateway/trade_executor_disabled.py", text))

    def test_disabled_executor_methods_raise_runtime_error(self):
        executor = DisabledTradeExecutor()
        with self.assertRaises(RuntimeError):
            executor.order_stock("000001.SZ", 23, 100)
        with self.assertRaises(RuntimeError):
            executor.cancel_order_stock("order-id")

    def test_disabled_executor_scan_does_not_fail_on_rejecting_methods(self):
        source = (
            "class DisabledTradeExecutor(object):\n"
            "    def order_stock(self, *args, **kwargs):\n"
            "        raise RuntimeError('真实下单 disabled refused 禁用')\n"
            "    def cancel_order_stock(self, *args, **kwargs):\n"
            "        raise RuntimeError('真实撤单 disabled refused 拒绝')\n"
        )
        self.assertEqual([], scan_source_text_for_trade_call_violations("qmt_gateway/trade_executor_disabled.py", source))

    def test_update_script_skips_disabled_executor_after_rejecting_validation(self):
        text = self._read("update_qmt_project.ps1")
        self.assertIn("$fileNorm = $file -replace '\\\\','/'", text)
        marker = 'if ($fileNorm -eq "qmt_gateway/trade_executor_disabled.py") {'
        start = text.index(marker)
        end = text.index('if ($fileNorm -like "tests/*") { continue }', start)
        block = text[start:end]
        self.assertIn('Test-DisabledExecutorRejects $text "order_stock"', block)
        self.assertIn('Test-DisabledExecutorRejects $text "cancel_order_stock"', block)
        self.assertIn('DisabledTradeExecutor 必须只抛出 RuntimeError 拒绝交易', block)
        self.assertIn('continue', block)

    def test_regular_source_order_stock_call_fails_scan(self):
        violations = scan_source_text_for_trade_call_violations("strategies/example.py", "trader.order_stock('000001.SZ')\n")
        self.assertTrue(violations)
        self.assertIn("trader.order_stock", violations[0])

    def test_regular_source_cancel_order_stock_call_fails_scan(self):
        violations = scan_source_text_for_trade_call_violations("strategies/example.py", "cancel_order_stock(order_id)\n")
        self.assertTrue(violations)
        self.assertIn("cancel_order_stock", violations[0])

    def test_test_files_may_contain_trade_call_strings(self):
        source = "trader.order_stock('000001.SZ')\ncancel_order_stock(order_id)\n"
        self.assertEqual([], scan_source_text_for_trade_call_violations("tests/test_example.py", source))

    def test_dryrun_shadow_and_pipeline_have_no_real_trade_calls(self):
        for rel in ["qmt_plan_order_dryrun_v2.py", "qmt_shadow_replay.py", "qmt_daily_shadow_pipeline.py"]:
            self.assertEqual([], scan_source_text_for_trade_call_violations(rel, self._read(rel)), rel)


if __name__ == "__main__":
    unittest.main()
