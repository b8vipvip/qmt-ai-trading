from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.providers import fetch_historical_bars
from qmt_ai_trading.datahub.qmt_diagnostics import format_qmt_runtime_info, inspect_qmt_runtime
from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider, QmtProviderError
from qmt_ai_trading.datahub.symbols import normalize_symbol


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check optional QMT xtdata historical provider availability without trading APIs.")
    parser.add_argument("--try-connect", action="store_true", help="Call xtdata.connect() when available")
    parser.add_argument("--diagnose", action="store_true", help="Print QmtRuntimeInfo diagnostics")
    parser.add_argument("--print-functions", action="store_true", help="Print xtdata callable function summary")
    parser.add_argument("--symbol", default="510300.SH")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2024-01-10")
    parser.add_argument("--frequency", default="1d")
    parser.add_argument("--fetch-sample", action="store_true", help="Fetch and cache a small historical sample")
    parser.add_argument("--cache-root", default="market_data_qmt_check")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", default="qmt_runtime_report.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    info = inspect_qmt_runtime(try_connect=args.try_connect)
    print(f"xtquant.xtdata import available={info.xtdata_available}")
    print("trading APIs: not used; xttrader is not imported")
    report_parts = [format_qmt_runtime_info(info)]
    if args.diagnose:
        print(report_parts[0])
    if args.print_functions:
        summary = ", ".join(info.supported_functions[:80]) or "n/a"
        print(f"xtdata functions ({len(info.supported_functions)}): {summary}")
        report_parts.append(f"\nFunctions ({len(info.supported_functions)}):\n{summary}")
    if not info.xtdata_available:
        print("QMT historical provider unavailable: install/enable MiniQMT/QMT Python environment with xtquant.xtdata")
        if args.write_report:
            Path(args.report_path).write_text("\n\n".join(report_parts), encoding="utf-8")
        return 0
    if args.fetch_sample:
        provider = QmtHistoricalDataProvider()
        query = BarQuery([normalize_symbol(args.symbol)], args.start, args.end, args.frequency, provider="qmt")
        try:
            result = fetch_historical_bars(query, store=LocalBarStore(args.cache_root), provider=provider)
        except QmtProviderError as exc:
            print(f"sample fetch failed: {exc}")
            return 2
        paths = ", ".join(meta.path for meta in result.metadata) or "n/a"
        line = f"sample cache {'hit' if result.hit else 'miss'} rows={len(result.bars)} paths={paths}"
        print(line); report_parts.append(line)
    if args.write_report:
        Path(args.report_path).write_text("\n\n".join(report_parts), encoding="utf-8")
        print(f"report written: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
