#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.pre_gray_final_review.models import PreGrayFinalReviewDecision
from qmt_ai_trading.pre_gray_final_review.service import *

def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage60 pre-gray final review in read-only mode.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='pre_gray_final_review_stage60')
    p.add_argument('--live-gray-readonly-seal-dir',default='live_gray_readonly_seal_stage59'); p.add_argument('--live-gray-final-approval-dir',default='live_gray_final_approval_stage58'); p.add_argument('--live-gray-candidate-dir',default='live_gray_candidate_stage57'); p.add_argument('--real-cache-quality-dir',default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir',default='qmt_dryrun_calibration_stage55')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--material-output',default=None); p.add_argument('--material-json-output',default=None); p.add_argument('--gonogo-output',default=None); p.add_argument('--gonogo-json-output',default=None); p.add_argument('--blockers-output',default=None); p.add_argument('--blockers-json-output',default=None); p.add_argument('--conditions-output',default=None); p.add_argument('--conditions-json-output',default=None); p.add_argument('--api-plan-output',default=None); p.add_argument('--api-plan-json-output',default=None)
    a=p.parse_args(argv); out=Path(a.output_dir)
    cfg=build_default_pre_gray_final_review_config(repo_root=a.repo_root,output_dir=a.output_dir,live_gray_readonly_seal_dir=a.live_gray_readonly_seal_dir,live_gray_final_approval_dir=a.live_gray_final_approval_dir,live_gray_candidate_dir=a.live_gray_candidate_dir,real_cache_quality_dir=a.real_cache_quality_dir,qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir)
    r=run_pre_gray_final_review(cfg)
    save_pre_gray_final_review_report(r,a.output or out/'pre_gray_final_review.md',a.json_output or out/'pre_gray_final_review.json')
    save_material_recheck_report(run_material_recheck(r),a.material_output or out/'material_recheck.md',a.material_json_output or out/'material_recheck.json')
    save_go_no_go_draft_report(run_go_no_go_draft(r),a.gonogo_output or out/'go_no_go_draft.md',a.gonogo_json_output or out/'go_no_go_draft.json')
    save_no_go_blocker_report(run_no_go_blocker_report(r),a.blockers_output or out/'no_go_blockers.md',a.blockers_json_output or out/'no_go_blockers.json')
    save_go_condition_report(run_go_condition_report(r),a.conditions_output or out/'go_conditions.md',a.conditions_json_output or out/'go_conditions.json')
    save_stage61_api_gateway_plan_report(run_stage61_api_gateway_plan(r),a.api_plan_output or out/'stage61_api_gateway_plan.md',a.api_plan_json_output or out/'stage61_api_gateway_plan.json')
    print(f'Stage60 pre-gray final review package written: {out} decision={r.decision.value} go_no_go={r.go_no_go_decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==PreGrayFinalReviewDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
