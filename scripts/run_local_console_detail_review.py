#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.detail_models import LocalConsoleDetailDecision
from qmt_ai_trading.local_console.detail_service import *

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_detail_stage63')
    for a,d in [('local-console-dir','local_console_stage62'),('api-gateway-dir','api_gateway_stage61'),('pre-gray-final-review-dir','pre_gray_final_review_stage60'),('readonly-seal-dir','live_gray_readonly_seal_stage59'),('final-approval-dir','live_gray_final_approval_stage58'),('gray-candidate-dir','live_gray_candidate_stage57'),('real-cache-quality-dir','real_cache_quality_stage56'),('qmt-dryrun-calibration-dir','qmt_dryrun_calibration_stage55')]: p.add_argument('--'+a,default=d)
    outs=['output','json-output','filter-output','filter-json-output','warnings-output','warnings-json-output','blocking-output','blocking-json-output','manifest-output','manifest-json-output','validation-output','validation-json-output','plan-output','plan-json-output']
    defaults=['local_console_detail_stage63/local_console_detail_report.md','local_console_detail_stage63/local_console_detail_report.json','local_console_detail_stage63/filter_index.md','local_console_detail_stage63/filter_index.json','local_console_detail_stage63/warnings.md','local_console_detail_stage63/warnings.json','local_console_detail_stage63/blocking_reasons.md','local_console_detail_stage63/blocking_reasons.json','local_console_detail_stage63/manifest_detail.md','local_console_detail_stage63/manifest_detail.json','local_console_detail_stage63/validation_detail.md','local_console_detail_stage63/validation_detail.json','local_console_detail_stage63/next_console_overview_plan.md','local_console_detail_stage63/next_console_overview_plan.json']
    for a,d in zip(outs,defaults): p.add_argument('--'+a,default=d)
    a=p.parse_args(argv)
    cfg=build_default_local_console_detail_config(repo_root=a.repo_root,output_dir=a.output_dir,local_console_dir=a.local_console_dir,api_gateway_dir=a.api_gateway_dir,pre_gray_final_review_dir=a.pre_gray_final_review_dir,readonly_seal_dir=a.readonly_seal_dir,final_approval_dir=a.final_approval_dir,gray_candidate_dir=a.gray_candidate_dir,real_cache_quality_dir=a.real_cache_quality_dir,qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir)
    report=run_local_console_detail_review(cfg)
    save_local_console_detail_report(report,a.output,a.json_output)
    save_console_filter_index_report(build_console_filter_index_report(report),a.filter_output,a.filter_json_output)
    save_console_warnings_report(build_console_warnings_report(report),a.warnings_output,a.warnings_json_output)
    save_console_blocking_reasons_report(build_console_blocking_reasons_report(report),a.blocking_output,a.blocking_json_output)
    save_console_manifest_detail_report(build_console_manifest_detail_report(report),a.manifest_output,a.manifest_json_output)
    save_console_validation_detail_report(build_console_validation_detail_report(report),a.validation_output,a.validation_json_output)
    save_next_console_overview_plan_report(build_next_console_overview_plan_report(cfg),a.plan_output,a.plan_json_output)
    print(f'Stage63 local console detail review decision={report.decision.value}')
    return 1 if report.decision==LocalConsoleDetailDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
