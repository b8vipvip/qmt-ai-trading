#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.binding_service import *

def main(argv=None):
    p=argparse.ArgumentParser(description='Run Stage66 local console static data binding review (read-only).')
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_binding_stage66')
    p.add_argument('--local-console-shell-dir',default='local_console_shell_stage65'); p.add_argument('--local-console-dashboard-dir',default='local_console_dashboard_stage64'); p.add_argument('--local-console-detail-dir',default='local_console_detail_stage63'); p.add_argument('--local-console-dir',default='local_console_stage62'); p.add_argument('--api-gateway-dir',default='api_gateway_stage61')
    for a,d in [('output','local_console_binding_stage66/local_console_binding_report.md'),('json-output','local_console_binding_stage66/local_console_binding_report.json'),('bundle-output','local_console_binding_stage66/data_bundle.md'),('bundle-json-output','local_console_binding_stage66/data_bundle.json'),('manifest-output','local_console_binding_stage66/binding_manifest.md'),('manifest-json-output','local_console_binding_stage66/binding_manifest.json'),('source-map-output','local_console_binding_stage66/data_source_map.md'),('source-map-json-output','local_console_binding_stage66/data_source_map.json'),('missing-output','local_console_binding_stage66/missing_data_placeholders.md'),('missing-json-output','local_console_binding_stage66/missing_data_placeholders.json'),('asset-output','local_console_binding_stage66/bound_asset_index.md'),('asset-json-output','local_console_binding_stage66/bound_asset_index.json'),('safety-output','local_console_binding_stage66/static_data_safety.md'),('safety-json-output','local_console_binding_stage66/static_data_safety.json'),('plan-output','local_console_binding_stage66/next_console_preview_server_plan.md'),('plan-json-output','local_console_binding_stage66/next_console_preview_server_plan.json')]: p.add_argument('--'+a,default=d)
    a=p.parse_args(argv)
    cfg=build_default_local_console_binding_config(repo_root=a.repo_root,output_dir=a.output_dir,local_console_shell_dir=a.local_console_shell_dir,local_console_dashboard_dir=a.local_console_dashboard_dir,local_console_detail_dir=a.local_console_detail_dir,local_console_dir=a.local_console_dir,api_gateway_dir=a.api_gateway_dir)
    r=run_local_console_binding_review(cfg)
    save_local_console_binding_report(r,a.output,a.json_output)
    save_data_bundle_report(build_data_bundle_report(r),a.bundle_output,a.bundle_json_output)
    save_binding_manifest_report(build_binding_manifest_report(r),a.manifest_output,a.manifest_json_output)
    save_data_source_map_report(build_data_source_map_report(r),a.source_map_output,a.source_map_json_output)
    save_missing_data_placeholder_report(build_missing_data_placeholder_report(r),a.missing_output,a.missing_json_output)
    save_bound_asset_index_report(build_bound_asset_index_report(r),a.asset_output,a.asset_json_output)
    save_static_data_safety_report(build_static_data_safety_report(cfg),a.safety_output,a.safety_json_output)
    save_next_console_preview_server_plan_report(build_next_console_preview_server_plan_report(cfg),a.plan_output,a.plan_json_output)
    print(f'Stage66 local console binding review package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision.value=='NO_GO' else 0
if __name__=='__main__': raise SystemExit(main())
