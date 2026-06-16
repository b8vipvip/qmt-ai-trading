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

    def test_falls_back_to_newest_historical_update_summary(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "logs/update_20260101_010101_summary.json", {"final_status": "旧"})
            newest = os.path.join(root, "logs", "update_20260102_010101_summary.json")
            self.write_json(root, "logs/update_20260102_010101_summary.json", {"final_status": "更新成功", "unit_tests": "通过"})
            old = os.path.join(root, "logs", "update_20260101_010101_summary.json")
            os.utime(old, (100, 100))
            os.utime(newest, (200, 200))
            checks = diagnostic.collect_update_checks()
            self.assertEqual("更新成功", checks["final_status"])
            self.assertEqual("logs/update_20260102_010101_summary.json", checks["source_summary"])

    def test_successful_update_does_not_override_shadow_observation_stage(self):
        updates = {key: "通过" for key in ["config_check", "unit_tests", "python_compile", "safety_scan"]}
        updates.update({"final_status": "更新成功", "code_pull": "无需更新"})
        stage = diagnostic.determine_stage({}, updates, {"dry_run_passed": True}, {"pipeline_success": True},
                                           {"started": True, "running_days": 3})
        self.assertEqual("ETF 影子盘观察期", stage[0])

    def test_broken_update_summary_adds_error_and_report_still_generates(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            os.makedirs(os.path.join(root, "logs"))
            with open(os.path.join(root, "logs", "update_latest_summary.json"), "w", encoding="utf-8") as handle:
                handle.write("{broken")
            report = diagnostic.main()
            self.assertTrue(any(item["collector"] == "update_checks" for item in report["errors"]))
            self.assertTrue(os.path.exists(os.path.join(root, "logs", "assistant_diagnostic_latest.md")))

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

    def test_shadow_includes_latest_daily_review_ai_diagnostics(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "reports/daily_report_20260615.json", {
                "ai_called": True, "review_mode": "ai_failed_fallback",
                "provider": "example", "model": "model", "error_message": "timeout"
            })
            result = diagnostic.collect_shadow()
            self.assertTrue(result["daily_review_ai_called"])
            self.assertEqual("ai_failed_fallback", result["daily_review_mode"])
            self.assertEqual("example/model", result["daily_review_provider_model"])
            self.assertEqual("timeout", result["daily_review_error"])

    def test_shadow_defaults_daily_review_to_template_without_report(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            result = diagnostic.collect_shadow()
            self.assertFalse(result["daily_review_ai_called"])
            self.assertEqual("template", result["daily_review_mode"])

    def test_failed_collector_still_writes_reports(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root), mock.patch.object(diagnostic, "collect_etf", side_effect=RuntimeError("broken")):
            report = diagnostic.main()
            self.assertTrue(report["errors"])
            self.assertTrue(os.path.exists(os.path.join(root, "logs", "assistant_diagnostic_latest.md")))
            self.assertTrue(os.path.exists(os.path.join(root, "logs", "assistant_diagnostic_latest.json")))


    def test_collects_latest_shadow_replay_summary_without_stage_effect(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "shadow_replay/run_20260615_120000/replay_summary.json", {"final_asset": 123456, "total_trades": 3})
            self.write_json(root, "signals/order_plan.json", {"action": "PLAN_BUY"})
            self.write_json(root, "logs/ai_research_pipeline_20260615_summary.json", {"success": True})
            result = diagnostic.build_report()
            self.assertTrue(result["shadow_replay"]["exists"])
            self.assertEqual(123456, result["shadow_replay"]["summary"]["final_asset"])
            self.assertEqual("准备进入 ETF 影子盘", result["stage"])

    def test_shadow_replay_display_fields_and_warnings(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "shadow_replay/run_20260615_120000/replay_summary.json", {
                "start_date": "2025-01-01", "end_date": "2026-06-16", "total_return_pct": 1.2,
                "annualized_return_pct": 0.8, "max_drawdown_pct": 2.3, "total_trades": 1, "closed_trades": 0,
                "open_positions": True, "win_rate": None, "tradable_selected_etf_counts": {"510300.SH": 3},
                "benchmark_counts": {"000300.SH": 3}
            })
            result = diagnostic.collect_shadow_replay()
            self.assertTrue(result["exists"])
            self.assertEqual("2025-01-01 至 2026-06-16", result["display"]["period"])
            self.assertEqual({"510300.SH": 3}, result["display"]["tradable_selected_etf_counts"])
            self.assertEqual({"000300.SH": 3}, result["display"]["benchmark_counts"])

    def test_shadow_replay_detects_metric_warning(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "shadow_replay/run_20260615_120000/replay_summary.json", {"total_trades": 1, "closed_trades": 0, "win_rate": 0.0})
            result = diagnostic.collect_shadow_replay()
            self.assertTrue(any("win_rate" in item for item in result["display"]["metric_warnings"]))

    def test_collects_latest_shadow_replay_batch_summary(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.object(diagnostic, "ROOT", root):
            self.write_json(root, "shadow_replay_batch/run_20260616_120000/batch_summary.json", {
                "period_results": [{"period_name": "p1"}, {"period_name": "p2"}],
                "average_return_pct": 1.5, "worst_period": "p2", "max_drawdown_worst_period": "p2",
                "positive_period_count": 1, "negative_period_count": 1, "stability_score": 70,
                "overfit_warning": "无明显过拟合警告", "continue_shadow_replay_recommended": True,
                "live_trading_not_recommended": True
            })
            result = diagnostic.collect_shadow_replay_batch()
            self.assertTrue(result["exists"])
            self.assertEqual(2, result["display"]["period_count"])
            self.assertEqual(1.5, result["display"]["average_return_pct"])
            self.assertTrue(result["display"]["continue_shadow_replay_recommended"])

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
