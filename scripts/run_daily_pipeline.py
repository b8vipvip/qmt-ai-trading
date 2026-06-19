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

    if args.notify_dry_run:
        from qmt_ai_trading.reporting.notifier import notify_report

        notification_results = notify_report(artifacts, dry_run=True)
        print("\nNotification dry-run results:")
        for item in notification_results:
            print(f"- {item.channel}: success={item.success} dry_run={item.dry_run} message={item.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
