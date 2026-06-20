from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .reader import read_console_json, read_latest_validation_summary, read_console_markdown_summary
from .console_index import *
from .formatters import *
from .safety import scan_local_console_text_for_forbidden_markers
def build_default_local_console_config(**kw): return LocalConsoleConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _ev(cat,path,root):
    e=read_console_json(Path(root)/path); e.category=cat; e.title=Path(path).name; e.path=str(path)
    if e.status==LocalConsoleStatus.PASS: e.severity=LocalConsoleSeverity.INFO
    return e
def run_local_console_review(config=None):
    cfg=config or LocalConsoleConfig(); root=Path(cfg.repo_root)
    mapping=[(LocalConsoleCategory.STAGE61_API_GATEWAY,Path(cfg.api_gateway_dir)/'api_gateway_report.json'),(LocalConsoleCategory.STAGE60_PRE_GRAY_FINAL_REVIEW,Path(cfg.pre_gray_final_review_dir)/'pre_gray_final_review.json'),(LocalConsoleCategory.STAGE59_READONLY_SEAL,Path(cfg.readonly_seal_dir)/'live_gray_readonly_seal.json'),(LocalConsoleCategory.STAGE58_FINAL_APPROVAL,Path(cfg.final_approval_dir)/'live_gray_final_approval.json'),(LocalConsoleCategory.STAGE57_GRAY_CANDIDATE,Path(cfg.gray_candidate_dir)/'live_gray_candidate.json'),(LocalConsoleCategory.STAGE56_REAL_CACHE_QUALITY,Path(cfg.real_cache_quality_dir)/'real_cache_quality.json'),(LocalConsoleCategory.STAGE55_QMT_DRYRUN_CALIBRATION,Path(cfg.qmt_dryrun_calibration_dir)/'qmt_dryrun_calibration.json')]
    evidence=[_ev(c,p,root) for c,p in mapping]
    val=read_latest_validation_summary(root/'validation_logs'); evidence.append(val)
    routes=build_console_route_index(cfg); reports=build_console_report_list(cfg); safety=build_console_safety_boundary(cfg)
    warnings=[]; blocking=[]; decision=LocalConsoleDecision.READY_FOR_LOCAL_CONSOLE_REVIEW
    st61=evidence[0]; data=st61.metadata.get('data') or {}; critical=(data.get('summary') or {}).get('critical_count',data.get('critical_count',0)) or 0
    if st61.status==LocalConsoleStatus.UNAVAILABLE:
        decision=LocalConsoleDecision.NEED_MORE_EVIDENCE; warnings.append('Stage61 API Gateway package unavailable; local console review needs more evidence')
    elif data.get('decision')=='NO_GO' or critical:
        decision=LocalConsoleDecision.NO_GO; blocking.append('Stage61 NO_GO or critical findings present')
    for ev in evidence:
        if ev.metadata.get('data'):
            markers=scan_local_console_text_for_forbidden_markers(json.dumps(ev.metadata['data'],ensure_ascii=False), ev.path, generated=True)
            if any(m['severity']=='CRITICAL' for m in markers): blocking.append(f'critical forbidden marker in {ev.path}')
    manifest=read_console_markdown_summary(root/Path(cfg.api_gateway_dir)/'route_index.json',800)
    return LocalConsoleReport(decision=decision,evidence=evidence,route_index=routes,report_list=reports,safety_boundary=safety,validation_summary=val.summary[:1200],manifest_summary=manifest,scheduler_preview_summary='scheduler/register preview only; read_only=True; dry_run_only=True; no_trade_authorization=True; no_task_registered=True',blocking_reasons=blocking,warnings=warnings,summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True})
def save_local_console_report(r,output,json_output): _write(output,format_local_console_report_md(r)); _write_json(json_output,r)
def load_local_console_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_console_index_report(config=None): return LocalConsoleIndexReport(build_console_route_index(config),build_console_dashboard_sections(config))
def save_console_index_report(r,output,json_output): _write(output,format_console_index_md(r)); _write_json(json_output,r)
def build_console_report_list_report(config=None): return LocalConsoleReportListReport(build_console_report_list(config))
def save_console_report_list_report(r,output,json_output): _write(output,format_report_list_md(r)); _write_json(json_output,r)
def build_console_safety_report(config=None): return LocalConsoleSafetyReport(build_console_safety_boundary(config))
def save_console_safety_report(r,output,json_output): _write(output,format_console_safety_md(r)); _write_json(json_output,r)
def build_next_console_detail_plan_report(config=None): return build_next_console_detail_plan(config)
def save_next_console_detail_plan_report(r,output,json_output): _write(output,format_next_plan_md(r)); _write_json(json_output,r)
