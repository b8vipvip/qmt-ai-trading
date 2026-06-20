from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .formatters import *
from .reader import read_json_report
def build_default_api_gateway_config(**kw): return ApiGatewayConfig(**kw)
def build_route_index(config=None):
    routes=['/health','/api/v1/capabilities','/api/v1/safety-boundary','/api/v1/roadmap/summary','/api/v1/architecture/summary','/api/v1/stages/status','/api/v1/stages/latest','/api/v1/reports/stage60','/api/v1/reports/stage59','/api/v1/reports/stage58','/api/v1/reports/stage57','/api/v1/reports/stage56','/api/v1/reports/stage55','/api/v1/manifest/stage59','/api/v1/validation/latest','/api/v1/scheduler/preview','/api/v1/console/shell','/api/v1/console/shell/manifest','/api/v1/console/shell/routes','/api/v1/console/shell/assets','/api/v1/console/shell/bindings','/api/v1/console/shell/safety']
    forb=[('POST','/order'),('POST','/orders'),('POST','/trade'),('POST','/execute'),('POST','/approve'),('POST','/live'),('POST','/notify'),('GET','/account'),('GET','/positions'),('GET','/orders'),('GET','/trades'),('GET','/assets')]
    return ApiGatewayRouteIndex([ApiEndpointSpec(path=r,summary='Stage61 local read-only JSON endpoint') for r in routes],[ApiEndpointSpec(method=m,path=p,forbidden=True,summary='forbidden route') for m,p in forb])
def build_safety_boundary_report(config=None):
    items=['read_only=True','dry_run_only=True','no_trade_authorization=True','no_task_registered=True','不调用 xttrader','不查询真实账户','不下单','不发送真实通知','不绕过 Risk Gate','不绕过 Human Approval']
    return ApiSafetyBoundaryReport(items=items)
def build_stage_status_report(config=None): return ApiStageStatusReport()
def build_next_ui_dashboard_plan(config=None): return NextUiDashboardPlanReport(items=['读取 Stage61 API Gateway 报告','展示 Stage55-60 材料摘要','展示 validation log 摘要','展示 safety boundary','仍不直接访问 QMT'])
def _capabilities():
    names=['health','stage_status','roadmap_summary','architecture_summary','stage55_60_reports','latest_validation_log','manifest_hash','dry_run_pipeline_report','scheduler_preview','safety_boundary','api_capability']
    return [ApiGatewayCapability(name=n,summary='local read-only API capability') for n in names]
def _evidence(config):
    root=Path(config.repo_root); mapping=[(ApiGatewayCategory.STAGE60_PRE_GRAY_FINAL_REVIEW,Path(config.pre_gray_final_review_dir)/'pre_gray_final_review.json'),(ApiGatewayCategory.STAGE59_READONLY_SEAL,Path(config.readonly_seal_dir)/'live_gray_readonly_seal.json'),(ApiGatewayCategory.STAGE58_FINAL_APPROVAL,Path(config.final_approval_dir)/'live_gray_final_approval.json'),(ApiGatewayCategory.STAGE57_GRAY_CANDIDATE,Path(config.gray_candidate_dir)/'live_gray_candidate.json'),(ApiGatewayCategory.STAGE56_REAL_CACHE_QUALITY,Path(config.real_cache_quality_dir)/'real_cache_quality.json'),(ApiGatewayCategory.STAGE55_QMT_DRYRUN_CALIBRATION,Path(config.qmt_dryrun_calibration_dir)/'qmt_dryrun_calibration.json')]
    out=[]
    for cat,p in mapping:
        rr=read_json_report(root/p)
        out.append(ApiGatewayEvidence(category=cat,status=rr.status,severity=ApiGatewaySeverity.WARN if not rr.ok else ApiGatewaySeverity.INFO,title=p.name,summary=rr.summary or ';'.join(rr.blocking_reasons),path=str(p),metadata={'ok':rr.ok}))
    return out
def run_api_gateway_review(config=None):
    config=config or ApiGatewayConfig(); evidence=_evidence(config); warnings=[]; blocking=[]
    stage60=next((e for e in evidence if e.category==ApiGatewayCategory.STAGE60_PRE_GRAY_FINAL_REVIEW),None)
    decision=ApiGatewayDecision.READY_FOR_API_GATEWAY_REVIEW
    if not stage60 or stage60.status==ApiGatewayStatus.UNAVAILABLE:
        decision=ApiGatewayDecision.NEED_MORE_EVIDENCE; warnings.append('Stage60 package unavailable; API Gateway materials need more evidence')
    else:
        data=read_json_report(Path(config.repo_root)/stage60.path).data or {}
        critical=data.get('summary',{}).get('critical_count',0) or data.get('critical_count',0)
        if data.get('decision')=='NO_GO' or critical:
            decision=ApiGatewayDecision.NO_GO; blocking.append('Stage60 NO_GO or critical findings present')
    return ApiGatewayReport(decision=decision,evidence=evidence,capabilities=_capabilities(),route_index=build_route_index(config),safety_boundary=build_safety_boundary_report(config),stage_status=build_stage_status_report(config),blocking_reasons=blocking,warnings=warnings,summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True})
def _write(path, text): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(text,encoding='utf-8')
def _write_json(path, obj): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(to_plain(obj),ensure_ascii=False,indent=2),encoding='utf-8')
def save_api_gateway_report(report, output, json_output): _write(output,format_api_gateway_report_md(report)); _write_json(json_output,report)
def load_api_gateway_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save_all(config, report, output, json_output, route_output, route_json_output, safety_output, safety_json_output, stage_status_output, stage_status_json_output, plan_output, plan_json_output):
    save_api_gateway_report(report,output,json_output); _write(route_output,format_route_index_md(report.route_index)); _write_json(route_json_output,report.route_index); _write(safety_output,format_safety_boundary_md(report.safety_boundary)); _write_json(safety_json_output,report.safety_boundary); _write(stage_status_output,format_stage_status_md(report.stage_status)); _write_json(stage_status_json_output,report.stage_status); plan=build_next_ui_dashboard_plan(config); _write(plan_output,format_next_ui_dashboard_plan_md(plan)); _write_json(plan_json_output,plan)
