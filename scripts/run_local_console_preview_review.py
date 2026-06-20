from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.local_console.preview_service import *
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_preview_stage67'); p.add_argument('--static-dir',default='local_console_binding_stage66'); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8767); p.add_argument('--dry-run',action='store_true')
    for a,d in [('output','local_console_preview_report.md'),('json-output','local_console_preview_report.json'),('route-output','preview_route_map.md'),('route-json-output','preview_route_map.json'),('static-output','static_file_index.md'),('static-json-output','static_file_index.json'),('response-output','response_manifest.md'),('response-json-output','response_manifest.json'),('safety-output','preview_safety_boundary.md'),('safety-json-output','preview_safety_boundary.json'),('plan-output','next_console_refresh_plan.md'),('plan-json-output','next_console_refresh_plan.json')]: p.add_argument('--'+a, default=None)
    ns=p.parse_args(argv); out=Path(ns.output_dir)
    def path(v,d): return v or str(out/d)
    cfg=build_default_local_console_preview_config(repo_root=ns.repo_root,static_dir=ns.static_dir,host=ns.host,port=ns.port,dry_run=True)
    r=run_local_console_preview_review(cfg)
    save_local_console_preview_report(r,path(ns.output,'local_console_preview_report.md'),path(ns.json_output,'local_console_preview_report.json'))
    save_preview_route_map_report(build_preview_route_map_report(r),path(ns.route_output,'preview_route_map.md'),path(ns.route_json_output,'preview_route_map.json'))
    save_static_file_index_report(build_static_file_index_report(r),path(ns.static_output,'static_file_index.md'),path(ns.static_json_output,'static_file_index.json'))
    save_response_manifest_report(build_response_manifest_report(r),path(ns.response_output,'response_manifest.md'),path(ns.response_json_output,'response_manifest.json'))
    save_preview_safety_report(build_preview_safety_report(r),path(ns.safety_output,'preview_safety_boundary.md'),path(ns.safety_json_output,'preview_safety_boundary.json'))
    save_next_console_refresh_plan_report(build_next_console_refresh_plan_report(cfg),path(ns.plan_output,'next_console_refresh_plan.md'),path(ns.plan_json_output,'next_console_refresh_plan.json'))
    print(r.decision.value); return 0 if ns.dry_run or r.decision.value!='NO_GO' else 1
if __name__=='__main__': raise SystemExit(main())
