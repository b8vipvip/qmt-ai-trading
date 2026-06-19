# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_ARCHIVE_VERIFICATION_REVIEW 只表示最终只读归档核验与锁定材料复核材料可供人工复核。"
class LiveArchiveVerificationDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_ARCHIVE_VERIFICATION_REVIEW="READY_FOR_ARCHIVE_VERIFICATION_REVIEW"
class LiveArchiveVerificationStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveArchiveVerificationSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveArchiveVerificationCategory(str, Enum):
    STAGE49_CONSISTENCY="STAGE49_CONSISTENCY"; STAGE50_FINAL_ARCHIVE="STAGE50_FINAL_ARCHIVE"; STAGE51_ARCHIVE_LOCK="STAGE51_ARCHIVE_LOCK"; STAGE52_LOCK_CONSISTENCY="STAGE52_LOCK_CONSISTENCY"; ARCHIVE_VERIFICATION="ARCHIVE_VERIFICATION"; LOCKED_MATERIAL_REVIEW="LOCKED_MATERIAL_REVIEW"; HUMAN_CLOSURE_RECHECK="HUMAN_CLOSURE_RECHECK"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveArchiveVerificationConfig:
    repo_root:str="."; output_dir:str="live_archive_verification_stage53"; lock_consistency_dir:str="live_lock_consistency_stage52"; archive_lock_dir:str="live_archive_lock_stage51"; final_archive_dir:str="live_final_archive_stage50"; consistency_dir:str="live_consistency_stage49"; validation_logs_dir:str="validation_logs"; roadmap_path:str="docs/qmt-ai-trading-project-roadmap.md"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveVerificationEvidence:
    evidence_id:str="stage53-evidence"; category:LiveArchiveVerificationCategory|str=LiveArchiveVerificationCategory.SYSTEM; status:LiveArchiveVerificationStatus|str=LiveArchiveVerificationStatus.SKIPPED; severity:LiveArchiveVerificationSeverity|str=LiveArchiveVerificationSeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveVerificationItem:
    item_id:str="archive-verification"; title:str=""; status:LiveArchiveVerificationStatus|str=LiveArchiveVerificationStatus.PASS; summary:str=""; required_action:str="人工复核 Stage53 最终只读归档核验材料；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class LockedMaterialReviewItem:
    item_id:str="locked-material-review"; title:str=""; status:LiveArchiveVerificationStatus|str=LiveArchiveVerificationStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckItem:
    item_id:str="human-recheck"; role:str=""; status:LiveArchiveVerificationStatus|str=LiveArchiveVerificationStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="next-readonly"; title:str=""; status:LiveArchiveVerificationStatus|str=LiveArchiveVerificationStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveVerificationReport:
    report_id:str="stage53-final-readonly-archive-verification"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveVerificationDecision|str=LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE; config:LiveArchiveVerificationConfig|dict[str,Any]=field(default_factory=LiveArchiveVerificationConfig); evidence:list[LiveArchiveVerificationEvidence]=field(default_factory=list); archive_verification:list[ArchiveVerificationItem]=field(default_factory=list); locked_material_review:list[LockedMaterialReviewItem]=field(default_factory=list); human_closure_recheck:list[HumanClosureRecheckItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage53 不代表实盘授权","确认 READY_FOR_ARCHIVE_VERIFICATION_REVIEW 只代表材料可供人工复核","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知","确认 UI 不能绕过 Risk Gate / Human Approval"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LockedMaterialReviewReport:
    report_id:str="stage53-locked-material-review"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveVerificationDecision|str=LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE; items:list[LockedMaterialReviewItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckReport:
    report_id:str="stage53-human-closure-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveVerificationDecision|str=LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE; items:list[HumanClosureRecheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage53-next-readonly-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveVerificationDecision|str=LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
