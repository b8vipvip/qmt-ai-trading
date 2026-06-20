#!/usr/bin/env python
"""Preview or register the Windows Task Scheduler daily dry-run pipeline task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.scheduler.models import ScheduleConfig
from qmt_ai_trading.scheduler.windows_task import register_windows_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register QMT AI Trading daily dry-run pipeline task.")
    parser.add_argument("--task-name", default="QmtAiTradingDailyDryRun")
    parser.add_argument("--time", default="15:30", help="Daily run time in HH:MM, default 15:30.")
    parser.add_argument("--report-dir", default="reports")
    parser.add_argument("--execute", action="store_true", help="Actually call schtasks /Create. Omit for dry-run preview only.")
    parser.add_argument("--warmup-cache", action="store_true", help="Include historical cache warmup before the scheduled pipeline.")
    parser.add_argument("--warmup-universe", action="store_true", help="Include ETF universe historical cache warmup before the scheduled pipeline.")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--universe-lookback-days", type=int, default=None)
    parser.add_argument("--universe-lookback-years", type=int, default=None)
    parser.add_argument("--warmup-provider", default="mock", choices=["mock", "qmt"])
    parser.add_argument("--warmup-start", default=None)
    parser.add_argument("--warmup-end", default=None)
    parser.add_argument("--warmup-frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--use-cached-research", action="store_true")
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
    parser.add_argument("--build-dashboard", action="store_true")
    parser.add_argument("--dashboard-output", default="dashboard/daily_dashboard.html")
    parser.add_argument("--dashboard-title", default="QMT AI Trading Dashboard")
    parser.add_argument("--enable-data-quality-tracking", action="store_true")
    parser.add_argument("--data-quality-tracking-output-dir", default="data_quality_tracking")
    parser.add_argument("--data-quality-tracking-report-dir", default="qmt_data_quality_reports")
    parser.add_argument("--data-quality-tracking-cache-root", default=None)
    parser.add_argument("--data-quality-tracking-symbols", default="")
    parser.add_argument("--data-quality-tracking-start", default=None)
    parser.add_argument("--data-quality-tracking-end", default=None)
    parser.add_argument("--enable-notification-dry-run", action="store_true")
    parser.add_argument("--notification-dry-run-output-dir", default="notification_dryrun")
    parser.add_argument("--notification-dry-run-channels", default="")
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
    parser.add_argument("--enable-live-manual-prep", action="store_true")
    parser.add_argument("--live-manual-prep-output-dir", default="live_manual_prep")
    parser.add_argument("--live-manual-prep-allowed-symbols", default="")
    parser.add_argument("--live-manual-prep-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--live-manual-prep-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--live-manual-prep-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--live-manual-prep-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--enable-live-env-check", action="store_true")
    parser.add_argument("--live-env-check-output-dir", default="live_env_check")
    parser.add_argument("--live-env-check-allowed-symbols", default="")
    parser.add_argument("--live-env-check-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--live-env-check-max-single-order-value", type=float, default=1000.0)
    parser.add_argument("--live-env-check-max-symbol-weight", type=float, default=0.1)
    parser.add_argument("--live-env-check-max-portfolio-weight", type=float, default=0.2)
    parser.add_argument("--enable-final-authorization-package", action="store_true")
    parser.add_argument("--final-authorization-output-dir", default="final_authorization")
    parser.add_argument("--final-authorization-allowed-symbols", default="")
    parser.add_argument("--final-authorization-max-total-capital", type=float, default=5000.0)
    parser.add_argument("--final-authorization-max-single-order-value", type=float, default=1000.0)
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
    args = parser.parse_args(argv)

    config = ScheduleConfig(
        task_name=args.task_name,
        project_root=ROOT,
        python_command="py",
        script_path=Path("scripts/run_scheduled_daily_pipeline.py"),
        run_time=args.time,
        report_dir=Path(args.report_dir),
        dry_run=not args.execute,
        warmup_cache=args.warmup_cache,
        warmup_universe=args.warmup_universe,
        universe_name=args.universe_name,
        universe_lookback_days=args.universe_lookback_days,
        universe_lookback_years=args.universe_lookback_years,
        warmup_provider=args.warmup_provider,
        warmup_start=args.warmup_start,
        warmup_end=args.warmup_end,
        warmup_frequency=args.warmup_frequency,
        cache_root=Path(args.cache_root),
        use_cached_research=args.use_cached_research,
        research_start=args.research_start,
        research_end=args.research_end,
        research_frequency=args.research_frequency,
        min_bars=args.min_bars,
        cached_strategy_top_n=args.cached_strategy_top_n,
        cached_strategy_min_score=args.cached_strategy_min_score,
        cached_strategy_min_bars=args.cached_strategy_min_bars,
        data_source_mode=args.data_source_mode,
        allow_mock_fallback=args.allow_mock_fallback,
        quality_report_dir=args.quality_report_dir,
        require_quality_report=args.require_quality_report,
        allow_unknown_quality_for_dry_run=args.allow_unknown_quality_for_dry_run,
        allow_mock_cache=args.allow_mock_cache,
        min_quality_level=args.min_quality_level,
        min_coverage_ratio=args.min_coverage_ratio,
        min_loaded_symbols=args.min_loaded_symbols,
        require_cached_research=args.require_cached_research,
        data_source_confidence_required=args.data_source_confidence_required,
        create_approval=args.create_approval,
        approval_root=Path(args.approval_root),
        approval_expires_hours=args.approval_expires_hours,
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
        enable_monitoring=args.enable_monitoring,
        monitoring_output_dir=Path(args.monitoring_output_dir),
        monitoring_dry_run_alerts=args.monitoring_dry_run_alerts,
        enable_agent_research=args.enable_agent_research,
        agent_research_output_dir=Path(args.agent_research_output_dir),
        agent_research_mode=args.agent_research_mode,
        agent_include_monitoring=args.agent_include_monitoring,
        agent_include_backtest=args.agent_include_backtest,
        agent_include_human_checklist=args.agent_include_human_checklist,
        enable_live_gray_readiness=args.enable_live_gray_readiness,
        live_gray_output_dir=Path(args.live_gray_output_dir),
        live_gray_allowed_symbols=args.live_gray_allowed_symbols,
        live_gray_max_total_capital=args.live_gray_max_total_capital,
        live_gray_max_single_order_value=args.live_gray_max_single_order_value,
        live_gray_max_symbol_weight=args.live_gray_max_symbol_weight,
        live_gray_max_portfolio_weight=args.live_gray_max_portfolio_weight,
        live_gray_enabled=args.live_gray_enabled,
        build_dashboard=args.build_dashboard,
        dashboard_output=Path(args.dashboard_output),
        dashboard_title=args.dashboard_title,
        enable_data_quality_tracking=args.enable_data_quality_tracking,
        data_quality_tracking_output_dir=Path(args.data_quality_tracking_output_dir),
        data_quality_tracking_report_dir=Path(args.data_quality_tracking_report_dir),
        data_quality_tracking_cache_root=args.data_quality_tracking_cache_root,
        data_quality_tracking_symbols=args.data_quality_tracking_symbols,
        data_quality_tracking_start=args.data_quality_tracking_start,
        data_quality_tracking_end=args.data_quality_tracking_end,
        enable_notification_dry_run=args.enable_notification_dry_run,
        notification_dry_run_output_dir=Path(args.notification_dry_run_output_dir),
        notification_dry_run_channels=args.notification_dry_run_channels,
        enable_gray_rehearsal=args.enable_gray_rehearsal,
        gray_rehearsal_output_dir=Path(args.gray_rehearsal_output_dir),
        gray_rehearsal_allowed_symbols=args.gray_rehearsal_allowed_symbols,
        gray_rehearsal_max_total_capital=args.gray_rehearsal_max_total_capital,
        gray_rehearsal_max_single_order_value=args.gray_rehearsal_max_single_order_value,
        enable_gray_decision_package=args.enable_gray_decision_package,
        gray_decision_output_dir=Path(args.gray_decision_output_dir),
        gray_decision_allowed_symbols=args.gray_decision_allowed_symbols,
        gray_decision_max_total_capital=args.gray_decision_max_total_capital,
        gray_decision_max_single_order_value=args.gray_decision_max_single_order_value,
        gray_decision_max_symbol_weight=args.gray_decision_max_symbol_weight,
        gray_decision_max_portfolio_weight=args.gray_decision_max_portfolio_weight,
        enable_live_manual_prep=args.enable_live_manual_prep,
        live_manual_prep_output_dir=Path(args.live_manual_prep_output_dir),
        live_manual_prep_allowed_symbols=args.live_manual_prep_allowed_symbols,
        live_manual_prep_max_total_capital=args.live_manual_prep_max_total_capital,
        live_manual_prep_max_single_order_value=args.live_manual_prep_max_single_order_value,
        live_manual_prep_max_symbol_weight=args.live_manual_prep_max_symbol_weight,
        live_manual_prep_max_portfolio_weight=args.live_manual_prep_max_portfolio_weight,
        enable_live_env_check=args.enable_live_env_check,
        live_env_check_output_dir=Path(args.live_env_check_output_dir),
        live_env_check_allowed_symbols=args.live_env_check_allowed_symbols,
        live_env_check_max_total_capital=args.live_env_check_max_total_capital,
        live_env_check_max_single_order_value=args.live_env_check_max_single_order_value,
        live_env_check_max_symbol_weight=args.live_env_check_max_symbol_weight,
        live_env_check_max_portfolio_weight=args.live_env_check_max_portfolio_weight,
        enable_final_authorization_package=args.enable_final_authorization_package,
        final_authorization_output_dir=Path(args.final_authorization_output_dir),
        final_authorization_allowed_symbols=args.final_authorization_allowed_symbols,
        final_authorization_max_total_capital=args.final_authorization_max_total_capital,
        final_authorization_max_single_order_value=args.final_authorization_max_single_order_value,
        enable_redline_review=args.enable_redline_review,
        redline_review_output_dir=Path(args.redline_review_output_dir),
        redline_review_operator_name=args.redline_review_operator_name,
        redline_review_reviewer_name=args.redline_review_reviewer_name,
        enable_live_gray_ledger=args.enable_live_gray_ledger,
        live_gray_ledger_output_dir=Path(args.live_gray_ledger_output_dir),
        enable_live_gray_review=args.enable_live_gray_review,
        live_gray_review_output_dir=Path(args.live_gray_review_output_dir),
        enable_live_signature_freeze=args.enable_live_signature_freeze,
        live_signature_freeze_output_dir=Path(args.live_signature_freeze_output_dir),
        enable_live_env_snapshot=args.enable_live_env_snapshot,
        live_env_snapshot_output_dir=Path(args.live_env_snapshot_output_dir),
        enable_live_runbook=args.enable_live_runbook,
        live_runbook_output_dir=Path(args.live_runbook_output_dir),
        enable_live_signoff=args.enable_live_signoff,
        live_signoff_output_dir=Path(args.live_signoff_output_dir),
        enable_live_final_review=args.enable_live_final_review,
        live_final_review_output_dir=Path(args.live_final_review_output_dir),
        enable_live_archive=args.enable_live_archive,
        live_archive_output_dir=Path(args.live_archive_output_dir),
        enable_live_consistency=args.enable_live_consistency,
        live_consistency_output_dir=Path(args.live_consistency_output_dir),
        enable_live_final_archive=args.enable_live_final_archive,
        live_final_archive_output_dir=Path(args.live_final_archive_output_dir),
        enable_live_archive_lock=args.enable_live_archive_lock,
        live_archive_lock_output_dir=Path(args.live_archive_lock_output_dir),
        enable_live_lock_consistency=args.enable_live_lock_consistency,
        live_lock_consistency_output_dir=Path(args.live_lock_consistency_output_dir),
        enable_live_archive_verification=args.enable_live_archive_verification,
        live_archive_verification_output_dir=Path(args.live_archive_verification_output_dir),
        enable_live_gap_clearance=args.enable_live_gap_clearance,
        live_gap_clearance_output_dir=Path(args.live_gap_clearance_output_dir),
        enable_qmt_dryrun_calibration=args.enable_qmt_dryrun_calibration,
        qmt_dryrun_calibration_output_dir=Path(args.qmt_dryrun_calibration_output_dir),
        qmt_dryrun_calibration_provider=args.qmt_dryrun_calibration_provider,
        enable_real_cache_quality=args.enable_real_cache_quality,
        real_cache_quality_output_dir=Path(args.real_cache_quality_output_dir),
        real_cache_quality_provider=args.real_cache_quality_provider,
        enable_live_gray_candidate=args.enable_live_gray_candidate,
        live_gray_candidate_output_dir=Path(args.live_gray_candidate_output_dir),
        enable_live_gray_final_approval=args.enable_live_gray_final_approval,
        live_gray_final_approval_output_dir=Path(args.live_gray_final_approval_output_dir),
        enable_live_gray_readonly_seal=args.enable_live_gray_readonly_seal,
        live_gray_readonly_seal_output_dir=Path(args.live_gray_readonly_seal_output_dir),
    )
    result = register_windows_task(config, dry_run=not args.execute)
    print("Windows Task Scheduler registration preview")
    print(f"Task name: {args.task_name}")
    print(f"Run time: {args.time}")
    print(f"Command: {result.command.metadata.get('display', '')}")
    if args.warmup_universe:
        print(f"Universe warmup: universe={args.universe_name} provider={args.warmup_provider} lookback_days={args.universe_lookback_days} lookback_years={args.universe_lookback_years} frequency={args.warmup_frequency} cache_root={args.cache_root}")
    elif args.warmup_cache:
        print(f"Warmup: provider={args.warmup_provider} start={args.warmup_start} end={args.warmup_end} frequency={args.warmup_frequency} cache_root={args.cache_root}")
    if args.data_source_mode != "legacy":
        print(f"Data source: mode={args.data_source_mode} allow_mock_fallback={args.allow_mock_fallback} min_coverage_ratio={args.min_coverage_ratio} min_loaded_symbols={args.min_loaded_symbols} quality_report_dir={args.quality_report_dir} min_quality_level={args.min_quality_level}")
    if args.create_approval:
        print(f"Human approval: create_approval=True approval_root={args.approval_root} expires_hours={args.approval_expires_hours} no_order_submitted=True")
    if args.enable_portfolio_plan:
        print(f"Portfolio plan: enable_portfolio_plan=True method={args.portfolio_method} top_n={args.portfolio_top_n} dry_run_only=True")
    if args.enable_monitoring:
        print(f"Monitoring: enable_monitoring=True output_dir={args.monitoring_output_dir} dry_run_alerts={args.monitoring_dry_run_alerts}")
    if args.enable_agent_research:
        print(f"Agent Research: enable_agent_research=True output_dir={args.agent_research_output_dir} mode={args.agent_research_mode} read_only=True")
    if args.enable_live_gray_readiness:
        print(f"Live Gray Readiness: enable_live_gray_readiness=True output_dir={args.live_gray_output_dir} allowed_symbols={args.live_gray_allowed_symbols} live_enabled_included=False preparation_only=True")
    if args.enable_data_quality_tracking:
        print(f"Data Quality Tracking: enable_data_quality_tracking=True output_dir={args.data_quality_tracking_output_dir} report_dir={args.data_quality_tracking_report_dir} read_only=True")
    if args.enable_gray_rehearsal:
        print(f"Gray Rehearsal: enable_gray_rehearsal=True output_dir={args.gray_rehearsal_output_dir} allowed_symbols={args.gray_rehearsal_allowed_symbols} dry_run_only=True")
    if args.enable_gray_decision_package:
        print(f"Gray Decision Package: enable_gray_decision_package=True output_dir={args.gray_decision_output_dir} allowed_symbols={args.gray_decision_allowed_symbols} manual_only=True")
    if args.enable_live_manual_prep:
        print(f"Live Manual Approval Prep: enable_live_manual_prep=True output_dir={args.live_manual_prep_output_dir} allowed_symbols={args.live_manual_prep_allowed_symbols} preparation_only=True")
    if args.enable_live_env_check:
        print(f"Live Environment Check: enable_live_env_check=True output_dir={args.live_env_check_output_dir} allowed_symbols={args.live_env_check_allowed_symbols} read_only=True")
    if args.enable_final_authorization_package:
        print(f"Final Authorization Package: enable_final_authorization_package=True output_dir={args.final_authorization_output_dir} allowed_symbols={args.final_authorization_allowed_symbols} review_only=True")
    if args.enable_redline_review:
        print(f"Red-line Review: enable_redline_review=True output_dir={args.redline_review_output_dir} review_only=True dry_run_only=True")
    if args.enable_live_gray_ledger:
        print(f"Stage41 Live Gray Ledger: enable_live_gray_ledger=True output_dir={args.live_gray_ledger_output_dir} read_only=True dry_run_only=True no_task_registered=True")
    if args.enable_live_gray_review:
        print(f"Stage42 Live Gray Review: enable_live_gray_review=True output_dir={args.live_gray_review_output_dir} read_only=True dry_run_only=True no_task_registered=True")
    if args.enable_live_signature_freeze:
        print(f"Stage43 Live Signature Freeze: enable_live_signature_freeze=True output_dir={args.live_signature_freeze_output_dir} read_only=True dry_run_only=True no_task_registered=True")
    if args.enable_live_env_snapshot:
        print(f"Stage44 Live Env Snapshot: enable_live_env_snapshot=True output_dir={args.live_env_snapshot_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_runbook:
        print(f"Stage45 Live Runbook: enable_live_runbook=True output_dir={args.live_runbook_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_signoff:
        print(f"Stage46 Live Signoff: enable_live_signoff=True output_dir={args.live_signoff_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_final_review:
        print(f"Stage47 Live Final Review: enable_live_final_review=True output_dir={args.live_final_review_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_archive:
        print(f"Stage48 Live Archive: enable_live_archive=True output_dir={args.live_archive_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_consistency:
        print(f"Stage49 Live Consistency: enable_live_consistency=True output_dir={args.live_consistency_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_final_archive:
        print(f"Stage50 Live Final Archive: enable_live_final_archive=True output_dir={args.live_final_archive_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_archive_lock:
        print(f"Stage51 Live Archive Lock: enable_live_archive_lock=True output_dir={args.live_archive_lock_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_lock_consistency:
        print(f"Stage52 Live Lock Consistency: enable_live_lock_consistency=True output_dir={args.live_lock_consistency_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_archive_verification:
        print(f"Stage53 Live Archive Verification: enable_live_archive_verification=True output_dir={args.live_archive_verification_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_gap_clearance:
        print(f"Stage54 Live Gap Clearance: enable_live_gap_clearance=True output_dir={args.live_gap_clearance_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_qmt_dryrun_calibration:
        print(f"Stage55 QMT Dry-run Calibration: enable_qmt_dryrun_calibration=True output_dir={args.qmt_dryrun_calibration_output_dir} provider={args.qmt_dryrun_calibration_provider} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_real_cache_quality:
        print(f"Stage56 Real Cache Quality: enable_real_cache_quality=True output_dir={args.real_cache_quality_output_dir} provider={args.real_cache_quality_provider} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_gray_candidate:
        print(f"Stage57 Live Gray Candidate: enable_live_gray_candidate=True output_dir={args.live_gray_candidate_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_gray_final_approval:
        print(f"Stage58 Live Gray Final Approval: enable_live_gray_final_approval=True output_dir={args.live_gray_final_approval_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.enable_live_gray_readonly_seal:
        print(f"Stage59 Live Gray Readonly Seal: enable_live_gray_readonly_seal=True output_dir={args.live_gray_readonly_seal_output_dir} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True")
    if args.build_dashboard:
        print(f"Dashboard: build_dashboard=True output={args.dashboard_output} title={args.dashboard_title} read_only=True no_order_submitted=True")
    if args.use_cached_research or args.data_source_mode in {"cached", "auto", "cached_real_first"}:
        print(f"Cached research: start={args.research_start} end={args.research_end} frequency={args.research_frequency} min_bars={args.min_bars} cache_root={args.cache_root}")
        print(f"Cached ETF rotation: top_n={args.cached_strategy_top_n} min_score={args.cached_strategy_min_score} min_bars={args.cached_strategy_min_bars}")
    print(f"Result: {result.message}")
    if result.dry_run:
        print("DRY-RUN ONLY: no task registered. A separate future stage is required before real registration.")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
