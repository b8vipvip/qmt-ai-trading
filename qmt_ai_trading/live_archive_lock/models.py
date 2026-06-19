# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCK_REVIEW 只表示最终只读封版复核与材料归档锁定材料可供人工复核。"
class LiveArchiveLockDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_LOCK_REVIEW="READY_FOR_LOCK_REVIEW"
class LiveArchiveLockStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveArchiveLockSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveArchiveLockCategory(str, Enum):
    STAGE47_FINAL_REVIEW="STAGE47_FINAL_REVIEW"; STAGE48_ARCHIVE="STAGE48_ARCHIVE"; STAGE49_CONSISTENCY="STAGE49_CONSISTENCY"; STAGE50_FINAL_ARCHIVE="STAGE50_FINAL_ARCHIVE"; FINAL_LOCK_REVIEW="FINAL_LOCK_REVIEW"; ARCHIVE_LOCK="ARCHIVE_LOCK"; HUMAN_CLOSURE_RECHECK="HUMAN_CLOSURE_RECHECK"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveArchiveLockConfig:
    repo_root:str="."; output_dir:str="live_archive_lock_stage51"; final_archive_dir:str="live_final_archive_stage50"; consistency_dir:str="live_consistency_stage49"; archive_dir:str="live_archive_stage48"; final_review_dir:str="live_final_review_stage47"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveLockEvidence:
    evidence_id:str="stage51-evidence"; category:LiveArchiveLockCategory|str=LiveArchiveLockCategory.SYSTEM; status:LiveArchiveLockStatus|str=LiveArchiveLockStatus.SKIPPED; severity:LiveArchiveLockSeverity|str=LiveArchiveLockSeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class FinalLockReviewItem:
    item_id:str="final-lock"; title:str=""; status:LiveArchiveLockStatus|str=LiveArchiveLockStatus.PASS; summary:str=""; required_action:str="人工复核 Stage51 最终只读封版材料；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveLockItem:
    item_id:str="archive-lock"; title:str=""; status:LiveArchiveLockStatus|str=LiveArchiveLockStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckItem:
    item_id:str="human-recheck"; role:str=""; status:LiveArchiveLockStatus|str=LiveArchiveLockStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="next-readonly"; title:str=""; status:LiveArchiveLockStatus|str=LiveArchiveLockStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveLockReport:
    report_id:str="stage51-final-readonly-seal-archive-lock"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveLockDecision|str=LiveArchiveLockDecision.NEED_MORE_EVIDENCE; config:LiveArchiveLockConfig|dict[str,Any]=field(default_factory=LiveArchiveLockConfig); evidence:list[LiveArchiveLockEvidence]=field(default_factory=list); final_lock_review:list[FinalLockReviewItem]=field(default_factory=list); archive_lock:list[ArchiveLockItem]=field(default_factory=list); human_closure_recheck:list[HumanClosureRecheckItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage51 不代表实盘授权","确认 READY_FOR_LOCK_REVIEW 只代表材料可供人工复核","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveLockReport:
    report_id:str="stage51-archive-lock"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveLockDecision|str=LiveArchiveLockDecision.NEED_MORE_EVIDENCE; items:list[ArchiveLockItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckReport:
    report_id:str="stage51-human-closure-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveLockDecision|str=LiveArchiveLockDecision.NEED_MORE_EVIDENCE; items:list[HumanClosureRecheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage51-next-readonly-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveLockDecision|str=LiveArchiveLockDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
