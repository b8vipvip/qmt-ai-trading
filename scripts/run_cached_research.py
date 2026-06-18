#!/usr/bin/env python
"""Run read-only cached Research scoring from LocalBarStore."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.research.cache_reader import format_cached_research_dataset
from qmt_ai_trading.research.cache_scoring import build_candidates_from_cached_research, score_symbols_from_cache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read local cached bars and run Research scoring. No downloads, QMT, or orders.")
    parser.add_argument("--symbols", default="", help="Comma-separated symbols.")
    parser.add_argument("--universe-name", default="", help="Use default_etf when symbols are omitted.")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--min-bars", type=int, default=20)
    parser.add_argument("--allow-partial", action="store_true", default=True)
    args = parser.parse_args(argv)

    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    if not symbols and (args.universe_name or "default_etf") == "default_etf":
        symbols = [item.symbol for item in get_default_etf_universe()]
    scores, dataset = score_symbols_from_cache(
        symbols,
        args.start,
        args.end,
        frequency=args.frequency,
        cache_root=args.cache_root,
        min_bars=args.min_bars,
        allow_partial=args.allow_partial,
    )
    candidates = build_candidates_from_cached_research(scores, dataset=dataset)
    print(format_cached_research_dataset(dataset))
    print("\nScores and candidates:")
    by_candidate = {item.symbol: item for item in candidates}
    for score in scores:
        candidate = by_candidate.get(score.symbol)
        print(
            f"- {score.symbol}: score={score.score} eligible={score.eligible} "
            f"bar_count={score.metrics.get('bar_count', 0)} source={score.metrics.get('source', 'cached_research')} "
            f"candidate_score={candidate.score if candidate else None} candidate_eligible={candidate.eligible if candidate else False}"
        )
    if dataset.failed_symbols:
        print(f"WARNING: {dataset.failed_symbols} symbols could not be loaded from local cache.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
