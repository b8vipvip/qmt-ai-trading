#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.api_gateway.models import ApiGatewayDecision
from qmt_ai_trading.api_gateway.service import build_default_api_gateway_config, run_api_gateway_review, save_all
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='api_gateway_stage61'); p.add_argument('--pre-gray-final-review-dir',default='pre_gray_final_review_stage60'); p.add_argument('--readonly-seal-dir',default='live_gray_readonly_seal_stage59'); p.add_argument('--final-approval-dir',default='live_gray_final_approval_stage58'); p.add_argument('--gray-candidate-dir',default='live_gray_candidate_stage57'); p.add_argument('--real-cache-quality-dir',default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir',default='qmt_dryrun_calibration_stage55')
    p.add_argument('--output',default='api_gateway_stage61/api_gateway_report.md'); p.add_argument('--json-output',default='api_gateway_stage61/api_gateway_report.json'); p.add_argument('--route-output',default='api_gateway_stage61/route_index.md'); p.add_argument('--route-json-output',default='api_gateway_stage61/route_index.json'); p.add_argument('--safety-output',default='api_gateway_stage61/safety_boundary.md'); p.add_argument('--safety-json-output',default='api_gateway_stage61/safety_boundary.json'); p.add_argument('--stage-status-output',default='api_gateway_stage61/stage_status.md'); p.add_argument('--stage-status-json-output',default='api_gateway_stage61/stage_status.json'); p.add_argument('--plan-output',default='api_gateway_stage61/next_ui_dashboard_plan.md'); p.add_argument('--plan-json-output',default='api_gateway_stage61/next_ui_dashboard_plan.json')
    a=p.parse_args(argv); cfg=build_default_api_gateway_config(repo_root=a.repo_root,output_dir=a.output_dir,pre_gray_final_review_dir=a.pre_gray_final_review_dir,readonly_seal_dir=a.readonly_seal_dir,final_approval_dir=a.final_approval_dir,gray_candidate_dir=a.gray_candidate_dir,real_cache_quality_dir=a.real_cache_quality_dir,qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir)
    r=run_api_gateway_review(cfg); save_all(cfg,r,a.output,a.json_output,a.route_output,a.route_json_output,a.safety_output,a.safety_json_output,a.stage_status_output,a.stage_status_json_output,a.plan_output,a.plan_json_output); print(f'Stage61 API Gateway review decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True'); return 1 if r.decision==ApiGatewayDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
