#!/usr/bin/env python
"""Run cached ETF rotation signal generation from local cache only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.research.cache_scoring import score_etf_universe_from_cache, score_symbols_from_cache
from qmt_ai_trading.strategies.cached_etf_rotation import CachedETFSignalConfig, generate_cached_etf_rotation_signal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate dry-run ETF rotation signals from cached research factors only.")
    parser.add_argument("--symbols", default="", help="Comma-separated symbols. Overrides universe when provided.")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--min-bars", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=1)
    parser.add_argument("--min-score", type=float, default=None)
    args = parser.parse_args(argv)

    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    if symbols:
        scores, dataset = score_symbols_from_cache(symbols, args.start, args.end, frequency=args.frequency, cache_root=args.cache_root, min_bars=args.min_bars)
    else:
        scores, dataset = score_etf_universe_from_cache(universe_name=args.universe_name, start_date=args.start, end_date=args.end, frequency=args.frequency, cache_root=args.cache_root, min_bars=args.min_bars)
    signal = generate_cached_etf_rotation_signal(scores, CachedETFSignalConfig(top_n=args.top_n, min_score=args.min_score, min_bars=args.min_bars))

    print("Cached ETF Rotation Signal")
    print(f"loaded symbols: {dataset.loaded_symbols}/{dataset.total_symbols}")
    print(f"eligible candidates: {sum(1 for c in signal.candidates if c.eligible)}")
    print("skipped symbols:")
    for item in signal.skipped_symbols:
        print(f"- {item.get('symbol')}: {item.get('reason')}")
    print("selected candidates:")
    for candidate in signal.selected_candidates:
        print(f"- {candidate.symbol}: score={candidate.score:.4f} target_percent={candidate.target_percent}")
    print("generated TradeIntent:")
    for intent in signal.trade_intents:
        print(f"- {intent.side} {intent.symbol} quantity={intent.quantity} target_percent={intent.target_percent} dry_run={intent.dry_run} source={intent.source}")
    if not signal.trade_intents:
        print(f"- none: {signal.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
