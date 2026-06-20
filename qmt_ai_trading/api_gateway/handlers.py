from __future__ import annotations
from pathlib import Path
from .models import to_plain
from .service import build_default_api_gateway_config, build_route_index, build_safety_boundary_report, build_stage_status_report
from .reader import read_markdown_report, read_latest_validation_log
from .safety import classify_api_gateway_route
def base_response(ok=True,data=None,warnings=None,blocking_reasons=None):
    return {'ok':ok,'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'no_task_registered':True,'data':data or {},'warnings':warnings or [],'blocking_reasons':blocking_reasons or []}
def handle_request(path: str, method: str='GET', repo_root='.'):
    spec=classify_api_gateway_route(path,method)
    if spec.forbidden: return 403, base_response(False, {'path':path,'method':method}, blocking_reasons=['forbidden route'])
    if method.upper()!='GET': return 405, base_response(False, blocking_reasons=['forbidden route','method not allowed'])
    root=Path(repo_root); cfg=build_default_api_gateway_config(repo_root=root)
    p=path.split('?')[0]
    if p=='/health': return 200, base_response(True, {'status':'PASS','host':'127.0.0.1'})
    if p=='/api/v1/capabilities': return 200, base_response(True, {'routes':[to_plain(e) for e in build_route_index(cfg).endpoints]})
    if p=='/api/v1/safety-boundary': return 200, base_response(True, to_plain(build_safety_boundary_report(cfg)))
    if p=='/api/v1/stages/status': return 200, base_response(True, to_plain(build_stage_status_report(cfg)))
    if p=='/api/v1/stages/latest': return 200, base_response(True, {'latest_completed':'Stage60','current':'Stage61','next':'Stage62'})
    if p=='/api/v1/roadmap/summary': return 200, base_response(True, to_plain(read_markdown_report(root/'docs/qmt-ai-trading-project-roadmap.md',2000)))
    if p=='/api/v1/architecture/summary': return 200, base_response(True, to_plain(read_markdown_report(root/'docs/qmt-ai-trading-architecture.md',2000)))
    stage_files={'/api/v1/reports/stage60':'pre_gray_final_review_stage60/pre_gray_final_review.md','/api/v1/reports/stage59':'live_gray_readonly_seal_stage59/live_gray_readonly_seal.md','/api/v1/reports/stage58':'live_gray_final_approval_stage58/live_gray_final_approval.md','/api/v1/reports/stage57':'live_gray_candidate_stage57/live_gray_candidate.md','/api/v1/reports/stage56':'real_cache_quality_stage56/real_cache_quality.md','/api/v1/reports/stage55':'qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.md','/api/v1/manifest/stage59':'live_gray_readonly_seal_stage59/readonly_seal_manifest.md'}
    if p in stage_files: return 200, base_response(True, to_plain(read_markdown_report(root/stage_files[p],3000)))
    if p=='/api/v1/validation/latest': return 200, base_response(True, to_plain(read_latest_validation_log(root/'validation_logs','stage*_validation_*.log')))
    if p=='/api/v1/scheduler/preview': return 200, base_response(True, {'preview_only':True,'read_only':True,'dry_run_only':True,'no_task_registered':True})
    return 404, base_response(False, blocking_reasons=['route not found'])
