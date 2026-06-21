from __future__ import annotations
import json, shutil
from pathlib import Path
from .acceptance_models import *
from .acceptance_assets import *
from .acceptance_reader import read_json
from .acceptance_formatters import format_local_console_ui_acceptance_report_md, format_json_md
from .acceptance_safety import assert_stage72_read_only, assert_no_forbidden_acceptance_actions, scan_acceptance_assets_for_forbidden_markers

def build_default_local_console_acceptance_config(**kw): return LocalConsoleAcceptanceConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage,path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleAcceptanceEvidence(stage,obj['source'],LocalConsoleAcceptanceStatus.PASS if obj['status']=='PASS' else LocalConsoleAcceptanceStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def run_local_console_ui_acceptance_review(config=None):
    cfg=config or LocalConsoleAcceptanceConfig(); assert_stage72_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_acceptance_index_html(); js=build_acceptance_app_js(); css=build_acceptance_style_css(); assert_no_forbidden_acceptance_actions(js)
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    for srcdir in [root/cfg.binding_dir, root/cfg.review_dir]:
        p=srcdir/'static_data_safety.json'
        if p.exists(): shutil.copyfile(p,out/'static_data_safety.json'); break
    else: _write_json(out/'static_data_safety.json',{'read_only':True,'safety_banner':SAFETY_BANNER})
    evid=[_evidence('Stage71',root/cfg.review_dir/'local_console_review_workbench_report.json'),_evidence('Stage70',root/cfg.drilldown_dir/'local_console_drilldown_report.json'),_evidence('Stage69',root/cfg.grouping_dir/'local_console_grouping_report.json'),_evidence('Stage68',root/cfg.refresh_dir/'local_console_refresh_report.json'),_evidence('Stage67',root/cfg.preview_dir/'local_console_preview_report.json'),_evidence('Stage66',root/cfg.binding_dir/'binding_manifest.json')]
    findings=scan_acceptance_assets_for_forbidden_markers({'index.html':html,'app.js':js,'style.css':css})
    warnings=[]; blocking=[]
    if evid[0].status==LocalConsoleAcceptanceStatus.UNAVAILABLE: warnings.append('Stage71 package unavailable; UI acceptance needs more evidence')
    if evid[0].decision=='NO_GO' or evid[0].critical_count>0: blocking.append('Stage71 NO_GO or critical findings present')
    for f in findings:
        if f.severity==LocalConsoleAcceptanceSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleAcceptanceDecision.READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW
    if evid[0].status==LocalConsoleAcceptanceStatus.UNAVAILABLE: decision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleAcceptanceDecision.NO_GO
    pages=build_page_inventory(); features=build_feature_inventory(); checklist=build_safety_checklist(); open_items=build_open_items(); routes=build_route_coverage(); assets=build_asset_coverage(); conclusion=build_acceptance_conclusion_draft(decision); package=build_acceptance_package_index(); summary=build_ui_acceptance_summary(decision)
    return LocalConsoleUiAcceptanceReport(decision,cfg,evid,summary,pages,features,checklist,open_items,routes,assets,conclusion,package,findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_ui_acceptance_report(r,output,json_output): _write(output,format_local_console_ui_acceptance_report_md(r)); _write_json(json_output,r)
def load_local_console_ui_acceptance_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_ui_acceptance_summary_report(r): return r.ui_summary
def save_ui_acceptance_summary_report(r,output,json_output): _write(output,format_json_md('Stage72 UI Acceptance Summary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_page_inventory_report(r): return UiPageInventoryReport(r.page_inventory)
def save_page_inventory_report(r,output,json_output): _write(output,format_json_md('Stage72 Page Inventory',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_feature_inventory_report(r): return UiFeatureInventoryReport(r.feature_inventory)
def save_feature_inventory_report(r,output,json_output): _write(output,format_json_md('Stage72 Feature Inventory',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_safety_checklist_report(r): return UiSafetyChecklistReport(r.safety_checklist)
def save_safety_checklist_report(r,output,json_output): _write(output,format_json_md('Stage72 Safety Checklist',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_open_items_report(r): return UiOpenItemsReport(r.open_items)
def save_open_items_report(r,output,json_output): _write(output,format_json_md('Stage72 Open Items',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_route_coverage_report(r): return UiRouteCoverageReport(r.route_coverage,FORBIDDEN)
def save_route_coverage_report(r,output,json_output): _write(output,format_json_md('Stage72 Route Coverage',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_asset_coverage_report(r): return UiAssetCoverageReport(r.asset_coverage)
def save_asset_coverage_report(r,output,json_output): _write(output,format_json_md('Stage72 Asset Coverage',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_acceptance_conclusion_draft_report(r): return AcceptanceConclusionDraftReport(r.conclusion_draft)
def save_acceptance_conclusion_draft_report(r,output,json_output): _write(output,format_json_md('Stage72 Acceptance Conclusion Draft',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_acceptance_package_index_report(r): return AcceptancePackageIndexReport(r.package_index)
def save_acceptance_package_index_report(r,output,json_output): _write(output,format_json_md('Stage72 Acceptance Package Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_ui_acceptance_safety_report(r): return build_ui_acceptance_safety_report_assets(r.safety_findings) if False else UiAcceptanceSafetyReport(r.safety_findings,sum(1 for x in r.safety_findings if x.severity==LocalConsoleAcceptanceSeverity.CRITICAL),r.warnings)
def save_ui_acceptance_safety_report(r,output,json_output): _write(output,format_json_md('Stage72 UI Acceptance Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_local_help_docs_plan_report(config=None): return build_next_local_help_docs_plan()
def save_next_local_help_docs_plan_report(r,output,json_output): _write(output,format_json_md('Stage73 Next Local Help Docs Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
