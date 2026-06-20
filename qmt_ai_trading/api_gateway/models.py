from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
class ApiGatewayDecision(str, Enum): NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_API_GATEWAY_REVIEW='READY_FOR_API_GATEWAY_REVIEW'
class ApiGatewayStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class ApiGatewaySeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class ApiGatewayCategory(str, Enum):
    HEALTH='HEALTH'; ROADMAP='ROADMAP'; ARCHITECTURE='ARCHITECTURE'; STAGE_STATUS='STAGE_STATUS'; VALIDATION_LOG='VALIDATION_LOG'; STAGE60_PRE_GRAY_FINAL_REVIEW='STAGE60_PRE_GRAY_FINAL_REVIEW'; STAGE59_READONLY_SEAL='STAGE59_READONLY_SEAL'; STAGE58_FINAL_APPROVAL='STAGE58_FINAL_APPROVAL'; STAGE57_GRAY_CANDIDATE='STAGE57_GRAY_CANDIDATE'; STAGE56_REAL_CACHE_QUALITY='STAGE56_REAL_CACHE_QUALITY'; STAGE55_QMT_DRYRUN_CALIBRATION='STAGE55_QMT_DRYRUN_CALIBRATION'; MANIFEST='MANIFEST'; DRY_RUN_REPORT='DRY_RUN_REPORT'; SCHEDULER_PREVIEW='SCHEDULER_PREVIEW'; SAFETY_BOUNDARY='SAFETY_BOUNDARY'; API_CAPABILITY='API_CAPABILITY'; UI_BOUNDARY='UI_BOUNDARY'; RISK_GATE='RISK_GATE'; HUMAN_APPROVAL='HUMAN_APPROVAL'; QMT_BOUNDARY='QMT_BOUNDARY'; RUNTIME_ARTIFACT='RUNTIME_ARTIFACT'; SENSITIVE_FILE='SENSITIVE_FILE'; SYSTEM='SYSTEM'
@dataclass
class ApiGatewayConfig:
    repo_root: str|Path='.'; output_dir: str|Path='api_gateway_stage61'; pre_gray_final_review_dir: str|Path='pre_gray_final_review_stage60'; readonly_seal_dir: str|Path='live_gray_readonly_seal_stage59'; final_approval_dir: str|Path='live_gray_final_approval_stage58'; gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; host: str='127.0.0.1'; port: int=8765; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True
@dataclass
class ApiGatewayEvidence:
    category: ApiGatewayCategory=ApiGatewayCategory.SYSTEM; status: ApiGatewayStatus=ApiGatewayStatus.SKIPPED; severity: ApiGatewaySeverity=ApiGatewaySeverity.INFO; title: str=''; summary: str=''; path: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class ApiEndpointSpec:
    method: str='GET'; path: str='/health'; category: ApiGatewayCategory=ApiGatewayCategory.HEALTH; read_only: bool=True; dry_run_only: bool=True; forbidden: bool=False; summary: str=''
@dataclass
class ApiGatewayCapability:
    name: str=''; enabled: bool=True; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; summary: str=''
@dataclass
class ApiGatewayReadResult:
    ok: bool=False; status: ApiGatewayStatus=ApiGatewayStatus.UNAVAILABLE; path: str=''; summary: str=''; data: Any=None; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class ApiGatewayHealth:
    ok: bool=True; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class ApiGatewayRouteIndex:
    endpoints: list[ApiEndpointSpec]=field(default_factory=list); forbidden_routes: list[ApiEndpointSpec]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class ApiSafetyBoundaryReport:
    status: ApiGatewayStatus=ApiGatewayStatus.PASS; items: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class ApiStageStatusReport:
    current_stage: str='Stage61'; stage_name: str='API Gateway 基础层'; previous_stage: str='Stage60 PASSED'; next_stage: str='Stage62 本地控制台报告读取层'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; warnings: list[str]=field(default_factory=list)
@dataclass
class NextUiDashboardPlanReport:
    stage: str='Stage62'; title: str='本地控制台报告读取层'; safety_note: str='Stage62 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'; items: list[str]=field(default_factory=list)
@dataclass
class ApiGatewayReport:
    decision: ApiGatewayDecision=ApiGatewayDecision.NEED_MORE_EVIDENCE; safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_API_GATEWAY_REVIEW 只表示 API Gateway 基础层材料可供人工复核。'; evidence: list[ApiGatewayEvidence]=field(default_factory=list); capabilities: list[ApiGatewayCapability]=field(default_factory=list); route_index: ApiGatewayRouteIndex=field(default_factory=ApiGatewayRouteIndex); safety_boundary: ApiSafetyBoundaryReport=field(default_factory=ApiSafetyBoundaryReport); stage_status: ApiStageStatusReport=field(default_factory=ApiStageStatusReport); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict)
def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
