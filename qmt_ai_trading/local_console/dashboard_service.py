from __future__ import annotations
import json
from pathlib import Path
from .dashboard_models import *
from .dashboard_reader import read_json_evidence, read_latest_validation_detail
from .dashboard_cards import *
from .dashboard_formatters import *
from .dashboard_safety import scan_local_console_dashboard_text_for_forbidden_markers, assert_no_forbidden_dashboard_routes

def build_default_local_console_dashboard_config(**kw): return LocalConsoleDashboardConfig(**kw)
def _write(p,t): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(t,encoding='utf-8')
def _write_json(p,o): _write(p,json.dumps(to_plain(o),ensure_ascii=False,indent=2))
def _paths(cfg):
    return [('Stage63',Path(cfg.local_console_detail_dir)/'local_console_detail_report.json'),('Stage62',Path(cfg.local_console_dir)/'local_console_report.json'),('Stage61',Path(cfg.api_gateway_dir)/'api_gateway_report.json'),('Stage60',Path(cfg.pre_gray_final_review_dir)/'pre_gray_final_review.json'),('Stage59',Path(cfg.readonly_seal_dir)/'live_gray_readonly_seal.json'),('Stage58',Path(cfg.final_approval_dir)/'live_gray_final_approval.json'),('Stage57',Path(cfg.gray_candidate_dir)/'live_gray_candidate.json'),('Stage56',Path(cfg.real_cache_quality_dir)/'real_cache_quality.json'),('Stage55',Path(cfg.qmt_dryrun_calibration_dir)/'qmt_dryrun_calibration.json')]
def run_local_console_dashboard_review(config=None):
    cfg=config or LocalConsoleDashboardConfig(); root=Path(cfg.repo_root)
    evidence=[read_json_evidence(s, root/p) for s,p in _paths(cfg)]
    validation=read_latest_validation_detail(root/'validation_logs')
    warnings=[]; blocking=[]; decision=LocalConsoleDashboardDecision.READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW
    st63=evidence[0]
    if st63.status==LocalConsoleDashboardStatus.UNAVAILABLE:
        decision=LocalConsoleDashboardDecision.NEED_MORE_EVIDENCE; warnings.append('Stage63 local console detail package unavailable; dashboard review needs more evidence')
    if st63.decision=='NO_GO' or st63.critical_count>0:
        decision=LocalConsoleDashboardDecision.NO_GO; blocking.append('Stage63 NO_GO or critical findings present')
    if st63.decision and st63.decision not in ('READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW','READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW') and st63.decision!='NO_GO': decision=LocalConsoleDashboardDecision.NEED_MORE_EVIDENCE
    for ev in evidence:
        text=json.dumps(ev.metadata.get('data',{}),ensure_ascii=False)
        for m in scan_local_console_dashboard_text_for_forbidden_markers(text, ev.path, generated=True):
            if m['severity']=='CRITICAL': blocking.append(f"critical forbidden marker {m['marker']} in {ev.stage}")
        warnings.extend([f'{ev.stage}: {w}' for w in ev.warnings])
    bad_routes=assert_no_forbidden_dashboard_routes(DASHBOARD_ROUTES)
    if bad_routes: blocking.append(f'forbidden dashboard routes: {bad_routes}')
    if blocking: decision=LocalConsoleDashboardDecision.NO_GO
    cards=[build_stage_status_card(evidence),build_latest_validation_card(validation),build_warning_blocking_stats_card(evidence),build_manifest_hash_card(evidence),build_scheduler_preview_card(),build_safety_boundary_card(),build_api_capability_card(next((e for e in evidence if e.stage=='Stage61'),None)),build_detail_filter_card(st63)]
    return LocalConsoleDashboardReport(decision=decision,evidence=evidence,route_index=DASHBOARD_ROUTES,cards=cards,warnings=warnings,blocking_reasons=blocking)
def save_local_console_dashboard_report(r,output,json_output): _write(output,format_dashboard_report_md(r)); _write_json(json_output,r)
def load_local_console_dashboard_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def build_dashboard_card_index_report(r): return DashboardCardIndexReport(r.cards,r.route_index,r.warnings)
def save_dashboard_card_index_report(r,output,json_output): _write(output,format_card_index_md(r)); _write_json(json_output,r)
def build_stage_status_cards_report(r): return StageStatusCardsReport([c for c in r.cards if c.card_id=='stage-status'])
def save_stage_status_cards_report(r,output,json_output): _write(output,format_stage_status_cards_md(r)); _write_json(json_output,r)
def _find(r,cid): return next((c for c in r.cards if c.card_id==cid),DashboardCard(card_id=cid,title=cid))
def build_warning_blocking_stats_report(r): return WarningBlockingStatsReport(_find(r,'warning-blocking-stats'))
def save_warning_blocking_stats_report(r,output,json_output): _write(output,format_single_card_report_md('Warning Blocking Stats',r.card)); _write_json(json_output,r)
def build_manifest_hash_status_report(r): return ManifestHashStatusReport(_find(r,'manifest-hash'))
def save_manifest_hash_status_report(r,output,json_output): _write(output,format_single_card_report_md('Manifest Hash Status',r.card)); _write_json(json_output,r)
def build_scheduler_preview_status_report(r): return SchedulerPreviewStatusReport(_find(r,'scheduler-preview'))
def save_scheduler_preview_status_report(r,output,json_output): _write(output,format_single_card_report_md('Scheduler Preview Status',r.card)); _write_json(json_output,r)
def build_safety_boundary_status_report(r): return SafetyBoundaryStatusReport(_find(r,'safety-boundary'))
def save_safety_boundary_status_report(r,output,json_output): _write(output,format_single_card_report_md('Safety Boundary Status',r.card)); _write_json(json_output,r)
def build_next_console_shell_plan_report(config=None): return NextConsoleShellPlanReport()
def save_next_console_shell_plan_report(r,output,json_output): _write(output,format_next_shell_plan_md(r)); _write_json(json_output,r)
