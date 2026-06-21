from __future__ import annotations
import json
from pathlib import Path
from .help_models import *
from .help_assets import *
from .help_reader import read_json
from .help_formatters import format_local_console_help_docs_report_md, format_json_md
from .help_safety import assert_stage73_read_only, assert_no_forbidden_help_actions, scan_help_assets_for_forbidden_markers

def build_default_local_console_help_config(**kw): return LocalConsoleHelpConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage,path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleHelpEvidence(stage,obj['source'],LocalConsoleHelpStatus.PASS if obj['status']=='PASS' else LocalConsoleHelpStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def run_local_console_help_docs_review(config=None):
    cfg=config or LocalConsoleHelpConfig(); assert_stage73_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_help_index_html(); js=build_help_app_js(); css=build_help_style_css(); assert_no_forbidden_help_actions(js)
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    evidence=[_evidence('Stage72',root/cfg.acceptance_dir/'local_console_ui_acceptance_report.json'),_evidence('Stage71',root/cfg.review_dir/'local_console_review_workbench_report.json'),_evidence('Stage70',root/cfg.drilldown_dir/'local_console_drilldown_report.json'),_evidence('Stage69',root/cfg.grouping_dir/'local_console_grouping_report.json'),_evidence('Stage68',root/cfg.refresh_dir/'local_console_refresh_report.json')]
    findings=scan_help_assets_for_forbidden_markers({'index.html':html,'app.js':js,'style.css':css})
    warnings=[]; blocking=[]
    if evidence[0].status==LocalConsoleHelpStatus.UNAVAILABLE: warnings.append('Stage72 package unavailable; help docs need more evidence')
    if evidence[0].decision=='NO_GO' or evidence[0].critical_count>0: blocking.append('Stage72 NO_GO or critical findings present')
    for f in findings:
        if f.severity==LocalConsoleHelpSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleHelpDecision.READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW
    if evidence[0].status==LocalConsoleHelpStatus.UNAVAILABLE: decision=LocalConsoleHelpDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleHelpDecision.NO_GO
    return LocalConsoleHelpDocsReport(decision,cfg,evidence,build_help_home(),build_page_help(),build_feature_help(),build_safety_help(),build_faq(),build_error_handling_guide(),build_glossary(),build_route_help_map(),build_help_package_index(),findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_help_docs_report(r,output,json_output): _write(output,format_local_console_help_docs_report_md(r)); _write_json(json_output,r)
def load_local_console_help_docs_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_help_home_report(r=None): return HelpHomeReport((r.help_home if r else build_help_home()))
def save_help_home_report(r,output,json_output): _write(output,format_json_md('Stage73 Help Home',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_page_help_report(r=None): return PageHelpReport((r.page_help if r else build_page_help()))
def save_page_help_report(r,output,json_output): _write(output,format_json_md('Stage73 Page Help',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_feature_help_report(r=None): return FeatureHelpReport((r.feature_help if r else build_feature_help()))
def save_feature_help_report(r,output,json_output): _write(output,format_json_md('Stage73 Feature Help',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_safety_help_report(r=None): return SafetyHelpReport((r.safety_help if r else build_safety_help()))
def save_safety_help_report(r,output,json_output): _write(output,format_json_md('Stage73 Safety Help',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_faq_report(r=None): return FaqReport((r.faq if r else build_faq()))
def save_faq_report(r,output,json_output): _write(output,format_json_md('Stage73 FAQ',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_error_handling_report(r=None): return ErrorHandlingReport((r.error_handling if r else build_error_handling_guide()))
def save_error_handling_report(r,output,json_output): _write(output,format_json_md('Stage73 Error Handling Guide',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_glossary_report(r=None): return GlossaryReport((r.glossary if r else build_glossary()))
def save_glossary_report(r,output,json_output): _write(output,format_json_md('Stage73 Glossary',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_route_help_map_report(r=None): return RouteHelpMapReport((r.route_help_map if r else build_route_help_map()),FORBIDDEN_ROUTES)
def save_route_help_map_report(r,output,json_output): _write(output,format_json_md('Stage73 Route Help Map',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_help_package_index_report(r=None): return HelpPackageIndexReport((r.help_package_index if r else build_help_package_index()))
def save_help_package_index_report(r,output,json_output): _write(output,format_json_md('Stage73 Help Package Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_docs_safety_report(r=None): return DocsSafetyReport((r.docs_safety_findings if r else []), sum(1 for x in (r.docs_safety_findings if r else []) if x.severity==LocalConsoleHelpSeverity.CRITICAL), (r.warnings if r else []))
def save_docs_safety_report(r,output,json_output): _write(output,format_json_md('Stage73 Docs Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_local_demo_package_plan_report(config=None): return build_next_local_demo_package_plan()
def save_next_local_demo_package_plan_report(r,output,json_output): _write(output,format_json_md('Stage74 Next Local Demo Package Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
