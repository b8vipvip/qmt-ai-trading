#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.closure_service import *
from qmt_ai_trading.local_console.closure_models import LocalConsoleClosureDecision

def add(p,n,d): p.add_argument(n,default=d)
def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage75 UI productization closure package, read-only.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_closure_stage75')
    for n,d in [('--demo-dir','local_console_demo_stage74'),('--help-dir','local_console_help_stage73'),('--acceptance-dir','local_console_acceptance_stage72'),('--review-dir','local_console_review_stage71'),('--drilldown-dir','local_console_drilldown_stage70'),('--grouping-dir','local_console_grouping_stage69'),('--refresh-dir','local_console_refresh_stage68')]: add(p,n,d)
    outputs={'output':'local_console_closure_stage75/ui_productization_closure_report.md','json_output':'local_console_closure_stage75/ui_productization_closure_report.json','stage_output':'local_console_closure_stage75/stage_overview.md','stage_json_output':'local_console_closure_stage75/stage_overview.json','matrix_output':'local_console_closure_stage75/capability_matrix.md','matrix_json_output':'local_console_closure_stage75/capability_matrix.json','safety_output':'local_console_closure_stage75/safety_boundary_table.md','safety_json_output':'local_console_closure_stage75/safety_boundary_table.json','demo_output':'local_console_closure_stage75/readonly_demo_entry.md','demo_json_output':'local_console_closure_stage75/readonly_demo_entry.json','route_output':'local_console_closure_stage75/route_coverage_summary.md','route_json_output':'local_console_closure_stage75/route_coverage_summary.json','asset_output':'local_console_closure_stage75/asset_coverage_summary.md','asset_json_output':'local_console_closure_stage75/asset_coverage_summary.json','risk_output':'local_console_closure_stage75/risk_limitation_summary.md','risk_json_output':'local_console_closure_stage75/risk_limitation_summary.json','conclusion_output':'local_console_closure_stage75/final_acceptance_conclusion_draft.md','conclusion_json_output':'local_console_closure_stage75/final_acceptance_conclusion_draft.json','future_output':'local_console_closure_stage75/future_roadmap_recommendation.md','future_json_output':'local_console_closure_stage75/future_roadmap_recommendation.json','closure_safety_output':'local_console_closure_stage75/closure_safety_report.md','closure_safety_json_output':'local_console_closure_stage75/closure_safety_report.json'}
    for k,d in outputs.items(): p.add_argument('--'+k.replace('_','-'),default=d)
    a=p.parse_args(argv); base=Path(a.output_dir)
    for key, default in outputs.items():
        if getattr(a,key)==default: setattr(a,key,str(base/Path(default).name))
    cfg=build_default_local_console_closure_config(repo_root=a.repo_root,output_dir=a.output_dir,demo_dir=a.demo_dir,help_dir=a.help_dir,acceptance_dir=a.acceptance_dir,review_dir=a.review_dir,drilldown_dir=a.drilldown_dir,grouping_dir=a.grouping_dir,refresh_dir=a.refresh_dir)
    r=run_ui_productization_closure_review(cfg)
    save_ui_productization_closure_report(r,a.output,a.json_output)
    save_stage_overview_report(build_stage_overview_report(r),a.stage_output,a.stage_json_output)
    save_capability_matrix_report(build_capability_matrix_report(r),a.matrix_output,a.matrix_json_output)
    save_safety_boundary_table_report(build_safety_boundary_table_report(r),a.safety_output,a.safety_json_output)
    save_readonly_demo_entry_report(build_readonly_demo_entry_report(r),a.demo_output,a.demo_json_output)
    save_route_coverage_summary_report(build_route_coverage_summary_report(r),a.route_output,a.route_json_output)
    save_asset_coverage_summary_report(build_asset_coverage_summary_report(r),a.asset_output,a.asset_json_output)
    save_risk_limitation_summary_report(build_risk_limitation_summary_report(r),a.risk_output,a.risk_json_output)
    save_final_acceptance_conclusion_draft_report(build_final_acceptance_conclusion_draft_report(r),a.conclusion_output,a.conclusion_json_output)
    save_future_roadmap_recommendation_report(build_future_roadmap_recommendation_report(r),a.future_output,a.future_json_output)
    save_closure_safety_report(build_closure_safety_report(r),a.closure_safety_output,a.closure_safety_json_output)
    print(f'Stage75 UI productization closure package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LocalConsoleClosureDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
