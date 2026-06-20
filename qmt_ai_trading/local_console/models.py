from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
class LocalConsoleDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_REVIEW='READY_FOR_LOCAL_CONSOLE_REVIEW'
class LocalConsoleStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleCategory(str, Enum):
    CONSOLE_INDEX='CONSOLE_INDEX'; REPORT_LIST='REPORT_LIST'; REPORT_DETAIL='REPORT_DETAIL'; STAGE61_API_GATEWAY='STAGE61_API_GATEWAY'; STAGE60_PRE_GRAY_FINAL_REVIEW='STAGE60_PRE_GRAY_FINAL_REVIEW'; STAGE59_READONLY_SEAL='STAGE59_READONLY_SEAL'; STAGE58_FINAL_APPROVAL='STAGE58_FINAL_APPROVAL'; STAGE57_GRAY_CANDIDATE='STAGE57_GRAY_CANDIDATE'; STAGE56_REAL_CACHE_QUALITY='STAGE56_REAL_CACHE_QUALITY'; STAGE55_QMT_DRYRUN_CALIBRATION='STAGE55_QMT_DRYRUN_CALIBRATION'; VALIDATION_LOG='VALIDATION_LOG'; MANIFEST='MANIFEST'; DRY_RUN_PIPELINE='DRY_RUN_PIPELINE'; SCHEDULER_PREVIEW='SCHEDULER_PREVIEW'; SAFETY_BOUNDARY='SAFETY_BOUNDARY'; API_CAPABILITY='API_CAPABILITY'; UI_BOUNDARY='UI_BOUNDARY'; RISK_GATE='RISK_GATE'; HUMAN_APPROVAL='HUMAN_APPROVAL'; QMT_BOUNDARY='QMT_BOUNDARY'; RUNTIME_ARTIFACT='RUNTIME_ARTIFACT'; SENSITIVE_FILE='SENSITIVE_FILE'; SYSTEM='SYSTEM'
@dataclass
class LocalConsoleConfig:
    repo_root: str|Path='.'; output_dir: str|Path='local_console_stage62'; api_gateway_dir: str|Path='api_gateway_stage61'; pre_gray_final_review_dir: str|Path='pre_gray_final_review_stage60'; readonly_seal_dir: str|Path='live_gray_readonly_seal_stage59'; final_approval_dir: str|Path='live_gray_final_approval_stage58'; gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleEvidence:
    category: LocalConsoleCategory=LocalConsoleCategory.SYSTEM; status: LocalConsoleStatus=LocalConsoleStatus.UNAVAILABLE; severity: LocalConsoleSeverity=LocalConsoleSeverity.WARN; title: str=''; summary: str=''; path: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleReportItem:
    stage: str=''; title: str=''; path: str=''; status: LocalConsoleStatus=LocalConsoleStatus.UNAVAILABLE; summary: str=''
@dataclass
class LocalConsoleReportDetail:
    stage: str=''; title: str=''; path: str=''; status: LocalConsoleStatus=LocalConsoleStatus.UNAVAILABLE; summary: str=''; decision: str=''; critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleRouteItem:
    path: str=''; method: str='GET'; title: str=''; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; forbidden: bool=False; summary: str=''
@dataclass
class LocalConsoleDashboardSection:
    name: str=''; title: str=''; summary: str=''; routes: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleSafetyBoundary:
    read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True; items: list[str]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleReport:
    decision: LocalConsoleDecision=LocalConsoleDecision.NEED_MORE_EVIDENCE; safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCAL_CONSOLE_REVIEW 只表示本地控制台报告读取层材料可供人工复核。'; evidence: list[LocalConsoleEvidence]=field(default_factory=list); route_index: list[LocalConsoleRouteItem]=field(default_factory=list); report_list: list[LocalConsoleReportItem]=field(default_factory=list); safety_boundary: LocalConsoleSafetyBoundary=field(default_factory=LocalConsoleSafetyBoundary); validation_summary: str=''; manifest_summary: str=''; scheduler_preview_summary: str='preview only; read_only=True; dry_run_only=True; no_task_registered=True'; blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleIndexReport: routes: list[LocalConsoleRouteItem]=field(default_factory=list); sections: list[LocalConsoleDashboardSection]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleReportListReport: items: list[LocalConsoleReportItem]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleStageDetailReport: detail: LocalConsoleReportDetail=field(default_factory=LocalConsoleReportDetail)
@dataclass
class LocalConsoleSafetyReport: boundary: LocalConsoleSafetyBoundary=field(default_factory=LocalConsoleSafetyBoundary)
@dataclass
class NextConsoleDetailPlanReport:
    stage: str='Stage63'; title: str='本地控制台报告详情页与过滤层'; safety_note: str='Stage63 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'; items: list[str]=field(default_factory=lambda:['报告详情页','阶段/状态筛选','warning/blocking reason 过滤','manifest 摘要详情','validation log 摘要详情'])
def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
