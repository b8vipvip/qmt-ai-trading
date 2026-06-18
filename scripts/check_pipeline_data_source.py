#!/usr/bin/env python
"""Check daily pipeline data source decision without QMT, downloads, or orders."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.pipeline.data_source import build_data_source_policy, choose_pipeline_data_source, format_data_source_decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check pipeline data source coverage and selection. No downloads, QMT, xttrader, or orders.")
    parser.add_argument("--data-source-mode", default="legacy", choices=["legacy", "cached", "auto", "mock"])
    parser.add_argument("--symbols", default="")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--min-bars", type=int, default=20)
    parser.add_argument("--allow-mock-fallback", action="store_true")
    parser.add_argument("--min-coverage-ratio", type=float, default=0.8)
    parser.add_argument("--min-loaded-symbols", type=int, default=1)
    args = parser.parse_args(argv)
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    if not symbols and args.universe_name == "default_etf":
        symbols = [item.symbol for item in get_default_etf_universe()]
    policy = build_data_source_policy(mode=args.data_source_mode, allow_mock_fallback=args.allow_mock_fallback, min_coverage_ratio=args.min_coverage_ratio, min_loaded_symbols=args.min_loaded_symbols, cache_root=args.cache_root, start_date=args.start, end_date=args.end, frequency=args.frequency, min_bars=args.min_bars, metadata={"entrypoint": "check_pipeline_data_source", "universe_name": args.universe_name})
    decision = choose_pipeline_data_source(policy, symbols)
    print(format_data_source_decision(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
