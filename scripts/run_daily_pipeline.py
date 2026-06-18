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
    )
    print(result.report_text)

    artifacts = []
    if args.write_reports:
        from qmt_ai_trading.reporting.writer import write_pipeline_reports

        artifacts = write_pipeline_reports(result, args.report_dir)
        print("\nReports written:")
        for artifact in artifacts:
            print(f"- {artifact.format}: {artifact.path}")

    if args.notify_dry_run:
        from qmt_ai_trading.reporting.notifier import notify_report

        notification_results = notify_report(artifacts, dry_run=True)
        print("\nNotification dry-run results:")
        for item in notification_results:
            print(f"- {item.channel}: success={item.success} dry_run={item.dry_run} message={item.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
