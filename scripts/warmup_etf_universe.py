#!/usr/bin/env python
"""Warm ETF universe historical cache. Historical data only; no trading APIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.universe_warmup import build_universe_warmup_request, format_universe_warmup_result, warmup_etf_universe_history


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Warm local ETF universe historical bar cache in mock or optional QMT mode.")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--symbols", default=None, help="Optional comma-separated symbols. Overrides universe-name when provided.")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument("--lookback-years", type=int, default=None)
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--provider", default="mock", choices=["mock", "qmt"])
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)
    request = build_universe_warmup_request(universe_name=args.universe_name, symbols=args.symbols, start_date=args.start, end_date=args.end, lookback_days=args.lookback_days, lookback_years=args.lookback_years, frequency=args.frequency, provider=args.provider, cache_root=args.cache_root, fail_fast=args.fail_fast, metadata={"entrypoint": "warmup_etf_universe.py"})
    result = warmup_etf_universe_history(request)
    print(format_universe_warmup_result(result))
    return 0 if result.success or (args.provider == "qmt" and result.warmup_result.skipped_count > 0 and result.warmup_result.failed_count == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
