# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCK_CONSISTENCY_REVIEW 只表示最终只读锁定复核与归档一致性核验材料可供人工复核。"
class LiveLockConsistencyDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_LOCK_CONSISTENCY_REVIEW="READY_FOR_LOCK_CONSISTENCY_REVIEW"
class LiveLockConsistencyStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveLockConsistencySeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveLockConsistencyCategory(str, Enum):
    STAGE48_ARCHIVE="STAGE48_ARCHIVE"; STAGE49_CONSISTENCY="STAGE49_CONSISTENCY"; STAGE50_FINAL_ARCHIVE="STAGE50_FINAL_ARCHIVE"; STAGE51_ARCHIVE_LOCK="STAGE51_ARCHIVE_LOCK"; FINAL_LOCK_CONSISTENCY="FINAL_LOCK_CONSISTENCY"; ARCHIVE_CONSISTENCY="ARCHIVE_CONSISTENCY"; HUMAN_CLOSURE_RECHECK="HUMAN_CLOSURE_RECHECK"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveLockConsistencyConfig:
    repo_root:str="."; output_dir:str="live_lock_consistency_stage52"; archive_lock_dir:str="live_archive_lock_stage51"; final_archive_dir:str="live_final_archive_stage50"; consistency_dir:str="live_consistency_stage49"; archive_dir:str="live_archive_stage48"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveLockConsistencyEvidence:
    evidence_id:str="stage52-evidence"; category:LiveLockConsistencyCategory|str=LiveLockConsistencyCategory.SYSTEM; status:LiveLockConsistencyStatus|str=LiveLockConsistencyStatus.SKIPPED; severity:LiveLockConsistencySeverity|str=LiveLockConsistencySeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class FinalLockConsistencyItem:
    item_id:str="final-lock-consistency"; title:str=""; status:LiveLockConsistencyStatus|str=LiveLockConsistencyStatus.PASS; summary:str=""; required_action:str="人工复核 Stage52 最终只读锁定材料；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveConsistencyItem:
    item_id:str="archive-consistency"; title:str=""; status:LiveLockConsistencyStatus|str=LiveLockConsistencyStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckItem:
    item_id:str="human-recheck"; role:str=""; status:LiveLockConsistencyStatus|str=LiveLockConsistencyStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="next-readonly"; title:str=""; status:LiveLockConsistencyStatus|str=LiveLockConsistencyStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveLockConsistencyReport:
    report_id:str="stage52-final-readonly-lock-archive-consistency"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveLockConsistencyDecision|str=LiveLockConsistencyDecision.NEED_MORE_EVIDENCE; config:LiveLockConsistencyConfig|dict[str,Any]=field(default_factory=LiveLockConsistencyConfig); evidence:list[LiveLockConsistencyEvidence]=field(default_factory=list); final_lock_consistency:list[FinalLockConsistencyItem]=field(default_factory=list); archive_consistency:list[ArchiveConsistencyItem]=field(default_factory=list); human_closure_recheck:list[HumanClosureRecheckItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage52 不代表实盘授权","确认 READY_FOR_LOCK_CONSISTENCY_REVIEW 只代表材料可供人工复核","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveConsistencyReport:
    report_id:str="stage52-archive-consistency"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveLockConsistencyDecision|str=LiveLockConsistencyDecision.NEED_MORE_EVIDENCE; items:list[ArchiveConsistencyItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckReport:
    report_id:str="stage52-human-closure-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveLockConsistencyDecision|str=LiveLockConsistencyDecision.NEED_MORE_EVIDENCE; items:list[HumanClosureRecheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage52-next-readonly-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveLockConsistencyDecision|str=LiveLockConsistencyDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
