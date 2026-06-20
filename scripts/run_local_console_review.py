from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from qmt_ai_trading.local_console.models import LocalConsoleDecision
from qmt_ai_trading.local_console.service import *
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_stage62'); p.add_argument('--api-gateway-dir',default='api_gateway_stage61'); p.add_argument('--pre-gray-final-review-dir',default='pre_gray_final_review_stage60'); p.add_argument('--readonly-seal-dir',default='live_gray_readonly_seal_stage59'); p.add_argument('--final-approval-dir',default='live_gray_final_approval_stage58'); p.add_argument('--gray-candidate-dir',default='live_gray_candidate_stage57'); p.add_argument('--real-cache-quality-dir',default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir',default='qmt_dryrun_calibration_stage55')
    p.add_argument('--output'); p.add_argument('--json-output'); p.add_argument('--index-output'); p.add_argument('--index-json-output'); p.add_argument('--report-list-output'); p.add_argument('--report-list-json-output'); p.add_argument('--safety-output'); p.add_argument('--safety-json-output'); p.add_argument('--plan-output'); p.add_argument('--plan-json-output')
    a=p.parse_args(argv); out=a.output_dir
    cfg=build_default_local_console_config(repo_root=a.repo_root,output_dir=out,api_gateway_dir=a.api_gateway_dir,pre_gray_final_review_dir=a.pre_gray_final_review_dir,readonly_seal_dir=a.readonly_seal_dir,final_approval_dir=a.final_approval_dir,gray_candidate_dir=a.gray_candidate_dir,real_cache_quality_dir=a.real_cache_quality_dir,qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir)
    r=run_local_console_review(cfg)
    save_local_console_report(r,a.output or f'{out}/local_console_report.md',a.json_output or f'{out}/local_console_report.json')
    save_console_index_report(build_console_index_report(cfg),a.index_output or f'{out}/console_index.md',a.index_json_output or f'{out}/console_index.json')
    save_console_report_list_report(build_console_report_list_report(cfg),a.report_list_output or f'{out}/report_list.md',a.report_list_json_output or f'{out}/report_list.json')
    save_console_safety_report(build_console_safety_report(cfg),a.safety_output or f'{out}/console_safety.md',a.safety_json_output or f'{out}/console_safety.json')
    save_next_console_detail_plan_report(build_next_console_detail_plan_report(cfg),a.plan_output or f'{out}/next_console_detail_plan.md',a.plan_json_output or f'{out}/next_console_detail_plan.json')
    print(f'Stage62 local console review decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleDecision.NO_GO else 0
if __name__=='__main__': sys.exit(main())
