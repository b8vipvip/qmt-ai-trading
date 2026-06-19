#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_signoff.models import LiveSignoffDecision
from qmt_ai_trading.live_signoff.service import build_default_live_signoff_config, run_live_signoff, run_manual_signoff, run_incident_rehearsal, save_live_signoff_report, save_manual_signoff_report, save_incident_rehearsal_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage46 read-only live signoff package.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_signoff_stage46')
    p.add_argument('--runbook-dir',default='live_runbook_stage45'); p.add_argument('--env-snapshot-dir',default='live_env_snapshot_stage44'); p.add_argument('--signature-freeze-dir',default='live_signature_freeze_stage43'); p.add_argument('--review-dir',default='live_gray_review_stage42')
    p.add_argument('--output',default='live_signoff_stage46/live_signoff.md'); p.add_argument('--json-output',default='live_signoff_stage46/live_signoff.json')
    p.add_argument('--manual-output',default='live_signoff_stage46/manual_signoff.md'); p.add_argument('--manual-json-output',default='live_signoff_stage46/manual_signoff.json')
    p.add_argument('--incident-output',default='live_signoff_stage46/incident_rehearsal.md'); p.add_argument('--incident-json-output',default='live_signoff_stage46/incident_rehearsal.json')
    a=p.parse_args(argv)
    cfg=build_default_live_signoff_config(repo_root=a.repo_root,output_dir=a.output_dir,runbook_dir=a.runbook_dir,env_snapshot_dir=a.env_snapshot_dir,signature_freeze_dir=a.signature_freeze_dir,review_dir=a.review_dir)
    report=run_live_signoff(cfg); manual=run_manual_signoff(report); inc=run_incident_rehearsal(report)
    save_live_signoff_report(report,a.output,a.json_output); save_manual_signoff_report(manual,a.manual_output,a.manual_json_output); save_incident_rehearsal_report(inc,a.incident_output,a.incident_json_output)
    print(f'Stage46 signoff decision={report.decision.value if hasattr(report.decision,"value") else report.decision}; output={a.output}; read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if report.decision==LiveSignoffDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
