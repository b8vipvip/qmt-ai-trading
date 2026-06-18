from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.live_manual_prep.formatters import format_live_manual_prep_package_markdown
from qmt_ai_trading.live_manual_prep.safety import assert_no_live_execution_flags, build_default_live_manual_prep_config
from qmt_ai_trading.live_manual_prep.service import run_live_manual_prep_package_from_files, save_live_manual_prep_package

def _symbols(s): return [x.strip() for x in (s or "").split(",") if x.strip()]
def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv); assert_no_live_execution_flags(" ".join(argv))
    p=argparse.ArgumentParser(description="Generate preparation-only Live Manual Approval Prep package.")
    for a in ["gray-decision-package","live-gray-report","gray-rehearsal-report","live-readiness-audit-report","pipeline-report","approval-file","paper-report","monitoring-report","data-quality-report","agent-memo","notification-dry-run-report","dashboard-path","final-acceptance-report"]: p.add_argument(f"--{a}")
    p.add_argument("--allowed-symbols",default=""); p.add_argument("--max-total-capital",type=float,default=5000.0); p.add_argument("--max-single-order-value",type=float,default=1000.0); p.add_argument("--max-symbol-weight",type=float,default=0.1); p.add_argument("--max-portfolio-weight",type=float,default=0.2)
    p.add_argument("--operator-name",default=""); p.add_argument("--reviewer-name",default=""); p.add_argument("--risk-owner-name",default=""); p.add_argument("--output"); p.add_argument("--json-output"); p.add_argument("--strict",action="store_true")
    ns=p.parse_args(argv)
    cfg=build_default_live_manual_prep_config(allowed_symbols=_symbols(ns.allowed_symbols), max_total_capital=ns.max_total_capital, max_single_order_value=ns.max_single_order_value, max_symbol_weight=ns.max_symbol_weight, max_portfolio_weight=ns.max_portfolio_weight, operator_name=ns.operator_name, reviewer_name=ns.reviewer_name, risk_owner_name=ns.risk_owner_name)
    keys={k:getattr(ns,k) for k in vars(ns) if k in {"gray_decision_package","live_gray_report","gray_rehearsal_report","live_readiness_audit_report","pipeline_report","approval_file","paper_report","monitoring_report","data_quality_report","agent_memo","notification_dry_run_report","dashboard_path","final_acceptance_report"}}
    pkg=run_live_manual_prep_package_from_files(config=cfg, **keys)
    if ns.output: save_live_manual_prep_package(pkg, ns.output)
    else: print(format_live_manual_prep_package_markdown(pkg))
    if ns.json_output: save_live_manual_prep_package(pkg, ns.json_output)
    return 2 if ns.strict and getattr(pkg.decision,"value",pkg.decision)=="BLOCKED" else 0
if __name__=="__main__": raise SystemExit(main())
