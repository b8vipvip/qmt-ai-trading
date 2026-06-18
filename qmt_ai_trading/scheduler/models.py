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
    data_source_mode: str = "legacy"
    allow_mock_fallback: bool = False
    min_coverage_ratio: float = 0.8
    min_loaded_symbols: int = 1
    require_cached_research: bool = False
    data_source_confidence_required: str | None = None
    create_approval: bool = False
    approval_root: Path = Path("approvals")
    approval_expires_hours: float = 24.0
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
