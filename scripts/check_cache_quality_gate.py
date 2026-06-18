#!/usr/bin/env python
"""Check local cache coverage plus Stage 25 cache quality gate only."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.pipeline.cache_quality_gate import build_cache_quality_gate_policy, evaluate_cache_quality_gate, format_cache_quality_gate_decision
from qmt_ai_trading.pipeline.data_source import build_data_source_policy, evaluate_cache_coverage


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Check cached real data quality gate without QMT trading calls.")
    p.add_argument("--cache-root", default="market_data")
    p.add_argument("--quality-report-dir", default="qmt_data_quality_reports")
    p.add_argument("--symbols", default="")
    p.add_argument("--universe-name", default="default_etf")
    p.add_argument("--start", dest="start_date", default=None)
    p.add_argument("--end", dest="end_date", default=None)
    p.add_argument("--frequency", default="1d")
    p.add_argument("--min-bars", type=int, default=20)
    p.add_argument("--require-quality-report", action="store_true")
    p.add_argument("--allow-unknown-quality-for-dry-run", action="store_true", default=True)
    p.add_argument("--allow-mock-cache", action="store_true")
    p.add_argument("--min-quality-level", default="UNKNOWN", choices=["UNKNOWN", "LOW", "MEDIUM", "HIGH", "UNAVAILABLE"])
    p.add_argument("--min-coverage-ratio", type=float, default=0.8)
    args = p.parse_args(argv)
    symbols = [x.strip() for x in args.symbols.split(",") if x.strip()] or None
    policy = build_data_source_policy(mode="cached_real_first", cache_root=args.cache_root, start_date=args.start_date, end_date=args.end_date, frequency=args.frequency, min_bars=args.min_bars, min_coverage_ratio=args.min_coverage_ratio)
    coverage, _ = evaluate_cache_coverage(policy, symbols)
    gate_policy = build_cache_quality_gate_policy(require_quality_report=args.require_quality_report, allow_unknown_quality_for_dry_run=args.allow_unknown_quality_for_dry_run, allow_mock_cache=args.allow_mock_cache, min_quality_level=args.min_quality_level, min_coverage_ratio=args.min_coverage_ratio)
    decision = evaluate_cache_quality_gate(coverage_ratio=coverage.coverage_ratio, quality_report_dir=args.quality_report_dir, policy=gate_policy, cache_available=coverage.loaded_symbols > 0)
    print(format_cache_quality_gate_decision(decision))
    print(f"coverage_loaded={coverage.loaded_symbols}/{coverage.total_symbols}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
