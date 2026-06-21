from __future__ import annotations
import json, shutil
from pathlib import Path
from .grouping_models import *
from .grouping_assets import *
from .grouping_reader import read_json
from .grouping_formatters import format_local_console_grouping_report_md, format_json_md
from .grouping_safety import assert_stage69_read_only, assert_no_forbidden_grouping_actions

def build_default_local_console_grouping_config(**kw): return LocalConsoleGroupingConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))

def run_local_console_grouping_review(config=None):
    cfg=config or LocalConsoleGroupingConfig(); assert_stage69_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; binding=root/cfg.binding_dir; refresh=root/cfg.refresh_dir; preview=root/cfg.preview_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_grouping_index_html(); js=build_grouping_app_js(); css=build_grouping_style_css()
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    for n in ['data_bundle.json','binding_manifest.json','data_source_map.json','static_data_safety.json']:
        src=binding/n
        if src.exists(): shutil.copyfile(src,out/n)
        else: _write_json(out/n, {'read_only':True,'warning':f'{n} unavailable'})
    warnings=[]; blocking=[]
    ref=read_json(refresh/'local_console_refresh_report.json'); data=ref.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0); dec=str(data.get('decision',''))
    evidence=[LocalConsoleGroupingEvidence('Stage68',ref['source'],LocalConsoleGroupingStatus.PASS if ref['status']=='PASS' else LocalConsoleGroupingStatus.UNAVAILABLE,dec,crit,ref['summary'],ref.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])]
    if not refresh.exists(): warnings.append('Stage68 package unavailable; grouping review needs more evidence')
    if dec=='NO_GO' or crit>0: blocking.append('Stage68 NO_GO or critical findings present')
    try: assert_no_forbidden_grouping_actions(js)
    except ValueError as exc: blocking.append(str(exc))
    safety=build_frontend_grouping_safety_report({'index.html':html,'app.js':js,'style.css':css})
    for f in safety.findings:
        if f.severity==LocalConsoleGroupingSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleGroupingDecision.READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW
    if not refresh.exists(): decision=LocalConsoleGroupingDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleGroupingDecision.NO_GO
    return LocalConsoleGroupingReport(decision,cfg,evidence,build_grouping_manifest(),build_filter_state_schema(),build_grouped_card_index(),build_search_index(),safety.findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking),'status_groups':['PASS','WARN','FAIL','SKIPPED','UNAVAILABLE'],'severity_groups':['INFO','WARN','CRITICAL']})

def save_local_console_grouping_report(r,output,json_output): _write(output,format_local_console_grouping_report_md(r)); _write_json(json_output,r)
def load_local_console_grouping_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_grouping_manifest_report(r): return r.manifest
def save_grouping_manifest_report(r,output,json_output): _write(output,format_json_md('Stage69 Grouping Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_filter_state_schema_report(r): return GroupingFilterStateReport(r.filter_state)
def save_filter_state_schema_report(r,output,json_output): _write(output,format_json_md('Stage69 Filter State Schema',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_grouped_card_index_report(r): return GroupedCardIndexReport(r.card_index)
def save_grouped_card_index_report(r,output,json_output): _write(output,format_json_md('Stage69 Grouped Card Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_search_index_report(r): return SearchIndexReport(r.search_index)
def save_search_index_report(r,output,json_output): _write(output,format_json_md('Stage69 Search Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_frontend_grouping_safety_report_from_report(r): return GroupingFrontendSafetyReport(r.safety_findings, sum(1 for x in r.safety_findings if x.severity==LocalConsoleGroupingSeverity.CRITICAL), r.warnings)
def save_frontend_grouping_safety_report(r,output,json_output): _write(output,format_json_md('Stage69 Frontend Grouping Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_console_drilldown_export_plan_report(config=None): return NextConsoleDrilldownExportPlanReport()
def save_next_console_drilldown_export_plan_report(r,output,json_output): _write(output,format_json_md('Stage70 Next Console Drilldown Export Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_frontend_grouping_safety_report(r):
    if isinstance(r, dict):
        from .grouping_assets import build_frontend_grouping_safety_report as asset_builder
        return asset_builder(r)
    return build_frontend_grouping_safety_report_from_report(r)
