"""Windows Task Scheduler helpers for the dry-run daily pipeline.

The defaults are intentionally safe: functions return command previews and do not
call ``schtasks`` unless ``dry_run=False`` is explicitly requested.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import ScheduleCommand, ScheduleConfig, ScheduleResult

DEFAULT_TASK_NAME = "QmtAiTradingDailyDryRun"
DEFAULT_RUN_TIME = "15:30"


def _quote_for_display(value: str | Path) -> str:
    text = str(value)
    escaped = text.replace('"', '\\"')
    return f'"{escaped}"' if any(ch.isspace() for ch in escaped) else escaped


def _project_root(project_root: str | Path | None = None) -> Path:
    return Path(project_root).resolve() if project_root else Path.cwd().resolve()


def build_daily_pipeline_command(
    *,
    project_root: str | Path | None = None,
    python_command: str = "py",
    script_path: str | Path = Path("scripts/run_daily_pipeline.py"),
    report_dir: str | Path = Path("reports"),
    write_reports: bool = True,
    notify_dry_run: bool = True,
    warmup_cache: bool = False,
    warmup_universe: bool = False,
    universe_name: str = "default_etf",
    universe_lookback_days: int | None = None,
    universe_lookback_years: int | None = None,
    warmup_provider: str = "mock",
    warmup_start: str | None = None,
    warmup_end: str | None = None,
    warmup_frequency: str = "1d",
    cache_root: str | Path = Path("market_data"),
    use_cached_research: bool = False,
    research_start: str | None = None,
    research_end: str | None = None,
    research_frequency: str = "1d",
    min_bars: int = 20,
    cached_strategy_top_n: int = 1,
    cached_strategy_min_score: float | None = None,
    cached_strategy_min_bars: int = 20,
    data_source_mode: str = "cached_real_first",
    allow_mock_fallback: bool = False,
    quality_report_dir: str | Path = Path("qmt_data_quality_reports"),
    require_quality_report: bool = False,
    allow_unknown_quality_for_dry_run: bool = True,
    allow_mock_cache: bool = False,
    min_quality_level: str = "UNKNOWN",
    min_coverage_ratio: float = 0.8,
    min_loaded_symbols: int = 1,
    require_cached_research: bool = False,
    data_source_confidence_required: str | None = None,
    create_approval: bool = False,
    approval_root: str | Path = Path("approvals"),
    approval_expires_hours: float = 24.0,
    enable_portfolio_plan: bool = False,
    portfolio_method: str = "score_weight",
    portfolio_top_n: int = 2,
    portfolio_cash_reserve_ratio: float = 0.2,
    portfolio_max_symbol_weight: float = 0.3,
    portfolio_max_weight: float = 0.8,
    portfolio_rebalance_threshold: float = 0.05,
    portfolio_total_asset: float = 1000000.0,
    portfolio_current_cash: float = 1000000.0,
    portfolio_snapshot_path: str | None = None,
    enable_monitoring: bool = False,
    monitoring_output_dir: str | Path = Path("monitoring_reports"),
    monitoring_dry_run_alerts: bool = False,
    enable_agent_research: bool = False,
    agent_research_output_dir: str | Path = Path("agent_reports"),
    agent_research_mode: str = "local_rules",
    agent_include_monitoring: bool = True,
    agent_include_backtest: bool = True,
    agent_include_human_checklist: bool = True,
    enable_live_gray_readiness: bool = False,
    live_gray_output_dir: str | Path = Path("live_gray_reports"),
    live_gray_allowed_symbols: str = "",
    live_gray_max_total_capital: float = 5000.0,
    live_gray_max_single_order_value: float = 1000.0,
    live_gray_max_symbol_weight: float = 0.1,
    live_gray_max_portfolio_weight: float = 0.2,
    live_gray_enabled: bool = False,
    build_dashboard: bool = False,
    dashboard_output: str | Path = Path("dashboard/daily_dashboard.html"),
    dashboard_title: str = "QMT AI Trading Dashboard",
    enable_data_quality_tracking: bool = False,
    data_quality_tracking_output_dir: str | Path = Path("data_quality_tracking"),
    data_quality_tracking_report_dir: str | Path = Path("qmt_data_quality_reports"),
    data_quality_tracking_cache_root: str | None = None,
    data_quality_tracking_symbols: str = "",
    data_quality_tracking_start: str | None = None,
    data_quality_tracking_end: str | None = None,
    enable_notification_dry_run: bool = False,
    notification_dry_run_output_dir: str | Path = Path("notification_dryrun"),
    notification_dry_run_channels: str = "",
    enable_gray_rehearsal: bool = False,
    gray_rehearsal_output_dir: str | Path = Path("gray_rehearsal"),
    gray_rehearsal_allowed_symbols: str = "",
    gray_rehearsal_max_total_capital: float = 5000.0,
    gray_rehearsal_max_single_order_value: float = 1000.0,
    enable_gray_decision_package: bool = False,
    gray_decision_output_dir: str | Path = Path("gray_decision"),
    gray_decision_allowed_symbols: str = "",
    gray_decision_max_total_capital: float = 5000.0,
    gray_decision_max_single_order_value: float = 1000.0,
    gray_decision_max_symbol_weight: float = 0.1,
    gray_decision_max_portfolio_weight: float = 0.2,
    enable_live_manual_prep: bool = False,
    live_manual_prep_output_dir: str | Path = Path("live_manual_prep"),
    live_manual_prep_allowed_symbols: str = "",
    live_manual_prep_max_total_capital: float = 5000.0,
    live_manual_prep_max_single_order_value: float = 1000.0,
    live_manual_prep_max_symbol_weight: float = 0.1,
    live_manual_prep_max_portfolio_weight: float = 0.2,
    enable_live_env_check: bool = False,
    live_env_check_output_dir: str | Path = Path("live_env_check"),
    live_env_check_allowed_symbols: str = "",
    live_env_check_max_total_capital: float = 5000.0,
    live_env_check_max_single_order_value: float = 1000.0,
    live_env_check_max_symbol_weight: float = 0.1,
    live_env_check_max_portfolio_weight: float = 0.2,
    enable_final_authorization_package: bool = False,
    final_authorization_output_dir: str | Path = Path("final_authorization"),
    final_authorization_allowed_symbols: str = "",
    final_authorization_max_total_capital: float = 5000.0,
    final_authorization_max_single_order_value: float = 1000.0,
    final_authorization_max_symbol_weight: float = 0.1,
    final_authorization_max_portfolio_weight: float = 0.2,
    enable_redline_review: bool = False,
    redline_review_output_dir: Path | str = Path("redline_review"),
    redline_review_operator_name: str = "",
    redline_review_reviewer_name: str = "",
    enable_live_gray_ledger: bool = False,
    live_gray_ledger_output_dir: Path | str = Path("live_gray_ledger"),
    enable_live_gray_review: bool = False,
    live_gray_review_output_dir: Path | str = Path("live_gray_review"),
    enable_live_signature_freeze: bool = False,
    live_signature_freeze_output_dir: Path | str = Path("live_signature_freeze"),
    enable_live_env_snapshot: bool = False,
    live_env_snapshot_output_dir: Path | str = Path("live_env_snapshot"),
    enable_live_runbook: bool = False,
    live_runbook_output_dir: Path | str = Path("live_runbook"),
    enable_live_signoff: bool = False,
    live_signoff_output_dir: Path | str = Path("live_signoff"),
    enable_live_final_review: bool = False,
    live_final_review_output_dir: Path | str = Path("live_final_review"),
    enable_live_archive: bool = False,
    live_archive_output_dir: Path | str = Path("live_archive"),
    enable_live_consistency: bool = False,
    live_consistency_output_dir: Path | str = Path("live_consistency"),
    enable_live_final_archive: bool = False,
    live_final_archive_output_dir: Path | str = Path("live_final_archive"),
    enable_live_archive_lock: bool = False,
    live_archive_lock_output_dir: Path | str = Path("live_archive_lock"),
    enable_live_lock_consistency: bool = False,
    live_lock_consistency_output_dir: Path | str = Path("live_lock_consistency"),
    enable_live_archive_verification: bool = False,
    live_archive_verification_output_dir: Path | str = Path("live_archive_verification"),
    enable_live_gap_clearance: bool = False,
    live_gap_clearance_output_dir: Path | str = Path("live_gap_clearance"),
    enable_qmt_dryrun_calibration: bool = False,
    qmt_dryrun_calibration_output_dir: Path | str = Path("qmt_dryrun_calibration"),
    qmt_dryrun_calibration_provider: str = "mock",
    enable_real_cache_quality: bool = False,
    real_cache_quality_output_dir: Path | str = Path("real_cache_quality"),
    real_cache_quality_provider: str = "mock",
    enable_live_gray_candidate: bool = False,
    live_gray_candidate_output_dir: Path | str = Path("live_gray_candidate"),
    enable_live_gray_final_approval: bool = False,
    live_gray_final_approval_output_dir: Path | str = Path("live_gray_final_approval"),
    enable_live_gray_readonly_seal: bool = False,
    live_gray_readonly_seal_output_dir: Path | str = Path("live_gray_readonly_seal"),
    enable_pre_gray_final_review: bool = False,
    pre_gray_final_review_output_dir: Path | str = Path("pre_gray_final_review"),
) -> ScheduleCommand:
    """Build the safe daily pipeline command used by the scheduled task."""

    args = [str(script_path)]
    if warmup_universe:
        args.append("--warmup-universe")
        args.extend(["--universe-name", str(universe_name)])
        if universe_lookback_days is not None:
            args.extend(["--universe-lookback-days", str(universe_lookback_days)])
        if universe_lookback_years is not None:
            args.extend(["--universe-lookback-years", str(universe_lookback_years)])
        args.extend(["--warmup-provider", str(warmup_provider)])
        if warmup_start:
            args.extend(["--warmup-start", str(warmup_start)])
        if warmup_end:
            args.extend(["--warmup-end", str(warmup_end)])
        args.extend(["--warmup-frequency", str(warmup_frequency)])
        args.extend(["--cache-root", str(cache_root)])
    elif warmup_cache:
        args.append("--warmup-cache")
        args.extend(["--warmup-provider", str(warmup_provider)])
        if warmup_start:
            args.extend(["--warmup-start", str(warmup_start)])
        if warmup_end:
            args.extend(["--warmup-end", str(warmup_end)])
        args.extend(["--warmup-frequency", str(warmup_frequency)])
        args.extend(["--cache-root", str(cache_root)])
    if data_source_mode != "legacy":
        args.extend(["--data-source-mode", str(data_source_mode)])
    if allow_mock_fallback:
        args.append("--allow-mock-fallback")
    if data_source_mode != "legacy" or str(quality_report_dir) != "qmt_data_quality_reports":
        args.extend(["--quality-report-dir", str(quality_report_dir)])
    if require_quality_report:
        args.append("--require-quality-report")
    if allow_unknown_quality_for_dry_run and data_source_mode != "legacy":
        args.append("--allow-unknown-quality-for-dry-run")
    if allow_mock_cache:
        args.append("--allow-mock-cache")
    if data_source_mode != "legacy" or str(min_quality_level) != "UNKNOWN":
        args.extend(["--min-quality-level", str(min_quality_level)])
    if data_source_mode != "legacy" or min_coverage_ratio != 0.8:
        args.extend(["--min-coverage-ratio", str(min_coverage_ratio)])
    if data_source_mode != "legacy" or min_loaded_symbols != 1:
        args.extend(["--min-loaded-symbols", str(min_loaded_symbols)])
    if require_cached_research:
        args.append("--require-cached-research")
    if data_source_confidence_required:
        args.extend(["--data-source-confidence-required", str(data_source_confidence_required)])
    if create_approval:
        args.append("--create-approval")
    if create_approval or str(approval_root) != "approvals":
        args.extend(["--approval-root", str(approval_root)])
    if create_approval or float(approval_expires_hours) != 24.0:
        args.extend(["--approval-expires-hours", str(approval_expires_hours)])
    if enable_portfolio_plan:
        args.append("--enable-portfolio-plan")
    if enable_portfolio_plan or portfolio_method != "score_weight":
        args.extend(["--portfolio-method", str(portfolio_method)])
    if enable_portfolio_plan or int(portfolio_top_n) != 2:
        args.extend(["--portfolio-top-n", str(portfolio_top_n)])
    if enable_portfolio_plan:
        args.extend(["--portfolio-cash-reserve-ratio", str(portfolio_cash_reserve_ratio), "--portfolio-max-symbol-weight", str(portfolio_max_symbol_weight)])
        args.extend(["--portfolio-max-weight", str(portfolio_max_weight), "--portfolio-rebalance-threshold", str(portfolio_rebalance_threshold)])
        args.extend(["--portfolio-total-asset", str(portfolio_total_asset), "--portfolio-current-cash", str(portfolio_current_cash)])
        if portfolio_snapshot_path:
            args.extend(["--portfolio-snapshot-path", str(portfolio_snapshot_path)])
    if enable_monitoring:
        args.append("--enable-monitoring")
        args.extend(["--monitoring-output-dir", str(monitoring_output_dir)])
        if monitoring_dry_run_alerts:
            args.append("--monitoring-dry-run-alerts")
    if enable_agent_research:
        args.append("--enable-agent-research")
        args.extend(["--agent-research-output-dir", str(agent_research_output_dir), "--agent-research-mode", str(agent_research_mode)])
        if agent_include_monitoring:
            args.append("--agent-include-monitoring")
        if agent_include_backtest:
            args.append("--agent-include-backtest")
        if agent_include_human_checklist:
            args.append("--agent-include-human-checklist")
    if enable_live_gray_readiness:
        args.append("--enable-live-gray-readiness")
        args.extend(["--live-gray-output-dir", str(live_gray_output_dir)])
        if live_gray_allowed_symbols:
            args.extend(["--live-gray-allowed-symbols", str(live_gray_allowed_symbols)])
        args.extend(["--live-gray-max-total-capital", str(live_gray_max_total_capital), "--live-gray-max-single-order-value", str(live_gray_max_single_order_value)])
        args.extend(["--live-gray-max-symbol-weight", str(live_gray_max_symbol_weight), "--live-gray-max-portfolio-weight", str(live_gray_max_portfolio_weight)])
        if live_gray_enabled:
            args.append("--live-gray-enabled")
    if enable_data_quality_tracking:
        args.append("--enable-data-quality-tracking")
        args.extend(["--data-quality-tracking-output-dir", str(data_quality_tracking_output_dir), "--data-quality-tracking-report-dir", str(data_quality_tracking_report_dir)])
        if data_quality_tracking_cache_root:
            args.extend(["--data-quality-tracking-cache-root", str(data_quality_tracking_cache_root)])
        if data_quality_tracking_symbols:
            args.extend(["--data-quality-tracking-symbols", str(data_quality_tracking_symbols)])
        if data_quality_tracking_start:
            args.extend(["--data-quality-tracking-start", str(data_quality_tracking_start)])
        if data_quality_tracking_end:
            args.extend(["--data-quality-tracking-end", str(data_quality_tracking_end)])
    if enable_notification_dry_run:
        args.append("--enable-notification-dry-run")
        args.extend(["--notification-dry-run-output-dir", str(notification_dry_run_output_dir)])
        if notification_dry_run_channels:
            args.extend(["--notification-dry-run-channels", str(notification_dry_run_channels)])
    if enable_gray_rehearsal:
        args.append("--enable-gray-rehearsal")
        args.extend(["--gray-rehearsal-output-dir", str(gray_rehearsal_output_dir)])
        if gray_rehearsal_allowed_symbols:
            args.extend(["--gray-rehearsal-allowed-symbols", str(gray_rehearsal_allowed_symbols)])
        args.extend(["--gray-rehearsal-max-total-capital", str(gray_rehearsal_max_total_capital), "--gray-rehearsal-max-single-order-value", str(gray_rehearsal_max_single_order_value)])
    if enable_gray_decision_package:
        args.append("--enable-gray-decision-package")
        args.extend(["--gray-decision-output-dir", str(gray_decision_output_dir)])
        if gray_decision_allowed_symbols:
            args.extend(["--gray-decision-allowed-symbols", str(gray_decision_allowed_symbols)])
        args.extend(["--gray-decision-max-total-capital", str(gray_decision_max_total_capital)])
        args.extend(["--gray-decision-max-single-order-value", str(gray_decision_max_single_order_value)])
        args.extend(["--gray-decision-max-symbol-weight", str(gray_decision_max_symbol_weight)])
        args.extend(["--gray-decision-max-portfolio-weight", str(gray_decision_max_portfolio_weight)])
    if enable_live_manual_prep:
        args.append("--enable-live-manual-prep")
        args.extend(["--live-manual-prep-output-dir", str(live_manual_prep_output_dir)])
        if live_manual_prep_allowed_symbols:
            args.extend(["--live-manual-prep-allowed-symbols", str(live_manual_prep_allowed_symbols)])
        args.extend(["--live-manual-prep-max-total-capital", str(live_manual_prep_max_total_capital), "--live-manual-prep-max-single-order-value", str(live_manual_prep_max_single_order_value)])
        args.extend(["--live-manual-prep-max-symbol-weight", str(live_manual_prep_max_symbol_weight), "--live-manual-prep-max-portfolio-weight", str(live_manual_prep_max_portfolio_weight)])
    if enable_live_env_check:
        args.append("--enable-live-env-check")
        args.extend(["--live-env-check-output-dir", str(live_env_check_output_dir)])
        if live_env_check_allowed_symbols:
            args.extend(["--live-env-check-allowed-symbols", str(live_env_check_allowed_symbols)])
        args.extend(["--live-env-check-max-total-capital", str(live_env_check_max_total_capital), "--live-env-check-max-single-order-value", str(live_env_check_max_single_order_value)])
        if float(live_env_check_max_symbol_weight) != 0.1:
            args.extend(["--live-env-check-max-symbol-weight", str(live_env_check_max_symbol_weight)])
        if float(live_env_check_max_portfolio_weight) != 0.2:
            args.extend(["--live-env-check-max-portfolio-weight", str(live_env_check_max_portfolio_weight)])
    if enable_final_authorization_package:
        args.append("--enable-final-authorization-package")
        args.extend(["--final-authorization-output-dir", str(final_authorization_output_dir)])
        if final_authorization_allowed_symbols:
            args.extend(["--final-authorization-allowed-symbols", str(final_authorization_allowed_symbols)])
        args.extend(["--final-authorization-max-total-capital", str(final_authorization_max_total_capital), "--final-authorization-max-single-order-value", str(final_authorization_max_single_order_value)])
        args.extend(["--final-authorization-max-symbol-weight", str(final_authorization_max_symbol_weight), "--final-authorization-max-portfolio-weight", str(final_authorization_max_portfolio_weight)])
    if enable_redline_review:
        args.append("--enable-redline-review")
        args.extend(["--redline-review-output-dir", str(redline_review_output_dir)])
        if redline_review_operator_name:
            args.extend(["--redline-review-operator-name", str(redline_review_operator_name)])
        if redline_review_reviewer_name:
            args.extend(["--redline-review-reviewer-name", str(redline_review_reviewer_name)])
    if enable_live_gray_ledger:
        args.append("--enable-live-gray-ledger")
        args.extend(["--live-gray-ledger-output-dir", str(live_gray_ledger_output_dir)])
    if enable_live_gray_review:
        args.append("--enable-live-gray-review")
        args.extend(["--live-gray-review-output-dir", str(live_gray_review_output_dir)])
    if enable_live_signature_freeze:
        args.append("--enable-live-signature-freeze")
        args.extend(["--live-signature-freeze-output-dir", str(live_signature_freeze_output_dir)])
    if enable_live_env_snapshot:
        args.append("--enable-live-env-snapshot")
        args.extend(["--live-env-snapshot-output-dir", str(live_env_snapshot_output_dir)])
    if enable_live_runbook:
        args.append("--enable-live-runbook")
        args.extend(["--live-runbook-output-dir", str(live_runbook_output_dir)])
    if enable_live_signoff:
        args.append("--enable-live-signoff")
        args.extend(["--live-signoff-output-dir", str(live_signoff_output_dir)])
    if enable_live_final_review:
        args.append("--enable-live-final-review")
        args.extend(["--live-final-review-output-dir", str(live_final_review_output_dir)])
    if enable_live_archive:
        args.append("--enable-live-archive")
        args.extend(["--live-archive-output-dir", str(live_archive_output_dir)])
    if enable_live_consistency:
        args.append("--enable-live-consistency")
        args.extend(["--live-consistency-output-dir", str(live_consistency_output_dir)])
    if enable_live_final_archive:
        args.append("--enable-live-final-archive")
        args.extend(["--live-final-archive-output-dir", str(live_final_archive_output_dir)])
    if enable_live_archive_lock:
        args.append("--enable-live-archive-lock")
        args.extend(["--live-archive-lock-output-dir", str(live_archive_lock_output_dir)])
    if enable_live_lock_consistency:
        args.append("--enable-live-lock-consistency")
        args.extend(["--live-lock-consistency-output-dir", str(live_lock_consistency_output_dir)])
    if enable_live_archive_verification:
        args.append("--enable-live-archive-verification")
        args.extend(["--live-archive-verification-output-dir", str(live_archive_verification_output_dir)])
    if enable_live_gap_clearance:
        args.append("--enable-live-gap-clearance")
        args.extend(["--live-gap-clearance-output-dir", str(live_gap_clearance_output_dir)])
    if enable_qmt_dryrun_calibration:
        args.append("--enable-qmt-dryrun-calibration")
        args.extend(["--qmt-dryrun-calibration-output-dir", str(qmt_dryrun_calibration_output_dir), "--qmt-dryrun-calibration-provider", str(qmt_dryrun_calibration_provider)])
    if enable_real_cache_quality:
        args.append("--enable-real-cache-quality")
        args.extend(["--real-cache-quality-output-dir", str(real_cache_quality_output_dir), "--real-cache-quality-provider", str(real_cache_quality_provider)])
    if enable_live_gray_candidate:
        args.append("--enable-live-gray-candidate")
        args.extend(["--live-gray-candidate-output-dir", str(live_gray_candidate_output_dir)])
    if enable_live_gray_final_approval:
        args.append("--enable-live-gray-final-approval")
        args.extend(["--live-gray-final-approval-output-dir", str(live_gray_final_approval_output_dir)])
    if enable_live_gray_readonly_seal:
        args.append("--enable-live-gray-readonly-seal")
        args.extend(["--live-gray-readonly-seal-output-dir", str(live_gray_readonly_seal_output_dir)])
    if enable_pre_gray_final_review:
        args.append("--enable-pre-gray-final-review")
        args.extend(["--pre-gray-final-review-output-dir", str(pre_gray_final_review_output_dir)])
    if build_dashboard:
        args.append("--build-dashboard")
        args.extend(["--dashboard-output", str(dashboard_output), "--dashboard-title", str(dashboard_title)])
    if use_cached_research or data_source_mode in {"cached", "auto", "cached_real_first"}:
        if use_cached_research:
            args.append("--use-cached-research")
        if "--cache-root" not in args:
            args.extend(["--cache-root", str(cache_root)])
        if research_start:
            args.extend(["--research-start", str(research_start)])
        if research_end:
            args.extend(["--research-end", str(research_end)])
        args.extend(["--research-frequency", str(research_frequency)])
        args.extend(["--min-bars", str(min_bars)])
        args.extend(["--cached-strategy-top-n", str(cached_strategy_top_n)])
        args.extend(["--cached-strategy-min-bars", str(cached_strategy_min_bars)])
        if cached_strategy_min_score is not None:
            args.extend(["--cached-strategy-min-score", str(cached_strategy_min_score)])
    if write_reports:
        args.append("--write-reports")
    args.extend(["--report-dir", str(report_dir)])
    if notify_dry_run:
        args.append("--notify-dry-run")
    display = " ".join([_quote_for_display(python_command), *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand(
        command=str(python_command),
        arguments=args,
        working_directory=_project_root(project_root),
        description="Run the QMT AI Trading daily pipeline in dry-run/shadow mode.",
        metadata={"display": display, "safe_mode": "dry-run/shadow", "real_notifications": False, "real_orders": False},
    )


def build_schtasks_create_command(config: ScheduleConfig | None = None, **overrides: object) -> ScheduleCommand:
    """Build a ``schtasks /Create`` command preview for the daily dry-run task."""

    cfg = config or ScheduleConfig()
    for key, value in overrides.items():
        if value is not None and hasattr(cfg, key):
            setattr(cfg, key, value)
    project_root = _project_root(cfg.project_root)
    pipeline = build_daily_pipeline_command(
        project_root=project_root,
        python_command=cfg.python_command,
        script_path=cfg.script_path,
        report_dir=cfg.report_dir,
        write_reports=cfg.write_reports,
        notify_dry_run=cfg.notify_dry_run,
        warmup_cache=cfg.warmup_cache,
        warmup_universe=cfg.warmup_universe,
        universe_name=cfg.universe_name,
        universe_lookback_days=cfg.universe_lookback_days,
        universe_lookback_years=cfg.universe_lookback_years,
        warmup_provider=cfg.warmup_provider,
        warmup_start=cfg.warmup_start,
        warmup_end=cfg.warmup_end,
        warmup_frequency=cfg.warmup_frequency,
        cache_root=cfg.cache_root,
        use_cached_research=cfg.use_cached_research,
        research_start=cfg.research_start,
        research_end=cfg.research_end,
        research_frequency=cfg.research_frequency,
        min_bars=cfg.min_bars,
        cached_strategy_top_n=cfg.cached_strategy_top_n,
        cached_strategy_min_score=cfg.cached_strategy_min_score,
        cached_strategy_min_bars=cfg.cached_strategy_min_bars,
        data_source_mode=cfg.data_source_mode,
        allow_mock_fallback=cfg.allow_mock_fallback,
        quality_report_dir=cfg.quality_report_dir,
        require_quality_report=cfg.require_quality_report,
        allow_unknown_quality_for_dry_run=cfg.allow_unknown_quality_for_dry_run,
        allow_mock_cache=cfg.allow_mock_cache,
        min_quality_level=cfg.min_quality_level,
        min_coverage_ratio=cfg.min_coverage_ratio,
        min_loaded_symbols=cfg.min_loaded_symbols,
        require_cached_research=cfg.require_cached_research,
        data_source_confidence_required=cfg.data_source_confidence_required,
        create_approval=cfg.create_approval,
        approval_root=cfg.approval_root,
        approval_expires_hours=cfg.approval_expires_hours,
        enable_portfolio_plan=cfg.enable_portfolio_plan,
        portfolio_method=cfg.portfolio_method,
        portfolio_top_n=cfg.portfolio_top_n,
        portfolio_cash_reserve_ratio=cfg.portfolio_cash_reserve_ratio,
        portfolio_max_symbol_weight=cfg.portfolio_max_symbol_weight,
        portfolio_max_weight=cfg.portfolio_max_weight,
        portfolio_rebalance_threshold=cfg.portfolio_rebalance_threshold,
        portfolio_total_asset=cfg.portfolio_total_asset,
        portfolio_current_cash=cfg.portfolio_current_cash,
        portfolio_snapshot_path=cfg.portfolio_snapshot_path,
        enable_monitoring=cfg.enable_monitoring,
        monitoring_output_dir=cfg.monitoring_output_dir,
        monitoring_dry_run_alerts=cfg.monitoring_dry_run_alerts,
        enable_agent_research=cfg.enable_agent_research,
        agent_research_output_dir=cfg.agent_research_output_dir,
        agent_research_mode=cfg.agent_research_mode,
        agent_include_monitoring=cfg.agent_include_monitoring,
        agent_include_backtest=cfg.agent_include_backtest,
        agent_include_human_checklist=cfg.agent_include_human_checklist,
        enable_live_gray_readiness=cfg.enable_live_gray_readiness,
        live_gray_output_dir=cfg.live_gray_output_dir,
        live_gray_allowed_symbols=cfg.live_gray_allowed_symbols,
        live_gray_max_total_capital=cfg.live_gray_max_total_capital,
        live_gray_max_single_order_value=cfg.live_gray_max_single_order_value,
        live_gray_max_symbol_weight=cfg.live_gray_max_symbol_weight,
        live_gray_max_portfolio_weight=cfg.live_gray_max_portfolio_weight,
        live_gray_enabled=cfg.live_gray_enabled,
        build_dashboard=cfg.build_dashboard,
        dashboard_output=cfg.dashboard_output,
        dashboard_title=cfg.dashboard_title,
        enable_data_quality_tracking=cfg.enable_data_quality_tracking,
        data_quality_tracking_output_dir=cfg.data_quality_tracking_output_dir,
        data_quality_tracking_report_dir=cfg.data_quality_tracking_report_dir,
        data_quality_tracking_cache_root=cfg.data_quality_tracking_cache_root,
        data_quality_tracking_symbols=cfg.data_quality_tracking_symbols,
        data_quality_tracking_start=cfg.data_quality_tracking_start,
        data_quality_tracking_end=cfg.data_quality_tracking_end,
        enable_notification_dry_run=cfg.enable_notification_dry_run,
        notification_dry_run_output_dir=cfg.notification_dry_run_output_dir,
        notification_dry_run_channels=cfg.notification_dry_run_channels,
        enable_gray_rehearsal=cfg.enable_gray_rehearsal,
        gray_rehearsal_output_dir=cfg.gray_rehearsal_output_dir,
        gray_rehearsal_allowed_symbols=cfg.gray_rehearsal_allowed_symbols,
        gray_rehearsal_max_total_capital=cfg.gray_rehearsal_max_total_capital,
        gray_rehearsal_max_single_order_value=cfg.gray_rehearsal_max_single_order_value,
        enable_gray_decision_package=cfg.enable_gray_decision_package,
        gray_decision_output_dir=cfg.gray_decision_output_dir,
        gray_decision_allowed_symbols=cfg.gray_decision_allowed_symbols,
        gray_decision_max_total_capital=cfg.gray_decision_max_total_capital,
        gray_decision_max_single_order_value=cfg.gray_decision_max_single_order_value,
        gray_decision_max_symbol_weight=cfg.gray_decision_max_symbol_weight,
        gray_decision_max_portfolio_weight=cfg.gray_decision_max_portfolio_weight,
        enable_live_manual_prep=cfg.enable_live_manual_prep,
        live_manual_prep_output_dir=cfg.live_manual_prep_output_dir,
        live_manual_prep_allowed_symbols=cfg.live_manual_prep_allowed_symbols,
        live_manual_prep_max_total_capital=cfg.live_manual_prep_max_total_capital,
        live_manual_prep_max_single_order_value=cfg.live_manual_prep_max_single_order_value,
        live_manual_prep_max_symbol_weight=cfg.live_manual_prep_max_symbol_weight,
        live_manual_prep_max_portfolio_weight=cfg.live_manual_prep_max_portfolio_weight,
        enable_live_env_check=cfg.enable_live_env_check,
        live_env_check_output_dir=cfg.live_env_check_output_dir,
        live_env_check_allowed_symbols=cfg.live_env_check_allowed_symbols,
        live_env_check_max_total_capital=cfg.live_env_check_max_total_capital,
        live_env_check_max_single_order_value=cfg.live_env_check_max_single_order_value,
        live_env_check_max_symbol_weight=cfg.live_env_check_max_symbol_weight,
        live_env_check_max_portfolio_weight=cfg.live_env_check_max_portfolio_weight,
        enable_final_authorization_package=cfg.enable_final_authorization_package,
        final_authorization_output_dir=cfg.final_authorization_output_dir,
        enable_redline_review=cfg.enable_redline_review,
        redline_review_output_dir=cfg.redline_review_output_dir,
        redline_review_operator_name=cfg.redline_review_operator_name,
        redline_review_reviewer_name=cfg.redline_review_reviewer_name,
        enable_live_gray_ledger=cfg.enable_live_gray_ledger,
        live_gray_ledger_output_dir=cfg.live_gray_ledger_output_dir,
        enable_live_gray_review=cfg.enable_live_gray_review,
        live_gray_review_output_dir=cfg.live_gray_review_output_dir,
        enable_live_signature_freeze=cfg.enable_live_signature_freeze,
        live_signature_freeze_output_dir=cfg.live_signature_freeze_output_dir,
        enable_live_env_snapshot=cfg.enable_live_env_snapshot,
        live_env_snapshot_output_dir=cfg.live_env_snapshot_output_dir,
        enable_live_runbook=cfg.enable_live_runbook,
        live_runbook_output_dir=cfg.live_runbook_output_dir,
        enable_live_signoff=cfg.enable_live_signoff,
        live_signoff_output_dir=cfg.live_signoff_output_dir,
        enable_live_final_review=cfg.enable_live_final_review,
        live_final_review_output_dir=cfg.live_final_review_output_dir,
        enable_live_archive=cfg.enable_live_archive,
        live_archive_output_dir=cfg.live_archive_output_dir,
        enable_live_consistency=cfg.enable_live_consistency,
        live_consistency_output_dir=cfg.live_consistency_output_dir,
        enable_live_final_archive=cfg.enable_live_final_archive,
        live_final_archive_output_dir=cfg.live_final_archive_output_dir,
        enable_live_archive_lock=cfg.enable_live_archive_lock,
        live_archive_lock_output_dir=cfg.live_archive_lock_output_dir,
        enable_live_lock_consistency=cfg.enable_live_lock_consistency,
        live_lock_consistency_output_dir=cfg.live_lock_consistency_output_dir,
        enable_live_archive_verification=cfg.enable_live_archive_verification,
        live_archive_verification_output_dir=cfg.live_archive_verification_output_dir,
        enable_live_gap_clearance=cfg.enable_live_gap_clearance,
        live_gap_clearance_output_dir=cfg.live_gap_clearance_output_dir,
        enable_qmt_dryrun_calibration=cfg.enable_qmt_dryrun_calibration,
        qmt_dryrun_calibration_output_dir=cfg.qmt_dryrun_calibration_output_dir,
        qmt_dryrun_calibration_provider=cfg.qmt_dryrun_calibration_provider,
        enable_real_cache_quality=cfg.enable_real_cache_quality,
        real_cache_quality_output_dir=cfg.real_cache_quality_output_dir,
        real_cache_quality_provider=cfg.real_cache_quality_provider,
        enable_live_gray_candidate=cfg.enable_live_gray_candidate,
        live_gray_candidate_output_dir=cfg.live_gray_candidate_output_dir,
        enable_live_gray_final_approval=cfg.enable_live_gray_final_approval,
        live_gray_final_approval_output_dir=cfg.live_gray_final_approval_output_dir,
        enable_live_gray_readonly_seal=cfg.enable_live_gray_readonly_seal,
        live_gray_readonly_seal_output_dir=cfg.live_gray_readonly_seal_output_dir,
        enable_pre_gray_final_review=cfg.enable_pre_gray_final_review,
        pre_gray_final_review_output_dir=cfg.pre_gray_final_review_output_dir,
        final_authorization_allowed_symbols=cfg.final_authorization_allowed_symbols,
        final_authorization_max_total_capital=cfg.final_authorization_max_total_capital,
        final_authorization_max_single_order_value=cfg.final_authorization_max_single_order_value,
        final_authorization_max_symbol_weight=cfg.final_authorization_max_symbol_weight,
        final_authorization_max_portfolio_weight=cfg.final_authorization_max_portfolio_weight,
    )
    task_run = pipeline.metadata["display"]
    args = ["/Create", "/F", "/SC", "DAILY", "/TN", cfg.task_name, "/TR", task_run, "/ST", cfg.run_time]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, project_root, "Create Windows scheduled task for dry-run daily pipeline.", {"display": display, "task_run": task_run})


def build_schtasks_delete_command(task_name: str = DEFAULT_TASK_NAME, project_root: str | Path | None = None) -> ScheduleCommand:
    args = ["/Delete", "/F", "/TN", task_name]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, _project_root(project_root), "Delete Windows scheduled task.", {"display": display})


def build_schtasks_query_command(task_name: str = DEFAULT_TASK_NAME, project_root: str | Path | None = None) -> ScheduleCommand:
    args = ["/Query", "/TN", task_name]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, _project_root(project_root), "Query Windows scheduled task.", {"display": display})


def _run_command(command: ScheduleCommand) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [command.command, *command.arguments],
        cwd=command.working_directory,
        check=False,
        capture_output=True,
        text=True,
    )


def register_windows_task(config: ScheduleConfig | None = None, *, dry_run: bool = True, **overrides: object) -> ScheduleResult:
    command = build_schtasks_create_command(config, **overrides)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task registered", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})


def unregister_windows_task(task_name: str = DEFAULT_TASK_NAME, *, project_root: str | Path | None = None, dry_run: bool = True) -> ScheduleResult:
    command = build_schtasks_delete_command(task_name, project_root)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task deleted", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})


def query_windows_task(task_name: str = DEFAULT_TASK_NAME, *, project_root: str | Path | None = None, dry_run: bool = True) -> ScheduleResult:
    command = build_schtasks_query_command(task_name, project_root)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task queried", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})
