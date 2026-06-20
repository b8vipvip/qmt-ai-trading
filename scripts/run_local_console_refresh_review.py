#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.local_console.refresh_service import *
from qmt_ai_trading.local_console.refresh_models import LocalConsoleRefreshDecision

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',default='.') ; p.add_argument('--output-dir',default='local_console_refresh_stage68')
    p.add_argument('--binding-dir',default='local_console_binding_stage66'); p.add_argument('--preview-dir',default='local_console_preview_stage67')
    p.add_argument('--output',default=None); p.add_argument('--json-output',default=None); p.add_argument('--route-output',default=None); p.add_argument('--route-json-output',default=None)
    p.add_argument('--manifest-output',default=None); p.add_argument('--manifest-json-output',default=None); p.add_argument('--state-output',default=None); p.add_argument('--state-json-output',default=None)
    p.add_argument('--safety-output',default=None); p.add_argument('--safety-json-output',default=None); p.add_argument('--plan-output',default=None); p.add_argument('--plan-json-output',default=None)
    a=p.parse_args(argv); out=Path(a.output_dir)
    cfg=build_default_local_console_refresh_config(repo_root=a.repo_root, output_dir=a.output_dir, binding_dir=a.binding_dir, preview_dir=a.preview_dir)
    r=run_local_console_refresh_review(cfg)
    save_local_console_refresh_report(r, a.output or out/'local_console_refresh_report.md', a.json_output or out/'local_console_refresh_report.json')
    save_navigation_route_map_report(build_navigation_route_map_report(r), a.route_output or out/'navigation_route_map.md', a.route_json_output or out/'navigation_route_map.json')
    save_refresh_manifest_report(build_refresh_manifest_report(r), a.manifest_output or out/'refresh_manifest.md', a.manifest_json_output or out/'refresh_manifest.json')
    save_ui_state_placeholder_report(build_ui_state_placeholder_report(r), a.state_output or out/'ui_state_placeholders.md', a.state_json_output or out/'ui_state_placeholders.json')
    save_frontend_safety_report(build_frontend_safety_report(r), a.safety_output or out/'frontend_safety_report.md', a.safety_json_output or out/'frontend_safety_report.json')
    save_next_console_grouping_filter_plan_report(build_next_console_grouping_filter_plan_report(cfg), a.plan_output or out/'next_console_grouping_filter_plan.md', a.plan_json_output or out/'next_console_grouping_filter_plan.json')
    print(f'Stage68 local console refresh review package written: {out / "local_console_refresh_report.md"} decision={r.decision.value} read_only=True dry_run_only=True no_trade_authorization=True')
    return 1 if r.decision==LocalConsoleRefreshDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
