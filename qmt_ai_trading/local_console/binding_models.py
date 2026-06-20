from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleBindingDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW="READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW"
class LocalConsoleBindingStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"; UNAVAILABLE="UNAVAILABLE"
class LocalConsoleBindingSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LocalConsoleBindingSourceType(str, Enum):
    DASHBOARD_CARD="DASHBOARD_CARD"; REPORT_LIST="REPORT_LIST"; DETAIL_FILTER="DETAIL_FILTER"; API_CAPABILITY="API_CAPABILITY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; SAFETY_BOUNDARY="SAFETY_BOUNDARY"; VALIDATION_SUMMARY="VALIDATION_SUMMARY"; MANIFEST_HASH="MANIFEST_HASH"; PLACEHOLDER="PLACEHOLDER"; NEXT_STAGE_PLAN="NEXT_STAGE_PLAN"
@dataclass
class LocalConsoleBindingConfig:
    repo_root: str|Path="."; output_dir: str|Path="local_console_binding_stage66"; local_console_shell_dir: str|Path="local_console_shell_stage65"; local_console_dashboard_dir: str|Path="local_console_dashboard_stage64"; local_console_detail_dir: str|Path="local_console_detail_stage63"; local_console_dir: str|Path="local_console_stage62"; api_gateway_dir: str|Path="api_gateway_stage61"; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True
@dataclass
class LocalConsoleBindingEvidence:
    stage: str=""; title: str=""; path: str=""; status: LocalConsoleBindingStatus=LocalConsoleBindingStatus.UNAVAILABLE; severity: LocalConsoleBindingSeverity=LocalConsoleBindingSeverity.WARN; summary: str=""; decision: str=""; critical_count: int=0; warning_count: int=0; blocking_reason_count: int=0; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleDataSource:
    source_path: str=""; source_type: LocalConsoleBindingSourceType=LocalConsoleBindingSourceType.PLACEHOLDER; target_section_id: str=""; status: LocalConsoleBindingStatus=LocalConsoleBindingStatus.UNAVAILABLE; severity: LocalConsoleBindingSeverity=LocalConsoleBindingSeverity.WARN; encoding: str=""; fallback_used: bool=False; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleDataBinding:
    source: LocalConsoleDataSource=field(default_factory=LocalConsoleDataSource); payload: Any=field(default_factory=dict)
@dataclass
class LocalConsoleDataBundle:
    metadata: dict[str,Any]=field(default_factory=dict); dashboard: dict[str,Any]=field(default_factory=dict); stage_status: dict[str,Any]=field(default_factory=dict); latest_validation: dict[str,Any]=field(default_factory=dict); warnings: dict[str,Any]=field(default_factory=dict); blocking_reasons: dict[str,Any]=field(default_factory=dict); manifest: dict[str,Any]=field(default_factory=dict); scheduler_preview: dict[str,Any]=field(default_factory=dict); safety_boundary: dict[str,Any]=field(default_factory=dict); api_capability: dict[str,Any]=field(default_factory=dict); report_list: dict[str,Any]=field(default_factory=dict); detail_filters: dict[str,Any]=field(default_factory=dict); placeholders: dict[str,Any]=field(default_factory=dict); warnings_summary: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleMissingDataPlaceholder:
    source_path: str=""; target_section_id: str=""; reason: str="missing or unreadable"; status: LocalConsoleBindingStatus=LocalConsoleBindingStatus.UNAVAILABLE
@dataclass
class LocalConsoleBindingManifest:
    stage: str="Stage66"; sources: list[LocalConsoleDataSource]=field(default_factory=list); read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleBindingReport:
    decision: LocalConsoleBindingDecision=LocalConsoleBindingDecision.NEED_MORE_EVIDENCE; safety_note: str="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW 只表示本地控制台静态数据绑定层材料可供人工复核。"; evidence: list[LocalConsoleBindingEvidence]=field(default_factory=list); data_bundle: dict[str,Any]=field(default_factory=dict); manifest: dict[str,Any]=field(default_factory=dict); data_source_map: dict[str,Any]=field(default_factory=dict); placeholders: list[LocalConsoleMissingDataPlaceholder]=field(default_factory=list); assets: list[dict[str,Any]]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{"read_only":True,"dry_run_only":True,"no_trade_authorization":True,"critical_count":0})
@dataclass
class LocalConsoleDataBundleReport: bundle: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleDataSourceMapReport: source_map: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleMissingDataReport: placeholders: list[LocalConsoleMissingDataPlaceholder]=field(default_factory=list)
@dataclass
class LocalConsoleBoundAssetReport: assets: list[dict[str,Any]]=field(default_factory=list)
@dataclass
class StaticDataSafetyReport:
    read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True; critical_findings: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); safety_items: list[str]=field(default_factory=lambda:["不调用 xttrader","不下单","不查询真实账户","不发送真实通知","不自动 approve","不绕过 Risk Gate","不绕过 Human Approval"])
@dataclass
class NextConsolePreviewServerPlanReport:
    stage: str="Stage67"; title: str="本地只读预览服务层"; safety_note: str="Stage67 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。"; items: list[str]=field(default_factory=lambda:["只绑定 127.0.0.1","只读 GET 静态预览","禁止 POST/PUT/PATCH/DELETE","不访问 QMT","不发送真实通知"])
def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,"__dataclass_fields__"): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
