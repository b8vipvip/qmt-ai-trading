#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_runbook.models import LiveRunbookDecision
from qmt_ai_trading.live_runbook.service import build_default_live_runbook_config, run_live_runbook, run_manual_rehearsal, run_incident_playbook, save_live_runbook_report, save_manual_rehearsal_report, save_incident_playbook_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage45 read-only live runbook package.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_runbook_stage45')
    p.add_argument('--env-snapshot-dir',default='live_env_snapshot_stage44'); p.add_argument('--signature-freeze-dir',default='live_signature_freeze_stage43'); p.add_argument('--review-dir',default='live_gray_review_stage42'); p.add_argument('--ledger-dir',default='live_gray_ledger_stage41')
    p.add_argument('--output',default='live_runbook_stage45/live_runbook.md'); p.add_argument('--json-output',default='live_runbook_stage45/live_runbook.json')
    p.add_argument('--rehearsal-output',default='live_runbook_stage45/manual_rehearsal.md'); p.add_argument('--rehearsal-json-output',default='live_runbook_stage45/manual_rehearsal.json')
    p.add_argument('--incident-output',default='live_runbook_stage45/incident_playbook.md'); p.add_argument('--incident-json-output',default='live_runbook_stage45/incident_playbook.json')
    a=p.parse_args(argv)
    cfg=build_default_live_runbook_config(repo_root=a.repo_root, output_dir=a.output_dir, env_snapshot_dir=a.env_snapshot_dir, signature_freeze_dir=a.signature_freeze_dir, review_dir=a.review_dir, ledger_dir=a.ledger_dir)
    report=run_live_runbook(cfg); reh=run_manual_rehearsal(report); inc=run_incident_playbook(report)
    save_live_runbook_report(report,a.output,a.json_output); save_manual_rehearsal_report(reh,a.rehearsal_output,a.rehearsal_json_output); save_incident_playbook_report(inc,a.incident_output,a.incident_json_output)
    print(f'Stage45 read-only live runbook package written: {a.output}')
    print(f'decision={report.decision.value if hasattr(report.decision,"value") else report.decision} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if report.decision==LiveRunbookDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
