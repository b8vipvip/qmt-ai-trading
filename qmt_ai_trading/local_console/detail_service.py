from __future__ import annotations
import json
from pathlib import Path
from .detail_models import *
from .detail_reader import build_stage_detail_from_json, read_latest_validation_detail
from .filtering import *
from .detail_formatters import *
from .safety import FORBIDDEN_ROUTES, scan_local_console_detail_text_for_forbidden_markers

DETAIL_ROUTES=['/dashboard/detail','/reports/detail','/reports/stage62/detail','/reports/stage61/detail','/reports/stage60/detail','/reports/stage59/detail','/reports/stage58/detail','/reports/stage57/detail','/reports/stage56/detail','/reports/stage55/detail','/filters/stage','/filters/status','/filters/severity','/filters/warnings','/filters/blocking-reasons','/manifest/detail','/validation/latest/detail','/safety/detail','/api-capabilities/detail','/scheduler-preview/detail']

def build_default_local_console_detail_config(**kw): return LocalConsoleDetailConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _paths(cfg):
    return [('Stage62',Path(cfg.local_console_dir)/'local_console_report.json'),('Stage61',Path(cfg.api_gateway_dir)/'api_gateway_report.json'),('Stage60',Path(cfg.pre_gray_final_review_dir)/'pre_gray_final_review.json'),('Stage59',Path(cfg.readonly_seal_dir)/'live_gray_readonly_seal.json'),('Stage58',Path(cfg.final_approval_dir)/'live_gray_final_approval.json'),('Stage57',Path(cfg.gray_candidate_dir)/'live_gray_candidate.json'),('Stage56',Path(cfg.real_cache_quality_dir)/'real_cache_quality.json'),('Stage55',Path(cfg.qmt_dryrun_calibration_dir)/'qmt_dryrun_calibration.json')]
def run_local_console_detail_review(config=None):
    cfg=config or LocalConsoleDetailConfig(); root=Path(cfg.repo_root)
    evidence=[build_stage_detail_from_json(s, root/p) for s,p in _paths(cfg)]
    validation=read_latest_validation_detail(root/'validation_logs')
    warnings=[]; blocking=[]; decision=LocalConsoleDetailDecision.READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW
    st62=evidence[0]
    if st62.status==LocalConsoleDetailStatus.UNAVAILABLE:
        decision=LocalConsoleDetailDecision.NEED_MORE_EVIDENCE; warnings.append('Stage62 local console package unavailable; detail review needs more evidence')
    if st62.decision=='NO_GO' or st62.critical_count>0:
        decision=LocalConsoleDetailDecision.NO_GO; blocking.append('Stage62 NO_GO or critical findings present')
    if st62.decision and st62.decision not in ('READY_FOR_LOCAL_CONSOLE_REVIEW','READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW') and st62.decision!='NO_GO':
        decision=LocalConsoleDetailDecision.NEED_MORE_EVIDENCE
    for ev in evidence:
        text=json.dumps(ev.metadata.get('data',{}),ensure_ascii=False)
        markers=scan_local_console_detail_text_for_forbidden_markers(text, ev.path, generated=True)
        for m in markers:
            if m['severity']=='CRITICAL': blocking.append(f"critical forbidden marker {m['marker']} in {ev.stage}")
        warnings.extend([f"{ev.stage}: {w}" for w in ev.warnings])
    if blocking: decision=LocalConsoleDetailDecision.NO_GO
    fidx=build_filter_index(evidence,validation,DETAIL_ROUTES)
    safety=ConsoleSafetyDetail(forbidden_routes=sorted(FORBIDDEN_ROUTES),warnings=['Stage63 detail layer is read-only and cannot expose forbidden routes/actions'])
    return LocalConsoleDetailReport(decision=decision,evidence=evidence,route_index=DETAIL_ROUTES,filter_index=fidx,validation_detail=validation,safety_detail=safety,warnings=warnings,blocking_reasons=blocking,summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True})
def save_local_console_detail_report(r,output,json_output): _write(output,format_detail_report_md(r)); _write_json(json_output,r)
def load_local_console_detail_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_console_filter_index_report(report_or_config=None):
    r=report_or_config if isinstance(report_or_config,LocalConsoleDetailReport) else run_local_console_detail_review(report_or_config)
    return ConsoleFilterIndexReport(r.filter_index,r.route_index,r.warnings)
def save_console_filter_index_report(r,output,json_output): _write(output,format_filter_index_md(r)); _write_json(json_output,r)
def build_console_warnings_report(report): return ConsoleWarningsReport(collect_warnings(report.evidence)+[ConsoleWarningItem('Stage63',w) for w in report.warnings])
def save_console_warnings_report(r,output,json_output): _write(output,format_warnings_md(r)); _write_json(json_output,r)
def build_console_blocking_reasons_report(report): return ConsoleBlockingReasonsReport(collect_blocking_reasons(report.evidence)+[ConsoleBlockingReasonItem('Stage63',b) for b in report.blocking_reasons])
def save_console_blocking_reasons_report(r,output,json_output): _write(output,format_blocking_md(r)); _write_json(json_output,r)
def build_console_manifest_detail_report(report): return ConsoleManifestDetailReport(collect_manifest_items(report.evidence))
def save_console_manifest_detail_report(r,output,json_output): _write(output,format_manifest_md(r)); _write_json(json_output,r)
def build_console_validation_detail_report(report): return ConsoleValidationDetailReport(report.validation_detail)
def save_console_validation_detail_report(r,output,json_output): _write(output,format_validation_md(r)); _write_json(json_output,r)
def build_next_console_overview_plan_report(config=None): return NextConsoleOverviewPlanReport()
def save_next_console_overview_plan_report(r,output,json_output): _write(output,format_next_overview_plan_md(r)); _write_json(json_output,r)
