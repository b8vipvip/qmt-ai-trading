from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.providers import fetch_historical_bars
from qmt_ai_trading.datahub.qmt_diagnostics import build_qmt_data_quality_report, calibrate_qmt_bar_fields, format_qmt_data_quality_report, format_qmt_runtime_info, inspect_qmt_runtime
from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider, QmtProviderError
from qmt_ai_trading.datahub.symbols import normalize_symbol


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch a small QMT historical sample and calibrate bar fields. No trading APIs are used.")
    p.add_argument("--symbol", default="510300.SH")
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-01-10")
    p.add_argument("--frequency", default="1d")
    p.add_argument("--cache-root", default="market_data_qmt_check")
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--report-path", default="qmt_sample_calibration_report.md")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    info = inspect_qmt_runtime()
    parts = [format_qmt_runtime_info(info)]
    print(parts[0])
    if not info.xtdata_available:
        print("xtquant.xtdata unavailable; sample fetch skipped. Start MiniQMT/use its Python environment, then retry.")
        if args.write_report:
            Path(args.report_path).write_text("\n\n".join(parts), encoding="utf-8")
        return 2
    query = BarQuery([normalize_symbol(args.symbol)], args.start, args.end, args.frequency, provider="qmt")
    try:
        result = fetch_historical_bars(query, store=LocalBarStore(args.cache_root), provider=QmtHistoricalDataProvider())
    except QmtProviderError as exc:
        print(f"sample fetch failed: {exc}")
        return 2
    calib = calibrate_qmt_bar_fields([bar.__dict__ for bar in result.bars], args.frequency)
    quality = build_qmt_data_quality_report(result.bars, normalize_symbol(args.symbol), args.frequency, args.start, args.end)
    cache_path = ", ".join(meta.path for meta in result.metadata) or "n/a"
    lines = [f"raw schema columns={calib.raw_columns}", f"mapped_fields={calib.mapped_fields}", f"normalized bars count={len(result.bars)}", f"cache path={cache_path}", format_qmt_data_quality_report(quality), "trading APIs: not used; xttrader is not imported; no orders are sent"]
    for line in lines: print(line)
    parts.extend(lines)
    if args.write_report:
        Path(args.report_path).write_text("\n\n".join(parts), encoding="utf-8")
        print(f"report written: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
