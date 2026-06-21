from __future__ import annotations
import json, shutil
from pathlib import Path
from .drilldown_models import *
from .drilldown_assets import *
from .drilldown_reader import read_json
from .drilldown_formatters import format_local_console_drilldown_report_md, format_json_md
from .drilldown_safety import assert_stage70_read_only, assert_no_forbidden_drilldown_actions
from .drilldown_export import build_markdown_snapshot, build_json_snapshot

def build_default_local_console_drilldown_config(**kw): return LocalConsoleDrilldownConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))

def _evidence(stage, path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleDrilldownEvidence(stage,obj['source'],LocalConsoleDrilldownStatus.PASS if obj['status']=='PASS' else LocalConsoleDrilldownStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def run_local_console_drilldown_review(config=None):
    cfg=config or LocalConsoleDrilldownConfig(); assert_stage70_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_drilldown_index_html(); js=build_drilldown_app_js(); css=build_drilldown_style_css()
    assert_no_forbidden_drilldown_actions(js)
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    binding=root/cfg.binding_dir
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:
        src=binding/n
        if src.exists(): shutil.copyfile(src,out/n)
        else: _write_json(out/n, {'read_only':True,'warning':f'{n} unavailable'})
    items=build_report_detail_index(); routes=build_drilldown_route_map(); manifest=build_export_manifest(); snap=build_export_snapshot(); safety=build_export_safety_report({'index.html':html,'app.js':js,'style.css':css})
    _write_json(out/'report_detail_index.json', ReportDetailIndexReport(items)); _write_json(out/'export_manifest.json', ExportManifestReport(manifest))
    evid=[_evidence('Stage69', root/cfg.grouping_dir/'local_console_grouping_report.json'), _evidence('Stage68', root/cfg.refresh_dir/'local_console_refresh_report.json'), _evidence('Stage67', root/cfg.preview_dir/'local_console_preview_report.json'), _evidence('Stage66', root/cfg.binding_dir/'binding_manifest.json')]
    warnings=[]; blocking=[]
    if evid[0].status==LocalConsoleDrilldownStatus.UNAVAILABLE: warnings.append('Stage69 package unavailable; drilldown review needs more evidence')
    if evid[0].decision=='NO_GO' or evid[0].critical_count>0: blocking.append('Stage69 NO_GO or critical findings present')
    for f in safety.findings:
        if f.severity==LocalConsoleDrilldownSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleDrilldownDecision.READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW
    if evid[0].status==LocalConsoleDrilldownStatus.UNAVAILABLE: decision=LocalConsoleDrilldownDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleDrilldownDecision.NO_GO
    return LocalConsoleDrilldownReport(decision,cfg,evid,items,routes,manifest,snap,safety.findings,ReviewPackageEntry(),warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_drilldown_report(r,output,json_output): _write(output,format_local_console_drilldown_report_md(r)); _write_json(json_output,r)
def load_local_console_drilldown_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_report_detail_index_report(r): return ReportDetailIndexReport(r.detail_items)
def save_report_detail_index_report(r,output,json_output): _write(output,format_json_md('Stage70 Report Detail Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_drilldown_route_map_report(r): return ReportDrilldownRouteMapReport(r.routes)
def save_drilldown_route_map_report(r,output,json_output): _write(output,format_json_md('Stage70 Drilldown Route Map',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_export_manifest_report(r): return ExportManifestReport(r.export_manifest)
def save_export_manifest_report(r,output,json_output): _write(output,format_json_md('Stage70 Export Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_export_snapshot_report(r): return ExportSnapshotReport(r.export_snapshot)
def save_export_snapshot_report(r,output,json_output): _write(output,build_markdown_snapshot(r.snapshot)); _write(json_output,build_json_snapshot(r.snapshot))
def build_export_safety_report_from_report(r): return ExportSafetyReport(r.safety_findings, sum(1 for x in r.safety_findings if x.severity==LocalConsoleDrilldownSeverity.CRITICAL), r.warnings)
def save_export_safety_report(r,output,json_output): _write(output,format_json_md('Stage70 Export Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_manual_review_workbench_plan_report(config=None): return NextManualReviewWorkbenchPlanReport()
def save_next_manual_review_workbench_plan_report(r,output,json_output): _write(output,format_json_md('Stage71 Next Manual Review Workbench Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
