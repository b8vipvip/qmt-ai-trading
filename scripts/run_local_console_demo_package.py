#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.demo_service import *
from qmt_ai_trading.local_console.demo_models import LocalConsoleDemoDecision

def add(p,n,d): p.add_argument(n,default=d)
def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage74 local console demo package, read-only.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_demo_stage74')
    for n,d in [('--help-dir','local_console_help_stage73'),('--acceptance-dir','local_console_acceptance_stage72'),('--review-dir','local_console_review_stage71'),('--drilldown-dir','local_console_drilldown_stage70'),('--grouping-dir','local_console_grouping_stage69'),('--refresh-dir','local_console_refresh_stage68')]: add(p,n,d)
    outputs={'output':'local_console_demo_stage74/local_console_demo_package_report.md','json_output':'local_console_demo_stage74/local_console_demo_package_report.json','manifest_output':'local_console_demo_stage74/demo_manifest.md','manifest_json_output':'local_console_demo_stage74/demo_manifest.json','guide_output':'local_console_demo_stage74/demo_guide.md','guide_json_output':'local_console_demo_stage74/demo_guide.json','route_output':'local_console_demo_stage74/demo_route_map.md','route_json_output':'local_console_demo_stage74/demo_route_map.json','asset_output':'local_console_demo_stage74/demo_asset_manifest.md','asset_json_output':'local_console_demo_stage74/demo_asset_manifest.json','package_output':'local_console_demo_stage74/demo_package_index.md','package_json_output':'local_console_demo_stage74/demo_package_index.json','safety_output':'local_console_demo_stage74/demo_safety_report.md','safety_json_output':'local_console_demo_stage74/demo_safety_report.json','validation_output':'local_console_demo_stage74/demo_validation_summary.md','validation_json_output':'local_console_demo_stage74/demo_validation_summary.json','plan_output':'local_console_demo_stage74/next_ui_productization_closure_plan.md','plan_json_output':'local_console_demo_stage74/next_ui_productization_closure_plan.json'}
    for k,d in outputs.items(): p.add_argument('--'+k.replace('_','-'),default=d)
    a=p.parse_args(argv); base=Path(a.output_dir)
    for key, default in outputs.items():
        if getattr(a,key)==default: setattr(a,key,str(base/Path(default).name))
    cfg=build_default_local_console_demo_config(repo_root=a.repo_root,output_dir=a.output_dir,help_dir=a.help_dir,acceptance_dir=a.acceptance_dir,review_dir=a.review_dir,drilldown_dir=a.drilldown_dir,grouping_dir=a.grouping_dir,refresh_dir=a.refresh_dir)
    r=run_local_console_demo_package_review(cfg)
    save_local_console_demo_package_report(r,a.output,a.json_output)
    save_demo_manifest_report(build_demo_manifest_report(r),a.manifest_output,a.manifest_json_output)
    save_demo_guide_report(build_demo_guide_report(r),a.guide_output,a.guide_json_output)
    save_demo_route_map_report(build_demo_route_map_report(r),a.route_output,a.route_json_output)
    save_demo_asset_manifest_report(build_demo_asset_manifest_report(r),a.asset_output,a.asset_json_output)
    save_demo_package_index_report(build_demo_package_index_report(r),a.package_output,a.package_json_output)
    save_demo_safety_report(build_demo_safety_report(r),a.safety_output,a.safety_json_output)
    save_demo_validation_summary_report(build_demo_validation_summary_report(r),a.validation_output,a.validation_json_output)
    save_next_ui_productization_closure_plan_report(build_next_ui_productization_closure_plan_report(cfg),a.plan_output,a.plan_json_output)
    print(f'Stage74 local console demo package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LocalConsoleDemoDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
