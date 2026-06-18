#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_env_check.formatters import format_live_env_check_report_markdown
from qmt_ai_trading.live_env_check.models import LiveEnvCheckDecision
from qmt_ai_trading.live_env_check.safety import assert_no_live_execution_flags, build_default_live_env_check_config
from qmt_ai_trading.live_env_check.service import run_live_env_check_from_files, save_live_env_check_report

def main(argv=None):
    if argv is None: argv=sys.argv[1:]
    joined=" ".join(argv)
    if "--live-enabled" in argv or "--execute-live" in argv or "real-send" in joined:
        print("Forbidden live execution argument detected.", file=sys.stderr); return 2
    assert_no_live_execution_flags(joined.replace("run_live_env_check.py", ""))
    p=argparse.ArgumentParser(description="Generate Stage 38 read-only live environment check report.")
    for name in ["scheduler-preview-file","dashboard-path","notification-dry-run-report","data-quality-report","agent-memo","live-manual-prep-package","gray-decision-package","pipeline-report","final-acceptance-report"]: p.add_argument(f"--{name}", default=None)
    p.add_argument("--allowed-symbols", default=""); p.add_argument("--max-total-capital", type=float, default=5000.0); p.add_argument("--max-single-order-value", type=float, default=1000.0); p.add_argument("--max-symbol-weight", type=float, default=0.1); p.add_argument("--max-portfolio-weight", type=float, default=0.2); p.add_argument("--operator-name", default=""); p.add_argument("--reviewer-name", default=""); p.add_argument("--output", default=None); p.add_argument("--json-output", default=None); p.add_argument("--strict", action="store_true")
    a=p.parse_args(argv)
    cfg=build_default_live_env_check_config(allowed_symbols=[x.strip() for x in a.allowed_symbols.split(',') if x.strip()], max_total_capital=a.max_total_capital, max_single_order_value=a.max_single_order_value, max_symbol_weight=a.max_symbol_weight, max_portfolio_weight=a.max_portfolio_weight, operator_name=a.operator_name, reviewer_name=a.reviewer_name)
    report=run_live_env_check_from_files(repo_root=ROOT, config=cfg, scheduler_preview_file=a.scheduler_preview_file, dashboard_path=a.dashboard_path, notification_dry_run_report=a.notification_dry_run_report, data_quality_report=a.data_quality_report, agent_memo=a.agent_memo, live_manual_prep_package=a.live_manual_prep_package, gray_decision_package=a.gray_decision_package, pipeline_report=a.pipeline_report, final_acceptance_report=a.final_acceptance_report)
    if a.output: save_live_env_check_report(report, a.output)
    if a.json_output: save_live_env_check_report(report, a.json_output)
    print(format_live_env_check_report_markdown(report))
    return 3 if a.strict and report.decision==LiveEnvCheckDecision.BLOCKED else 0
if __name__ == "__main__": raise SystemExit(main())
