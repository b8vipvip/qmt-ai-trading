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
    )
    print(result.report_text)

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

    if args.notify_dry_run:
        from qmt_ai_trading.reporting.notifier import notify_report

        notification_results = notify_report(artifacts, dry_run=True)
        print("\nNotification dry-run results:")
        for item in notification_results:
            print(f"- {item.channel}: success={item.success} dry_run={item.dry_run} message={item.message}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
