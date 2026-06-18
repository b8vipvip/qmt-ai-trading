from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.qmt_quality import QmtDataAvailabilityStatus, build_qmt_quality_report, format_qmt_quality_report_json, format_qmt_quality_report_markdown


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check local QMT cache quality only; no QMT fetch, no xttrader.")
    p.add_argument("--symbols", default="510300.SH")
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-01-10")
    p.add_argument("--frequency", default="1d")
    p.add_argument("--cache-root", default="market_data_qmt_stage24")
    p.add_argument("--report-dir", default="qmt_data_quality_reports")
    p.add_argument("--write-json", action="store_true")
    p.add_argument("--min-bars", type=int, default=1)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    store = LocalBarStore(args.cache_root)
    report_dir = Path(args.report_dir); report_dir.mkdir(parents=True, exist_ok=True)
    combined = ["# QMT Cache Quality Summary", "", "| symbol | decision | bar_count | missing_ohlc | duplicate | zero_volume | sorted |", "|---|---:|---:|---:|---:|---:|---:|"]
    for symbol in symbols:
        result = store.query_bars(BarQuery([symbol], args.start, args.end, frequency=args.frequency))
        msg = "cache hit" if result.hit else "SKIP/WARN: cache unavailable or does not cover requested range"
        report = build_qmt_quality_report(symbol=symbol, frequency=args.frequency, start_date=args.start, end_date=args.end, provider="local_cache", cache_root=args.cache_root, bars=result.bars, xtdata_available=QmtDataAvailabilityStatus.SKIPPED, qmt_available=QmtDataAvailabilityStatus.SKIPPED, cache_hit_after_save=bool(result.hit and result.bars), message=msg, min_bars=args.min_bars)
        decision = report.decision.value if hasattr(report.decision, "value") else report.decision
        print(f"{symbol}: decision={decision} bar_count={report.normalized_bar_count} missing={report.missing_ohlc_count} duplicate={report.duplicate_datetime_count} zero_volume={report.zero_volume_count} sorted={report.sorted_by_datetime}")
        combined.append(f"| {symbol} | {decision} | {report.normalized_bar_count} | {report.missing_ohlc_count} | {report.duplicate_datetime_count} | {report.zero_volume_count} | {report.sorted_by_datetime} |")
        (report_dir / f"{symbol}.{args.frequency}.qmt_quality.md").write_text(format_qmt_quality_report_markdown(report), encoding="utf-8")
        if args.write_json:
            (report_dir / f"{symbol}.{args.frequency}.qmt_quality.json").write_text(format_qmt_quality_report_json(report), encoding="utf-8")
    (report_dir / "qmt_cache_quality_summary.md").write_text("\n".join(combined) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
