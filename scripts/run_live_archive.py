#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_archive.models import LiveArchiveDecision as D
from qmt_ai_trading.live_archive.service import build_default_live_archive_config, run_live_archive, save_live_archive_report, run_evidence_remediation, save_evidence_remediation_report, run_human_verification_summary, save_human_verification_summary_report, run_next_readonly_check, save_next_readonly_check_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage48 final read-only archive materials.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_archive_stage48')
    p.add_argument('--final-review-dir',default='live_final_review_stage47'); p.add_argument('--signoff-dir',default='live_signoff_stage46'); p.add_argument('--runbook-dir',default='live_runbook_stage45'); p.add_argument('--env-snapshot-dir',default='live_env_snapshot_stage44')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--remediation-output',default=None); p.add_argument('--remediation-json-output',default=None); p.add_argument('--human-output',default=None); p.add_argument('--human-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); out=Path(a.output_dir)
    cfg=build_default_live_archive_config(repo_root=a.repo_root, output_dir=a.output_dir, final_review_dir=a.final_review_dir, signoff_dir=a.signoff_dir, runbook_dir=a.runbook_dir, env_snapshot_dir=a.env_snapshot_dir)
    report=run_live_archive(cfg); rem=run_evidence_remediation(report); human=run_human_verification_summary(report); plan=run_next_readonly_check(report)
    save_live_archive_report(report, a.output or out/'live_archive.md', a.json_output or out/'live_archive.json')
    save_evidence_remediation_report(rem, a.remediation_output or out/'evidence_remediation_plan.md', a.remediation_json_output or out/'evidence_remediation_plan.json')
    save_human_verification_summary_report(human, a.human_output or out/'human_verification_summary.md', a.human_json_output or out/'human_verification_summary.json')
    save_next_readonly_check_report(plan, a.plan_output or out/'next_readonly_check_plan.md', a.plan_json_output or out/'next_readonly_check_plan.json')
    print(f'Stage48 final read-only archive package written to {out}; decision={report.decision.value if hasattr(report.decision,"value") else report.decision}; read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if report.decision==D.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
