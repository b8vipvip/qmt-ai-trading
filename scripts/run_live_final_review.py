#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_final_review.models import LiveFinalReviewDecision as D
from qmt_ai_trading.live_final_review.service import build_default_live_final_review_config, run_evidence_gap_report, run_live_final_review, run_next_readonly_plan, run_signature_verification, save_evidence_gap_report, save_live_final_review_report, save_next_readonly_plan_report, save_signature_verification_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage47 final read-only go/no-go review materials.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_final_review_stage47')
    p.add_argument('--signoff-dir',default='live_signoff_stage46'); p.add_argument('--runbook-dir',default='live_runbook_stage45'); p.add_argument('--env-snapshot-dir',default='live_env_snapshot_stage44'); p.add_argument('--signature-freeze-dir',default='live_signature_freeze_stage43')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--signature-output',default=None); p.add_argument('--signature-json-output',default=None); p.add_argument('--gap-output',default=None); p.add_argument('--gap-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); out=Path(a.output_dir)
    cfg=build_default_live_final_review_config(repo_root=a.repo_root, output_dir=a.output_dir, signoff_dir=a.signoff_dir, runbook_dir=a.runbook_dir, env_snapshot_dir=a.env_snapshot_dir, signature_freeze_dir=a.signature_freeze_dir)
    report=run_live_final_review(cfg); sig=run_signature_verification(report); gap=run_evidence_gap_report(report); plan=run_next_readonly_plan(report)
    save_live_final_review_report(report, a.output or out/'live_final_review.md', a.json_output or out/'live_final_review.json')
    save_signature_verification_report(sig, a.signature_output or out/'signature_verification.md', a.signature_json_output or out/'signature_verification.json')
    save_evidence_gap_report(gap, a.gap_output or out/'evidence_gap_report.md', a.gap_json_output or out/'evidence_gap_report.json')
    save_next_readonly_plan_report(plan, a.plan_output or out/'next_readonly_plan.md', a.plan_json_output or out/'next_readonly_plan.json')
    print(f'Stage47 final read-only review package written to {out}; decision={report.decision.value if hasattr(report.decision,"value") else report.decision}; read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if report.decision==D.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
