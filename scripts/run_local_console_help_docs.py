#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.help_service import *
from qmt_ai_trading.local_console.help_models import LocalConsoleHelpDecision

def add(p,n,d): p.add_argument(n,default=d)
def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage73 local console help docs, read-only.')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_help_stage73')
    for n,d in [('--acceptance-dir','local_console_acceptance_stage72'),('--review-dir','local_console_review_stage71'),('--drilldown-dir','local_console_drilldown_stage70'),('--grouping-dir','local_console_grouping_stage69'),('--refresh-dir','local_console_refresh_stage68')]: add(p,n,d)
    outputs={'output':'local_console_help_stage73/local_console_help_docs_report.md','json_output':'local_console_help_stage73/local_console_help_docs_report.json','home_output':'local_console_help_stage73/help_home.md','home_json_output':'local_console_help_stage73/help_home.json','page_output':'local_console_help_stage73/page_help.md','page_json_output':'local_console_help_stage73/page_help.json','feature_output':'local_console_help_stage73/feature_help.md','feature_json_output':'local_console_help_stage73/feature_help.json','safety_output':'local_console_help_stage73/safety_help.md','safety_json_output':'local_console_help_stage73/safety_help.json','faq_output':'local_console_help_stage73/faq.md','faq_json_output':'local_console_help_stage73/faq.json','error_output':'local_console_help_stage73/error_handling_guide.md','error_json_output':'local_console_help_stage73/error_handling_guide.json','glossary_output':'local_console_help_stage73/glossary.md','glossary_json_output':'local_console_help_stage73/glossary.json','route_output':'local_console_help_stage73/route_help_map.md','route_json_output':'local_console_help_stage73/route_help_map.json','package_output':'local_console_help_stage73/help_package_index.md','package_json_output':'local_console_help_stage73/help_package_index.json','docs_safety_output':'local_console_help_stage73/docs_safety_report.md','docs_safety_json_output':'local_console_help_stage73/docs_safety_report.json','plan_output':'local_console_help_stage73/next_local_demo_package_plan.md','plan_json_output':'local_console_help_stage73/next_local_demo_package_plan.json'}
    for k,d in outputs.items(): p.add_argument('--'+k.replace('_','-'),default=d)
    a=p.parse_args(argv)
    base=Path(a.output_dir)
    for key, default in outputs.items():
        if getattr(a, key) == default:
            setattr(a, key, str(base / Path(default).name))
    cfg=build_default_local_console_help_config(repo_root=a.repo_root,output_dir=a.output_dir,acceptance_dir=a.acceptance_dir,review_dir=a.review_dir,drilldown_dir=a.drilldown_dir,grouping_dir=a.grouping_dir,refresh_dir=a.refresh_dir)
    r=run_local_console_help_docs_review(cfg)
    save_local_console_help_docs_report(r,a.output,a.json_output)
    save_help_home_report(build_help_home_report(r),a.home_output,a.home_json_output)
    save_page_help_report(build_page_help_report(r),a.page_output,a.page_json_output)
    save_feature_help_report(build_feature_help_report(r),a.feature_output,a.feature_json_output)
    save_safety_help_report(build_safety_help_report(r),a.safety_output,a.safety_json_output)
    save_faq_report(build_faq_report(r),a.faq_output,a.faq_json_output)
    save_error_handling_report(build_error_handling_report(r),a.error_output,a.error_json_output)
    save_glossary_report(build_glossary_report(r),a.glossary_output,a.glossary_json_output)
    save_route_help_map_report(build_route_help_map_report(r),a.route_output,a.route_json_output)
    save_help_package_index_report(build_help_package_index_report(r),a.package_output,a.package_json_output)
    save_docs_safety_report(build_docs_safety_report(r),a.docs_safety_output,a.docs_safety_json_output)
    save_next_local_demo_package_plan_report(build_next_local_demo_package_plan_report(cfg),a.plan_output,a.plan_json_output)
    print(f'Stage73 local console help docs package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LocalConsoleHelpDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
