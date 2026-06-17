#!/usr/bin/env python
"""Scheduled-task entrypoint for the safe daily dry-run pipeline."""

from __future__ import annotations

import contextlib
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_daily_pipeline import main as run_daily_pipeline_main


def main(argv: list[str] | None = None) -> int:
    log_dir = ROOT / "logs" / "daily_pipeline"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"daily_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    args = argv if argv is not None else ["--write-reports", "--report-dir", "reports", "--notify-dry-run"]
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("QMT AI Trading scheduled dry-run pipeline\n")
        log_file.write(f"Started at: {datetime.now().isoformat()}\n")
        log_file.write(f"Arguments: {' '.join(args)}\n\n")
        try:
            with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
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
