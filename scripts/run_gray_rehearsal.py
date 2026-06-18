#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.gray_rehearsal.safety import build_default_gray_rehearsal_config, contains_forbidden_gray_rehearsal_action
from qmt_ai_trading.gray_rehearsal.service import run_gray_rehearsal_from_files, save_gray_rehearsal_report
from qmt_ai_trading.gray_rehearsal.formatters import format_gray_rehearsal_report_markdown

def main(argv=None):
    raw=" ".join(argv or sys.argv[1:])
    if contains_forbidden_gray_rehearsal_action(raw):
        print("Forbidden live/send/order argument detected for gray rehearsal.", file=sys.stderr); return 2
    p=argparse.ArgumentParser(description="Run Stage 35 gray rehearsal in dry-run/local-file mode.")
    for a in ["pipeline-report","monitoring-report","data-quality-report","agent-memo","live-gray-report","notification-dry-run-report","dashboard-path","allowed-symbols","output","json-output"]: p.add_argument("--"+a, default=None)
    p.add_argument("--max-total-capital", type=float, default=5000.0); p.add_argument("--max-single-order-value", type=float, default=1000.0); p.add_argument("--strict", action="store_true")
    args=p.parse_args(argv)
    cfg=build_default_gray_rehearsal_config(allowed_symbols=[x.strip() for x in (args.allowed_symbols or "").split(",") if x.strip()], max_total_capital=args.max_total_capital, max_single_order_value=args.max_single_order_value, metadata={"entrypoint":"run_gray_rehearsal.py"})
    report=run_gray_rehearsal_from_files(pipeline_report=args.pipeline_report, monitoring_report=args.monitoring_report, data_quality_report=args.data_quality_report, agent_memo=args.agent_memo, live_gray_report=args.live_gray_report, notification_dry_run_report=args.notification_dry_run_report, dashboard_path=args.dashboard_path, config=cfg)
    if args.output: save_gray_rehearsal_report(report,args.output)
    if args.json_output: save_gray_rehearsal_report(report,args.json_output)
    print(format_gray_rehearsal_report_markdown(report))
    return 1 if args.strict and getattr(report.decision,"value",report.decision)=="FAIL" else 0
if __name__=="__main__": raise SystemExit(main())
