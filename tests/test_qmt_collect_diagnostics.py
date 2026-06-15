# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest import mock
import qmt_collect_diagnostics as diagnostic

class DiagnosticTests(unittest.TestCase):
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
        stage = diagnostic.determine_stage(config, {"code_pull": "未知", "unit_tests": "未知", "safety_scan": "未知"}, {"dry_run_passed": True}, {"pipeline_success": True})
        self.assertTrue(stage[1])
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            with open(os.path.join(root, "config.json"), "w", encoding="utf-8") as handle: json.dump(config, handle)
            self.assertFalse(diagnostic.collect_config()["live_trading_enabled"])

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

if __name__ == "__main__": unittest.main()
