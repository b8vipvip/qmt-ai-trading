"""Data models for local scheduler commands and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScheduleConfig:
    """Configuration for the local Windows Task Scheduler dry-run task."""

    task_name: str = "QmtAiTradingDailyDryRun"
    project_root: Path = Path.cwd()
    python_command: str = "py"
    script_path: Path = Path("scripts/run_daily_pipeline.py")
    run_time: str = "15:30"
    report_dir: Path = Path("reports")
    write_reports: bool = True
    notify_dry_run: bool = True
    warmup_cache: bool = False
    warmup_universe: bool = False
    universe_name: str = "default_etf"
    universe_lookback_days: int | None = None
    universe_lookback_years: int | None = None
    warmup_provider: str = "mock"
    warmup_start: str | None = None
    warmup_end: str | None = None
    warmup_frequency: str = "1d"
    cache_root: Path = Path("market_data")
    use_cached_research: bool = False
    research_start: str | None = None
    research_end: str | None = None
    research_frequency: str = "1d"
    min_bars: int = 20
    cached_strategy_top_n: int = 1
    cached_strategy_min_score: float | None = None
    cached_strategy_min_bars: int = 20
    data_source_mode: str = "cached_real_first"
    allow_mock_fallback: bool = False
    quality_report_dir: Path = Path("qmt_data_quality_reports")
    require_quality_report: bool = False
    allow_unknown_quality_for_dry_run: bool = True
    allow_mock_cache: bool = False
    min_quality_level: str = "UNKNOWN"
    min_coverage_ratio: float = 0.8
    min_loaded_symbols: int = 1
    require_cached_research: bool = False
    data_source_confidence_required: str | None = None
    create_approval: bool = False
    approval_root: Path = Path("approvals")
    approval_expires_hours: float = 24.0
    enable_portfolio_plan: bool = False
    portfolio_method: str = "score_weight"
    portfolio_top_n: int = 2
    portfolio_cash_reserve_ratio: float = 0.2
    portfolio_max_symbol_weight: float = 0.3
    portfolio_max_weight: float = 0.8
    portfolio_rebalance_threshold: float = 0.05
    portfolio_total_asset: float = 1000000.0
    portfolio_current_cash: float = 1000000.0
    portfolio_snapshot_path: str | None = None
    enable_monitoring: bool = False
    monitoring_output_dir: Path = Path("monitoring_reports")
    monitoring_dry_run_alerts: bool = False
    dry_run: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleCommand:
    """A command preview that can be printed or executed by the scheduler layer."""

    command: str
    arguments: list[str] = field(default_factory=list)
    working_directory: Path | str = Path.cwd()
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleResult:
    """Result returned by scheduler registration, deletion, and query helpers."""

    success: bool
    dry_run: bool
    message: str
    command: ScheduleCommand
    metadata: dict[str, Any] = field(default_factory=dict)
