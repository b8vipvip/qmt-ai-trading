#!/usr/bin/env python
"""Scheduled-task entrypoint for the safe daily dry-run pipeline."""

from __future__ import annotations

import argparse
import contextlib
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.cache_warmup import build_default_warmup_request, format_cache_warmup_result, warmup_history_cache
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.universe_warmup import build_universe_warmup_request, format_universe_warmup_result, warmup_etf_universe_history
from scripts.run_daily_pipeline import main as run_daily_pipeline_main


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scheduled dry-run daily pipeline with optional historical cache warmup.")
    parser.add_argument("--warmup-cache", action="store_true", help="Warm historical bar cache before running the dry-run pipeline.")
    parser.add_argument("--warmup-universe", action="store_true", help="Warm ETF universe historical cache before running the dry-run pipeline.")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--universe-lookback-days", type=int, default=None)
    parser.add_argument("--universe-lookback-years", type=int, default=None)
    parser.add_argument("--warmup-provider", default="mock", choices=["mock", "qmt"], help="Historical provider for cache warmup.")
    parser.add_argument("--warmup-start", default=None, help="Warmup start date, e.g. 2024-01-01.")
    parser.add_argument("--warmup-end", default=None, help="Warmup end date, e.g. 2024-01-10.")
    parser.add_argument("--warmup-frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--warmup-fail-fast", action="store_true")
    parser.add_argument("--use-cached-research", action="store_true", help="Pass cached Research mode to the daily pipeline.")
    parser.add_argument("--research-start", default=None)
    parser.add_argument("--research-end", default=None)
    parser.add_argument("--research-frequency", default="1d")
    parser.add_argument("--min-bars", type=int, default=20)
    parser.add_argument("--cached-strategy-top-n", type=int, default=1)
    parser.add_argument("--cached-strategy-min-score", type=float, default=None)
    parser.add_argument("--cached-strategy-min-bars", type=int, default=20)
    parser.add_argument("--data-source-mode", default="cached_real_first", choices=["legacy", "cached", "auto", "mock", "cached_real_first"])
    parser.add_argument("--allow-mock-fallback", action="store_true")
    parser.add_argument("--quality-report-dir", default="qmt_data_quality_reports")
    parser.add_argument("--require-quality-report", action="store_true")
    parser.add_argument("--allow-unknown-quality-for-dry-run", action="store_true", default=True)
    parser.add_argument("--allow-mock-cache", action="store_true")
    parser.add_argument("--min-quality-level", default="UNKNOWN", choices=["UNKNOWN", "LOW", "MEDIUM", "HIGH", "UNAVAILABLE"])
    parser.add_argument("--min-coverage-ratio", type=float, default=0.8)
    parser.add_argument("--min-loaded-symbols", type=int, default=1)
    parser.add_argument("--require-cached-research", action="store_true")
    parser.add_argument("--data-source-confidence-required", default=None, choices=["LOW", "MEDIUM", "HIGH"])
    parser.add_argument("--create-approval", action="store_true")
    parser.add_argument("--approval-root", default="approvals")
    parser.add_argument("--approval-expires-hours", type=float, default=24.0)

    parser.add_argument("--enable-portfolio-plan", action="store_true", help="Generate dry-run/paper portfolio plan before Risk Gate.")
    parser.add_argument("--portfolio-method", default="score_weight", choices=["equal_weight", "score_weight", "risk_adjusted_weight"])
    parser.add_argument("--portfolio-top-n", type=int, default=2)
    parser.add_argument("--portfolio-cash-reserve-ratio", type=float, default=0.2)
    parser.add_argument("--portfolio-max-symbol-weight", type=float, default=0.3)
    parser.add_argument("--portfolio-max-weight", type=float, default=0.8)
    parser.add_argument("--portfolio-rebalance-threshold", type=float, default=0.05)
    parser.add_argument("--portfolio-total-asset", type=float, default=1000000.0)
    parser.add_argument("--portfolio-current-cash", type=float, default=1000000.0)
    parser.add_argument("--portfolio-snapshot-path", default=None)
    parser.add_argument("--enable-monitoring", action="store_true")
    parser.add_argument("--monitoring-output-dir", default="monitoring_reports")
    parser.add_argument("--monitoring-dry-run-alerts", action="store_true")
    parser.add_argument("--enable-agent-research", action="store_true")
    parser.add_argument("--agent-research-output-dir", default="agent_reports")
    parser.add_argument("--agent-research-mode", default="local_rules", choices=["mock", "local_rules", "external_llm_disabled"])
    parser.add_argument("--agent-include-monitoring", action="store_true", default=True)
    parser.add_argument("--agent-include-backtest", action="store_true", default=True)
    parser.add_argument("--agent-include-human-checklist", action="store_true", default=True)
    parser.add_argument("--enable-live-gray-readiness", action="store_true")
    parser.add_argument("--live-gray-output-dir", default="live_gray_reports")
    parser.add_argument("--live-gray-allowed-symbols", default="")
    parser.add_argument("--live-gray-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--live-gray-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--live-gray-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--live-gray-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--live-gray-enabled", action="store_true")
    parser.add_argument("--live-enabled", action="store_true")
    parser.add_argument("--live-gray-operator-name", default="")
    parser.add_argument("--build-dashboard", action="store_true")
    parser.add_argument("--dashboard-output", default="dashboard_stage31/scheduled_dashboard.html")
    parser.add_argument("--dashboard-report-dir", default=None)
    parser.add_argument("--dashboard-title", default="QMT AI Trading Scheduled Dashboard")
    parser.add_argument("--enable-data-quality-tracking", action="store_true")
    parser.add_argument("--data-quality-tracking-output-dir", default="data_quality_tracking")
    parser.add_argument("--data-quality-tracking-report-dir", default="qmt_data_quality_reports")
    parser.add_argument("--data-quality-tracking-cache-root", default=None)
    parser.add_argument("--data-quality-tracking-symbols", default="")
    parser.add_argument("--data-quality-tracking-start", default=None)
    parser.add_argument("--data-quality-tracking-end", default=None)
    parser.add_argument("--enable-notification-dry-run", action="store_true")
    parser.add_argument("--notification-dry-run-output-dir", default="notification_dryrun")
    parser.add_argument("--notification-dry-run-channels", default=None)
    parser.add_argument("--notification-dry-run-recipients", default=None)
    parser.add_argument("--notification-dry-run-preview-output-dir", default=None)
    parser.add_argument("--enable-gray-rehearsal", action="store_true")
    parser.add_argument("--gray-rehearsal-output-dir", default="gray_rehearsal")
    parser.add_argument("--gray-rehearsal-allowed-symbols", default="")
    parser.add_argument("--gray-rehearsal-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--gray-rehearsal-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--enable-gray-decision-package", action="store_true")
    parser.add_argument("--gray-decision-output-dir", default="gray_decision")
    parser.add_argument("--gray-decision-allowed-symbols", default="")
    parser.add_argument("--gray-decision-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--gray-decision-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--gray-decision-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--gray-decision-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--gray-decision-operator-name", default="")
    parser.add_argument("--gray-decision-reviewer-name", default="")
    parser.add_argument("--enable-live-manual-prep", action="store_true")
    parser.add_argument("--live-manual-prep-output-dir", default="live_manual_prep")
    parser.add_argument("--live-manual-prep-allowed-symbols", default="")
    parser.add_argument("--live-manual-prep-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--live-manual-prep-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--live-manual-prep-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--live-manual-prep-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--live-manual-prep-operator-name", default="")
    parser.add_argument("--live-manual-prep-reviewer-name", default="")
    parser.add_argument("--live-manual-prep-risk-owner-name", default="")
    parser.add_argument("--enable-live-env-check", action="store_true")
    parser.add_argument("--live-env-check-output-dir", default="live_env_check")
    parser.add_argument("--live-env-check-allowed-symbols", default="")
    parser.add_argument("--live-env-check-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--live-env-check-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--live-env-check-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--live-env-check-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--live-env-check-operator-name", default="")
    parser.add_argument("--live-env-check-reviewer-name", default="")
    parser.add_argument("--enable-final-authorization-package", action="store_true")
    parser.add_argument("--final-authorization-output-dir", default="final_authorization")
    parser.add_argument("--final-authorization-allowed-symbols", default="")
    parser.add_argument("--final-authorization-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--final-authorization-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--final-authorization-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--final-authorization-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--final-authorization-operator-name", default="")
    parser.add_argument("--final-authorization-reviewer-name", default="")
    parser.add_argument("--final-authorization-risk-owner-name", default="")
    parser.add_argument("--final-authorization-final-approver-name", default="")
    parser.add_argument("--enable-redline-review", action="store_true")
    parser.add_argument("--redline-review-output-dir", default="redline_review")
    parser.add_argument("--redline-review-operator-name", default="")
    parser.add_argument("--redline-review-reviewer-name", default="")
    parser.add_argument("--enable-live-gray-ledger", action="store_true")
    parser.add_argument("--live-gray-ledger-output-dir", default="live_gray_ledger")
    parser.add_argument("--enable-live-gray-review", action="store_true")
    parser.add_argument("--live-gray-review-output-dir", default="live_gray_review")
    parser.add_argument("--enable-live-signature-freeze", action="store_true")
    parser.add_argument("--live-signature-freeze-output-dir", default="live_signature_freeze")
    parser.add_argument("--enable-live-env-snapshot", action="store_true")
    parser.add_argument("--live-env-snapshot-output-dir", default="live_env_snapshot")
    parser.add_argument("--enable-live-runbook", action="store_true")
    parser.add_argument("--live-runbook-output-dir", default="live_runbook")
    parser.add_argument("--enable-live-signoff", action="store_true")
    parser.add_argument("--live-signoff-output-dir", default="live_signoff")
    known, pipeline_args = parser.parse_known_args(argv)
    known.pipeline_args = pipeline_args
    return known


def main(argv: list[str] | None = None) -> int:
    parsed = _parse_args(argv)
    log_dir = ROOT / "logs" / "daily_pipeline"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"daily_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    args = list(parsed.pipeline_args or ["--write-reports", "--report-dir", "reports", "--notify-dry-run"])
    if parsed.data_source_mode != "legacy":
        args.extend(["--data-source-mode", parsed.data_source_mode])
    if parsed.allow_mock_fallback:
        args.append("--allow-mock-fallback")
    args.extend(["--quality-report-dir", parsed.quality_report_dir, "--min-quality-level", parsed.min_quality_level])
    if parsed.require_quality_report:
        args.append("--require-quality-report")
    if parsed.allow_unknown_quality_for_dry_run:
        args.append("--allow-unknown-quality-for-dry-run")
    if parsed.allow_mock_cache:
        args.append("--allow-mock-cache")
    args.extend(["--min-coverage-ratio", str(parsed.min_coverage_ratio), "--min-loaded-symbols", str(parsed.min_loaded_symbols)])
    if parsed.require_cached_research:
        args.append("--require-cached-research")
    if parsed.data_source_confidence_required:
        args.extend(["--data-source-confidence-required", parsed.data_source_confidence_required])
    if parsed.create_approval:
        args.append("--create-approval")

    if parsed.enable_portfolio_plan:
        args.append("--enable-portfolio-plan")
    if parsed.enable_monitoring:
        args.append("--enable-monitoring")
        args.extend(["--monitoring-output-dir", parsed.monitoring_output_dir])
        if parsed.monitoring_dry_run_alerts:
            args.append("--monitoring-dry-run-alerts")
    if parsed.enable_agent_research:
        args.append("--enable-agent-research")
        args.extend(["--agent-research-output-dir", parsed.agent_research_output_dir, "--agent-research-mode", parsed.agent_research_mode])
        if parsed.agent_include_monitoring:
            args.append("--agent-include-monitoring")
        if parsed.agent_include_backtest:
            args.append("--agent-include-backtest")
        if parsed.agent_include_human_checklist:
            args.append("--agent-include-human-checklist")
    if parsed.enable_live_gray_readiness:
        args.append("--enable-live-gray-readiness")
        args.extend(["--live-gray-output-dir", parsed.live_gray_output_dir])
        if parsed.live_gray_allowed_symbols:
            args.extend(["--live-gray-allowed-symbols", parsed.live_gray_allowed_symbols])
        args.extend(["--live-gray-max-total-capital", str(parsed.live_gray_max_total_capital), "--live-gray-max-single-order-value", str(parsed.live_gray_max_single_order_value)])
        args.extend(["--live-gray-max-symbol-weight", str(parsed.live_gray_max_symbol_weight), "--live-gray-max-portfolio-weight", str(parsed.live_gray_max_portfolio_weight)])
        if parsed.live_gray_enabled:
            args.append("--live-gray-enabled")
        if parsed.live_enabled:
            args.append("--live-enabled")
        if parsed.live_gray_operator_name:
            args.extend(["--live-gray-operator-name", parsed.live_gray_operator_name])
    if parsed.enable_data_quality_tracking:
        args.append("--enable-data-quality-tracking")
        args.extend(["--data-quality-tracking-output-dir", parsed.data_quality_tracking_output_dir, "--data-quality-tracking-report-dir", parsed.data_quality_tracking_report_dir])
        if parsed.data_quality_tracking_cache_root:
            args.extend(["--data-quality-tracking-cache-root", parsed.data_quality_tracking_cache_root])
        if parsed.data_quality_tracking_symbols:
            args.extend(["--data-quality-tracking-symbols", parsed.data_quality_tracking_symbols])
        if parsed.data_quality_tracking_start:
            args.extend(["--data-quality-tracking-start", parsed.data_quality_tracking_start])
        if parsed.data_quality_tracking_end:
            args.extend(["--data-quality-tracking-end", parsed.data_quality_tracking_end])
    if parsed.enable_notification_dry_run:
        args.append("--enable-notification-dry-run")
        args.extend(["--notification-dry-run-output-dir", parsed.notification_dry_run_output_dir])
        if parsed.notification_dry_run_channels:
            args.extend(["--notification-dry-run-channels", parsed.notification_dry_run_channels])
        if parsed.notification_dry_run_recipients:
            args.extend(["--notification-dry-run-recipients", parsed.notification_dry_run_recipients])
        if parsed.notification_dry_run_preview_output_dir:
            args.extend(["--notification-dry-run-preview-output-dir", parsed.notification_dry_run_preview_output_dir])
    if parsed.enable_gray_rehearsal:
        args.append("--enable-gray-rehearsal")
        args.extend(["--gray-rehearsal-output-dir", parsed.gray_rehearsal_output_dir])
        if parsed.gray_rehearsal_allowed_symbols:
            args.extend(["--gray-rehearsal-allowed-symbols", parsed.gray_rehearsal_allowed_symbols])
        args.extend(["--gray-rehearsal-max-total-capital", str(parsed.gray_rehearsal_max_total_capital), "--gray-rehearsal-max-single-order-value", str(parsed.gray_rehearsal_max_single_order_value)])
    if parsed.enable_gray_decision_package:
        args.append("--enable-gray-decision-package")
        args.extend(["--gray-decision-output-dir", parsed.gray_decision_output_dir])
        if parsed.gray_decision_allowed_symbols:
            args.extend(["--gray-decision-allowed-symbols", parsed.gray_decision_allowed_symbols])
        args.extend(["--gray-decision-max-total-capital", str(parsed.gray_decision_max_total_capital), "--gray-decision-max-single-order-value", str(parsed.gray_decision_max_single_order_value)])
        args.extend(["--gray-decision-max-symbol-weight", str(parsed.gray_decision_max_symbol_weight), "--gray-decision-max-portfolio-weight", str(parsed.gray_decision_max_portfolio_weight)])
        if parsed.gray_decision_operator_name:
            args.extend(["--gray-decision-operator-name", parsed.gray_decision_operator_name])
        if parsed.gray_decision_reviewer_name:
            args.extend(["--gray-decision-reviewer-name", parsed.gray_decision_reviewer_name])
    if parsed.enable_live_manual_prep:
        args.append("--enable-live-manual-prep")
        args.extend(["--live-manual-prep-output-dir", parsed.live_manual_prep_output_dir])
        if parsed.live_manual_prep_allowed_symbols:
            args.extend(["--live-manual-prep-allowed-symbols", parsed.live_manual_prep_allowed_symbols])
        args.extend(["--live-manual-prep-max-total-capital", str(parsed.live_manual_prep_max_total_capital), "--live-manual-prep-max-single-order-value", str(parsed.live_manual_prep_max_single_order_value)])
        args.extend(["--live-manual-prep-max-symbol-weight", str(parsed.live_manual_prep_max_symbol_weight), "--live-manual-prep-max-portfolio-weight", str(parsed.live_manual_prep_max_portfolio_weight)])

    if parsed.enable_final_authorization_package:
        args.append("--enable-final-authorization-package")
        args.extend(["--final-authorization-output-dir", parsed.final_authorization_output_dir])
        if parsed.final_authorization_allowed_symbols:
            args.extend(["--final-authorization-allowed-symbols", parsed.final_authorization_allowed_symbols])
        args.extend(["--final-authorization-max-total-capital", str(parsed.final_authorization_max_total_capital), "--final-authorization-max-single-order-value", str(parsed.final_authorization_max_single_order_value)])
        args.extend(["--final-authorization-max-symbol-weight", str(parsed.final_authorization_max_symbol_weight), "--final-authorization-max-portfolio-weight", str(parsed.final_authorization_max_portfolio_weight)])
    if parsed.enable_redline_review:
        args.append("--enable-redline-review")
        args.extend(["--redline-review-output-dir", parsed.redline_review_output_dir])
        if parsed.redline_review_operator_name:
            args.extend(["--redline-review-operator-name", parsed.redline_review_operator_name])
        if parsed.redline_review_reviewer_name:
            args.extend(["--redline-review-reviewer-name", parsed.redline_review_reviewer_name])
    if parsed.enable_live_gray_ledger:
        args.append("--enable-live-gray-ledger")
        args.extend(["--live-gray-ledger-output-dir", parsed.live_gray_ledger_output_dir])
    if parsed.enable_live_gray_review:
        args.append("--enable-live-gray-review")
        args.extend(["--live-gray-review-output-dir", parsed.live_gray_review_output_dir])
    if parsed.enable_live_signature_freeze:
        args.append("--enable-live-signature-freeze")
        args.extend(["--live-signature-freeze-output-dir", parsed.live_signature_freeze_output_dir])
    if parsed.enable_live_env_snapshot:
        args.append("--enable-live-env-snapshot")
        args.extend(["--live-env-snapshot-output-dir", parsed.live_env_snapshot_output_dir])
    if parsed.enable_live_runbook:
        args.append("--enable-live-runbook")
        args.extend(["--live-runbook-output-dir", parsed.live_runbook_output_dir])
    if parsed.enable_live_signoff:
        args.append("--enable-live-signoff")
        args.extend(["--live-signoff-output-dir", parsed.live_signoff_output_dir])
    if parsed.build_dashboard:
        args.append("--build-dashboard")
        args.extend(["--dashboard-output", parsed.dashboard_output, "--dashboard-title", parsed.dashboard_title])
        if parsed.dashboard_report_dir:
            args.extend(["--dashboard-report-dir", parsed.dashboard_report_dir])
    args.extend(["--portfolio-method", parsed.portfolio_method, "--portfolio-top-n", str(parsed.portfolio_top_n)])
    args.extend(["--portfolio-cash-reserve-ratio", str(parsed.portfolio_cash_reserve_ratio), "--portfolio-max-symbol-weight", str(parsed.portfolio_max_symbol_weight)])
    args.extend(["--portfolio-max-weight", str(parsed.portfolio_max_weight), "--portfolio-rebalance-threshold", str(parsed.portfolio_rebalance_threshold)])
    args.extend(["--portfolio-total-asset", str(parsed.portfolio_total_asset), "--portfolio-current-cash", str(parsed.portfolio_current_cash)])
    if parsed.portfolio_snapshot_path:
        args.extend(["--portfolio-snapshot-path", parsed.portfolio_snapshot_path])
    args.extend(["--approval-root", parsed.approval_root, "--approval-expires-hours", str(parsed.approval_expires_hours)])
    if parsed.use_cached_research or parsed.data_source_mode in {"cached", "auto", "cached_real_first"}:
        if parsed.use_cached_research:
            args.append("--use-cached-research")
        args.extend(["--cache-root", parsed.cache_root])
        if parsed.research_start:
            args.extend(["--research-start", parsed.research_start])
        if parsed.research_end:
            args.extend(["--research-end", parsed.research_end])
        args.extend(["--research-frequency", parsed.research_frequency, "--min-bars", str(parsed.min_bars)])
        args.extend(["--cached-strategy-top-n", str(parsed.cached_strategy_top_n), "--cached-strategy-min-bars", str(parsed.cached_strategy_min_bars)])
        if parsed.cached_strategy_min_score is not None:
            args.extend(["--cached-strategy-min-score", str(parsed.cached_strategy_min_score)])
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("QMT AI Trading scheduled dry-run pipeline\n")
        log_file.write(f"Started at: {datetime.now().isoformat()}\n")
        log_file.write(f"Arguments: {' '.join(args)}\n\n")
        try:
            with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
                if parsed.warmup_universe:
                    request = build_universe_warmup_request(
                        universe_name=parsed.universe_name,
                        start_date=parsed.warmup_start,
                        end_date=parsed.warmup_end,
                        lookback_days=parsed.universe_lookback_days,
                        lookback_years=parsed.universe_lookback_years,
                        frequency=parsed.warmup_frequency,
                        provider=parsed.warmup_provider,
                        cache_root=parsed.cache_root,
                        fail_fast=parsed.warmup_fail_fast,
                        metadata={"entrypoint": "run_scheduled_daily_pipeline", "mode": "universe"},
                    )
                    universe_result = warmup_etf_universe_history(request)
                    print(format_universe_warmup_result(universe_result))
                elif parsed.warmup_cache:
                    if not parsed.warmup_start or not parsed.warmup_end:
                        raise ValueError("--warmup-start and --warmup-end are required when --warmup-cache is used")
                    symbols = [item.symbol for item in get_default_etf_universe()]
                    request = build_default_warmup_request(
                        symbols=symbols,
                        start_date=parsed.warmup_start,
                        end_date=parsed.warmup_end,
                        frequency=parsed.warmup_frequency,
                        provider=parsed.warmup_provider,
                        cache_root=parsed.cache_root,
                        fail_fast=parsed.warmup_fail_fast,
                        metadata={"entrypoint": "run_scheduled_daily_pipeline"},
                    )
                    warmup_result = warmup_history_cache(request)
                    print(format_cache_warmup_result(warmup_result))
                code = run_daily_pipeline_main(args)
        except Exception:
            traceback.print_exc(file=log_file)
            code = 1
        log_file.write(f"\nFinished at: {datetime.now().isoformat()}\n")
        log_file.write(f"Exit code: {code}\n")
    print(f"Scheduled dry-run pipeline finished with exit code {code}. Log: {log_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
