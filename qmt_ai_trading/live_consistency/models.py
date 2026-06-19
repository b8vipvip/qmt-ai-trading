# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_CONSISTENCY_REVIEW 只表示补证后只读复核与一致性材料可供人工复核。"
class LiveConsistencyDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_CONSISTENCY_REVIEW="READY_FOR_CONSISTENCY_REVIEW"
class LiveConsistencyStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveConsistencySeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveConsistencyCategory(str, Enum):
    STAGE45_RUNBOOK="STAGE45_RUNBOOK"; STAGE46_SIGNOFF="STAGE46_SIGNOFF"; STAGE47_FINAL_REVIEW="STAGE47_FINAL_REVIEW"; STAGE48_ARCHIVE="STAGE48_ARCHIVE"; REMEDIATION_REVIEW="REMEDIATION_REVIEW"; MATERIAL_CONSISTENCY="MATERIAL_CONSISTENCY"; HUMAN_RECHECK="HUMAN_RECHECK"; NEXT_GRAY_CHECK="NEXT_GRAY_CHECK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveConsistencyConfig:
    repo_root:str="."; output_dir:str="live_consistency_stage49"; archive_dir:str="live_archive_stage48"; final_review_dir:str="live_final_review_stage47"; signoff_dir:str="live_signoff_stage46"; runbook_dir:str="live_runbook_stage45"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveConsistencyEvidence:
    evidence_id:str="stage49-evidence"; category:LiveConsistencyCategory|str=LiveConsistencyCategory.SYSTEM; status:LiveConsistencyStatus|str=LiveConsistencyStatus.SKIPPED; severity:LiveConsistencySeverity|str=LiveConsistencySeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class RemediationReviewItem:
    item_id:str="remediation"; title:str=""; status:LiveConsistencyStatus|str=LiveConsistencyStatus.PASS; summary:str=""; required_action:str="人工复核补证材料；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class MaterialConsistencyItem:
    item_id:str="material"; title:str=""; status:LiveConsistencyStatus|str=LiveConsistencyStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanRecheckItem:
    item_id:str="human"; role:str=""; status:LiveConsistencyStatus|str=LiveConsistencyStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextGrayCheckItem:
    item_id:str="gray"; title:str=""; status:LiveConsistencyStatus|str=LiveConsistencyStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveConsistencyReport:
    report_id:str="stage49-remediation-consistency-review"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveConsistencyDecision|str=LiveConsistencyDecision.NEED_MORE_EVIDENCE; config:LiveConsistencyConfig|dict[str,Any]=field(default_factory=LiveConsistencyConfig); evidence:list[LiveConsistencyEvidence]=field(default_factory=list); remediation_review:list[RemediationReviewItem]=field(default_factory=list); material_consistency:list[MaterialConsistencyItem]=field(default_factory=list); human_recheck:list[HumanRecheckItem]=field(default_factory=list); next_gray_check_plan:list[NextGrayCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage49 不代表实盘授权","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class MaterialConsistencyReport:
    report_id:str="stage49-material-consistency"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveConsistencyDecision|str=LiveConsistencyDecision.NEED_MORE_EVIDENCE; items:list[MaterialConsistencyItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanRecheckReport:
    report_id:str="stage49-human-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveConsistencyDecision|str=LiveConsistencyDecision.NEED_MORE_EVIDENCE; items:list[HumanRecheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextGrayCheckReport:
    report_id:str="stage49-next-gray-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveConsistencyDecision|str=LiveConsistencyDecision.NEED_MORE_EVIDENCE; items:list[NextGrayCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
