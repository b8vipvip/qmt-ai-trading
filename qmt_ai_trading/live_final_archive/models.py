# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_FINAL_ARCHIVE_REVIEW 只表示最终归档复核与材料一致性封版材料可供人工复核。"
class LiveFinalArchiveDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_FINAL_ARCHIVE_REVIEW="READY_FOR_FINAL_ARCHIVE_REVIEW"
class LiveFinalArchiveStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveFinalArchiveSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveFinalArchiveCategory(str, Enum):
    STAGE46_SIGNOFF="STAGE46_SIGNOFF"; STAGE47_FINAL_REVIEW="STAGE47_FINAL_REVIEW"; STAGE48_ARCHIVE="STAGE48_ARCHIVE"; STAGE49_CONSISTENCY="STAGE49_CONSISTENCY"; FINAL_ARCHIVE_REVIEW="FINAL_ARCHIVE_REVIEW"; MATERIAL_SEAL="MATERIAL_SEAL"; HUMAN_CLOSURE="HUMAN_CLOSURE"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveFinalArchiveConfig:
    repo_root:str="."; output_dir:str="live_final_archive_stage50"; archive_dir:str="live_archive_stage48"; final_review_dir:str="live_final_review_stage47"; signoff_dir:str="live_signoff_stage46"; consistency_dir:str="live_consistency_stage49"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveFinalArchiveEvidence:
    evidence_id:str="stage50-evidence"; category:LiveFinalArchiveCategory|str=LiveFinalArchiveCategory.SYSTEM; status:LiveFinalArchiveStatus|str=LiveFinalArchiveStatus.SKIPPED; severity:LiveFinalArchiveSeverity|str=LiveFinalArchiveSeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class FinalArchiveReviewItem:
    item_id:str="remediation"; title:str=""; status:LiveFinalArchiveStatus|str=LiveFinalArchiveStatus.PASS; summary:str=""; required_action:str="人工复核补证材料；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class MaterialSealItem:
    item_id:str="material"; title:str=""; status:LiveFinalArchiveStatus|str=LiveFinalArchiveStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureItem:
    item_id:str="human"; role:str=""; status:LiveFinalArchiveStatus|str=LiveFinalArchiveStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="gray"; title:str=""; status:LiveFinalArchiveStatus|str=LiveFinalArchiveStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveFinalArchiveReport:
    report_id:str="stage50-remediation-final_archive-review"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalArchiveDecision|str=LiveFinalArchiveDecision.NEED_MORE_EVIDENCE; config:LiveFinalArchiveConfig|dict[str,Any]=field(default_factory=LiveFinalArchiveConfig); evidence:list[LiveFinalArchiveEvidence]=field(default_factory=list); final_archive_review:list[FinalArchiveReviewItem]=field(default_factory=list); material_seal:list[MaterialSealItem]=field(default_factory=list); human_closure:list[HumanClosureItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage50 不代表实盘授权","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class MaterialSealReport:
    report_id:str="stage50-material-final_archive"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalArchiveDecision|str=LiveFinalArchiveDecision.NEED_MORE_EVIDENCE; items:list[MaterialSealItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureReport:
    report_id:str="stage50-human-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalArchiveDecision|str=LiveFinalArchiveDecision.NEED_MORE_EVIDENCE; items:list[HumanClosureItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage50-next-gray-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalArchiveDecision|str=LiveFinalArchiveDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
