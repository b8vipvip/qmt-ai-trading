#!/usr/bin/env python
"""Preview or delete the Windows Task Scheduler daily dry-run pipeline task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.scheduler.windows_task import unregister_windows_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unregister QMT AI Trading daily dry-run pipeline task.")
    parser.add_argument("--task-name", default="QmtAiTradingDailyDryRun")
    parser.add_argument("--execute", action="store_true", help="Actually call schtasks /Delete. Omit for dry-run preview only.")
    args = parser.parse_args(argv)

    result = unregister_windows_task(args.task_name, project_root=ROOT, dry_run=not args.execute)
    print("Windows Task Scheduler deletion preview")
    print(f"Task name: {args.task_name}")
    print(f"Command: {result.command.metadata.get('display', '')}")
    print(f"Result: {result.message}")
    if result.dry_run:
        print("DRY-RUN ONLY: no task deleted. Re-run with --execute to delete on Windows.")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
