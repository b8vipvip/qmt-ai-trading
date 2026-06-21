from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.acceptance_models import LocalConsoleAcceptanceDecision
from qmt_ai_trading.local_console.acceptance_service import *

def main(argv=None):
    p=argparse.ArgumentParser()
    for name,default in [('repo-root','.'),('output-dir','local_console_acceptance_stage72'),('review-dir','local_console_review_stage71'),('drilldown-dir','local_console_drilldown_stage70'),('grouping-dir','local_console_grouping_stage69'),('refresh-dir','local_console_refresh_stage68'),('preview-dir','local_console_preview_stage67'),('binding-dir','local_console_binding_stage66')]: p.add_argument('--'+name,default=default)
    for n in ['output','json-output','summary-output','summary-json-output','page-output','page-json-output','feature-output','feature-json-output','safety-output','safety-json-output','open-output','open-json-output','route-output','route-json-output','asset-output','asset-json-output','conclusion-output','conclusion-json-output','package-output','package-json-output','ui-safety-output','ui-safety-json-output','plan-output','plan-json-output']: p.add_argument('--'+n)
    a=p.parse_args(argv); out=a.output_dir
    base=Path(a.repo_root)
    def op(x, default):
        p=Path(x or default)
        return str(p if p.is_absolute() else base/p)
    cfg=build_default_local_console_acceptance_config(repo_root=a.repo_root,output_dir=out,review_dir=a.review_dir,drilldown_dir=a.drilldown_dir,grouping_dir=a.grouping_dir,refresh_dir=a.refresh_dir,preview_dir=a.preview_dir,binding_dir=a.binding_dir)
    r=run_local_console_ui_acceptance_review(cfg)
    save_local_console_ui_acceptance_report(r,op(a.output, f'{out}/local_console_ui_acceptance_report.md'),op(a.json_output, f'{out}/local_console_ui_acceptance_report.json'))
    save_ui_acceptance_summary_report(build_ui_acceptance_summary_report(r),op(a.summary_output, f'{out}/ui_acceptance_summary.md'),op(a.summary_json_output, f'{out}/ui_acceptance_summary.json'))
    save_page_inventory_report(build_page_inventory_report(r),op(a.page_output, f'{out}/page_inventory.md'),op(a.page_json_output, f'{out}/page_inventory.json'))
    save_feature_inventory_report(build_feature_inventory_report(r),op(a.feature_output, f'{out}/feature_inventory.md'),op(a.feature_json_output, f'{out}/feature_inventory.json'))
    save_safety_checklist_report(build_safety_checklist_report(r),op(a.safety_output, f'{out}/safety_checklist.md'),op(a.safety_json_output, f'{out}/safety_checklist.json'))
    save_open_items_report(build_open_items_report(r),op(a.open_output, f'{out}/open_items.md'),op(a.open_json_output, f'{out}/open_items.json'))
    save_route_coverage_report(build_route_coverage_report(r),op(a.route_output, f'{out}/route_coverage.md'),op(a.route_json_output, f'{out}/route_coverage.json'))
    save_asset_coverage_report(build_asset_coverage_report(r),op(a.asset_output, f'{out}/asset_coverage.md'),op(a.asset_json_output, f'{out}/asset_coverage.json'))
    save_acceptance_conclusion_draft_report(build_acceptance_conclusion_draft_report(r),op(a.conclusion_output, f'{out}/acceptance_conclusion_draft.md'),op(a.conclusion_json_output, f'{out}/acceptance_conclusion_draft.json'))
    save_acceptance_package_index_report(build_acceptance_package_index_report(r),op(a.package_output, f'{out}/acceptance_package_index.md'),op(a.package_json_output, f'{out}/acceptance_package_index.json'))
    save_ui_acceptance_safety_report(build_ui_acceptance_safety_report(r),op(a.ui_safety_output, f'{out}/ui_acceptance_safety_report.md'),op(a.ui_safety_json_output, f'{out}/ui_acceptance_safety_report.json'))
    save_next_local_help_docs_plan_report(build_next_local_help_docs_plan_report(cfg),op(a.plan_output, f'{out}/next_local_help_docs_plan.md'),op(a.plan_json_output, f'{out}/next_local_help_docs_plan.json'))
    print(f'Stage72 local console UI acceptance decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleAcceptanceDecision.NO_GO else 0
if __name__=='__main__': sys.exit(main())
