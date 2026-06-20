from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleDetailDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW='READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW'
class LocalConsoleDetailStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleDetailSeverity(str, Enum):
    INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleFilterMode(str, Enum):
    ALL='ALL'; STAGE='STAGE'; STATUS='STATUS'; SEVERITY='SEVERITY'; WARNINGS='WARNINGS'; BLOCKING_REASONS='BLOCKING_REASONS'; MANIFEST='MANIFEST'; VALIDATION_LOG='VALIDATION_LOG'; SAFETY_BOUNDARY='SAFETY_BOUNDARY'

@dataclass
class LocalConsoleDetailConfig:
    repo_root: str|Path='.'; output_dir: str|Path='local_console_detail_stage63'; local_console_dir: str|Path='local_console_stage62'; api_gateway_dir: str|Path='api_gateway_stage61'; pre_gray_final_review_dir: str|Path='pre_gray_final_review_stage60'; readonly_seal_dir: str|Path='live_gray_readonly_seal_stage59'; final_approval_dir: str|Path='live_gray_final_approval_stage58'; gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleDetailEvidence:
    stage: str=''; title: str=''; path: str=''; status: LocalConsoleDetailStatus=LocalConsoleDetailStatus.UNAVAILABLE; severity: LocalConsoleDetailSeverity=LocalConsoleDetailSeverity.WARN; summary: str=''; decision: str=''; critical_count: int=0; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class ConsoleStageDetail(LocalConsoleDetailEvidence): pass
@dataclass
class ConsoleReportFilter: mode: LocalConsoleFilterMode=LocalConsoleFilterMode.ALL; value: str=''
@dataclass
class ConsoleFilterResult: filter: ConsoleReportFilter=field(default_factory=ConsoleReportFilter); items: list[ConsoleStageDetail]=field(default_factory=list)
@dataclass
class ConsoleWarningItem: stage: str=''; message: str=''; severity: LocalConsoleDetailSeverity=LocalConsoleDetailSeverity.WARN; path: str=''
@dataclass
class ConsoleBlockingReasonItem: stage: str=''; message: str=''; severity: LocalConsoleDetailSeverity=LocalConsoleDetailSeverity.CRITICAL; path: str=''
@dataclass
class ConsoleManifestDetailItem: stage: str=''; path: str=''; status: LocalConsoleDetailStatus=LocalConsoleDetailStatus.UNAVAILABLE; summary: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class ConsoleValidationLogDetail: path: str=''; status: LocalConsoleDetailStatus=LocalConsoleDetailStatus.UNAVAILABLE; severity: LocalConsoleDetailSeverity=LocalConsoleDetailSeverity.WARN; encoding: str=''; head: str=''; tail: str=''; summary: str=''; warnings: list[str]=field(default_factory=list)
@dataclass
class ConsoleSafetyDetail: read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True; forbidden_routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleDetailReport:
    decision: LocalConsoleDetailDecision=LocalConsoleDetailDecision.NEED_MORE_EVIDENCE; safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW 只表示本地控制台报告详情页与过滤层材料可供人工复核。'; evidence: list[ConsoleStageDetail]=field(default_factory=list); route_index: list[str]=field(default_factory=list); filter_index: dict[str,Any]=field(default_factory=dict); validation_detail: ConsoleValidationLogDetail=field(default_factory=ConsoleValidationLogDetail); safety_detail: ConsoleSafetyDetail=field(default_factory=ConsoleSafetyDetail); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict)
@dataclass
class ConsoleFilterIndexReport: filters: dict[str,Any]=field(default_factory=dict); routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class ConsoleWarningsReport: items: list[ConsoleWarningItem]=field(default_factory=list)
@dataclass
class ConsoleBlockingReasonsReport: items: list[ConsoleBlockingReasonItem]=field(default_factory=list)
@dataclass
class ConsoleManifestDetailReport: items: list[ConsoleManifestDetailItem]=field(default_factory=list)
@dataclass
class ConsoleValidationDetailReport: detail: ConsoleValidationLogDetail=field(default_factory=ConsoleValidationLogDetail)
@dataclass
class NextConsoleOverviewPlanReport: stage: str='Stage64'; title: str='本地控制台概览面板层'; safety_note: str='Stage64 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'; items: list[str]=field(default_factory=lambda:['阶段状态卡片','最新 validation 状态卡片','warning/blocking reason 统计','manifest/hash 状态卡片','scheduler preview 状态卡片','safety boundary 状态卡片'])

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
