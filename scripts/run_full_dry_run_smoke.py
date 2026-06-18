#!/usr/bin/env python
"""Run Stage 32 full dry-run smoke chain. No live flag, no QMT trading API, no xttrader."""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def _run(cmd:list[str])->dict:
    text=" ".join(cmd)
    if "--live-enabled" in text:
        return {"command": text, "returncode": 98, "success": False, "stdout":"", "stderr":"forbidden --live-enabled detected"}
    p=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    return {"command": text, "returncode": p.returncode, "success": p.returncode==0, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}

def main(argv=None)->int:
    ap=argparse.ArgumentParser(description="Run full dry-run smoke chain for Stage 32.")
    ap.add_argument("--cache-root", default="market_data_test_stage32"); ap.add_argument("--output-dir", default="smoke_reports_stage32"); ap.add_argument("--strict", action="store_true")
    a=ap.parse_args(argv); out=ROOT/a.output_dir; out.mkdir(parents=True, exist_ok=True)
    py=sys.executable
    cmds=[
        [py,"scripts/warmup_etf_universe.py","--provider","mock","--cache-root",a.cache_root,"--lookback-days","40","--frequency","1d"],
        [py,"scripts/run_daily_pipeline.py","--data-source-mode","cached_real_first","--cache-root",a.cache_root,"--allow-mock-fallback","--use-cached-research","--enable-portfolio-plan","--enable-monitoring","--monitoring-output-dir",str(out/"monitoring"),"--monitoring-dry-run-alerts","--enable-agent-research","--agent-research-output-dir",str(out/"agent"),"--agent-research-mode","local_rules","--enable-live-gray-readiness","--live-gray-output-dir",str(out/"live_gray"),"--live-gray-allowed-symbols","510300.SH,510500.SH","--build-dashboard","--dashboard-output",str(out/"dashboard.html"),"--dashboard-title","Stage 32 Dry Run Dashboard"],
        [py,"scripts/run_monitoring_check.py","--output",str(out/"monitoring_check.md"),"--json-output",str(out/"monitoring_check.json"),"--dry-run-alerts"],
        [py,"scripts/run_agent_research.py","--output",str(out/"agent_research.md"),"--json-output",str(out/"agent_research.json"),"--mode","local_rules","--include-monitoring","--include-backtest","--include-human-checklist"],
        [py,"scripts/run_live_gray_readiness.py","--output",str(out/"live_gray_readiness.md"),"--json-output",str(out/"live_gray_readiness.json"),"--allowed-symbols","510300.SH,510500.SH"],
        [py,"scripts/build_dashboard.py","--output",str(out/"dashboard_final.html"),"--report-dir",str(out),"--monitoring-dir",str(out/"monitoring"),"--agent-dir",str(out/"agent"),"--live-gray-dir",str(out/"live_gray")],
        [py,"scripts/run_final_acceptance.py","--output",str(out/"final_acceptance.md"),"--json-output",str(out/"final_acceptance.json")],
    ]
    results=[_run(c) for c in cmds]
    success=all(r["success"] for r in results)
    summary={"created_at":datetime.now(timezone.utc).isoformat(),"success":success,"safety_note":"Dry-run smoke only. It does not enable live trading, submit orders, call xttrader, or call QMT trading APIs.","steps":results}
    (out/"smoke_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Stage 32 Full Dry Run Smoke Summary","",f"- Success: `{success}`","- Safety: dry-run only; no live trading, no order submission, no xttrader, no QMT trading APIs.","","## Steps"]
    for i,r in enumerate(results,1): lines.append(f"{i}. `{r['command']}` => `{r['returncode']}`")
    (out/"smoke_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print((out/"smoke_summary.md").read_text(encoding="utf-8"))
    return 1 if a.strict and not success else 0
if __name__=="__main__": raise SystemExit(main())
