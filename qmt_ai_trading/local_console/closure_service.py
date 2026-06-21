from __future__ import annotations
import json
from pathlib import Path
from .closure_models import *
from .closure_assets import *
from .closure_reader import read_json
from .closure_formatters import format_ui_productization_closure_report_md, format_json_md
from .closure_safety import assert_stage75_read_only, scan_closure_assets_for_forbidden_markers

def build_default_local_console_closure_config(**kw): return LocalConsoleClosureConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage,path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleClosureEvidence(stage,obj['source'],LocalConsoleClosureStatus.PASS if obj['status']=='PASS' else LocalConsoleClosureStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])
def run_ui_productization_closure_review(config=None):
    cfg=config or LocalConsoleClosureConfig(); assert_stage75_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_closure_index_html(); js=build_closure_app_js(); css=build_closure_style_css(); _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    evidence=[_evidence('Stage74',root/cfg.demo_dir/'local_console_demo_package_report.json'),_evidence('Stage73',root/cfg.help_dir/'local_console_help_docs_report.json'),_evidence('Stage72',root/cfg.acceptance_dir/'local_console_ui_acceptance_report.json'),_evidence('Stage71',root/cfg.review_dir/'local_console_review_workbench_report.json'),_evidence('Stage70',root/cfg.drilldown_dir/'local_console_drilldown_report.json'),_evidence('Stage69',root/cfg.grouping_dir/'local_console_grouping_report.json'),_evidence('Stage68',root/cfg.refresh_dir/'local_console_refresh_report.json')]
    findings=scan_closure_assets_for_forbidden_markers({'index.html':html,'app.js':js,'style.css':css})
    warnings=[]; blocking=[]
    if evidence[0].status==LocalConsoleClosureStatus.UNAVAILABLE: warnings.append('Stage74 package unavailable; closure review needs more evidence')
    if evidence[0].decision=='NO_GO' or evidence[0].critical_count>0: blocking.append('Stage74 NO_GO or critical findings present')
    for f in findings:
        if f.severity==LocalConsoleClosureSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleClosureDecision.READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW
    if evidence[0].status==LocalConsoleClosureStatus.UNAVAILABLE: decision=LocalConsoleClosureDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleClosureDecision.NO_GO
    return UiProductizationClosureReport(decision,cfg,evidence,build_stage_overview(),build_capability_matrix(),build_safety_boundary_table(),build_readonly_demo_entry(),build_route_coverage_summary(),build_asset_coverage_summary(),build_risk_limitation_summary(),build_final_acceptance_conclusion_draft(),build_future_roadmap_recommendation(),findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':sum(1 for f in findings if f.severity==LocalConsoleClosureSeverity.CRITICAL)+len(blocking)})
def save_ui_productization_closure_report(r,output,json_output): _write(output,format_ui_productization_closure_report_md(r)); _write_json(json_output,r)
def load_ui_productization_closure_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_stage_overview_report(r=None): return UiStageOverviewReport(r.stage_overview if r else build_stage_overview())
def save_stage_overview_report(r,output,json_output): _write(output,format_json_md('Stage75 Stage Overview',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_capability_matrix_report(r=None): return UiCapabilityMatrixReport(r.capability_matrix if r else build_capability_matrix())
def save_capability_matrix_report(r,output,json_output): _write(output,format_json_md('Stage75 UI Capability Matrix',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_safety_boundary_table_report(r=None): return SafetyBoundaryTableReport(r.safety_boundary_table if r else build_safety_boundary_table())
def save_safety_boundary_table_report(r,output,json_output): _write(output,format_json_md('Stage75 Safety Boundary Table',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_readonly_demo_entry_report(r=None): return ReadonlyDemoEntryReport(r.readonly_demo_entry if r else build_readonly_demo_entry())
def save_readonly_demo_entry_report(r,output,json_output): _write(output,format_json_md('Stage75 Read-only Demo Entry',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_route_coverage_summary_report(r=None): return UiRouteCoverageSummaryReport(r.route_coverage_summary if r else build_route_coverage_summary(),FORBIDDEN_ROUTES)
def save_route_coverage_summary_report(r,output,json_output): _write(output,format_json_md('Stage75 Route Coverage Summary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_asset_coverage_summary_report(r=None): return UiAssetCoverageSummaryReport(r.asset_coverage_summary if r else build_asset_coverage_summary())
def save_asset_coverage_summary_report(r,output,json_output): _write(output,format_json_md('Stage75 Asset Coverage Summary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_risk_limitation_summary_report(r=None): return RiskLimitationSummaryReport(r.risk_limitation_summary if r else build_risk_limitation_summary())
def save_risk_limitation_summary_report(r,output,json_output): _write(output,format_json_md('Stage75 Risk Limitation Summary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_final_acceptance_conclusion_draft_report(r=None): return FinalAcceptanceConclusionDraftReport(r.final_acceptance_conclusion_draft if r else build_final_acceptance_conclusion_draft())
def save_final_acceptance_conclusion_draft_report(r,output,json_output): _write(output,format_json_md('Stage75 Final Acceptance Conclusion Draft',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_future_roadmap_recommendation_report(r=None): return FutureRoadmapRecommendationReport(r.future_roadmap_recommendation if r else build_future_roadmap_recommendation())
def save_future_roadmap_recommendation_report(r,output,json_output): _write(output,format_json_md('Stage75 Future Roadmap Recommendation',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_closure_safety_report(r=None): return ClosureSafetyReport(r.closure_safety_findings if r else [], sum(1 for x in (r.closure_safety_findings if r else []) if x.severity==LocalConsoleClosureSeverity.CRITICAL), (r.warnings if r else []))
def save_closure_safety_report(r,output,json_output): _write(output,format_json_md('Stage75 Closure Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
