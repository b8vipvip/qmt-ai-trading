#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.gray_decision.safety import build_default_gray_decision_config, contains_forbidden_gray_decision_action
from qmt_ai_trading.gray_decision.service import run_gray_decision_package_from_files, save_gray_decision_package
from qmt_ai_trading.gray_decision.formatters import format_gray_decision_package_markdown
from qmt_ai_trading.gray_decision.models import GrayDecision

def main(argv=None):
    raw=" ".join(argv or sys.argv[1:])
    if contains_forbidden_gray_decision_action(raw): print("Forbidden live execution argument detected.", file=sys.stderr); return 2
    p=argparse.ArgumentParser()
    for a in ["pipeline-report","approval-file","paper-report","live-readiness-audit-report","monitoring-report","data-quality-report","agent-memo","live-gray-report","notification-dry-run-report","dashboard-path","gray-rehearsal-report","final-acceptance-report"]: p.add_argument("--"+a, default=None)
    p.add_argument("--allowed-symbols",default=""); p.add_argument("--max-total-capital",type=float,default=5000.0); p.add_argument("--max-single-order-value",type=float,default=1000.0); p.add_argument("--max-symbol-weight",type=float,default=0.1); p.add_argument("--max-portfolio-weight",type=float,default=0.2); p.add_argument("--operator-name",default=""); p.add_argument("--reviewer-name",default=""); p.add_argument("--output",default=None); p.add_argument("--json-output",default=None); p.add_argument("--strict",action="store_true")
    a=p.parse_args(argv)
    cfg=build_default_gray_decision_config(allowed_symbols=[x.strip() for x in a.allowed_symbols.split(',') if x.strip()], max_total_capital=a.max_total_capital, max_single_order_value=a.max_single_order_value, max_symbol_weight=a.max_symbol_weight, max_portfolio_weight=a.max_portfolio_weight, operator_name=a.operator_name, reviewer_name=a.reviewer_name, metadata={"entrypoint":"run_gray_decision_package.py"})
    pkg=run_gray_decision_package_from_files(config=cfg, pipeline_report=a.pipeline_report, approval_file=a.approval_file, paper_report=a.paper_report, live_readiness_audit_report=a.live_readiness_audit_report, monitoring_report=a.monitoring_report, data_quality_report=a.data_quality_report, agent_memo=a.agent_memo, live_gray_report=a.live_gray_report, notification_dry_run_report=a.notification_dry_run_report, dashboard_path=a.dashboard_path, gray_rehearsal_report=a.gray_rehearsal_report, final_acceptance_report=a.final_acceptance_report)
    if a.output: save_gray_decision_package(pkg,a.output)
    if a.json_output: save_gray_decision_package(pkg,a.json_output)
    print(format_gray_decision_package_markdown(pkg))
    return 1 if a.strict and pkg.decision==GrayDecision.BLOCKED else 0
if __name__=="__main__": raise SystemExit(main())
