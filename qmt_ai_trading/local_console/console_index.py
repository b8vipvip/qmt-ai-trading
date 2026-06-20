from __future__ import annotations
from .models import *
from .safety import FORBIDDEN_ROUTES, classify_local_console_route
ROUTES=['/dashboard','/reports','/reports/stage61','/reports/stage60','/reports/stage59','/reports/stage58','/reports/stage57','/reports/stage56','/reports/stage55','/manifest','/validation/latest','/safety','/api-capabilities','/scheduler-preview']
def build_console_route_index(config=None):
    return [LocalConsoleRouteItem(path=p,title='Stage62 read-only console view',summary='local report reader route') for p in ROUTES]
def build_console_report_list(config=None):
    data=[('Stage61','API Gateway Evidence','api_gateway_stage61/api_gateway_report.json'),('Stage60','Pre-gray Final Review','pre_gray_final_review_stage60/pre_gray_final_review.json'),('Stage59','Read-only Seal','live_gray_readonly_seal_stage59/live_gray_readonly_seal.json'),('Stage58','Final Approval','live_gray_final_approval_stage58/live_gray_final_approval.json'),('Stage57','Gray Candidate','live_gray_candidate_stage57/live_gray_candidate.json'),('Stage56','Real Cache Quality','real_cache_quality_stage56/real_cache_quality.json'),('Stage55','QMT Dry-run Calibration','qmt_dryrun_calibration_stage55/qmt_dryrun_calibration.json')]
    return [LocalConsoleReportItem(stage=s,title=t,path=p,summary='read-only stage package entry') for s,t,p in data]
def build_console_dashboard_sections(config=None):
    return [LocalConsoleDashboardSection('reports','Reports','Stage55-61 report list',['/reports']),LocalConsoleDashboardSection('safety','Safety','Stage62 safety boundary',['/safety']),LocalConsoleDashboardSection('validation','Validation','latest validation summary only',['/validation/latest'])]
def build_console_safety_boundary(config=None):
    return LocalConsoleSafetyBoundary(items=['read_only=True','dry_run_only=True','no_trade_authorization=True','no_task_registered=True','不调用 xttrader','不查询真实账户','不下单','不发送真实通知','不绕过 Risk Gate','不绕过 Human Approval'], forbidden_routes=sorted(FORBIDDEN_ROUTES), warnings=['禁止控制台写操作、交易操作、账户查询、真实通知和自动审批'])
def build_next_console_detail_plan(config=None): return NextConsoleDetailPlanReport()
