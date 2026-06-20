#!/usr/bin/env python
"""Command line entrypoint for the dry-run ETF daily signal pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.pipeline.daily_runner import run_etf_daily_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run QMT AI Trading daily ETF pipeline in dry-run/shadow mode.")
    parser.add_argument("--date", dest="trade_date", default=None, help="Trade date, for example 2026-06-17.")
    parser.add_argument("--symbols", default="", help="Comma-separated ETF symbols. Defaults to Data Hub ETF universe.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Keep dry-run mode enabled (default).")
    parser.add_argument("--write-reports", action="store_true", help="Write Markdown/JSON/HTML reports to disk.")
    parser.add_argument("--report-dir", default=None, help="Report output directory. Defaults to reports/YYYY-MM-DD when writing reports.")
    parser.add_argument("--notify-dry-run", action="store_true", help="Run notification adapters in dry-run placeholder mode only.")
    parser.add_argument("--use-cached-research", action="store_true", help="Read local cached bars for Research scoring before ETF strategy.")
    parser.add_argument("--cache-root", default="market_data", help="Local market data cache root.")
    parser.add_argument("--research-start", default=None, help="Cached Research start date.")
    parser.add_argument("--research-end", default=None, help="Cached Research end date.")
    parser.add_argument("--research-frequency", default="1d", help="Cached Research bar frequency.")
    parser.add_argument("--min-bars", type=int, default=20, help="Minimum cached bars required per symbol.")
    parser.add_argument("--cached-strategy-top-n", type=int, default=1, help="Top N cached ETF rotation candidates to select.")
    parser.add_argument("--cached-strategy-min-score", type=float, default=None, help="Minimum cached ETF rotation score.")
    parser.add_argument("--cached-strategy-min-bars", type=int, default=20, help="Minimum bars required by cached ETF rotation.")
    parser.add_argument("--data-source-mode", default="cached_real_first", choices=["legacy", "cached", "auto", "mock", "cached_real_first"], help="Pipeline data source mode.")
    parser.add_argument("--allow-mock-fallback", action="store_true", help="Allow explicit mock fallback when cache is insufficient in auto/cached_real_first mode.")
    parser.add_argument("--quality-report-dir", default="qmt_data_quality_reports")
    parser.add_argument("--require-quality-report", action="store_true")
    parser.add_argument("--allow-unknown-quality-for-dry-run", action="store_true", default=True)
    parser.add_argument("--allow-mock-cache", action="store_true")
    parser.add_argument("--min-quality-level", default="UNKNOWN", choices=["UNKNOWN", "LOW", "MEDIUM", "HIGH", "UNAVAILABLE"])
    parser.add_argument("--min-coverage-ratio", type=float, default=0.8)
    parser.add_argument("--min-loaded-symbols", type=int, default=1)
    parser.add_argument("--require-cached-research", action="store_true")
    parser.add_argument("--data-source-confidence-required", default=None, choices=["LOW", "MEDIUM", "HIGH"])
    parser.add_argument("--create-approval", action="store_true", help="Create a pending human approval request when TradeIntent exists.")
    parser.add_argument("--approval-root", default="approvals", help="Local approval JSON root directory.")
    parser.add_argument("--approval-expires-hours", type=float, default=24.0, help="Pending approval expiry window in hours.")

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

    parser.add_argument("--enable-monitoring", action="store_true", help="Run Stage 28 dry-run monitoring checks after the pipeline.")
    parser.add_argument("--monitoring-output-dir", default="monitoring_reports")
    parser.add_argument("--monitoring-dry-run-alerts", action="store_true", default=False)
    parser.add_argument("--enable-agent-research", action="store_true", help="Generate Stage 29 read-only Agent Research memo.")
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
    parser.add_argument("--build-dashboard", action="store_true", help="Build read-only Stage 31 dashboard after pipeline completes.")
    parser.add_argument("--dashboard-output", default="dashboard_stage31/daily_dashboard.html")
    parser.add_argument("--dashboard-report-dir", default=None)
    parser.add_argument("--dashboard-title", default="QMT AI Trading Daily Dashboard")
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
    parser.add_argument("--enable-live-final-review", action="store_true")
    parser.add_argument("--live-final-review-output-dir", default="live_final_review")
    parser.add_argument("--enable-live-archive", action="store_true")
    parser.add_argument("--live-archive-output-dir", default="live_archive")
    parser.add_argument("--enable-live-consistency", action="store_true")
    parser.add_argument("--live-consistency-output-dir", default="live_consistency")
    parser.add_argument("--enable-live-final-archive", action="store_true")
    parser.add_argument("--live-final-archive-output-dir", default="live_final_archive")
    parser.add_argument("--enable-live-archive-lock", action="store_true")
    parser.add_argument("--live-archive-lock-output-dir", default="live_archive_lock")
    parser.add_argument("--enable-live-lock-consistency", action="store_true")
    parser.add_argument("--live-lock-consistency-output-dir", default="live_lock_consistency")
    parser.add_argument("--enable-live-archive-verification", action="store_true")
    parser.add_argument("--live-archive-verification-output-dir", default="live_archive_verification")
    parser.add_argument("--enable-live-gap-clearance", action="store_true")
    parser.add_argument("--live-gap-clearance-output-dir", default="live_gap_clearance")
    parser.add_argument("--enable-qmt-dryrun-calibration", action="store_true")
    parser.add_argument("--qmt-dryrun-calibration-output-dir", default="qmt_dryrun_calibration")
    parser.add_argument("--qmt-dryrun-calibration-provider", default="mock", choices=["mock", "qmt_xtdata"])
    parser.add_argument("--enable-real-cache-quality", action="store_true")
    parser.add_argument("--real-cache-quality-output-dir", default="real_cache_quality")
    parser.add_argument("--real-cache-quality-provider", default="mock", choices=["mock", "qmt_xtdata"])
    parser.add_argument("--enable-live-gray-candidate", action="store_true")
    parser.add_argument("--live-gray-candidate-output-dir", default="live_gray_candidate")
    parser.add_argument("--enable-live-gray-final-approval", action="store_true")
    parser.add_argument("--live-gray-final-approval-output-dir", default="live_gray_final_approval")
    parser.add_argument("--enable-live-gray-readonly-seal", action="store_true")
    parser.add_argument("--live-gray-readonly-seal-output-dir", default="live_gray_readonly_seal")
    parser.add_argument("--enable-pre-gray-final-review", action="store_true")
    parser.add_argument("--pre-gray-final-review-output-dir", default="pre_gray_final_review")
    parser.add_argument("--enable-api-gateway-review", action="store_true")
    parser.add_argument("--api-gateway-review-output-dir", default="api_gateway")
    parser.add_argument("--enable-local-console-review", action="store_true")
    parser.add_argument("--local-console-review-output-dir", default="local_console")
    parser.add_argument("--enable-local-console-detail-review", action="store_true")
    parser.add_argument("--local-console-detail-review-output-dir", default="local_console_detail")
    parser.add_argument("--enable-local-console-dashboard-review", action="store_true")
    parser.add_argument("--local-console-dashboard-review-output-dir", default="local_console_dashboard")
    parser.add_argument("--enable-local-console-shell-review", action="store_true")
    parser.add_argument("--local-console-shell-review-output-dir", default="local_console_shell")
    parser.add_argument("--enable-local-console-binding-review", action="store_true")
    parser.add_argument("--local-console-binding-review-output-dir", default="local_console_binding")
    parser.add_argument("--enable-local-console-preview-review", action="store_true")
    parser.add_argument("--local-console-preview-review-output-dir", default="local_console_preview")
    parser.add_argument("--enable-local-console-refresh-review", action="store_true")
    parser.add_argument("--local-console-refresh-review-output-dir", default="local_console_refresh")
    args = parser.parse_args(argv)

    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    result = run_etf_daily_pipeline(
        trade_date=args.trade_date,
        symbols=symbols or None,
        dry_run=True,
        use_cached_research=args.use_cached_research,
        cache_root=args.cache_root,
        research_start_date=args.research_start,
        research_end_date=args.research_end,
        research_frequency=args.research_frequency,
        min_bars=args.min_bars,
        cached_strategy_top_n=args.cached_strategy_top_n,
        cached_strategy_min_score=args.cached_strategy_min_score,
        cached_strategy_min_bars=args.cached_strategy_min_bars,
        data_source_mode=args.data_source_mode,
        quality_report_dir=args.quality_report_dir,
        require_quality_report=args.require_quality_report,
        allow_unknown_quality_for_dry_run=args.allow_unknown_quality_for_dry_run,
        allow_mock_cache=args.allow_mock_cache,
        min_quality_level=args.min_quality_level,
        allow_mock_fallback=args.allow_mock_fallback,
        min_coverage_ratio=args.min_coverage_ratio,
        min_loaded_symbols=args.min_loaded_symbols,
        require_cached_research=args.require_cached_research,
        data_source_confidence_required=args.data_source_confidence_required,
        enable_portfolio_plan=args.enable_portfolio_plan,
        portfolio_method=args.portfolio_method,
        portfolio_top_n=args.portfolio_top_n,
        portfolio_cash_reserve_ratio=args.portfolio_cash_reserve_ratio,
        portfolio_max_symbol_weight=args.portfolio_max_symbol_weight,
        portfolio_max_weight=args.portfolio_max_weight,
        portfolio_rebalance_threshold=args.portfolio_rebalance_threshold,
        portfolio_total_asset=args.portfolio_total_asset,
        portfolio_current_cash=args.portfolio_current_cash,
        portfolio_snapshot_path=args.portfolio_snapshot_path,
        enable_agent_research=args.enable_agent_research,
        agent_research_output_dir=args.agent_research_output_dir,
        agent_research_mode=args.agent_research_mode,
        agent_include_monitoring=args.agent_include_monitoring,
        agent_include_backtest=args.agent_include_backtest,
        agent_include_human_checklist=args.agent_include_human_checklist,
        enable_live_gray_readiness=args.enable_live_gray_readiness,
        live_gray_output_dir=args.live_gray_output_dir,
        live_gray_allowed_symbols=[x.strip() for x in args.live_gray_allowed_symbols.split(",") if x.strip()] or None,
        live_gray_max_total_capital=args.live_gray_max_total_capital,
        live_gray_max_single_order_value=args.live_gray_max_single_order_value,
        live_gray_max_symbol_weight=args.live_gray_max_symbol_weight,
        live_gray_max_portfolio_weight=args.live_gray_max_portfolio_weight,
        live_gray_enabled=args.live_gray_enabled,
        live_enabled=args.live_enabled,
        live_gray_operator_name=args.live_gray_operator_name,
        enable_data_quality_tracking=args.enable_data_quality_tracking,
        data_quality_tracking_output_dir=args.data_quality_tracking_output_dir,
        data_quality_tracking_report_dir=args.data_quality_tracking_report_dir,
        data_quality_tracking_cache_root=args.data_quality_tracking_cache_root,
        data_quality_tracking_symbols=[x.strip() for x in args.data_quality_tracking_symbols.split(",") if x.strip()] or None,
        data_quality_tracking_start=args.data_quality_tracking_start,
        data_quality_tracking_end=args.data_quality_tracking_end,
        enable_notification_dry_run=args.enable_notification_dry_run,
        notification_dry_run_output_dir=args.notification_dry_run_output_dir,
        notification_dry_run_channels=args.notification_dry_run_channels,
        notification_dry_run_recipients=args.notification_dry_run_recipients,
        notification_dry_run_preview_output_dir=args.notification_dry_run_preview_output_dir,
        enable_gray_rehearsal=args.enable_gray_rehearsal,
        gray_rehearsal_output_dir=args.gray_rehearsal_output_dir,
        gray_rehearsal_allowed_symbols=[x.strip() for x in args.gray_rehearsal_allowed_symbols.split(",") if x.strip()] or None,
        gray_rehearsal_max_total_capital=args.gray_rehearsal_max_total_capital,
        gray_rehearsal_max_single_order_value=args.gray_rehearsal_max_single_order_value,
        enable_gray_decision_package=args.enable_gray_decision_package,
        gray_decision_output_dir=args.gray_decision_output_dir,
        gray_decision_allowed_symbols=[x.strip() for x in args.gray_decision_allowed_symbols.split(",") if x.strip()] or None,
        gray_decision_max_total_capital=args.gray_decision_max_total_capital,
        gray_decision_max_single_order_value=args.gray_decision_max_single_order_value,
        gray_decision_max_symbol_weight=args.gray_decision_max_symbol_weight,
        gray_decision_max_portfolio_weight=args.gray_decision_max_portfolio_weight,
        gray_decision_operator_name=args.gray_decision_operator_name,
        gray_decision_reviewer_name=args.gray_decision_reviewer_name,
        enable_live_manual_prep=args.enable_live_manual_prep,
        live_manual_prep_output_dir=args.live_manual_prep_output_dir,
        live_manual_prep_allowed_symbols=[x.strip() for x in args.live_manual_prep_allowed_symbols.split(",") if x.strip()] or None,
        live_manual_prep_max_total_capital=args.live_manual_prep_max_total_capital,
        live_manual_prep_max_single_order_value=args.live_manual_prep_max_single_order_value,
        live_manual_prep_max_symbol_weight=args.live_manual_prep_max_symbol_weight,
        live_manual_prep_max_portfolio_weight=args.live_manual_prep_max_portfolio_weight,
        live_manual_prep_operator_name=args.live_manual_prep_operator_name,
        live_manual_prep_reviewer_name=args.live_manual_prep_reviewer_name,
        live_manual_prep_risk_owner_name=args.live_manual_prep_risk_owner_name,
        enable_live_env_check=args.enable_live_env_check,
        live_env_check_output_dir=args.live_env_check_output_dir,
        live_env_check_allowed_symbols=[x.strip() for x in args.live_env_check_allowed_symbols.split(",") if x.strip()] or None,
        live_env_check_max_total_capital=args.live_env_check_max_total_capital,
        live_env_check_max_single_order_value=args.live_env_check_max_single_order_value,
        live_env_check_max_symbol_weight=args.live_env_check_max_symbol_weight,
        live_env_check_max_portfolio_weight=args.live_env_check_max_portfolio_weight,
        live_env_check_operator_name=args.live_env_check_operator_name,
        live_env_check_reviewer_name=args.live_env_check_reviewer_name,
        enable_final_authorization_package=args.enable_final_authorization_package,
        final_authorization_output_dir=args.final_authorization_output_dir,
        final_authorization_allowed_symbols=[x.strip() for x in args.final_authorization_allowed_symbols.split(",") if x.strip()] or None,
        final_authorization_max_total_capital=args.final_authorization_max_total_capital,
        final_authorization_max_single_order_value=args.final_authorization_max_single_order_value,
        final_authorization_max_symbol_weight=args.final_authorization_max_symbol_weight,
        final_authorization_max_portfolio_weight=args.final_authorization_max_portfolio_weight,
        final_authorization_operator_name=args.final_authorization_operator_name,
        final_authorization_reviewer_name=args.final_authorization_reviewer_name,
        final_authorization_risk_owner_name=args.final_authorization_risk_owner_name,
        final_authorization_final_approver_name=args.final_authorization_final_approver_name,
        enable_redline_review=args.enable_redline_review,
        redline_review_output_dir=args.redline_review_output_dir,
        redline_review_operator_name=args.redline_review_operator_name,
        redline_review_reviewer_name=args.redline_review_reviewer_name,
    )
    print(result.report_text)

    if args.enable_monitoring:
        from qmt_ai_trading.monitoring.service import MonitoringConfig, run_monitoring_check, save_monitoring_json
        from qmt_ai_trading.monitoring.formatters import format_monitoring_markdown

        data_source = result.metadata.get("data_source", {}) if isinstance(result.metadata, dict) else {}
        risk_reject_count = sum(1 for item in result.risk_decisions if not getattr(item, "allowed", False))
        monitoring_report = run_monitoring_check(MonitoringConfig(
            quality_level=str(data_source.get("quality_level", "UNKNOWN")),
            fallback_used=bool(data_source.get("fallback_used", False)),
            risk_reject_count=risk_reject_count,
            scheduler_exit_code=0,
            max_drawdown=float((getattr(result.backtest_result, "summary", {}) or {}).get("max_drawdown", 0.0)) if isinstance(getattr(result, "backtest_result", None), object) else 0.0,
            dry_run_alerts=args.monitoring_dry_run_alerts,
            alert_output_dir=str(Path(args.monitoring_output_dir) / "alerts"),
            metadata={"pipeline_run_id": result.context.run_id},
        ))
        out_dir = Path(args.monitoring_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "monitoring.md").write_text(format_monitoring_markdown(monitoring_report), encoding="utf-8")
        save_monitoring_json(monitoring_report, out_dir / "monitoring.json")
        print("\n" + format_monitoring_markdown(monitoring_report))

    if args.create_approval:
        from qmt_ai_trading.approval.service import approval_request_from_pipeline_result
        from qmt_ai_trading.approval.store import ApprovalStore

        store = ApprovalStore(args.approval_root)
        request = approval_request_from_pipeline_result(result, store=store, expires_hours=args.approval_expires_hours)
        if request is None:
            print("\nNo approval created: pipeline generated no TradeIntent.")
        else:
            print("\nPending approval created. Approval is not an order. No QMT order has been submitted.")
            print(f"approval_id={request.approval_id}")
            print(f"approval_file={store.get_request_path(request.approval_id)}")

    artifacts = []
    if args.write_reports:
        from qmt_ai_trading.reporting.writer import write_pipeline_reports

        artifacts = write_pipeline_reports(result, args.report_dir)
        print("\nReports written:")
        for artifact in artifacts:
            print(f"- {artifact.format}: {artifact.path}")

    if args.build_dashboard:
        from qmt_ai_trading.dashboard.safety import build_default_dashboard_config
        from qmt_ai_trading.dashboard.service import build_and_save_dashboard

        dashboard_config = build_default_dashboard_config(
            output_path=args.dashboard_output,
            report_dir=args.dashboard_report_dir or args.report_dir or "reports",
            monitoring_dir=args.monitoring_output_dir,
            agent_dir=args.agent_research_output_dir,
            live_gray_dir=args.live_gray_output_dir,
            approval_dir=args.approval_root,
            paper_dir="paper_orders",
            cache_quality_dir=args.quality_report_dir,
            title=args.dashboard_title,
            data_quality_dir=args.data_quality_tracking_output_dir,
            include_data_quality_tracking=args.enable_data_quality_tracking,
            notification_dry_run_dir=args.notification_dry_run_output_dir,
            include_notification_dry_run=args.enable_notification_dry_run,
            gray_rehearsal_dir=args.gray_rehearsal_output_dir,
            include_gray_rehearsal=args.enable_gray_rehearsal,
            gray_decision_dir=args.gray_decision_output_dir,
            include_gray_decision=args.enable_gray_decision_package,
            live_manual_prep_dir=args.live_manual_prep_output_dir,
            include_live_manual_prep=args.enable_live_manual_prep,
            live_env_check_dir=args.live_env_check_output_dir,
            include_live_env_check=args.enable_live_env_check,
            final_authorization_dir=args.final_authorization_output_dir,
            include_final_authorization=args.enable_final_authorization_package,
            redline_review_dir=args.redline_review_output_dir,
            include_redline_review=args.enable_redline_review,
        )
        _, dashboard_path = build_and_save_dashboard(dashboard_config)
        print(f"\nRead-only dashboard written: {dashboard_path}")


    if args.enable_live_gray_ledger:
        from qmt_ai_trading.live_gray_ledger.service import build_default_live_gray_ledger_config, run_live_gray_ledger, save_live_gray_ledger_report

        ledger_dir = Path(args.live_gray_ledger_output_dir)
        ledger_config = build_default_live_gray_ledger_config(repo_root=ROOT, output_dir=str(ledger_dir))
        ledger_report = run_live_gray_ledger(ledger_config)
        save_live_gray_ledger_report(ledger_report, ledger_dir / "live_gray_ledger.md", ledger_dir / "live_gray_ledger.json")
        print(f"\nStage41 read-only ledger written: {ledger_dir / 'live_gray_ledger.md'}")

    if args.enable_live_gray_review:
        from qmt_ai_trading.live_gray_review.service import build_default_live_gray_review_config, run_live_gray_review, save_live_gray_review_report, save_readonly_rehearsal_report

        review_dir = Path(args.live_gray_review_output_dir)
        review_config = build_default_live_gray_review_config(repo_root=ROOT, output_dir=str(review_dir))
        review_report = run_live_gray_review(review_config)
        save_live_gray_review_report(review_report, review_dir / "live_gray_review.md", review_dir / "live_gray_review.json")
        save_readonly_rehearsal_report(review_report.rehearsal, review_dir / "readonly_rehearsal.md", review_dir / "readonly_rehearsal.json")
        print(f"\nStage42 read-only live gray review package written: {review_dir / 'live_gray_review.md'}")

    if args.enable_live_signature_freeze:
        from qmt_ai_trading.live_signature_freeze.service import build_default_live_signature_freeze_config, run_config_freeze_summary, run_live_signature_freeze, save_config_freeze_report, save_live_signature_freeze_report

        sig_dir = Path(args.live_signature_freeze_output_dir)
        sig_config = build_default_live_signature_freeze_config(repo_root=ROOT, output_dir=str(sig_dir))
        sig_report = run_live_signature_freeze(sig_config)
        freeze_report = run_config_freeze_summary(sig_report)
        save_live_signature_freeze_report(sig_report, sig_dir / "live_signature_freeze.md", sig_dir / "live_signature_freeze.json")
        save_config_freeze_report(freeze_report, sig_dir / "config_freeze.md", sig_dir / "config_freeze.json")
        print(f"\nStage43 read-only live signature freeze package written: {sig_dir / 'live_signature_freeze.md'}")

    if args.enable_live_env_snapshot:
        from qmt_ai_trading.live_env_snapshot.service import build_default_live_env_snapshot_config, run_live_env_snapshot, run_readonly_environment_snapshot, save_live_env_snapshot_report, save_readonly_environment_snapshot_report

        env_dir = Path(args.live_env_snapshot_output_dir)
        env_config = build_default_live_env_snapshot_config(repo_root=ROOT, output_dir=str(env_dir))
        env_report = run_live_env_snapshot(env_config)
        readonly_report = run_readonly_environment_snapshot(env_report)
        save_live_env_snapshot_report(env_report, env_dir / "live_env_snapshot.md", env_dir / "live_env_snapshot.json")
        save_readonly_environment_snapshot_report(readonly_report, env_dir / "readonly_environment_snapshot.md", env_dir / "readonly_environment_snapshot.json")
        print(f"\nStage44 read-only live environment snapshot package written: {env_dir / 'live_env_snapshot.md'}")

    if args.enable_live_runbook:
        from qmt_ai_trading.live_runbook.service import build_default_live_runbook_config, run_incident_playbook, run_live_runbook, run_manual_rehearsal, save_incident_playbook_report, save_live_runbook_report, save_manual_rehearsal_report

        rb_dir = Path(args.live_runbook_output_dir)
        rb_config = build_default_live_runbook_config(repo_root=ROOT, output_dir=str(rb_dir))
        rb_report = run_live_runbook(rb_config)
        rehearsal_report = run_manual_rehearsal(rb_report)
        incident_report = run_incident_playbook(rb_report)
        save_live_runbook_report(rb_report, rb_dir / "live_runbook.md", rb_dir / "live_runbook.json")
        save_manual_rehearsal_report(rehearsal_report, rb_dir / "manual_rehearsal.md", rb_dir / "manual_rehearsal.json")
        save_incident_playbook_report(incident_report, rb_dir / "incident_playbook.md", rb_dir / "incident_playbook.json")
        print(f"\nStage45 read-only live runbook package written: {rb_dir / 'live_runbook.md'}")

    if args.enable_live_signoff:
        from qmt_ai_trading.live_signoff.service import build_default_live_signoff_config, run_incident_rehearsal, run_live_signoff, run_manual_signoff, save_incident_rehearsal_report, save_live_signoff_report, save_manual_signoff_report

        so_dir = Path(args.live_signoff_output_dir)
        so_config = build_default_live_signoff_config(repo_root=ROOT, output_dir=str(so_dir))
        so_report = run_live_signoff(so_config)
        manual_report = run_manual_signoff(so_report)
        incident_report = run_incident_rehearsal(so_report)
        save_live_signoff_report(so_report, so_dir / "live_signoff.md", so_dir / "live_signoff.json")
        save_manual_signoff_report(manual_report, so_dir / "manual_signoff.md", so_dir / "manual_signoff.json")
        save_incident_rehearsal_report(incident_report, so_dir / "incident_rehearsal.md", so_dir / "incident_rehearsal.json")
        print(f"\nStage46 read-only live signoff package written: {so_dir / 'live_signoff.md'}")


    if args.enable_live_final_review:
        from qmt_ai_trading.live_final_review.service import build_default_live_final_review_config, run_evidence_gap_report, run_live_final_review, run_next_readonly_plan, run_signature_verification, save_evidence_gap_report, save_live_final_review_report, save_next_readonly_plan_report, save_signature_verification_report

        fr_dir = Path(args.live_final_review_output_dir)
        fr_config = build_default_live_final_review_config(repo_root=ROOT, output_dir=str(fr_dir))
        fr_report = run_live_final_review(fr_config)
        sig_report = run_signature_verification(fr_report)
        gap_report = run_evidence_gap_report(fr_report)
        plan_report = run_next_readonly_plan(fr_report)
        save_live_final_review_report(fr_report, fr_dir / "live_final_review.md", fr_dir / "live_final_review.json")
        save_signature_verification_report(sig_report, fr_dir / "signature_verification.md", fr_dir / "signature_verification.json")
        save_evidence_gap_report(gap_report, fr_dir / "evidence_gap_report.md", fr_dir / "evidence_gap_report.json")
        save_next_readonly_plan_report(plan_report, fr_dir / "next_readonly_plan.md", fr_dir / "next_readonly_plan.json")
        print(f"\nStage47 final read-only live review package written: {fr_dir / 'live_final_review.md'}")

    if args.enable_live_archive:
        from qmt_ai_trading.live_archive.service import build_default_live_archive_config, run_evidence_remediation, run_human_verification_summary, run_live_archive, run_next_readonly_check, save_evidence_remediation_report, save_human_verification_summary_report, save_live_archive_report, save_next_readonly_check_report

        archive_dir = Path(args.live_archive_output_dir)
        archive_config = build_default_live_archive_config(repo_root=ROOT, output_dir=str(archive_dir))
        archive_report = run_live_archive(archive_config)
        remediation_report = run_evidence_remediation(archive_report)
        human_report = run_human_verification_summary(archive_report)
        check_report = run_next_readonly_check(archive_report)
        save_live_archive_report(archive_report, archive_dir / "live_archive.md", archive_dir / "live_archive.json")
        save_evidence_remediation_report(remediation_report, archive_dir / "evidence_remediation_plan.md", archive_dir / "evidence_remediation_plan.json")
        save_human_verification_summary_report(human_report, archive_dir / "human_verification_summary.md", archive_dir / "human_verification_summary.json")
        save_next_readonly_check_report(check_report, archive_dir / "next_readonly_check_plan.md", archive_dir / "next_readonly_check_plan.json")
        print(f"\nStage48 read-only live archive package written: {archive_dir / 'live_archive.md'}")


    if args.enable_live_consistency:
        from qmt_ai_trading.live_consistency.service import build_default_live_consistency_config, run_human_recheck, run_live_consistency, run_material_consistency, run_next_gray_check, save_human_recheck_report, save_live_consistency_report, save_material_consistency_report, save_next_gray_check_report

        consistency_dir = Path(args.live_consistency_output_dir)
        consistency_config = build_default_live_consistency_config(repo_root=ROOT, output_dir=str(consistency_dir))
        consistency_report = run_live_consistency(consistency_config)
        material_report = run_material_consistency(consistency_report)
        human_report = run_human_recheck(consistency_report)
        plan_report = run_next_gray_check(consistency_report)
        save_live_consistency_report(consistency_report, consistency_dir / "live_consistency.md", consistency_dir / "live_consistency.json")
        save_material_consistency_report(material_report, consistency_dir / "material_consistency.md", consistency_dir / "material_consistency.json")
        save_human_recheck_report(human_report, consistency_dir / "human_recheck.md", consistency_dir / "human_recheck.json")
        save_next_gray_check_report(plan_report, consistency_dir / "next_gray_check_plan.md", consistency_dir / "next_gray_check_plan.json")
        print(f"\nStage49 read-only live consistency package written: {consistency_dir / 'live_consistency.md'}")

    if args.enable_live_final_archive:
        from qmt_ai_trading.live_final_archive.service import build_default_live_final_archive_config, run_human_closure, run_live_final_archive, run_material_seal, run_next_readonly_check, save_human_closure_report, save_live_final_archive_report, save_material_seal_report, save_next_readonly_check_report

        final_archive_dir = Path(args.live_final_archive_output_dir)
        final_archive_config = build_default_live_final_archive_config(repo_root=ROOT, output_dir=str(final_archive_dir))
        final_archive_report = run_live_final_archive(final_archive_config)
        seal_report = run_material_seal(final_archive_report)
        human_closure_report = run_human_closure(final_archive_report)
        readonly_plan_report = run_next_readonly_check(final_archive_report)
        save_live_final_archive_report(final_archive_report, final_archive_dir / "live_final_archive.md", final_archive_dir / "live_final_archive.json")
        save_material_seal_report(seal_report, final_archive_dir / "material_seal.md", final_archive_dir / "material_seal.json")
        save_human_closure_report(human_closure_report, final_archive_dir / "human_closure.md", final_archive_dir / "human_closure.json")
        save_next_readonly_check_report(readonly_plan_report, final_archive_dir / "next_readonly_check_plan.md", final_archive_dir / "next_readonly_check_plan.json")
        print(f"\nStage50 final archive read-only package written: {final_archive_dir / 'live_final_archive.md'}")

    if args.enable_live_archive_lock:
        from qmt_ai_trading.live_archive_lock.service import build_default_live_archive_lock_config, run_archive_lock, run_human_closure_recheck, run_live_archive_lock, run_next_readonly_check, save_archive_lock_report, save_human_closure_recheck_report, save_live_archive_lock_report, save_next_readonly_check_report
        lock_dir = Path(args.live_archive_lock_output_dir)
        lock_config = build_default_live_archive_lock_config(repo_root=ROOT, output_dir=str(lock_dir))
        lock_report = run_live_archive_lock(lock_config)
        archive_lock_report = run_archive_lock(lock_report)
        human_recheck_report = run_human_closure_recheck(lock_report)
        readonly_plan_report = run_next_readonly_check(lock_report)
        save_live_archive_lock_report(lock_report, lock_dir / "live_archive_lock.md", lock_dir / "live_archive_lock.json")
        save_archive_lock_report(archive_lock_report, lock_dir / "archive_lock.md", lock_dir / "archive_lock.json")
        save_human_closure_recheck_report(human_recheck_report, lock_dir / "human_closure_recheck.md", lock_dir / "human_closure_recheck.json")
        save_next_readonly_check_report(readonly_plan_report, lock_dir / "next_readonly_check_plan.md", lock_dir / "next_readonly_check_plan.json")
        print(f"\nStage51 final read-only archive lock package written: {lock_dir / 'live_archive_lock.md'}")

    if args.enable_live_lock_consistency:
        from qmt_ai_trading.live_lock_consistency.service import build_default_live_lock_consistency_config, run_archive_consistency, run_human_closure_recheck, run_live_lock_consistency, run_next_readonly_check, save_archive_consistency_report, save_human_closure_recheck_report, save_live_lock_consistency_report, save_next_readonly_check_report
        lc_dir = Path(args.live_lock_consistency_output_dir)
        lc_config = build_default_live_lock_consistency_config(repo_root=ROOT, output_dir=str(lc_dir))
        lc_report = run_live_lock_consistency(lc_config)
        archive_consistency_report = run_archive_consistency(lc_report)
        human_recheck_report = run_human_closure_recheck(lc_report)
        readonly_plan_report = run_next_readonly_check(lc_report)
        save_live_lock_consistency_report(lc_report, lc_dir / "live_lock_consistency.md", lc_dir / "live_lock_consistency.json")
        save_archive_consistency_report(archive_consistency_report, lc_dir / "archive_consistency.md", lc_dir / "archive_consistency.json")
        save_human_closure_recheck_report(human_recheck_report, lc_dir / "human_closure_recheck.md", lc_dir / "human_closure_recheck.json")
        save_next_readonly_check_report(readonly_plan_report, lc_dir / "next_readonly_check_plan.md", lc_dir / "next_readonly_check_plan.json")
        print(f"\nStage52 final read-only lock consistency package written: {lc_dir / 'live_lock_consistency.md'}")

    if args.enable_live_archive_verification:
        from qmt_ai_trading.live_archive_verification.service import build_default_live_archive_verification_config, run_human_closure_recheck, run_live_archive_verification, run_locked_material_review, run_next_readonly_check, save_human_closure_recheck_report, save_live_archive_verification_report, save_locked_material_review_report, save_next_readonly_check_report
        av_dir = Path(args.live_archive_verification_output_dir)
        av_config = build_default_live_archive_verification_config(repo_root=ROOT, output_dir=str(av_dir))
        av_report = run_live_archive_verification(av_config)
        locked_report = run_locked_material_review(av_report)
        human_recheck_report = run_human_closure_recheck(av_report)
        readonly_plan_report = run_next_readonly_check(av_report)
        save_live_archive_verification_report(av_report, av_dir / "live_archive_verification.md", av_dir / "live_archive_verification.json")
        save_locked_material_review_report(locked_report, av_dir / "locked_material_review.md", av_dir / "locked_material_review.json")
        save_human_closure_recheck_report(human_recheck_report, av_dir / "human_closure_recheck.md", av_dir / "human_closure_recheck.json")
        save_next_readonly_check_report(readonly_plan_report, av_dir / "next_readonly_check_plan.md", av_dir / "next_readonly_check_plan.json")
        print(f"\nStage53 final read-only archive verification package written: {av_dir / 'live_archive_verification.md'}")


    if args.enable_live_gap_clearance:
        from qmt_ai_trading.live_gap_clearance.service import build_default_live_gap_clearance_config, run_evidence_remediation, run_human_closure_recheck, run_live_gap_clearance, run_next_readonly_check, save_evidence_remediation_report, save_human_closure_recheck_report, save_live_gap_clearance_report, save_next_readonly_check_report
        lg_dir = Path(args.live_gap_clearance_output_dir)
        lg_config = build_default_live_gap_clearance_config(repo_root=ROOT, output_dir=str(lg_dir))
        lg_report = run_live_gap_clearance(lg_config)
        remediation_report = run_evidence_remediation(lg_report)
        human_recheck_report = run_human_closure_recheck(lg_report)
        readonly_plan_report = run_next_readonly_check(lg_report)
        save_live_gap_clearance_report(lg_report, lg_dir / "live_gap_clearance.md", lg_dir / "live_gap_clearance.json")
        save_evidence_remediation_report(remediation_report, lg_dir / "evidence_remediation.md", lg_dir / "evidence_remediation.json")
        save_human_closure_recheck_report(human_recheck_report, lg_dir / "human_closure_recheck.md", lg_dir / "human_closure_recheck.json")
        save_next_readonly_check_report(readonly_plan_report, lg_dir / "next_readonly_check_plan.md", lg_dir / "next_readonly_check_plan.json")
        print(f"\nStage54 final pre-gray gap clearance package written: {lg_dir / 'live_gap_clearance.md'}")

    if args.enable_qmt_dryrun_calibration:
        from qmt_ai_trading.qmt_dryrun_calibration.service import build_default_qmt_dryrun_calibration_config, run_qmt_dryrun_calibration, run_xtdata_capability_check, run_etf_whitelist_calibration, run_next_real_cache_quality_plan, save_qmt_dryrun_calibration_report, save_xtdata_capability_report, save_etf_whitelist_calibration_report, save_next_real_cache_quality_plan_report
        qd = Path(args.qmt_dryrun_calibration_output_dir)
        qc = build_default_qmt_dryrun_calibration_config(repo_root=ROOT, output_dir=str(qd), provider=args.qmt_dryrun_calibration_provider)
        qr = run_qmt_dryrun_calibration(qc)
        save_qmt_dryrun_calibration_report(qr, qd / "qmt_dryrun_calibration.md", qd / "qmt_dryrun_calibration.json")
        save_xtdata_capability_report(run_xtdata_capability_check(qr), qd / "xtdata_capability.md", qd / "xtdata_capability.json")
        save_etf_whitelist_calibration_report(run_etf_whitelist_calibration(qr), qd / "etf_whitelist_calibration.md", qd / "etf_whitelist_calibration.json")
        save_next_real_cache_quality_plan_report(run_next_real_cache_quality_plan(qr), qd / "next_real_cache_quality_plan.md", qd / "next_real_cache_quality_plan.json")
        print(f"\nStage55 QMT dry-run calibration package written: {qd / 'qmt_dryrun_calibration.md'}")

    if args.enable_real_cache_quality:
        from qmt_ai_trading.real_cache_quality.service import build_default_real_cache_quality_config, run_real_cache_quality, run_long_sample_gap_fill_plan, run_field_quality_review, run_next_backtest_attribution_plan, save_real_cache_quality_report, save_long_sample_gap_fill_report, save_field_quality_review_report, save_next_backtest_attribution_plan_report
        rcq_dir = Path(args.real_cache_quality_output_dir)
        rcq_cfg = build_default_real_cache_quality_config(repo_root=ROOT, output_dir=str(rcq_dir), cache_root=args.cache_root, provider=args.real_cache_quality_provider, max_symbols=5, min_days=args.min_bars, target_days=90)
        rcq_report = run_real_cache_quality(rcq_cfg)
        save_real_cache_quality_report(rcq_report, rcq_dir / "real_cache_quality.md", rcq_dir / "real_cache_quality.json")
        save_long_sample_gap_fill_report(run_long_sample_gap_fill_plan(rcq_report), rcq_dir / "long_sample_gap_fill.md", rcq_dir / "long_sample_gap_fill.json")
        save_field_quality_review_report(run_field_quality_review(rcq_report), rcq_dir / "field_quality_review.md", rcq_dir / "field_quality_review.json")
        save_next_backtest_attribution_plan_report(run_next_backtest_attribution_plan(rcq_report), rcq_dir / "next_backtest_attribution_plan.md", rcq_dir / "next_backtest_attribution_plan.json")
        print(f"\nStage56 real cache quality package written: {rcq_dir / 'real_cache_quality.md'}")

    if args.enable_live_gray_candidate:
        from qmt_ai_trading.live_gray_candidate.service import build_default_live_gray_candidate_config, run_live_gray_candidate, run_gray_risk_limit_review, run_gray_approval_checklist, run_gray_rollback_circuit_breaker_plan, run_next_gray_approval_package_plan, save_live_gray_candidate_report, save_gray_risk_limit_report, save_gray_approval_checklist_report, save_gray_rollback_circuit_breaker_report, save_next_gray_approval_package_plan_report
        lgc_dir = Path(args.live_gray_candidate_output_dir)
        lgc_cfg = build_default_live_gray_candidate_config(repo_root=ROOT, output_dir=str(lgc_dir))
        lgc_report = run_live_gray_candidate(lgc_cfg)
        save_live_gray_candidate_report(lgc_report, lgc_dir / "live_gray_candidate.md", lgc_dir / "live_gray_candidate.json")
        save_gray_risk_limit_report(run_gray_risk_limit_review(lgc_report), lgc_dir / "gray_risk_limits.md", lgc_dir / "gray_risk_limits.json")
        save_gray_approval_checklist_report(run_gray_approval_checklist(lgc_report), lgc_dir / "gray_approval_checklist.md", lgc_dir / "gray_approval_checklist.json")
        save_gray_rollback_circuit_breaker_report(run_gray_rollback_circuit_breaker_plan(lgc_report), lgc_dir / "gray_rollback_circuit_breaker.md", lgc_dir / "gray_rollback_circuit_breaker.json")
        save_next_gray_approval_package_plan_report(run_next_gray_approval_package_plan(lgc_report), lgc_dir / "next_gray_approval_package_plan.md", lgc_dir / "next_gray_approval_package_plan.json")
        print(f"\nStage57 live gray candidate package written: {lgc_dir / 'live_gray_candidate.md'} read_only=True dry_run_only=True no_trade_authorization=True")

    if args.enable_live_gray_final_approval:
        from qmt_ai_trading.live_gray_final_approval.service import build_default_live_gray_final_approval_config, run_live_gray_final_approval, run_capital_position_approval, run_risk_human_approval_review, run_rollback_circuit_approval, run_final_signoff_checklist, run_next_readonly_seal_plan, save_live_gray_final_approval_report, save_capital_position_approval_report, save_risk_human_approval_review_report, save_rollback_circuit_approval_report, save_final_signoff_checklist_report, save_next_readonly_seal_plan_report
        lga_dir = Path(args.live_gray_final_approval_output_dir)
        lga_cfg = build_default_live_gray_final_approval_config(repo_root=ROOT, output_dir=str(lga_dir))
        lga_report = run_live_gray_final_approval(lga_cfg)
        save_live_gray_final_approval_report(lga_report, lga_dir / "live_gray_final_approval.md", lga_dir / "live_gray_final_approval.json")
        save_capital_position_approval_report(run_capital_position_approval(lga_report), lga_dir / "capital_position_approval.md", lga_dir / "capital_position_approval.json")
        save_risk_human_approval_review_report(run_risk_human_approval_review(lga_report), lga_dir / "risk_human_approval_review.md", lga_dir / "risk_human_approval_review.json")
        save_rollback_circuit_approval_report(run_rollback_circuit_approval(lga_report), lga_dir / "rollback_circuit_approval.md", lga_dir / "rollback_circuit_approval.json")
        save_final_signoff_checklist_report(run_final_signoff_checklist(lga_report), lga_dir / "final_signoff_checklist.md", lga_dir / "final_signoff_checklist.json")
        save_next_readonly_seal_plan_report(run_next_readonly_seal_plan(lga_report), lga_dir / "next_readonly_seal_plan.md", lga_dir / "next_readonly_seal_plan.json")
        print(f"\nStage58 live gray final approval package written: {lga_dir / 'live_gray_final_approval.md'} read_only=True dry_run_only=True no_trade_authorization=True")

    if args.enable_live_gray_readonly_seal:
        from qmt_ai_trading.live_gray_readonly_seal.service import build_default_live_gray_readonly_seal_config, run_live_gray_readonly_seal, run_material_lock_report, run_pre_run_checklist, run_readonly_seal_manifest, run_final_signoff_recheck, run_next_pre_gray_review_plan, save_live_gray_readonly_seal_report, save_material_lock_report, save_pre_run_checklist_report, save_readonly_seal_manifest_report, save_final_signoff_recheck_report, save_next_pre_gray_review_plan_report
        seal_dir = Path(args.live_gray_readonly_seal_output_dir)
        seal_cfg = build_default_live_gray_readonly_seal_config(repo_root=ROOT, output_dir=str(seal_dir))
        seal_report = run_live_gray_readonly_seal(seal_cfg)
        save_live_gray_readonly_seal_report(seal_report, seal_dir / "live_gray_readonly_seal.md", seal_dir / "live_gray_readonly_seal.json")
        save_material_lock_report(run_material_lock_report(seal_report), seal_dir / "material_lock.md", seal_dir / "material_lock.json")
        save_pre_run_checklist_report(run_pre_run_checklist(seal_report), seal_dir / "pre_run_checklist.md", seal_dir / "pre_run_checklist.json")
        save_readonly_seal_manifest_report(run_readonly_seal_manifest(seal_report), seal_dir / "readonly_seal_manifest.md", seal_dir / "readonly_seal_manifest.json")
        save_final_signoff_recheck_report(run_final_signoff_recheck(seal_report), seal_dir / "final_signoff_recheck.md", seal_dir / "final_signoff_recheck.json")
        save_next_pre_gray_review_plan_report(run_next_pre_gray_review_plan(seal_report), seal_dir / "next_pre_gray_review_plan.md", seal_dir / "next_pre_gray_review_plan.json")
        print(f"\nStage59 live gray readonly seal package written: {seal_dir / 'live_gray_readonly_seal.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")


    if args.enable_pre_gray_final_review:
        from qmt_ai_trading.pre_gray_final_review.service import build_default_pre_gray_final_review_config, run_pre_gray_final_review, run_material_recheck, run_go_no_go_draft, run_no_go_blocker_report, run_go_condition_report, run_stage61_api_gateway_plan, save_pre_gray_final_review_report, save_material_recheck_report, save_go_no_go_draft_report, save_no_go_blocker_report, save_go_condition_report, save_stage61_api_gateway_plan_report
        pg_dir = Path(args.pre_gray_final_review_output_dir)
        pg_cfg = build_default_pre_gray_final_review_config(repo_root=ROOT, output_dir=str(pg_dir))
        pg_report = run_pre_gray_final_review(pg_cfg)
        save_pre_gray_final_review_report(pg_report, pg_dir / "pre_gray_final_review.md", pg_dir / "pre_gray_final_review.json")
        save_material_recheck_report(run_material_recheck(pg_report), pg_dir / "material_recheck.md", pg_dir / "material_recheck.json")
        save_go_no_go_draft_report(run_go_no_go_draft(pg_report), pg_dir / "go_no_go_draft.md", pg_dir / "go_no_go_draft.json")
        save_no_go_blocker_report(run_no_go_blocker_report(pg_report), pg_dir / "no_go_blockers.md", pg_dir / "no_go_blockers.json")
        save_go_condition_report(run_go_condition_report(pg_report), pg_dir / "go_conditions.md", pg_dir / "go_conditions.json")
        save_stage61_api_gateway_plan_report(run_stage61_api_gateway_plan(pg_report), pg_dir / "stage61_api_gateway_plan.md", pg_dir / "stage61_api_gateway_plan.json")
        print(f"\nStage60 pre-gray final review package written: {pg_dir / 'pre_gray_final_review.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")

    if args.enable_api_gateway_review:
        from qmt_ai_trading.api_gateway.service import build_default_api_gateway_config, run_api_gateway_review, save_all
        ag_dir = Path(args.api_gateway_review_output_dir)
        ag_cfg = build_default_api_gateway_config(repo_root=ROOT, output_dir=str(ag_dir))
        ag_report = run_api_gateway_review(ag_cfg)
        save_all(ag_cfg, ag_report, ag_dir / "api_gateway_report.md", ag_dir / "api_gateway_report.json", ag_dir / "route_index.md", ag_dir / "route_index.json", ag_dir / "safety_boundary.md", ag_dir / "safety_boundary.json", ag_dir / "stage_status.md", ag_dir / "stage_status.json", ag_dir / "next_ui_dashboard_plan.md", ag_dir / "next_ui_dashboard_plan.json")
        print(f"\nStage61 API Gateway review package written: {ag_dir / 'api_gateway_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")

    if args.enable_local_console_review:
        from qmt_ai_trading.local_console.service import build_default_local_console_config, run_local_console_review, save_local_console_report, build_console_index_report, save_console_index_report, build_console_report_list_report, save_console_report_list_report, build_console_safety_report, save_console_safety_report, build_next_console_detail_plan_report, save_next_console_detail_plan_report
        lc_dir = Path(args.local_console_review_output_dir)
        lc_cfg = build_default_local_console_config(repo_root=ROOT, output_dir=str(lc_dir))
        lc_report = run_local_console_review(lc_cfg)
        save_local_console_report(lc_report, lc_dir / "local_console_report.md", lc_dir / "local_console_report.json")
        save_console_index_report(build_console_index_report(lc_cfg), lc_dir / "console_index.md", lc_dir / "console_index.json")
        save_console_report_list_report(build_console_report_list_report(lc_cfg), lc_dir / "report_list.md", lc_dir / "report_list.json")
        save_console_safety_report(build_console_safety_report(lc_cfg), lc_dir / "console_safety.md", lc_dir / "console_safety.json")
        save_next_console_detail_plan_report(build_next_console_detail_plan_report(lc_cfg), lc_dir / "next_console_detail_plan.md", lc_dir / "next_console_detail_plan.json")
        print(f"\nStage62 local console review package written: {lc_dir / 'local_console_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")

    if args.enable_local_console_detail_review:
        from qmt_ai_trading.local_console.detail_service import build_default_local_console_detail_config, run_local_console_detail_review, save_local_console_detail_report, build_console_filter_index_report, save_console_filter_index_report, build_console_warnings_report, save_console_warnings_report, build_console_blocking_reasons_report, save_console_blocking_reasons_report, build_console_manifest_detail_report, save_console_manifest_detail_report, build_console_validation_detail_report, save_console_validation_detail_report, build_next_console_overview_plan_report, save_next_console_overview_plan_report
        lcd_dir = Path(args.local_console_detail_review_output_dir)
        lcd_cfg = build_default_local_console_detail_config(repo_root=ROOT, output_dir=str(lcd_dir))
        lcd_report = run_local_console_detail_review(lcd_cfg)
        save_local_console_detail_report(lcd_report, lcd_dir / "local_console_detail_report.md", lcd_dir / "local_console_detail_report.json")
        save_console_filter_index_report(build_console_filter_index_report(lcd_report), lcd_dir / "filter_index.md", lcd_dir / "filter_index.json")
        save_console_warnings_report(build_console_warnings_report(lcd_report), lcd_dir / "warnings.md", lcd_dir / "warnings.json")
        save_console_blocking_reasons_report(build_console_blocking_reasons_report(lcd_report), lcd_dir / "blocking_reasons.md", lcd_dir / "blocking_reasons.json")
        save_console_manifest_detail_report(build_console_manifest_detail_report(lcd_report), lcd_dir / "manifest_detail.md", lcd_dir / "manifest_detail.json")
        save_console_validation_detail_report(build_console_validation_detail_report(lcd_report), lcd_dir / "validation_detail.md", lcd_dir / "validation_detail.json")
        save_next_console_overview_plan_report(build_next_console_overview_plan_report(lcd_cfg), lcd_dir / "next_console_overview_plan.md", lcd_dir / "next_console_overview_plan.json")
        print(f"\nStage63 local console detail review package written: {lcd_dir / 'local_console_detail_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")


    if args.enable_local_console_dashboard_review:
        from qmt_ai_trading.local_console.dashboard_service import build_default_local_console_dashboard_config, run_local_console_dashboard_review, save_local_console_dashboard_report, build_dashboard_card_index_report, save_dashboard_card_index_report, build_stage_status_cards_report, save_stage_status_cards_report, build_warning_blocking_stats_report, save_warning_blocking_stats_report, build_manifest_hash_status_report, save_manifest_hash_status_report, build_scheduler_preview_status_report, save_scheduler_preview_status_report, build_safety_boundary_status_report, save_safety_boundary_status_report, build_next_console_shell_plan_report, save_next_console_shell_plan_report
        lcdash_dir = Path(args.local_console_dashboard_review_output_dir)
        lcdash_cfg = build_default_local_console_dashboard_config(repo_root=ROOT, output_dir=str(lcdash_dir))
        lcdash_report = run_local_console_dashboard_review(lcdash_cfg)
        save_local_console_dashboard_report(lcdash_report, lcdash_dir / "local_console_dashboard_report.md", lcdash_dir / "local_console_dashboard_report.json")
        save_dashboard_card_index_report(build_dashboard_card_index_report(lcdash_report), lcdash_dir / "dashboard_card_index.md", lcdash_dir / "dashboard_card_index.json")
        save_stage_status_cards_report(build_stage_status_cards_report(lcdash_report), lcdash_dir / "stage_status_cards.md", lcdash_dir / "stage_status_cards.json")
        save_warning_blocking_stats_report(build_warning_blocking_stats_report(lcdash_report), lcdash_dir / "warning_blocking_stats.md", lcdash_dir / "warning_blocking_stats.json")
        save_manifest_hash_status_report(build_manifest_hash_status_report(lcdash_report), lcdash_dir / "manifest_hash_status.md", lcdash_dir / "manifest_hash_status.json")
        save_scheduler_preview_status_report(build_scheduler_preview_status_report(lcdash_report), lcdash_dir / "scheduler_preview_status.md", lcdash_dir / "scheduler_preview_status.json")
        save_safety_boundary_status_report(build_safety_boundary_status_report(lcdash_report), lcdash_dir / "safety_boundary_status.md", lcdash_dir / "safety_boundary_status.json")
        save_next_console_shell_plan_report(build_next_console_shell_plan_report(lcdash_cfg), lcdash_dir / "next_console_shell_plan.md", lcdash_dir / "next_console_shell_plan.json")
        print(f"\nStage64 local console dashboard review package written: {lcdash_dir / 'local_console_dashboard_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")

    if args.enable_local_console_shell_review:
        from qmt_ai_trading.local_console.shell_service import build_default_local_console_shell_config, run_local_console_shell_review, save_local_console_shell_report, save_shell_manifest_report, build_shell_route_map_report, save_shell_route_map_report, build_shell_asset_index_report, save_shell_asset_index_report, build_data_binding_placeholder_report, save_data_binding_placeholder_report, build_static_safety_report, save_static_safety_report, build_next_console_data_binding_plan_report, save_next_console_data_binding_plan_report
        shell_dir = Path(args.local_console_shell_review_output_dir)
        shell_cfg = build_default_local_console_shell_config(repo_root=ROOT, output_dir=str(shell_dir))
        shell_report = run_local_console_shell_review(shell_cfg)
        save_local_console_shell_report(shell_report, shell_dir / "local_console_shell_report.md", shell_dir / "local_console_shell_report.json")
        save_shell_manifest_report(shell_report, shell_dir / "shell_manifest.md", shell_dir / "shell_manifest.json")
        save_shell_route_map_report(build_shell_route_map_report(shell_report), shell_dir / "route_map.md", shell_dir / "route_map.json")
        save_shell_asset_index_report(build_shell_asset_index_report(shell_report), shell_dir / "asset_index.md", shell_dir / "asset_index.json")
        save_data_binding_placeholder_report(build_data_binding_placeholder_report(shell_report), shell_dir / "data_binding_placeholders.md", shell_dir / "data_binding_placeholders.json")
        save_static_safety_report(build_static_safety_report(shell_cfg), shell_dir / "static_safety_boundary.md", shell_dir / "static_safety_boundary.json")
        save_next_console_data_binding_plan_report(build_next_console_data_binding_plan_report(shell_cfg), shell_dir / "next_console_data_binding_plan.md", shell_dir / "next_console_data_binding_plan.json")
        print(f"\nStage65 local console shell review package written: {shell_dir / 'local_console_shell_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_local_console_binding_review:
        from qmt_ai_trading.local_console.binding_service import build_default_local_console_binding_config, run_local_console_binding_review, save_local_console_binding_report, build_data_bundle_report, save_data_bundle_report, build_binding_manifest_report, save_binding_manifest_report, build_data_source_map_report, save_data_source_map_report, build_missing_data_placeholder_report, save_missing_data_placeholder_report, build_bound_asset_index_report, save_bound_asset_index_report, build_static_data_safety_report, save_static_data_safety_report, build_next_console_preview_server_plan_report, save_next_console_preview_server_plan_report
        binding_dir = Path(args.local_console_binding_review_output_dir)
        binding_cfg = build_default_local_console_binding_config(repo_root=ROOT, output_dir=str(binding_dir))
        binding_report = run_local_console_binding_review(binding_cfg)
        save_local_console_binding_report(binding_report, binding_dir / "local_console_binding_report.md", binding_dir / "local_console_binding_report.json")
        save_data_bundle_report(build_data_bundle_report(binding_report), binding_dir / "data_bundle.md", binding_dir / "data_bundle.json")
        save_binding_manifest_report(build_binding_manifest_report(binding_report), binding_dir / "binding_manifest.md", binding_dir / "binding_manifest.json")
        save_data_source_map_report(build_data_source_map_report(binding_report), binding_dir / "data_source_map.md", binding_dir / "data_source_map.json")
        save_missing_data_placeholder_report(build_missing_data_placeholder_report(binding_report), binding_dir / "missing_data_placeholders.md", binding_dir / "missing_data_placeholders.json")
        save_bound_asset_index_report(build_bound_asset_index_report(binding_report), binding_dir / "bound_asset_index.md", binding_dir / "bound_asset_index.json")
        save_static_data_safety_report(build_static_data_safety_report(binding_cfg), binding_dir / "static_data_safety.md", binding_dir / "static_data_safety.json")
        save_next_console_preview_server_plan_report(build_next_console_preview_server_plan_report(binding_cfg), binding_dir / "next_console_preview_server_plan.md", binding_dir / "next_console_preview_server_plan.json")
        print(f"\nStage66 local console binding review package written: {binding_dir / 'local_console_binding_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True no_task_registered=True")

    if args.enable_local_console_preview_review:
        from qmt_ai_trading.local_console.preview_service import build_default_local_console_preview_config, run_local_console_preview_review, save_local_console_preview_report, build_preview_route_map_report, save_preview_route_map_report, build_static_file_index_report, save_static_file_index_report, build_response_manifest_report, save_response_manifest_report, build_preview_safety_report, save_preview_safety_report, build_next_console_refresh_plan_report, save_next_console_refresh_plan_report
        preview_dir = Path(args.local_console_preview_review_output_dir)
        preview_cfg = build_default_local_console_preview_config(repo_root=ROOT, static_dir="local_console_binding_stage66", host="127.0.0.1", port=8767, dry_run=True)
        preview_report = run_local_console_preview_review(preview_cfg)
        save_local_console_preview_report(preview_report, preview_dir / "local_console_preview_report.md", preview_dir / "local_console_preview_report.json")
        save_preview_route_map_report(build_preview_route_map_report(preview_report), preview_dir / "preview_route_map.md", preview_dir / "preview_route_map.json")
        save_static_file_index_report(build_static_file_index_report(preview_report), preview_dir / "static_file_index.md", preview_dir / "static_file_index.json")
        save_response_manifest_report(build_response_manifest_report(preview_report), preview_dir / "response_manifest.md", preview_dir / "response_manifest.json")
        save_preview_safety_report(build_preview_safety_report(preview_report), preview_dir / "preview_safety_boundary.md", preview_dir / "preview_safety_boundary.json")
        save_next_console_refresh_plan_report(build_next_console_refresh_plan_report(preview_cfg), preview_dir / "next_console_refresh_plan.md", preview_dir / "next_console_refresh_plan.json")
        print(f"\nStage67 local console preview review package written: {preview_dir / 'local_console_preview_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")


    if args.enable_local_console_refresh_review:
        from qmt_ai_trading.local_console.refresh_service import build_default_local_console_refresh_config, run_local_console_refresh_review, save_local_console_refresh_report, build_navigation_route_map_report, save_navigation_route_map_report, build_refresh_manifest_report, save_refresh_manifest_report, build_ui_state_placeholder_report, save_ui_state_placeholder_report, build_frontend_safety_report, save_frontend_safety_report, build_next_console_grouping_filter_plan_report, save_next_console_grouping_filter_plan_report
        refresh_dir = Path(args.local_console_refresh_review_output_dir)
        refresh_cfg = build_default_local_console_refresh_config(repo_root=ROOT, output_dir=str(refresh_dir), binding_dir="local_console_binding_stage66", preview_dir="local_console_preview_stage67")
        refresh_report = run_local_console_refresh_review(refresh_cfg)
        save_local_console_refresh_report(refresh_report, refresh_dir / "local_console_refresh_report.md", refresh_dir / "local_console_refresh_report.json")
        save_navigation_route_map_report(build_navigation_route_map_report(refresh_report), refresh_dir / "navigation_route_map.md", refresh_dir / "navigation_route_map.json")
        save_refresh_manifest_report(build_refresh_manifest_report(refresh_report), refresh_dir / "refresh_manifest.md", refresh_dir / "refresh_manifest.json")
        save_ui_state_placeholder_report(build_ui_state_placeholder_report(refresh_report), refresh_dir / "ui_state_placeholders.md", refresh_dir / "ui_state_placeholders.json")
        save_frontend_safety_report(build_frontend_safety_report(refresh_report), refresh_dir / "frontend_safety_report.md", refresh_dir / "frontend_safety_report.json")
        save_next_console_grouping_filter_plan_report(build_next_console_grouping_filter_plan_report(refresh_cfg), refresh_dir / "next_console_grouping_filter_plan.md", refresh_dir / "next_console_grouping_filter_plan.json")
        print(f"\nStage68 local console refresh review package written: {refresh_dir / 'local_console_refresh_report.md'} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")

    if args.notify_dry_run:
        from qmt_ai_trading.reporting.notifier import notify_report

        notification_results = notify_report(artifacts, dry_run=True)
        print("\nNotification dry-run results:")
        for item in notification_results:
            print(f"- {item.channel}: success={item.success} dry_run={item.dry_run} message={item.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
