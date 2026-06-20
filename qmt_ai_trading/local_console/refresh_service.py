from __future__ import annotations
import json, shutil
from pathlib import Path
from .refresh_models import *
from .refresh_assets import *
from .refresh_assets import build_frontend_safety_report as build_assets_frontend_safety_report
from .refresh_reader import read_json
from .refresh_formatters import format_local_console_refresh_report_md, format_json_md
from .refresh_safety import FORBIDDEN_HASH_ROUTES, assert_no_forbidden_refresh_actions

def build_default_local_console_refresh_config(**kw): return LocalConsoleRefreshConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))

def run_local_console_refresh_review(config=None):
    cfg=config or LocalConsoleRefreshConfig(); root=Path(cfg.repo_root); out=root/cfg.output_dir; binding=root/cfg.binding_dir; preview=root/cfg.preview_dir; warnings=[]; blocking=[]
    out.mkdir(parents=True,exist_ok=True)
    html=build_refresh_index_html(); js=build_refresh_app_js(); css=build_refresh_style_css()
    _write(out/'index.html', html); _write(out/'app.js', js); _write(out/'style.css', css)
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:
        src=binding/n
        if src.exists(): shutil.copyfile(src,out/n)
        else: _write_json(out/n, {'read_only':True,'warning':f'{n} unavailable'})
    prev=read_json(preview/'local_console_preview_report.json'); data=prev.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}
    crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0); dec=str(data.get('decision',''))
    evidence=[LocalConsoleRefreshEvidence('Stage67',prev['source'],LocalConsoleRefreshStatus.PASS if prev['status']=='PASS' else LocalConsoleRefreshStatus.UNAVAILABLE,dec,crit,prev['summary'],prev.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])]
    warnings += prev.get('warnings',[])
    if not preview.exists(): warnings.append('Stage67 package unavailable; refresh review needs more evidence')
    if dec=='NO_GO' or crit>0: blocking.append('Stage67 NO_GO or critical findings present')
    try: assert_no_forbidden_refresh_actions(js)
    except ValueError as exc: blocking.append(str(exc))
    safety=build_assets_frontend_safety_report({'index.html':html,'app.js':js,'style.css':css})
    for f in safety.findings:
        if f.severity==LocalConsoleRefreshSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        elif f.marker not in {'xttrader'}: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    features=[RefreshFeature('hash route 只读导航增强',LocalConsoleRefreshFeatureType.HASH_NAVIGATION),RefreshFeature('只读刷新按钮',LocalConsoleRefreshFeatureType.READONLY_REFRESH),RefreshFeature('本地 data_bundle reload',LocalConsoleRefreshFeatureType.DATA_BUNDLE_RELOAD),RefreshFeature('latest updated 时间显示',LocalConsoleRefreshFeatureType.UPDATED_AT_DISPLAY),RefreshFeature('loading/error/empty state 占位',LocalConsoleRefreshFeatureType.LOADING_STATE),RefreshFeature('安全横幅固定展示',LocalConsoleRefreshFeatureType.SAFETY_BANNER),RefreshFeature('Stage69 计划',LocalConsoleRefreshFeatureType.NEXT_STAGE_PLAN)]
    decision=LocalConsoleRefreshDecision.READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW
    if not preview.exists(): decision=LocalConsoleRefreshDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleRefreshDecision.NO_GO
    return LocalConsoleRefreshReport(decision,cfg,evidence,features,build_navigation_route_map(),ReadonlyRefreshAction(),build_ui_state_placeholders(),safety.findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_refresh_report(r,output,json_output): _write(output,format_local_console_refresh_report_md(r)); _write_json(json_output,r)
def load_local_console_refresh_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_navigation_route_map_report(r): return NavigationRouteMapReport(r.routes,FORBIDDEN_HASH_ROUTES)
def save_navigation_route_map_report(r,output,json_output): _write(output,format_json_md('Stage68 Navigation Route Map',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_refresh_manifest_report(r): return RefreshManifestReport(build_refresh_manifest())
def save_refresh_manifest_report(r,output,json_output): _write(output,format_json_md('Stage68 Refresh Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_ui_state_placeholder_report(r): return UiStatePlaceholderReport(r.ui_states)
def save_ui_state_placeholder_report(r,output,json_output): _write(output,format_json_md('Stage68 UI State Placeholders',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_frontend_safety_report_from_report(r): return FrontEndSafetyReport(r.safety_findings, sum(1 for x in r.safety_findings if x.severity==LocalConsoleRefreshSeverity.CRITICAL), r.warnings)
build_frontend_safety_report_service=build_frontend_safety_report_from_report
def save_frontend_safety_report(r,output,json_output): _write(output,format_json_md('Stage68 Frontend Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_console_grouping_filter_plan_report(config=None): return NextConsoleGroupingFilterPlanReport()
def save_next_console_grouping_filter_plan_report(r,output,json_output): _write(output,format_json_md('Stage69 Next Console Grouping Filter Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
# public Stage68 service name required by validation/tests
def build_frontend_safety_report(r):
    return FrontEndSafetyReport(r.safety_findings, sum(1 for x in r.safety_findings if x.severity==LocalConsoleRefreshSeverity.CRITICAL), r.warnings)
