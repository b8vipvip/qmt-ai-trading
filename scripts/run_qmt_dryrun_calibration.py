#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.qmt_dryrun_calibration.models import QmtDryrunCalibrationDecision
from qmt_ai_trading.qmt_dryrun_calibration.service import *
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='qmt_dryrun_calibration_stage55'); p.add_argument('--gap-clearance-dir',default='live_gap_clearance_stage54'); p.add_argument('--cache-root',default='market_data_test_stage55'); p.add_argument('--provider',default='mock',choices=['mock','qmt_xtdata']); p.add_argument('--max-symbols',type=int,default=5); p.add_argument('--max-days',type=int,default=90)
    p.add_argument('--output',default='qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.md'); p.add_argument('--json-output',default='qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.json'); p.add_argument('--xtdata-output',default='qmt_dryrun_calibration_stage55/xtdata_capability.md'); p.add_argument('--xtdata-json-output',default='qmt_dryrun_calibration_stage55/xtdata_capability.json'); p.add_argument('--whitelist-output',default='qmt_dryrun_calibration_stage55/etf_whitelist_calibration.md'); p.add_argument('--whitelist-json-output',default='qmt_dryrun_calibration_stage55/etf_whitelist_calibration.json'); p.add_argument('--plan-output',default='qmt_dryrun_calibration_stage55/next_real_cache_quality_plan.md'); p.add_argument('--plan-json-output',default='qmt_dryrun_calibration_stage55/next_real_cache_quality_plan.json')
    a=p.parse_args(argv); cfg=build_default_qmt_dryrun_calibration_config(repo_root=a.repo_root,output_dir=a.output_dir,gap_clearance_dir=a.gap_clearance_dir,cache_root=a.cache_root,provider=a.provider,max_symbols=min(a.max_symbols,5),max_days=min(a.max_days,90))
    r=run_qmt_dryrun_calibration(cfg); save_qmt_dryrun_calibration_report(r,a.output,a.json_output)
    x=run_xtdata_capability_check(r); save_xtdata_capability_report(x,a.xtdata_output,a.xtdata_json_output)
    w=run_etf_whitelist_calibration(r); save_etf_whitelist_calibration_report(w,a.whitelist_output,a.whitelist_json_output)
    n=run_next_real_cache_quality_plan(r); save_next_real_cache_quality_plan_report(n,a.plan_output,a.plan_json_output)
    print(format_qmt_dryrun_calibration_report_markdown(r)); print(f"Stage55 decision={r.decision}")
    return 1 if str(r.decision)==QmtDryrunCalibrationDecision.NO_GO.value else 0
if __name__=='__main__': raise SystemExit(main())
