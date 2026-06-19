#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_gap_clearance.models import LiveGapClearanceDecision
from qmt_ai_trading.live_gap_clearance.service import *
def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage54 final pre-gray gap clearance package in read-only mode.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_gap_clearance_stage54')
    p.add_argument('--archive-verification-dir',default='live_archive_verification_stage53'); p.add_argument('--lock-consistency-dir',default='live_lock_consistency_stage52'); p.add_argument('--archive-lock-dir',default='live_archive_lock_stage51'); p.add_argument('--final-archive-dir',default='live_final_archive_stage50')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--remediation-output',default=None); p.add_argument('--remediation-json-output',default=None); p.add_argument('--human-output',default=None); p.add_argument('--human-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); od=Path(a.output_dir)
    cfg=build_default_live_gap_clearance_config(repo_root=a.repo_root,output_dir=a.output_dir,archive_verification_dir=a.archive_verification_dir,lock_consistency_dir=a.lock_consistency_dir,archive_lock_dir=a.archive_lock_dir,final_archive_dir=a.final_archive_dir)
    r=run_live_gap_clearance(cfg); er=run_evidence_remediation(r); h=run_human_closure_recheck(r); n=run_next_readonly_check(r)
    save_live_gap_clearance_report(r,a.output or od/'live_gap_clearance.md',a.json_output or od/'live_gap_clearance.json')
    save_evidence_remediation_report(er,a.remediation_output or od/'evidence_remediation.md',a.remediation_json_output or od/'evidence_remediation.json')
    save_human_closure_recheck_report(h,a.human_output or od/'human_closure_recheck.md',a.human_json_output or od/'human_closure_recheck.json')
    save_next_readonly_check_report(n,a.plan_output or od/'next_readonly_check_plan.md',a.plan_json_output or od/'next_readonly_check_plan.json')
    print(f'Stage54 decision={r.decision}; output_dir={od}; read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LiveGapClearanceDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
