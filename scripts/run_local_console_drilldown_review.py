#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.drilldown_service import *
from qmt_ai_trading.local_console.drilldown_models import LocalConsoleDrilldownDecision

def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage70 local console drilldown/export review (read-only).')
    p.add_argument('--repo-root', default='.') ; p.add_argument('--output-dir', default='local_console_drilldown_stage70')
    p.add_argument('--binding-dir', default='local_console_binding_stage66'); p.add_argument('--grouping-dir', default='local_console_grouping_stage69'); p.add_argument('--refresh-dir', default='local_console_refresh_stage68'); p.add_argument('--preview-dir', default='local_console_preview_stage67')
    for a,d in [('--output','local_console_drilldown_stage70/local_console_drilldown_report.md'),('--json-output','local_console_drilldown_stage70/local_console_drilldown_report.json'),('--detail-output','local_console_drilldown_stage70/report_detail_index.md'),('--detail-json-output','local_console_drilldown_stage70/report_detail_index.json'),('--route-output','local_console_drilldown_stage70/drilldown_route_map.md'),('--route-json-output','local_console_drilldown_stage70/drilldown_route_map.json'),('--export-output','local_console_drilldown_stage70/export_manifest.md'),('--export-json-output','local_console_drilldown_stage70/export_manifest.json'),('--snapshot-output','local_console_drilldown_stage70/export_snapshot.md'),('--snapshot-json-output','local_console_drilldown_stage70/export_snapshot.json'),('--safety-output','local_console_drilldown_stage70/export_safety_report.md'),('--safety-json-output','local_console_drilldown_stage70/export_safety_report.json'),('--plan-output','local_console_drilldown_stage70/next_manual_review_workbench_plan.md'),('--plan-json-output','local_console_drilldown_stage70/next_manual_review_workbench_plan.json')]: p.add_argument(a, default=d)
    args=p.parse_args(argv)
    cfg=build_default_local_console_drilldown_config(repo_root=args.repo_root, output_dir=args.output_dir, binding_dir=args.binding_dir, grouping_dir=args.grouping_dir, refresh_dir=args.refresh_dir, preview_dir=args.preview_dir)
    r=run_local_console_drilldown_review(cfg)
    save_local_console_drilldown_report(r,args.output,args.json_output)
    save_report_detail_index_report(build_report_detail_index_report(r),args.detail_output,args.detail_json_output)
    save_drilldown_route_map_report(build_drilldown_route_map_report(r),args.route_output,args.route_json_output)
    save_export_manifest_report(build_export_manifest_report(r),args.export_output,args.export_json_output)
    save_export_snapshot_report(build_export_snapshot_report(r),args.snapshot_output,args.snapshot_json_output)
    save_export_safety_report(build_export_safety_report_from_report(r),args.safety_output,args.safety_json_output)
    save_next_manual_review_workbench_plan_report(build_next_manual_review_workbench_plan_report(cfg),args.plan_output,args.plan_json_output)
    print(f'Stage70 local console drilldown review written: {args.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleDrilldownDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
