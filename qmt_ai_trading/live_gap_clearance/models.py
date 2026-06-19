# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_GAP_CLEARANCE_REVIEW 只表示灰度前最终缺口清零计划材料可供人工复核。"
class LiveGapClearanceDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_GAP_CLEARANCE_REVIEW="READY_FOR_GAP_CLEARANCE_REVIEW"
class LiveGapClearanceStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveGapClearanceSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveGapClearanceCategory(str, Enum):
    STAGE50_FINAL_ARCHIVE="STAGE50_FINAL_ARCHIVE"; STAGE51_ARCHIVE_LOCK="STAGE51_ARCHIVE_LOCK"; STAGE52_LOCK_CONSISTENCY="STAGE52_LOCK_CONSISTENCY"; STAGE53_ARCHIVE_VERIFICATION="STAGE53_ARCHIVE_VERIFICATION"; GAP_CLEARANCE="GAP_CLEARANCE"; EVIDENCE_REMEDIATION="EVIDENCE_REMEDIATION"; HUMAN_CLOSURE_RECHECK="HUMAN_CLOSURE_RECHECK"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveGapClearanceConfig:
    repo_root:str="."; output_dir:str="live_gap_clearance_stage54"; archive_verification_dir:str="live_archive_verification_stage53"; lock_consistency_dir:str="live_lock_consistency_stage52"; archive_lock_dir:str="live_archive_lock_stage51"; final_archive_dir:str="live_final_archive_stage50"; validation_logs_dir:str="validation_logs"; roadmap_path:str="docs/qmt-ai-trading-project-roadmap.md"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveGapClearanceEvidence:
    evidence_id:str="stage54-evidence"; category:LiveGapClearanceCategory|str=LiveGapClearanceCategory.SYSTEM; status:LiveGapClearanceStatus|str=LiveGapClearanceStatus.SKIPPED; severity:LiveGapClearanceSeverity|str=LiveGapClearanceSeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class GapClearanceItem:
    item_id:str="gap-clearance"; title:str=""; status:LiveGapClearanceStatus|str=LiveGapClearanceStatus.PASS; summary:str=""; required_action:str="人工复核 Stage54 灰度前最终缺口清零计划；不代表实盘授权。"
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceRemediationItem:
    item_id:str="evidence-remediation"; title:str=""; status:LiveGapClearanceStatus|str=LiveGapClearanceStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckItem:
    item_id:str="human-recheck"; role:str=""; status:LiveGapClearanceStatus|str=LiveGapClearanceStatus.PASS; statement:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="next-readonly"; title:str=""; status:LiveGapClearanceStatus|str=LiveGapClearanceStatus.PASS; summary:str=""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveGapClearanceReport:
    report_id:str="stage54-final-pre-gray-gap-clearance"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveGapClearanceDecision|str=LiveGapClearanceDecision.NEED_MORE_EVIDENCE; config:LiveGapClearanceConfig|dict[str,Any]=field(default_factory=LiveGapClearanceConfig); evidence:list[LiveGapClearanceEvidence]=field(default_factory=list); gap_clearance:list[GapClearanceItem]=field(default_factory=list); evidence_remediation:list[EvidenceRemediationItem]=field(default_factory=list); human_closure_recheck:list[HumanClosureRecheckItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage54 不代表实盘授权","确认 READY_FOR_GAP_CLEARANCE_REVIEW 只代表材料可供人工复核","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知","确认 UI 不能绕过 Risk Gate / Human Approval"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceRemediationReport:
    report_id:str="stage54-evidence-remediation"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveGapClearanceDecision|str=LiveGapClearanceDecision.NEED_MORE_EVIDENCE; items:list[EvidenceRemediationItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanClosureRecheckReport:
    report_id:str="stage54-human-closure-recheck"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveGapClearanceDecision|str=LiveGapClearanceDecision.NEED_MORE_EVIDENCE; items:list[HumanClosureRecheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage54-next-readonly-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveGapClearanceDecision|str=LiveGapClearanceDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
