from __future__ import annotations
import json
from pathlib import Path
from .binding_models import *
from .binding_reader import read_json_or_markdown_tolerant, read_latest_validation_summary, build_data_source_entry
from .binding_assets import *
from .binding_formatters import format_binding_report_md, format_json_md
from .binding_safety import *

def build_default_local_console_binding_config(**kw): return LocalConsoleBindingConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _read(root,json_rel,md_rel,typ,target):
    r=read_json_or_markdown_tolerant(root/json_rel, root/md_rel if md_rel else None)
    src=build_data_source_entry(str(json_rel), typ, target, r)
    return LocalConsoleDataBinding(src, r.get('data') or {'summary':r.get('summary'),'warning':'missing data placeholder' if r.get('status')!='PASS' else ''})
def _evidence(stage, root, j, m):
    r=read_json_or_markdown_tolerant(root/j, root/m)
    data=r.get('data') if isinstance(r.get('data'),dict) else {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}
    crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0)
    return LocalConsoleBindingEvidence(stage=stage,path=r['source'],status=LocalConsoleBindingStatus.PASS if r['status']=='PASS' else LocalConsoleBindingStatus.WARN if r['status']=='WARN' else LocalConsoleBindingStatus.UNAVAILABLE,summary=r['summary'],decision=str(data.get('decision','')),critical_count=crit,warnings=list(data.get('warnings',[]))+r.get('warnings',[]),blocking_reasons=list(data.get('blocking_reasons',[])),metadata={'encoding':r.get('encoding'),'fallback_used':r.get('fallback_used')})
def run_local_console_binding_review(config=None):
    cfg=config or LocalConsoleBindingConfig(); root=Path(cfg.repo_root)
    ev=[_evidence('Stage65',root,Path(cfg.local_console_shell_dir)/'local_console_shell_report.json',Path(cfg.local_console_shell_dir)/'local_console_shell_report.md'),_evidence('Stage64',root,Path(cfg.local_console_dashboard_dir)/'local_console_dashboard_report.json',Path(cfg.local_console_dashboard_dir)/'local_console_dashboard_report.md'),_evidence('Stage63',root,Path(cfg.local_console_detail_dir)/'local_console_detail_report.json',Path(cfg.local_console_detail_dir)/'local_console_detail_report.md'),_evidence('Stage62',root,Path(cfg.local_console_dir)/'local_console_report.json',Path(cfg.local_console_dir)/'local_console_report.md'),_evidence('Stage61',root,Path(cfg.api_gateway_dir)/'api_gateway_report.json',Path(cfg.api_gateway_dir)/'api_gateway_report.md')]
    bindings=[_read(root,Path(cfg.local_console_dashboard_dir)/'dashboard_card_index.json',None,LocalConsoleBindingSourceType.DASHBOARD_CARD,'#dashboard-overview-section'),_read(root,Path(cfg.local_console_dashboard_dir)/'stage_status_cards.json',None,LocalConsoleBindingSourceType.DASHBOARD_CARD,'#stage-status-section'),_read(root,Path(cfg.local_console_dashboard_dir)/'warning_blocking_stats.json',None,LocalConsoleBindingSourceType.DASHBOARD_CARD,'#warning-blocking-section'),_read(root,Path(cfg.local_console_dashboard_dir)/'manifest_hash_status.json',None,LocalConsoleBindingSourceType.MANIFEST_HASH,'#manifest-section'),_read(root,Path(cfg.local_console_dashboard_dir)/'scheduler_preview_status.json',None,LocalConsoleBindingSourceType.SCHEDULER_PREVIEW,'#scheduler-preview-section'),_read(root,Path(cfg.local_console_dashboard_dir)/'safety_boundary_status.json',None,LocalConsoleBindingSourceType.SAFETY_BOUNDARY,'#safety-boundary-section'),_read(root,Path(cfg.local_console_dir)/'report_list.json',None,LocalConsoleBindingSourceType.REPORT_LIST,'#report-list-section'),_read(root,Path(cfg.local_console_detail_dir)/'filter_index.json',None,LocalConsoleBindingSourceType.DETAIL_FILTER,'#detail-filter-section'),_read(root,Path(cfg.api_gateway_dir)/'api_gateway_report.json',Path(cfg.api_gateway_dir)/'api_gateway_report.md',LocalConsoleBindingSourceType.API_CAPABILITY,'#api-capability-section')]
    val=read_latest_validation_summary(root/'validation_logs')
    warnings=[w for e in ev for w in e.warnings]+[w for b in bindings for w in b.source.warnings]+val.get('warnings',[])
    blocking=[]; decision=LocalConsoleBindingDecision.READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW
    st65=ev[0]
    if st65.status==LocalConsoleBindingStatus.UNAVAILABLE: decision=LocalConsoleBindingDecision.NEED_MORE_EVIDENCE; warnings.append('Stage65 package unavailable; binding review needs more evidence')
    if st65.decision=='NO_GO' or st65.critical_count>0: decision=LocalConsoleBindingDecision.NO_GO; blocking.append('Stage65 NO_GO or critical findings present')
    html,js,css=build_bound_index_html(),build_bound_app_js(),build_bound_style_css()
    for name,text,execflag in [('index.html',html,False),('app.js',js,True),('style.css',css,False)]:
        for m in scan_local_console_binding_asset_for_forbidden_markers(text,name,generated=True,executable=execflag):
            (blocking if m['severity']=='CRITICAL' else warnings).append(f"{m['severity']} marker {m['marker']} in {name}")
    if assert_no_forbidden_js_actions(js): blocking.append('forbidden JS action detected')
    bad=assert_no_forbidden_binding_routes(ROUTES)
    if bad: blocking.append(f'forbidden binding routes: {bad}')
    if blocking: decision=LocalConsoleBindingDecision.NO_GO
    bundle=build_data_bundle(bindings,val,warnings,blocking); manifest=to_plain(build_binding_manifest([b.source for b in bindings])); source_map=build_data_source_map(); placeholders=build_missing_data_placeholders([b.source for b in bindings]); assets=build_bound_asset_index()
    return LocalConsoleBindingReport(decision=decision,evidence=ev,data_bundle=bundle,manifest=manifest,data_source_map=source_map,placeholders=placeholders,assets=assets,warnings=warnings,blocking_reasons=blocking,summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})
def save_static_assets(out, report):
    out=Path(out); _write(out/'index.html',build_bound_index_html(report.data_bundle)); _write(out/'app.js',build_bound_app_js()); _write(out/'style.css',build_bound_style_css())
def save_local_console_binding_report(r,output,json_output): save_static_assets(Path(output).parent,r); _write(output,format_binding_report_md(r)); _write_json(json_output,r)
def load_local_console_binding_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_data_bundle_report(r): return LocalConsoleDataBundleReport(r.data_bundle)
def save_data_bundle_report(r,output,json_output): _write(output,format_json_md('Stage66 Data Bundle',json.dumps(r.bundle,ensure_ascii=False,indent=2))); _write_json(json_output,r.bundle)
def build_binding_manifest_report(r): return r.manifest
def save_binding_manifest_report(r,output,json_output): _write(output,format_json_md('Stage66 Binding Manifest',json.dumps(r,ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_data_source_map_report(r): return LocalConsoleDataSourceMapReport(r.data_source_map)
def save_data_source_map_report(r,output,json_output): _write(output,format_json_md('Stage66 Data Source Map',json.dumps(r.source_map,ensure_ascii=False,indent=2))); _write_json(json_output,r.source_map)
def build_missing_data_placeholder_report(r): return LocalConsoleMissingDataReport(r.placeholders)
def save_missing_data_placeholder_report(r,output,json_output): _write(output,format_json_md('Stage66 Missing Data Placeholders',json.dumps(to_plain(r.placeholders),ensure_ascii=False,indent=2))); _write_json(json_output,r.placeholders)
def build_bound_asset_index_report(r): return LocalConsoleBoundAssetReport(r.assets)
def save_bound_asset_index_report(r,output,json_output): _write(output,format_json_md('Stage66 Bound Asset Index',json.dumps(r.assets,ensure_ascii=False,indent=2))); _write_json(json_output,r.assets)
def build_static_data_safety_report(config=None): return build_static_data_safety()
def save_static_data_safety_report(r,output,json_output): _write(output,format_json_md('Stage66 Static Data Safety',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_console_preview_server_plan_report(config=None): return NextConsolePreviewServerPlanReport()
def save_next_console_preview_server_plan_report(r,output,json_output): _write(output,format_json_md('Stage67 Next Console Preview Server Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
