#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_lock_consistency.models import LiveLockConsistencyDecision
from qmt_ai_trading.live_lock_consistency.service import *
def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage52 final read-only lock review and archive consistency check.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_lock_consistency_stage52')
    p.add_argument('--archive-lock-dir',default='live_archive_lock_stage51'); p.add_argument('--final-archive-dir',default='live_final_archive_stage50'); p.add_argument('--consistency-dir',default='live_consistency_stage49'); p.add_argument('--archive-dir',default='live_archive_stage48')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--archive-output',default=None); p.add_argument('--archive-json-output',default=None); p.add_argument('--human-output',default=None); p.add_argument('--human-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); od=Path(a.output_dir)
    cfg=build_default_live_lock_consistency_config(repo_root=a.repo_root,output_dir=a.output_dir,archive_lock_dir=a.archive_lock_dir,final_archive_dir=a.final_archive_dir,consistency_dir=a.consistency_dir,archive_dir=a.archive_dir)
    r=run_live_lock_consistency(cfg); ac=run_archive_consistency(r); h=run_human_closure_recheck(r); n=run_next_readonly_check(r)
    save_live_lock_consistency_report(r,a.output or od/'live_lock_consistency.md',a.json_output or od/'live_lock_consistency.json')
    save_archive_consistency_report(ac,a.archive_output or od/'archive_consistency.md',a.archive_json_output or od/'archive_consistency.json')
    save_human_closure_recheck_report(h,a.human_output or od/'human_closure_recheck.md',a.human_json_output or od/'human_closure_recheck.json')
    save_next_readonly_check_report(n,a.plan_output or od/'next_readonly_check_plan.md',a.plan_json_output or od/'next_readonly_check_plan.json')
    print(f'Stage52 decision={r.decision}; output_dir={od}; read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LiveLockConsistencyDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
