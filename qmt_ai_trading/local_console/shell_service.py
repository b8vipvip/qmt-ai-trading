from __future__ import annotations
import hashlib, json
from pathlib import Path
from .shell_models import *
from .shell_assets import *
from .shell_formatters import *
from .shell_safety import *
from .tolerant_reader import safe_read_json_or_markdown, read_latest_validation_for_shell

def build_default_local_console_shell_config(**kw): return LocalConsoleShellConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _hash(t): return hashlib.sha256(t.encode('utf-8')).hexdigest()
def _evidence(stage,jsonp,mdp):
    r=safe_read_json_or_markdown(jsonp,mdp); data=r.get('data') if isinstance(r.get('data'),dict) else {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0)
    return LocalConsoleShellEvidence(stage=stage,path=r['source'],status=LocalConsoleShellStatus.PASS if r['status']=='PASS' else LocalConsoleShellStatus.WARN if r['status']=='WARN' else LocalConsoleShellStatus.UNAVAILABLE,summary=r['summary'],decision=str(data.get('decision','')),critical_count=crit,warnings=list(data.get('warnings',[]))+r.get('warnings',[]),blocking_reasons=list(data.get('blocking_reasons',[])),metadata={'data':data,'encoding_used':r.get('encoding_used')})
def run_local_console_shell_review(config=None):
    cfg=config or LocalConsoleShellConfig(); root=Path(cfg.repo_root)
    ev=[_evidence('Stage64',root/cfg.local_console_dashboard_dir/'local_console_dashboard_report.json',root/cfg.local_console_dashboard_dir/'local_console_dashboard_report.md'),_evidence('Stage63',root/cfg.local_console_detail_dir/'local_console_detail_report.json',root/cfg.local_console_detail_dir/'local_console_detail_report.md'),_evidence('Stage62',root/cfg.local_console_dir/'local_console_report.json',root/cfg.local_console_dir/'local_console_report.md'),_evidence('Stage61',root/cfg.api_gateway_dir/'api_gateway_report.json',root/cfg.api_gateway_dir/'api_gateway_report.md')]
    validation=read_latest_validation_for_shell(root/'validation_logs')
    warnings=[f'validation: {w}' for w in validation.get('warnings',[])]
    blocking=[]; decision=LocalConsoleShellDecision.READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW
    st64=ev[0]
    if st64.status==LocalConsoleShellStatus.UNAVAILABLE: decision=LocalConsoleShellDecision.NEED_MORE_EVIDENCE; warnings.append('Stage64 dashboard package unavailable; shell review needs more evidence')
    if st64.decision=='NO_GO' or st64.critical_count>0: decision=LocalConsoleShellDecision.NO_GO; blocking.append('Stage64 NO_GO or critical findings present')
    routes=build_shell_route_map(); bad=assert_no_forbidden_shell_routes(routes)
    if bad: blocking.append(f'forbidden shell routes: {bad}')
    html,js,css=build_index_html(),build_app_js(),build_style_css()
    for name,text,execflag in [('index.html',html,False),('app.js',js,True),('style.css',css,False)]:
        for m in scan_local_console_shell_asset_for_forbidden_markers(text,name,generated=True,executable=execflag):
            (blocking if m['severity']=='CRITICAL' else warnings).append(f"{m['severity']} marker {m['marker']} in {name}")
    if assert_no_forbidden_js_actions(js): blocking.append('forbidden JS action detected')
    assets=[LocalConsoleShellAsset('index.html','index.html',LocalConsoleShellAssetType.HTML,sha256=_hash(html)),LocalConsoleShellAsset('app.js','app.js',LocalConsoleShellAssetType.JAVASCRIPT,sha256=_hash(js)),LocalConsoleShellAsset('style.css','style.css',LocalConsoleShellAssetType.CSS,sha256=_hash(css)),LocalConsoleShellAsset('shell_manifest.json','shell_manifest.json',LocalConsoleShellAssetType.MANIFEST),LocalConsoleShellAsset('route_map.json','route_map.json',LocalConsoleShellAssetType.ROUTE_MAP),LocalConsoleShellAsset('data_binding_placeholders.json','data_binding_placeholders.json',LocalConsoleShellAssetType.DATA_BINDING_PLACEHOLDER)]
    if blocking: decision=LocalConsoleShellDecision.NO_GO
    return LocalConsoleShellReport(decision=decision,evidence=ev,assets=assets,routes=routes,data_binding_placeholders=build_data_binding_placeholders(),warnings=warnings,blocking_reasons=blocking,summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})
def save_static_assets(out):
    out=Path(out); _write(out/'index.html',build_index_html()); _write(out/'app.js',build_app_js()); _write(out/'style.css',build_style_css())
def save_local_console_shell_report(r,output,json_output): save_static_assets(Path(output).parent); _write(output,format_shell_report_md(r)); _write_json(json_output,r)
def load_local_console_shell_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_shell_route_map_report(r): return LocalConsoleShellRouteMapReport(r.routes, list(FORBIDDEN_ROUTES), r.warnings)
def save_shell_route_map_report(r,output,json_output): _write(output,format_route_map_md(r)); _write_json(json_output,r)
def build_shell_asset_index_report(r): return LocalConsoleShellAssetIndexReport(r.assets,r.warnings)
def save_shell_asset_index_report(r,output,json_output): _write(output,format_asset_index_md(r)); _write_json(json_output,r)
def build_data_binding_placeholder_report(r): return LocalConsoleDataBindingPlaceholderReport(r.data_binding_placeholders)
def save_data_binding_placeholder_report(r,output,json_output): _write(output,format_binding_md(r)); _write_json(json_output,r)
def build_static_safety_report(config=None): return build_static_safety_boundary()
def save_static_safety_report(r,output,json_output): _write(output,format_safety_md(r)); _write_json(json_output,r)
def build_next_console_data_binding_plan_report(config=None): return NextConsoleDataBindingPlanReport()
def save_next_console_data_binding_plan_report(r,output,json_output): _write(output,format_plan_md(r)); _write_json(json_output,r)
def save_shell_manifest_report(r,output,json_output):
    m=build_shell_manifest(r.assets); _write(output,format_manifest_md(m)); _write_json(json_output,m)
