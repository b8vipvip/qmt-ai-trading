#!/usr/bin/env python
"""Generate read-only Agent Research memo from local files."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.agent.formatters import format_agent_research_memo_json, format_agent_research_memo_markdown
from qmt_ai_trading.agent.service import run_agent_research_from_files
from qmt_ai_trading.agent.summarizer import AgentSummarizerConfig

def main(argv=None)->int:
    p=argparse.ArgumentParser(description="Run Stage 29 read-only Agent Research.")
    p.add_argument("--pipeline-report"); p.add_argument("--monitoring-report"); p.add_argument("--long-backtest-json"); p.add_argument("--portfolio-plan-json")
    p.add_argument("--output", default="agent_reports/agent_research.md"); p.add_argument("--json-output", default=None)
    p.add_argument("--mode", default="local_rules", choices=["mock","local_rules","external_llm_disabled"])
    p.add_argument("--include-monitoring", action="store_true", default=False); p.add_argument("--include-backtest", action="store_true", default=False); p.add_argument("--include-human-checklist", action="store_true", default=False); p.add_argument("--strict", action="store_true")
    a=p.parse_args(argv)
    cfg=AgentSummarizerConfig(mode=a.mode, include_monitoring=a.include_monitoring, include_backtest=a.include_backtest, include_human_checklist=a.include_human_checklist)
    memo=run_agent_research_from_files(a.pipeline_report,a.monitoring_report,a.long_backtest_json,a.portfolio_plan_json,config=cfg)
    out=Path(a.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(format_agent_research_memo_markdown(memo),encoding="utf-8")
    if a.json_output:
        jout=Path(a.json_output); jout.parent.mkdir(parents=True, exist_ok=True); jout.write_text(format_agent_research_memo_json(memo),encoding="utf-8")
    print(f"Agent Research memo written: {out}")
    if a.json_output: print(f"Agent Research JSON written: {a.json_output}")
    print(memo.message)
    return 0 if memo.success or not a.strict else 1
if __name__=="__main__": raise SystemExit(main())
