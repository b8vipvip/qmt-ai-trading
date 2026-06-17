from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.providers import fetch_historical_bars
from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider, QmtProviderError
from qmt_ai_trading.datahub.symbols import normalize_symbol


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check optional QMT xtdata historical provider availability without trading APIs.")
    parser.add_argument("--try-connect", action="store_true", help="Call xtdata.connect() when available")
    parser.add_argument("--symbol", default="510300.SH")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2024-01-10")
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--fetch-sample", action="store_true", help="Fetch and cache a small historical sample")
    parser.add_argument("--cache-root", default="market_data_qmt_check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = QmtHistoricalDataProvider()
    available = provider.is_available()
    print(f"xtquant.xtdata import available={available}")
    print("trading APIs: not used; xttrader is not imported")
    if not available:
        print("QMT historical provider unavailable: install/enable MiniQMT/QMT Python environment with xtquant.xtdata")
        return 0
    if args.try_connect:
        try:
            print(f"xtdata.connect result={provider.connect()}")
        except QmtProviderError as exc:
            print(f"xtdata.connect failed: {exc}")
            return 2
    print("QMT historical provider available=True")
    if args.fetch_sample:
        query = BarQuery([normalize_symbol(args.symbol)], args.start, args.end, args.frequency, provider="qmt")
        try:
            result = fetch_historical_bars(query, store=LocalBarStore(args.cache_root), provider=provider)
        except QmtProviderError as exc:
            print(f"sample fetch failed: {exc}")
            return 2
        paths = ", ".join(meta.path for meta in result.metadata) or "n/a"
        print(f"sample cache {'hit' if result.hit else 'miss'} rows={len(result.bars)} paths={paths}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
