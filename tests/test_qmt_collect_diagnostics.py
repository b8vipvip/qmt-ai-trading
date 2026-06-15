# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest import mock
import qmt_collect_diagnostics as diagnostic

class DiagnosticTests(unittest.TestCase):
    def write_json(self, root, relative, value):
        path = os.path.join(root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle)

    def test_redacts_api_key_and_account(self):
        text = json.dumps(diagnostic.redact({"api_key": "sk-super-secret", "account_id": "12345678"}))
        self.assertNotIn("sk-super-secret", text)
        self.assertNotIn("12345678", text)
        self.assertIn("12***78", text)

    def test_missing_signals_and_logs_do_not_crash(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.assertFalse(diagnostic.collect_etf()["dry_run_passed"])
            self.assertEqual(0, diagnostic.collect_ai_api()["total_calls"])

    def test_live_trading_false_is_safe(self):
        config = {"live_trading_enabled": False}
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            with open(os.path.join(root, "config.json"), "w", encoding="utf-8") as handle: json.dump(config, handle)
            self.write_json(root, "shadow/portfolio.json", {"cash": 100000})
            stage = diagnostic.determine_stage(config, {}, {"dry_run_passed": True}, {"pipeline_success": True})
            self.assertEqual("ETF 影子盘观察期", stage[0])
            self.assertFalse(stage[1])
            report = diagnostic.build_report()
            self.assertIn("live_trading_enabled=false：不会实盘下单", report["risks"])

    def test_update_summary_drives_checks_and_stage(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "logs/update_latest_summary.json", {
                "final_status": "代码已更新但后置检查失败", "code_pull": "成功",
                "config_check": "通过", "unit_tests": "失败", "python_compile": "未执行",
                "safety_scan": "未执行", "failure_reason": "单元测试失败", "suggestion": "修复测试",
                "backup_dir": "D:/backup"
            })
            open(os.path.join(root, "logs", "update_latest.log"), "w").close()
            checks = diagnostic.collect_update_checks()
            self.assertEqual("失败", checks["unit_tests"])
            self.assertEqual("logs/update_latest_summary.json", checks["source_summary"])
            stage = diagnostic.determine_stage({}, checks, {"dry_run_passed": True}, {"pipeline_success": True})
            self.assertEqual(("基础修复", False, "先修复更新脚本后置检查失败项，再继续影子盘"), stage)

    def test_order_plan_uses_volume_amount_and_price_fields(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "signals/order_plan.json", {
                "plan_volume": 2400, "plan_amount": 12345.6, "plan_price_ref": 5.144
            })
            result = diagnostic.collect_etf()
            self.assertEqual(2400, result["planned_volume"])
            self.assertEqual(12345.6, result["planned_amount"])
            self.assertEqual(5.144, result["planned_price_ref"])

    def test_does_not_call_real_trading_functions(self):
        with open(diagnostic.__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        forbidden = "order" + "_stock(" 
        forbidden_cancel = "cancel_order" + "_stock("
        self.assertNotIn(forbidden, source)
        self.assertNotIn(forbidden_cancel, source)

    def test_ai_api_report_shapes_and_bad_jsonl(self):
        for report in ([], {"average_duration_ms": 12}, None):
            with self.subTest(report=report), tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
                os.makedirs(os.path.join(root, "logs"))
                if report is not None:
                    with open(os.path.join(root, "logs", "ai_api_report.json"), "w", encoding="utf-8") as handle: json.dump(report, handle)
                with open(os.path.join(root, "logs", "ai_api_calls.jsonl"), "w", encoding="utf-8") as handle: handle.write("bad json\n{}\n")
                self.assertEqual("ok", diagnostic.collect_ai_api()["status"])

    def test_failed_collector_still_writes_reports(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root), mock.patch.object(diagnostic, "collect_etf", side_effect=RuntimeError("broken")):
            report = diagnostic.main()
            self.assertTrue(report["errors"])
            self.assertTrue(os.path.exists(os.path.join(root, "logs", "assistant_diagnostic_latest.md")))
            self.assertTrue(os.path.exists(os.path.join(root, "logs", "assistant_diagnostic_latest.json")))

    def test_etf_shadow_state_takes_priority_over_ma_daily_fields(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "signals/daily_status.json", {"stock_code": "600000.SH", "signal": "SELL_SIGNAL"})
            self.write_json(root, "signals/selected_etf.json", {"selected": [{"stock_code": "159915.SZ"}]})
            self.write_json(root, "signals/target_signal.json", {"stock_code": "159915.SZ", "signal": "BUY_SIGNAL"})
            self.write_json(root, "signals/order_plan.json", {"stock_code": "159915.SZ", "action": "PLAN_BUY"})
            self.write_json(root, "shadow/daily_snapshot.json", {"today_trades": [{"stock_code": "159915.SZ"}]})
            result = diagnostic.collect_etf()
            self.assertEqual("etf_rotation", result["strategy_source"])
            self.assertEqual("159915.SZ", result["selected_etf"])
            self.assertEqual("BUY_SIGNAL", result["signal_type"])
            self.assertNotIn("warning", result)

    def test_etf_shadow_mismatch_outputs_warning_and_details(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "signals/selected_etf.json", {"selected": [{"stock_code": "510300.SH"}]})
            self.write_json(root, "signals/target_signal.json", {"stock_code": "510300.SH", "signal": "BUY_SIGNAL"})
            self.write_json(root, "signals/order_plan.json", {"stock_code": "510300.SH", "action": "PLAN_BUY"})
            self.write_json(root, "shadow/daily_snapshot.json", {"today_trades": [{"stock_code": "159915.SZ"}]})
            result = diagnostic.collect_etf()
            self.assertEqual("order_plan 与 shadow 成交标的不一致", result["warning"])
            self.assertEqual("159915.SZ", result["mismatch_details"]["shadow_trade_code"])

if __name__ == "__main__": unittest.main()
