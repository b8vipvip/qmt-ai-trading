# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_ARCHIVE_REVIEW 只表示最终只读归档材料可供人工复核。"
class LiveArchiveDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_ARCHIVE_REVIEW="READY_FOR_ARCHIVE_REVIEW"
class LiveArchiveStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveArchiveSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveArchiveCategory(str, Enum):
    STAGE44_ENV_SNAPSHOT="STAGE44_ENV_SNAPSHOT"; STAGE45_RUNBOOK="STAGE45_RUNBOOK"; STAGE46_SIGNOFF="STAGE46_SIGNOFF"; STAGE47_FINAL_REVIEW="STAGE47_FINAL_REVIEW"; ARCHIVE_INDEX="ARCHIVE_INDEX"; EVIDENCE_REMEDIATION="EVIDENCE_REMEDIATION"; HUMAN_VERIFICATION="HUMAN_VERIFICATION"; NEXT_READONLY_CHECK="NEXT_READONLY_CHECK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveArchiveConfig:
    repo_root:str="."; output_dir:str="live_archive_stage48"; final_review_dir:str="live_final_review_stage47"; signoff_dir:str="live_signoff_stage46"; runbook_dir:str="live_runbook_stage45"; env_snapshot_dir:str="live_env_snapshot_stage44"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveEvidence:
    evidence_id:str="stage48-evidence"; category:LiveArchiveCategory|str=LiveArchiveCategory.SYSTEM; status:LiveArchiveStatus|str=LiveArchiveStatus.SKIPPED; severity:LiveArchiveSeverity|str=LiveArchiveSeverity.WARN; path:str=""; title:str=""; summary:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ArchiveIndexItem:
    item_id:str="go-no-go"; title:str=""; status:LiveArchiveStatus|str=LiveArchiveStatus.PASS; summary:str=""; confirmations:list[str]=field(default_factory=list)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanVerificationSummaryItem:
    item_id:str="signature"; role:str=""; statement:str=""; status:LiveArchiveStatus|str=LiveArchiveStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceRemediationItem:
    item_id:str="gap"; title:str=""; severity:LiveArchiveSeverity|str=LiveArchiveSeverity.WARN; summary:str=""; required_action:str="补齐证据后重新执行只读验收。"
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckItem:
    item_id:str="plan"; title:str=""; summary:str=""; status:LiveArchiveStatus|str=LiveArchiveStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class LiveArchiveReport:
    report_id:str="stage48-final-readonly-archive-remediation"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveDecision|str=LiveArchiveDecision.NEED_MORE_EVIDENCE; config:LiveArchiveConfig|dict[str,Any]=field(default_factory=LiveArchiveConfig); evidence:list[LiveArchiveEvidence]=field(default_factory=list); archive_index:list[ArchiveIndexItem]=field(default_factory=list); evidence_remediation_plan:list[EvidenceRemediationItem]=field(default_factory=list); human_verification_summary:list[HumanVerificationSummaryItem]=field(default_factory=list); next_readonly_check_plan:list[NextReadonlyCheckItem]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage48 不是实盘授权","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class HumanVerificationSummaryReport:
    report_id:str="stage48-human-verification-summary"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveDecision|str=LiveArchiveDecision.NEED_MORE_EVIDENCE; items:list[HumanVerificationSummaryItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceRemediationReport:
    report_id:str="stage48-evidence-remediation"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveDecision|str=LiveArchiveDecision.NEED_MORE_EVIDENCE; items:list[EvidenceRemediationItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyCheckReport:
    report_id:str="stage48-next-readonly-check"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveArchiveDecision|str=LiveArchiveDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyCheckItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
