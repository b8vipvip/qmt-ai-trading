from __future__ import annotations
import json
from pathlib import Path
from .demo_models import *
from .demo_assets import *
from .demo_reader import read_json
from .demo_formatters import format_local_console_demo_package_report_md, format_json_md
from .demo_safety import assert_stage74_read_only, scan_demo_assets_for_forbidden_markers

def build_default_local_console_demo_config(**kw): return LocalConsoleDemoConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage,path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleDemoEvidence(stage,obj['source'],LocalConsoleDemoStatus.PASS if obj['status']=='PASS' else LocalConsoleDemoStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def run_local_console_demo_package_review(config=None):
    cfg=config or LocalConsoleDemoConfig(); assert_stage74_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_demo_index_html(); js=build_demo_app_js(); css=build_demo_style_css();
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    evidence=[_evidence('Stage73',root/cfg.help_dir/'local_console_help_docs_report.json'),_evidence('Stage72',root/cfg.acceptance_dir/'local_console_ui_acceptance_report.json'),_evidence('Stage71',root/cfg.review_dir/'local_console_review_workbench_report.json'),_evidence('Stage70',root/cfg.drilldown_dir/'local_console_drilldown_report.json'),_evidence('Stage69',root/cfg.grouping_dir/'local_console_grouping_report.json'),_evidence('Stage68',root/cfg.refresh_dir/'local_console_refresh_report.json')]
    findings=scan_demo_assets_for_forbidden_markers({'index.html':html,'app.js':js,'style.css':css})
    warnings=[]; blocking=[]
    if evidence[0].status==LocalConsoleDemoStatus.UNAVAILABLE: warnings.append('Stage73 package unavailable; demo package needs more evidence')
    if evidence[0].decision=='NO_GO' or evidence[0].critical_count>0: blocking.append('Stage73 NO_GO or critical findings present')
    for f in findings:
        if f.severity==LocalConsoleDemoSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleDemoDecision.READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW
    if evidence[0].status==LocalConsoleDemoStatus.UNAVAILABLE: decision=LocalConsoleDemoDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleDemoDecision.NO_GO
    validation=build_demo_validation_summary(len(blocking))
    return LocalConsoleDemoPackageReport(decision,cfg,evidence,build_demo_home(),build_demo_manifest(),build_demo_guide(),build_demo_route_map(),build_demo_asset_manifest(),build_demo_package_index(),findings,validation,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_demo_package_report(r,output,json_output): _write(output,format_local_console_demo_package_report_md(r)); _write_json(json_output,r)
def load_local_console_demo_package_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_demo_manifest_report(r=None): return DemoManifestReport((r.demo_manifest if r else build_demo_manifest()))
def save_demo_manifest_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_guide_report(r=None): return DemoGuideReport((r.demo_guide if r else build_demo_guide()))
def save_demo_guide_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Guide',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_route_map_report(r=None): return DemoRouteMapReport((r.demo_route_map if r else build_demo_route_map()),FORBIDDEN_ROUTES)
def save_demo_route_map_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Route Map',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_asset_manifest_report(r=None): return DemoAssetManifestReport((r.demo_asset_manifest if r else build_demo_asset_manifest()))
def save_demo_asset_manifest_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Asset Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_package_index_report(r=None): return DemoPackageIndexReport((r.demo_package_index if r else build_demo_package_index()))
def save_demo_package_index_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Package Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_safety_report(r=None): return DemoSafetyReport((r.demo_safety_findings if r else []), sum(1 for x in (r.demo_safety_findings if r else []) if x.severity==LocalConsoleDemoSeverity.CRITICAL), (r.warnings if r else []))
def save_demo_safety_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_demo_validation_summary_report(r=None): return DemoValidationSummaryReport((r.demo_validation_summary if r else build_demo_validation_summary()), ['read_only=True','dry_run_only=True','no_trade_authorization=True'])
def save_demo_validation_summary_report(r,output,json_output): _write(output,format_json_md('Stage74 Demo Validation Summary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_ui_productization_closure_plan_report(config=None): return build_next_ui_productization_closure_plan()
def save_next_ui_productization_closure_plan_report(r,output,json_output): _write(output,format_json_md('Stage75 Next UI Productization Closure Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
