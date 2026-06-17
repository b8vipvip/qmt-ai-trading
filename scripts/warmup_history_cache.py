#!/usr/bin/env python
"""Manual historical bar cache warmup. Historical data only; no trading APIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.cache_warmup import build_default_warmup_request, format_cache_warmup_result, warmup_history_cache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Warm local historical bar cache in mock or optional QMT mode.")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols, e.g. 510300.SH,510500.SH")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--provider", default="mock", choices=["mock", "qmt"])
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    request = build_default_warmup_request(symbols=symbols, start_date=args.start, end_date=args.end, frequency=args.frequency, provider=args.provider, cache_root=args.cache_root, fail_fast=args.fail_fast, metadata={"entrypoint": "warmup_history_cache.py"})
    result = warmup_history_cache(request)
    print(format_cache_warmup_result(result))
    return 0 if result.success or (args.provider == "qmt" and result.skipped_count > 0 and result.failed_count == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
