from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.qmt_diagnostics import inspect_qmt_runtime
from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider, QmtProviderError
from qmt_ai_trading.datahub.qmt_quality import QmtDataAvailabilityStatus, build_qmt_quality_report, check_cache_roundtrip, format_qmt_quality_report_json, format_qmt_quality_report_markdown
from qmt_ai_trading.datahub.qmt_realdata_plan import build_default_qmt_realdata_plan, format_qmt_realdata_plan, validate_qmt_realdata_plan


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 24 QMT xtdata real-data smoke test; no xttrader, no trading.")
    p.add_argument("--symbol", default="510300.SH")
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-01-10")
    p.add_argument("--frequency", default="1d")
    p.add_argument("--cache-root", default="market_data_qmt_stage24")
    p.add_argument("--report-dir", default="qmt_data_quality_reports")
    p.add_argument("--write-json", action="store_true")
    p.add_argument("--skip-fetch", action="store_true")
    p.add_argument("--strict", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_default_qmt_realdata_plan([args.symbol], args.start, args.end, args.frequency, cache_root=args.cache_root, report_dir=args.report_dir, strict=args.strict)
    plan_checks = validate_qmt_realdata_plan(plan)
    print(format_qmt_realdata_plan(plan))
    runtime = inspect_qmt_runtime(try_connect=False)
    print(f"xtdata_available={runtime.xtdata_available}")
    print(f"qmt_connect_status={runtime.qmt_connect_status}")
    report_dir = Path(args.report_dir); report_dir.mkdir(parents=True, exist_ok=True)
    store = LocalBarStore(args.cache_root)
    bars = []
    cache_hit = False
    qmt_status = QmtDataAvailabilityStatus.SKIPPED
    xt_status = QmtDataAvailabilityStatus.AVAILABLE if runtime.xtdata_available else QmtDataAvailabilityStatus.UNAVAILABLE
    message = ""
    if args.skip_fetch:
        cache_hit, bars, msg = check_cache_roundtrip(store, symbol=args.symbol, frequency=args.frequency, start_date=args.start, end_date=args.end)
        message = f"SKIPPED fetch; existing cache roundtrip: {msg}"
        print(message)
    elif not runtime.xtdata_available:
        message = "UNAVAILABLE: xtquant.xtdata is not available. Re-run inside MiniQMT Python environment with xtquant installed and MiniQMT running."
        print(message)
    else:
        try:
            provider = QmtHistoricalDataProvider()
            bars = provider.fetch_bars(BarQuery([args.symbol], args.start, args.end, frequency=args.frequency, provider="qmt"))
            cache_hit, bars, msg = check_cache_roundtrip(store, symbol=args.symbol, frequency=args.frequency, start_date=args.start, end_date=args.end, bars=bars, provider="qmt")
            qmt_status = QmtDataAvailabilityStatus.AVAILABLE
            message = f"AVAILABLE: fetched {len(bars)} bars; cache roundtrip {msg}"
            print(message)
        except QmtProviderError as exc:
            qmt_status = QmtDataAvailabilityStatus.UNAVAILABLE
            message = f"UNAVAILABLE: {exc}"
            print(message)
        except Exception as exc:
            qmt_status = QmtDataAvailabilityStatus.ERROR
            message = f"ERROR: {exc}"
            print(message)
            if args.strict:
                raise
    report = build_qmt_quality_report(symbol=args.symbol, frequency=args.frequency, start_date=args.start, end_date=args.end, provider="qmt", cache_root=args.cache_root, bars=bars, xtdata_available=xt_status, qmt_available=qmt_status, cache_hit_after_save=cache_hit, checks=plan_checks, message=message, metadata={"runtime": runtime.__dict__, "skip_fetch": args.skip_fetch})
    md = format_qmt_quality_report_markdown(report)
    md_path = report_dir / f"{args.symbol}.{args.frequency}.qmt_quality.md"
    md_path.write_text(md, encoding="utf-8")
    print(md)
    if args.write_json:
        (report_dir / f"{args.symbol}.{args.frequency}.qmt_quality.json").write_text(format_qmt_quality_report_json(report), encoding="utf-8")
    return 1 if args.strict and (not runtime.xtdata_available or str(report.decision) in {"QmtCacheQualityStatus.FAIL", "FAIL"}) else 0

if __name__ == "__main__":
    raise SystemExit(main())
