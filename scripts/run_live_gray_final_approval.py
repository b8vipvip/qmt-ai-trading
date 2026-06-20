#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_gray_final_approval.models import LiveGrayFinalApprovalDecision
from qmt_ai_trading.live_gray_final_approval.service import *
def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage58 read-only final human approval package before small-money gray.')
    p.add_argument('--repo-root', default='.'); p.add_argument('--output-dir', default='live_gray_final_approval_stage58'); p.add_argument('--live-gray-candidate-dir', default='live_gray_candidate_stage57'); p.add_argument('--real-cache-quality-dir', default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir', default='qmt_dryrun_calibration_stage55')
    p.add_argument('--output', default='live_gray_final_approval_stage58/live_gray_final_approval.md'); p.add_argument('--json-output', default='live_gray_final_approval_stage58/live_gray_final_approval.json')
    p.add_argument('--capital-output', default='live_gray_final_approval_stage58/capital_position_approval.md'); p.add_argument('--capital-json-output', default='live_gray_final_approval_stage58/capital_position_approval.json')
    p.add_argument('--risk-output', default='live_gray_final_approval_stage58/risk_human_approval_review.md'); p.add_argument('--risk-json-output', default='live_gray_final_approval_stage58/risk_human_approval_review.json')
    p.add_argument('--rollback-output', default='live_gray_final_approval_stage58/rollback_circuit_approval.md'); p.add_argument('--rollback-json-output', default='live_gray_final_approval_stage58/rollback_circuit_approval.json')
    p.add_argument('--signoff-output', default='live_gray_final_approval_stage58/final_signoff_checklist.md'); p.add_argument('--signoff-json-output', default='live_gray_final_approval_stage58/final_signoff_checklist.json')
    p.add_argument('--plan-output', default='live_gray_final_approval_stage58/next_readonly_seal_plan.md'); p.add_argument('--plan-json-output', default='live_gray_final_approval_stage58/next_readonly_seal_plan.json')
    a=p.parse_args(argv)
    cfg=build_default_live_gray_final_approval_config(repo_root=a.repo_root, output_dir=a.output_dir, live_gray_candidate_dir=a.live_gray_candidate_dir, real_cache_quality_dir=a.real_cache_quality_dir, qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir)
    r=run_live_gray_final_approval(cfg)
    save_live_gray_final_approval_report(r,a.output,a.json_output); save_capital_position_approval_report(run_capital_position_approval(r),a.capital_output,a.capital_json_output); save_risk_human_approval_review_report(run_risk_human_approval_review(r),a.risk_output,a.risk_json_output); save_rollback_circuit_approval_report(run_rollback_circuit_approval(r),a.rollback_output,a.rollback_json_output); save_final_signoff_checklist_report(run_final_signoff_checklist(r),a.signoff_output,a.signoff_json_output); save_next_readonly_seal_plan_report(run_next_readonly_seal_plan(r),a.plan_output,a.plan_json_output)
    print(f'Stage58 live gray final approval package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LiveGrayFinalApprovalDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
