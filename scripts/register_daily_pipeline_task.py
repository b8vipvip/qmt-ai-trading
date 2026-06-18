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
    if args.use_cached_research:
        print(f"Cached research: start={args.research_start} end={args.research_end} frequency={args.research_frequency} min_bars={args.min_bars} cache_root={args.cache_root}")
    print(f"Result: {result.message}")
    if result.dry_run:
        print("DRY-RUN ONLY: no task registered. Re-run with --execute to register on Windows.")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
