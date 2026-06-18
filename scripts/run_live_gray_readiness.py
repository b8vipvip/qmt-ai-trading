#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.liveprep.safety import build_default_live_gray_config
from qmt_ai_trading.liveprep.service import run_live_gray_readiness_from_files, save_live_gray_readiness_report
from qmt_ai_trading.liveprep.formatters import format_live_gray_report_markdown
from qmt_ai_trading.liveprep.models import LiveGraySeverity

def main(argv=None):
    p=argparse.ArgumentParser(description="Generate Stage 30 live gray readiness preparation report only.")
    p.add_argument("--output", default=None); p.add_argument("--json-output", default=None); p.add_argument("--allowed-symbols", default="")
    p.add_argument("--max-total-capital", type=float, default=5000.0); p.add_argument("--max-single-order-value", type=float, default=1000.0); p.add_argument("--max-symbol-weight", type=float, default=0.1); p.add_argument("--max-portfolio-weight", type=float, default=0.2)
    p.add_argument("--gray-enabled", action="store_true"); p.add_argument("--live-enabled", action="store_true"); p.add_argument("--operator-name", default=""); p.add_argument("--allow-unknown-quality-for-review", action="store_true")
    for a in ["pipeline-report","approval-file","paper-report","audit-report","monitoring-report","agent-memo","quality-report"]: p.add_argument("--"+a, default=None)
    p.add_argument("--strict", action="store_true")
    a=p.parse_args(argv)
    cfg=build_default_live_gray_config(live_enabled=a.live_enabled, gray_enabled=a.gray_enabled, allowed_symbols=[x.strip() for x in a.allowed_symbols.split(',') if x.strip()], max_total_capital=a.max_total_capital, max_single_order_value=a.max_single_order_value, max_symbol_weight=a.max_symbol_weight, max_portfolio_weight=a.max_portfolio_weight, operator_name=a.operator_name, allow_unknown_quality_for_review=a.allow_unknown_quality_for_review, metadata={"entrypoint":"run_live_gray_readiness"})
    r=run_live_gray_readiness_from_files(config=cfg, pipeline_report=a.pipeline_report, approval_file=a.approval_file, paper_report=a.paper_report, audit_report=a.audit_report, monitoring_report=a.monitoring_report, agent_memo=a.agent_memo, quality_report=a.quality_report)
    if a.output: save_live_gray_readiness_report(r,a.output)
    if a.json_output: save_live_gray_readiness_report(r,a.json_output)
    print(format_live_gray_report_markdown(r))
    critical=any(getattr(c.severity,'value',c.severity)==LiveGraySeverity.CRITICAL.value for c in r.checks)
    return 2 if a.strict and critical else 0
if __name__=='__main__': raise SystemExit(main())
