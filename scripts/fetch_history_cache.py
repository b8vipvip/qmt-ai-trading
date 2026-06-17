from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.providers import create_historical_provider, fetch_historical_bars
from qmt_ai_trading.datahub.qmt_provider import QmtProviderError
from qmt_ai_trading.datahub.symbols import normalize_symbol


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate local historical bar cache in mock or optional QMT mode.")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols, e.g. 510300.SH,510500.SH")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD")
    parser.add_argument("--frequency", default="1d", help="Bar frequency, default: 1d")
    parser.add_argument("--cache-root", default="market_data", help="Local cache root directory")
    parser.add_argument("--provider", default="mock", choices=["mock", "qmt"], help="Historical provider, default: mock")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbols = [normalize_symbol(item.strip()) for item in args.symbols.split(",") if item.strip()]
    query = BarQuery(symbols=symbols, start_date=args.start, end_date=args.end, frequency=args.frequency, provider=args.provider)
    store = LocalBarStore(args.cache_root)
    if args.provider == "qmt":
        print("provider=qmt requires local MiniQMT/QMT to be running and xtquant.xtdata importable; no xttrader/trading APIs are used.")
    try:
        provider = create_historical_provider(args.provider)
        result = fetch_historical_bars(query, store=store, provider=provider)
    except QmtProviderError as exc:
        print(f"QMT provider error: {exc}", file=sys.stderr)
        return 2
    paths = ", ".join(meta.path for meta in result.metadata) or "n/a"
    print(f"query symbols={','.join(symbols)} start={args.start} end={args.end} frequency={args.frequency} provider={args.provider}")
    print(f"cache {'hit' if result.hit else 'miss'}")
    print(f"saved_or_loaded_rows={len(result.bars)}")
    print(f"local_paths={paths}")
    print(f"message={result.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
