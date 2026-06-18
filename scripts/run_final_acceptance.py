#!/usr/bin/env python
"""Run Stage 32 final acceptance checks. Read-only; no trading."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.acceptance.formatters import format_acceptance_report_markdown
from qmt_ai_trading.acceptance.service import run_final_acceptance_check, save_acceptance_report

def main(argv=None)->int:
    p=argparse.ArgumentParser(description="Run final acceptance dry-run/read-only checks.")
    p.add_argument("--output", default=None); p.add_argument("--json-output", default=None); p.add_argument("--strict", action="store_true")
    a=p.parse_args(argv)
    r=run_final_acceptance_check(ROOT)
    if a.output: save_acceptance_report(r,a.output); print(f"Acceptance Markdown written: {a.output}")
    if a.json_output: save_acceptance_report(r,a.json_output); print(f"Acceptance JSON written: {a.json_output}")
    if not a.output: print(format_acceptance_report_markdown(r))
    return 1 if a.strict and not r.success else 0
if __name__=="__main__": raise SystemExit(main())
