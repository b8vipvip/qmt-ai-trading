from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.shell_models import LocalConsoleShellDecision
from qmt_ai_trading.local_console.shell_service import *
def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_shell_stage65')
    p.add_argument('--local-console-dashboard-dir',default='local_console_dashboard_stage64'); p.add_argument('--local-console-detail-dir',default='local_console_detail_stage63'); p.add_argument('--local-console-dir',default='local_console_stage62'); p.add_argument('--api-gateway-dir',default='api_gateway_stage61')
    outs=['output','json-output','manifest-output','manifest-json-output','route-output','route-json-output','asset-output','asset-json-output','binding-output','binding-json-output','safety-output','safety-json-output','plan-output','plan-json-output']
    defs=['local_console_shell_stage65/local_console_shell_report.md','local_console_shell_stage65/local_console_shell_report.json','local_console_shell_stage65/shell_manifest.md','local_console_shell_stage65/shell_manifest.json','local_console_shell_stage65/route_map.md','local_console_shell_stage65/route_map.json','local_console_shell_stage65/asset_index.md','local_console_shell_stage65/asset_index.json','local_console_shell_stage65/data_binding_placeholders.md','local_console_shell_stage65/data_binding_placeholders.json','local_console_shell_stage65/static_safety_boundary.md','local_console_shell_stage65/static_safety_boundary.json','local_console_shell_stage65/next_console_data_binding_plan.md','local_console_shell_stage65/next_console_data_binding_plan.json']
    for o,d in zip(outs,defs): p.add_argument('--'+o,default=d)
    a=p.parse_args(argv)
    cfg=build_default_local_console_shell_config(repo_root=a.repo_root,output_dir=a.output_dir,local_console_dashboard_dir=a.local_console_dashboard_dir,local_console_detail_dir=a.local_console_detail_dir,local_console_dir=a.local_console_dir,api_gateway_dir=a.api_gateway_dir)
    r=run_local_console_shell_review(cfg)
    save_local_console_shell_report(r,a.output,a.json_output); save_shell_manifest_report(r,a.manifest_output,a.manifest_json_output); save_shell_route_map_report(build_shell_route_map_report(r),a.route_output,a.route_json_output); save_shell_asset_index_report(build_shell_asset_index_report(r),a.asset_output,a.asset_json_output); save_data_binding_placeholder_report(build_data_binding_placeholder_report(r),a.binding_output,a.binding_json_output); save_static_safety_report(build_static_safety_report(cfg),a.safety_output,a.safety_json_output); save_next_console_data_binding_plan_report(build_next_console_data_binding_plan_report(cfg),a.plan_output,a.plan_json_output)
    print(f'Stage65 local console shell review package written: {a.output} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True')
    return 1 if r.decision==LocalConsoleShellDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
