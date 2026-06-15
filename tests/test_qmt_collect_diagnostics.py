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
            with open(os.path.join(root, "config.json"), "w") as handle: json.dump(config, handle)
            self.assertFalse(diagnostic.collect_config()["live_trading_enabled"])

    def test_does_not_call_real_trading_functions(self):
        with open(diagnostic.__file__, "r") as handle:
            source = handle.read()
        forbidden = "order" + "_stock(" 
        forbidden_cancel = "cancel_order" + "_stock("
        self.assertNotIn(forbidden, source)
        self.assertNotIn(forbidden_cancel, source)

if __name__ == "__main__": unittest.main()
