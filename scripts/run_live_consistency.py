#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_consistency.models import LiveConsistencyDecision
from qmt_ai_trading.live_consistency.service import *
def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage49 read-only consistency review.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='live_consistency_stage49')
    p.add_argument('--archive-dir',default='live_archive_stage48'); p.add_argument('--final-review-dir',default='live_final_review_stage47'); p.add_argument('--signoff-dir',default='live_signoff_stage46'); p.add_argument('--runbook-dir',default='live_runbook_stage45')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--material-output',default=None); p.add_argument('--material-json-output',default=None); p.add_argument('--human-output',default=None); p.add_argument('--human-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); od=Path(a.output_dir)
    cfg=build_default_live_consistency_config(repo_root=a.repo_root,output_dir=a.output_dir,archive_dir=a.archive_dir,final_review_dir=a.final_review_dir,signoff_dir=a.signoff_dir,runbook_dir=a.runbook_dir)
    r=run_live_consistency(cfg); m=run_material_consistency(r); h=run_human_recheck(r); n=run_next_gray_check(r)
    save_live_consistency_report(r,a.output or od/'live_consistency.md',a.json_output or od/'live_consistency.json')
    save_material_consistency_report(m,a.material_output or od/'material_consistency.md',a.material_json_output or od/'material_consistency.json')
    save_human_recheck_report(h,a.human_output or od/'human_recheck.md',a.human_json_output or od/'human_recheck.json')
    save_next_gray_check_report(n,a.plan_output or od/'next_gray_check_plan.md',a.plan_json_output or od/'next_gray_check_plan.json')
    print(f'Stage49 decision={r.decision}; output_dir={od}; read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LiveConsistencyDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
