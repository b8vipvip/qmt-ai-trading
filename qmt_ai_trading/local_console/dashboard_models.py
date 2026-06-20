from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleDashboardDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW='READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW'
class LocalConsoleDashboardStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleDashboardSeverity(str, Enum):
    INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleDashboardCardType(str, Enum):
    STAGE_STATUS='STAGE_STATUS'; LATEST_VALIDATION='LATEST_VALIDATION'; WARNING_BLOCKING_STATS='WARNING_BLOCKING_STATS'; MANIFEST_HASH='MANIFEST_HASH'; SCHEDULER_PREVIEW='SCHEDULER_PREVIEW'; SAFETY_BOUNDARY='SAFETY_BOUNDARY'; API_CAPABILITY='API_CAPABILITY'; DETAIL_FILTER='DETAIL_FILTER'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleDashboardConfig:
    repo_root: str|Path='.'; output_dir: str|Path='local_console_dashboard_stage64'; local_console_detail_dir: str|Path='local_console_detail_stage63'; local_console_dir: str|Path='local_console_stage62'; api_gateway_dir: str|Path='api_gateway_stage61'; pre_gray_final_review_dir: str|Path='pre_gray_final_review_stage60'; readonly_seal_dir: str|Path='live_gray_readonly_seal_stage59'; final_approval_dir: str|Path='live_gray_final_approval_stage58'; gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleDashboardEvidence:
    stage: str=''; title: str=''; path: str=''; status: LocalConsoleDashboardStatus=LocalConsoleDashboardStatus.UNAVAILABLE; severity: LocalConsoleDashboardSeverity=LocalConsoleDashboardSeverity.WARN; summary: str=''; decision: str=''; critical_count: int=0; warning_count: int=0; blocking_reason_count: int=0; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class DashboardCardMetric:
    name: str=''; value: Any=None; status: LocalConsoleDashboardStatus=LocalConsoleDashboardStatus.PASS; severity: LocalConsoleDashboardSeverity=LocalConsoleDashboardSeverity.INFO; summary: str=''
@dataclass
class DashboardCard:
    card_id: str=''; title: str=''; card_type: LocalConsoleDashboardCardType=LocalConsoleDashboardCardType.STAGE_STATUS; status: LocalConsoleDashboardStatus=LocalConsoleDashboardStatus.UNAVAILABLE; severity: LocalConsoleDashboardSeverity=LocalConsoleDashboardSeverity.WARN; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; metrics: list[DashboardCardMetric]=field(default_factory=list); routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class StageStatusCard(DashboardCard): pass
@dataclass
class LatestValidationCard(DashboardCard): pass
@dataclass
class WarningBlockingStatsCard(DashboardCard): pass
@dataclass
class ManifestHashCard(DashboardCard): pass
@dataclass
class SchedulerPreviewCard(DashboardCard): pass
@dataclass
class SafetyBoundaryCard(DashboardCard): pass
@dataclass
class ApiCapabilityCard(DashboardCard): pass
@dataclass
class DetailFilterCard(DashboardCard): pass
@dataclass
class LocalConsoleDashboardReport:
    decision: LocalConsoleDashboardDecision=LocalConsoleDashboardDecision.NEED_MORE_EVIDENCE; safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCAL_CONSOLE_DASHBOARD_REVIEW 只表示本地控制台概览面板层材料可供人工复核。'; evidence: list[LocalConsoleDashboardEvidence]=field(default_factory=list); route_index: list[str]=field(default_factory=list); cards: list[DashboardCard]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True})
@dataclass
class DashboardCardIndexReport: cards: list[DashboardCard]=field(default_factory=list); routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class StageStatusCardsReport: cards: list[DashboardCard]=field(default_factory=list)
@dataclass
class WarningBlockingStatsReport: card: DashboardCard=field(default_factory=DashboardCard)
@dataclass
class ManifestHashStatusReport: card: DashboardCard=field(default_factory=DashboardCard)
@dataclass
class SchedulerPreviewStatusReport: card: DashboardCard=field(default_factory=DashboardCard)
@dataclass
class SafetyBoundaryStatusReport: card: DashboardCard=field(default_factory=DashboardCard)
@dataclass
class NextConsoleShellPlanReport:
    stage: str='Stage65'; title: str='本地控制台 shell / 静态页面骨架层'; safety_note: str='Stage65 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'; routes: list[str]=field(default_factory=lambda:['/dashboard/overview','/dashboard/stage-status','/dashboard/latest-validation','/dashboard/warnings','/dashboard/blocking-reasons','/dashboard/manifest','/dashboard/scheduler-preview','/dashboard/safety-boundary','/dashboard/api-capability','/dashboard/detail-filter','/dashboard/next']); items: list[str]=field(default_factory=lambda:['页面布局','导航','只读数据注入点','dashboard card 占位','报告列表占位','详情过滤占位','安全边界固定展示'])

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
