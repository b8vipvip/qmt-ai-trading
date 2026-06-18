#!/usr/bin/env python
"""Run the Stage 23 static live-readiness audit."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.audit.formatters import format_audit_report_json, format_audit_report_markdown
from qmt_ai_trading.audit.service import build_live_readiness_policy, run_live_readiness_audit, save_audit_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run static go/no-go live-readiness audit. Does not call QMT, xttrader, or order APIs.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--json-output")
    parser.add_argument("--allow-go", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when the audit decision is NO_GO.")
    args = parser.parse_args(argv)

    policy = build_live_readiness_policy(allow_go=bool(args.allow_go))
    report = run_live_readiness_audit(args.project_root, policy=policy)
    markdown = format_audit_report_markdown(report)
    if args.output:
        save_audit_report(report, args.output)
    else:
        print(markdown)
    if args.json_output:
        path = Path(args.json_output); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(format_audit_report_json(report), encoding="utf-8")
    if args.strict and str(report.decision) != "GoNoGoDecision.GO" and getattr(report.decision, "value", report.decision) != "GO":
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
