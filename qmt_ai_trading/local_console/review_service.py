from __future__ import annotations
import json, shutil
from pathlib import Path
from .review_models import *
from .review_assets import *
from .review_reader import read_json
from .review_formatters import format_local_console_review_workbench_report_md, format_json_md
from .review_safety import assert_stage71_read_only, assert_no_forbidden_review_actions

def build_default_local_console_review_config(**kw): return LocalConsoleReviewConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _evidence(stage, path):
    obj=read_json(path); data=obj.get('data') or {}; summ=data.get('summary',{}) if isinstance(data,dict) else {}; crit=int(summ.get('critical_count',data.get('critical_count',0) or 0) or 0) if isinstance(data,dict) else 0
    return LocalConsoleReviewEvidence(stage,obj['source'],LocalConsoleReviewStatus.PASS if obj['status']=='PASS' else LocalConsoleReviewStatus.UNAVAILABLE,str(data.get('decision','')) if isinstance(data,dict) else '',crit,obj['summary'],obj.get('warnings',[]),list(data.get('blocking_reasons',[])) if isinstance(data,dict) else [])

def run_local_console_review_workbench_review(config=None):
    cfg=config or LocalConsoleReviewConfig(); assert_stage71_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization)
    root=Path(cfg.repo_root); out=root/cfg.output_dir; out.mkdir(parents=True,exist_ok=True)
    html=build_review_index_html(); js=build_review_app_js(); css=build_review_style_css(); assert_no_forbidden_review_actions(js)
    _write(out/'index.html',html); _write(out/'app.js',js); _write(out/'style.css',css)
    binding=root/cfg.binding_dir
    for n in ['data_bundle.json','static_data_safety.json']:
        src=binding/n
        if src.exists(): shutil.copyfile(src,out/n)
        else: _write_json(out/n, {'read_only':True,'warning':f'{n} unavailable'})
    checklist=build_review_checklist(); notes=build_review_notes_template(); confirmations=build_local_confirmation_checklist(); package=build_review_package_index(); safety=build_review_safety_report({'index.html':html,'app.js':js,'style.css':css})
    evid=[_evidence('Stage70', root/cfg.drilldown_dir/'local_console_drilldown_report.json'), _evidence('Stage69', root/cfg.grouping_dir/'local_console_grouping_report.json'), _evidence('Stage68', root/cfg.refresh_dir/'local_console_refresh_report.json'), _evidence('Stage67', root/cfg.preview_dir/'local_console_preview_report.json'), _evidence('Stage66', root/cfg.binding_dir/'binding_manifest.json')]
    warnings=[]; blocking=[]
    if evid[0].status==LocalConsoleReviewStatus.UNAVAILABLE: warnings.append('Stage70 package unavailable; review workbench needs more evidence')
    if evid[0].decision=='NO_GO' or evid[0].critical_count>0: blocking.append('Stage70 NO_GO or critical findings present')
    for f in safety.findings:
        if f.severity==LocalConsoleReviewSeverity.CRITICAL: blocking.append(f'CRITICAL marker {f.marker} in {f.path}')
        else: warnings.append(f'{f.severity.value} marker {f.marker} in {f.path}')
    decision=LocalConsoleReviewDecision.READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW
    if evid[0].status==LocalConsoleReviewStatus.UNAVAILABLE: decision=LocalConsoleReviewDecision.NEED_MORE_EVIDENCE
    if blocking: decision=LocalConsoleReviewDecision.NO_GO
    return LocalConsoleReviewWorkbenchReport(decision,cfg,evid,checklist,notes,confirmations,package,ReviewStatusPlaceholder(),ReviewConclusionDraft(decision),safety.findings,warnings,blocking,{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':len(blocking)})

def save_local_console_review_workbench_report(r,output,json_output): _write(output,format_local_console_review_workbench_report_md(r)); _write_json(json_output,r)
def load_local_console_review_workbench_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_review_manifest_report(r=None): return build_review_manifest()
def save_review_manifest_report(r,output,json_output): _write(output,format_json_md('Stage71 Manual Review Manifest',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_review_checklist_report(r): return ReviewChecklistReport(r.checklist)
def save_review_checklist_report(r,output,json_output): _write(output,format_json_md('Stage71 Review Checklist',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_review_notes_template_report(r): return ReviewNotesTemplateReport(r.notes_template)
def save_review_notes_template_report(r,output,json_output): _write(output,format_json_md('Stage71 Review Notes Template',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_local_confirmation_checklist_report(r): return LocalConfirmationChecklistReport(r.confirmations)
def save_local_confirmation_checklist_report(r,output,json_output): _write(output,format_json_md('Stage71 Local Confirmation Checklist',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_review_package_index_report(r): return ReviewPackageIndexReport(r.package_index)
def save_review_package_index_report(r,output,json_output): _write(output,format_json_md('Stage71 Review Package Index',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_review_safety_report_from_report(r): return ReviewSafetyReport(r.safety_findings, sum(1 for x in r.safety_findings if x.severity==LocalConsoleReviewSeverity.CRITICAL), r.warnings)
def save_review_safety_report(r,output,json_output): _write(output,format_json_md('Stage71 Review Safety Report',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
def build_next_ui_acceptance_summary_plan_report(config=None): return build_next_ui_acceptance_summary_plan()
def save_next_ui_acceptance_summary_plan_report(r,output,json_output): _write(output,format_json_md('Stage72 Next UI Acceptance Summary Plan',json.dumps(to_plain(r),ensure_ascii=False,indent=2))); _write_json(json_output,r)
