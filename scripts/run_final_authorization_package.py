from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.final_authorization.formatters import format_final_authorization_package_markdown
from qmt_ai_trading.final_authorization.models import FinalAuthorizationDecision
from qmt_ai_trading.final_authorization.safety import assert_no_live_execution_flags, build_default_final_authorization_config
from qmt_ai_trading.final_authorization.service import run_final_authorization_package_from_files, save_final_authorization_package

def _symbols(s): return [x.strip() for x in (s or "").split(',') if x.strip()]
def main(argv=None):
    raw=" ".join(argv if argv is not None else sys.argv[1:])
    try: assert_no_live_execution_flags(raw.replace("run_final_authorization_package.py", ""))
    except ValueError as exc: print(str(exc), file=sys.stderr); return 2
    p=argparse.ArgumentParser(description="Generate review-only final authorization package.")
    for a in ["live-env-check-report","live-manual-prep-package","gray-decision-package","gray-rehearsal-report","live-gray-report","live-readiness-audit-report","pipeline-report","approval-file","paper-report","monitoring-report","data-quality-report","agent-memo","notification-dry-run-report","dashboard-path","final-acceptance-report"]: p.add_argument(f"--{a}")
    p.add_argument("--allowed-symbols", default=""); p.add_argument("--max-total-capital", type=float, default=5000.0); p.add_argument("--max-single-order-value", type=float, default=1000.0); p.add_argument("--max-symbol-weight", type=float, default=0.1); p.add_argument("--max-portfolio-weight", type=float, default=0.2)
    p.add_argument("--operator-name", default=""); p.add_argument("--reviewer-name", default=""); p.add_argument("--risk-owner-name", default=""); p.add_argument("--final-approver-name", default=""); p.add_argument("--output"); p.add_argument("--json-output"); p.add_argument("--strict", action="store_true")
    ns=p.parse_args(argv)
    cfg=build_default_final_authorization_config(allowed_symbols=_symbols(ns.allowed_symbols), max_total_capital=ns.max_total_capital, max_single_order_value=ns.max_single_order_value, max_symbol_weight=ns.max_symbol_weight, max_portfolio_weight=ns.max_portfolio_weight, operator_name=ns.operator_name, reviewer_name=ns.reviewer_name, risk_owner_name=ns.risk_owner_name, final_approver_name=ns.final_approver_name)
    keys={k:getattr(ns,k) for k in vars(ns) if k in {"live_env_check_report","live_manual_prep_package","gray_decision_package","gray_rehearsal_report","live_gray_report","live_readiness_audit_report","pipeline_report","approval_file","paper_report","monitoring_report","data_quality_report","agent_memo","notification_dry_run_report","dashboard_path","final_acceptance_report"}}
    pkg=run_final_authorization_package_from_files(config=cfg, **keys)
    if ns.output: save_final_authorization_package(pkg, ns.output)
    if ns.json_output: save_final_authorization_package(pkg, ns.json_output)
    print(format_final_authorization_package_markdown(pkg))
    return 1 if ns.strict and getattr(pkg.decision,"value",pkg.decision)==FinalAuthorizationDecision.BLOCKED.value else 0
if __name__=="__main__": raise SystemExit(main())
