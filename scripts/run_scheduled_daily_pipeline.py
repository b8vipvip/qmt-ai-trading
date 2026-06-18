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
from qmt_ai_trading.datahub.universe_warmup import build_universe_warmup_request, format_universe_warmup_result, warmup_etf_universe_history
from scripts.run_daily_pipeline import main as run_daily_pipeline_main


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scheduled dry-run daily pipeline with optional historical cache warmup.")
    parser.add_argument("--warmup-cache", action="store_true", help="Warm historical bar cache before running the dry-run pipeline.")
    parser.add_argument("--warmup-universe", action="store_true", help="Warm ETF universe historical cache before running the dry-run pipeline.")
    parser.add_argument("--universe-name", default="default_etf")
    parser.add_argument("--universe-lookback-days", type=int, default=None)
    parser.add_argument("--universe-lookback-years", type=int, default=None)
    parser.add_argument("--warmup-provider", default="mock", choices=["mock", "qmt"], help="Historical provider for cache warmup.")
    parser.add_argument("--warmup-start", default=None, help="Warmup start date, e.g. 2024-01-01.")
    parser.add_argument("--warmup-end", default=None, help="Warmup end date, e.g. 2024-01-10.")
    parser.add_argument("--warmup-frequency", default="1d")
    parser.add_argument("--cache-root", default="market_data")
    parser.add_argument("--warmup-fail-fast", action="store_true")
    parser.add_argument("--use-cached-research", action="store_true", help="Pass cached Research mode to the daily pipeline.")
    parser.add_argument("--research-start", default=None)
    parser.add_argument("--research-end", default=None)
    parser.add_argument("--research-frequency", default="1d")
    parser.add_argument("--min-bars", type=int, default=20)
    parser.add_argument("--cached-strategy-top-n", type=int, default=1)
    parser.add_argument("--cached-strategy-min-score", type=float, default=None)
    parser.add_argument("--cached-strategy-min-bars", type=int, default=20)
    known, pipeline_args = parser.parse_known_args(argv)
    known.pipeline_args = pipeline_args
    return known


def main(argv: list[str] | None = None) -> int:
    parsed = _parse_args(argv)
    log_dir = ROOT / "logs" / "daily_pipeline"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"daily_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    args = list(parsed.pipeline_args or ["--write-reports", "--report-dir", "reports", "--notify-dry-run"])
    if parsed.use_cached_research:
        args.append("--use-cached-research")
        args.extend(["--cache-root", parsed.cache_root])
        if parsed.research_start:
            args.extend(["--research-start", parsed.research_start])
        if parsed.research_end:
            args.extend(["--research-end", parsed.research_end])
        args.extend(["--research-frequency", parsed.research_frequency, "--min-bars", str(parsed.min_bars)])
        args.extend(["--cached-strategy-top-n", str(parsed.cached_strategy_top_n), "--cached-strategy-min-bars", str(parsed.cached_strategy_min_bars)])
        if parsed.cached_strategy_min_score is not None:
            args.extend(["--cached-strategy-min-score", str(parsed.cached_strategy_min_score)])
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("QMT AI Trading scheduled dry-run pipeline\n")
        log_file.write(f"Started at: {datetime.now().isoformat()}\n")
        log_file.write(f"Arguments: {' '.join(args)}\n\n")
        try:
            with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
                if parsed.warmup_universe:
                    request = build_universe_warmup_request(
                        universe_name=parsed.universe_name,
                        start_date=parsed.warmup_start,
                        end_date=parsed.warmup_end,
                        lookback_days=parsed.universe_lookback_days,
                        lookback_years=parsed.universe_lookback_years,
                        frequency=parsed.warmup_frequency,
                        provider=parsed.warmup_provider,
                        cache_root=parsed.cache_root,
                        fail_fast=parsed.warmup_fail_fast,
                        metadata={"entrypoint": "run_scheduled_daily_pipeline", "mode": "universe"},
                    )
                    universe_result = warmup_etf_universe_history(request)
                    print(format_universe_warmup_result(universe_result))
                elif parsed.warmup_cache:
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
