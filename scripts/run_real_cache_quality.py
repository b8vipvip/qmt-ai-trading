#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.real_cache_quality.service import *
from qmt_ai_trading.real_cache_quality.models import RealCacheQualityDecision

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='real_cache_quality_stage56'); p.add_argument('--qmt-dryrun-calibration-dir',default='qmt_dryrun_calibration_stage55'); p.add_argument('--cache-root',default='market_data_test_stage56'); p.add_argument('--provider',default='mock',choices=['mock','qmt_xtdata']); p.add_argument('--max-symbols',type=int,default=5); p.add_argument('--min-days',type=int,default=40); p.add_argument('--target-days',type=int,default=90)
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--gapfill-output',default=None); p.add_argument('--gapfill-json-output',default=None); p.add_argument('--field-output',default=None); p.add_argument('--field-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); od=Path(a.output_dir)
    cfg=build_default_real_cache_quality_config(repo_root=a.repo_root, output_dir=a.output_dir, qmt_dryrun_calibration_dir=a.qmt_dryrun_calibration_dir, cache_root=a.cache_root, provider=a.provider, max_symbols=a.max_symbols, min_days=a.min_days, target_days=a.target_days)
    r=run_real_cache_quality(cfg); save_real_cache_quality_report(r, a.output or od/'real_cache_quality.md', a.json_output or od/'real_cache_quality.json')
    g=run_long_sample_gap_fill_plan(r); save_long_sample_gap_fill_report(g, a.gapfill_output or od/'long_sample_gap_fill.md', a.gapfill_json_output or od/'long_sample_gap_fill.json')
    f=run_field_quality_review(r); save_field_quality_review_report(f, a.field_output or od/'field_quality_review.md', a.field_json_output or od/'field_quality_review.json')
    n=run_next_backtest_attribution_plan(r); save_next_backtest_attribution_plan_report(n, a.plan_output or od/'next_backtest_attribution_plan.md', a.plan_json_output or od/'next_backtest_attribution_plan.json')
    print(f'Stage56 real cache quality package written: {od / "real_cache_quality.md"} decision={r.decision.value}')
    return 1 if r.decision==RealCacheQualityDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
