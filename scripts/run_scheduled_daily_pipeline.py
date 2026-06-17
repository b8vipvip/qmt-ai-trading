#!/usr/bin/env python
"""Scheduled-task entrypoint for the safe daily dry-run pipeline."""

from __future__ import annotations

import argparse
import contextlib
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.datahub.cache_warmup import build_default_warmup_request, format_cache_warmup_result, warmup_history_cache
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from scripts.run_daily_pipeline import main as run_daily_pipeline_main


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scheduled dry-run daily pipeline with optional historical cache warmup.")
    parser.add_argument("--warmup-cache", action="store_true", help="Warm historical bar cache before running the dry-run pipeline.")
    parser.add_argument("--warmup-provider", default="mock", choices=["mock", "qmt"], help="Historical provider for cache warmup.")
    parser.add_argument("--warmup-start", default=None, help="Warmup start date, e.g. 2024-01-01.")
    parser.add_argument("--warmup-end", default=None, help="Warmup end date, e.g. 2024-01-10.")
    parser.add_argument("--warmup-frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--warmup-fail-fast", action="store_true")
    known, pipeline_args = parser.parse_known_args(argv)
    known.pipeline_args = pipeline_args
    return known


def main(argv: list[str] | None = None) -> int:
    parsed = _parse_args(argv) if argv is not None else _parse_args([])
    log_dir = ROOT / "logs" / "daily_pipeline"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"daily_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    args = parsed.pipeline_args or ["--write-reports", "--report-dir", "reports", "--notify-dry-run"]
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("QMT AI Trading scheduled dry-run pipeline\n")
        log_file.write(f"Started at: {datetime.now().isoformat()}\n")
        log_file.write(f"Arguments: {' '.join(args)}\n\n")
        try:
            with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
                if parsed.warmup_cache:
                    if not parsed.warmup_start or not parsed.warmup_end:
                        raise ValueError("--warmup-start and --warmup-end are required when --warmup-cache is used")
                    symbols = [item.symbol for item in get_default_etf_universe()]
                    request = build_default_warmup_request(
                        symbols=symbols,
                        start_date=parsed.warmup_start,
                        end_date=parsed.warmup_end,
                        frequency=parsed.warmup_frequency,
                        provider=parsed.warmup_provider,
                        cache_root=parsed.cache_root,
                        fail_fast=parsed.warmup_fail_fast,
                        metadata={"entrypoint": "run_scheduled_daily_pipeline"},
                    )
                    warmup_result = warmup_history_cache(request)
                    print(format_cache_warmup_result(warmup_result))
                code = run_daily_pipeline_main(args)
        except Exception:
            traceback.print_exc(file=log_file)
            code = 1
        log_file.write(f"\nFinished at: {datetime.now().isoformat()}\n")
        log_file.write(f"Exit code: {code}\n")
    print(f"Scheduled dry-run pipeline finished with exit code {code}. Log: {log_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
