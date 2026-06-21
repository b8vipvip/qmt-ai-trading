#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.grouping_service import *
from qmt_ai_trading.local_console.grouping_models import LocalConsoleGroupingDecision

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_grouping_stage69'); p.add_argument('--binding-dir',default='local_console_binding_stage66'); p.add_argument('--refresh-dir',default='local_console_refresh_stage68'); p.add_argument('--preview-dir',default='local_console_preview_stage67')
    for x in ['output','json-output','manifest-output','manifest-json-output','filter-output','filter-json-output','grouped-output','grouped-json-output','search-output','search-json-output','safety-output','safety-json-output','plan-output','plan-json-output']: p.add_argument('--'+x,default=None)
    a=p.parse_args(argv); out=Path(a.output_dir); cfg=build_default_local_console_grouping_config(repo_root=a.repo_root,output_dir=a.output_dir,binding_dir=a.binding_dir,refresh_dir=a.refresh_dir,preview_dir=a.preview_dir)
    r=run_local_console_grouping_review(cfg)
    save_local_console_grouping_report(r,a.output or out/'local_console_grouping_report.md',a.json_output or out/'local_console_grouping_report.json')
    save_grouping_manifest_report(build_grouping_manifest_report(r),a.manifest_output or out/'grouping_manifest.md',a.manifest_json_output or out/'grouping_manifest.json')
    save_filter_state_schema_report(build_filter_state_schema_report(r),a.filter_output or out/'filter_state_schema.md',a.filter_json_output or out/'filter_state_schema.json')
    save_grouped_card_index_report(build_grouped_card_index_report(r),a.grouped_output or out/'grouped_card_index.md',a.grouped_json_output or out/'grouped_card_index.json')
    save_search_index_report(build_search_index_report(r),a.search_output or out/'search_index.md',a.search_json_output or out/'search_index.json')
    save_frontend_grouping_safety_report(build_frontend_grouping_safety_report(r),a.safety_output or out/'frontend_grouping_safety_report.md',a.safety_json_output or out/'frontend_grouping_safety_report.json')
    save_next_console_drilldown_export_plan_report(build_next_console_drilldown_export_plan_report(cfg),a.plan_output or out/'next_console_drilldown_export_plan.md',a.plan_json_output or out/'next_console_drilldown_export_plan.json')
    print(f'Stage69 local console grouping review package written: {out / "local_console_grouping_report.md"} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleGroupingDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
