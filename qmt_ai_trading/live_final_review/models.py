# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_FINAL_REVIEW 只表示最终只读 go/no-go 材料可供人工复核。"
class LiveFinalReviewDecision(str, Enum): NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_FINAL_REVIEW="READY_FOR_FINAL_REVIEW"
class LiveFinalReviewStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveFinalReviewSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveFinalReviewCategory(str, Enum):
    STAGE43_SIGNATURE_FREEZE="STAGE43_SIGNATURE_FREEZE"; STAGE44_ENV_SNAPSHOT="STAGE44_ENV_SNAPSHOT"; STAGE45_RUNBOOK="STAGE45_RUNBOOK"; STAGE46_SIGNOFF="STAGE46_SIGNOFF"; FINAL_GO_NO_GO_SUMMARY="FINAL_GO_NO_GO_SUMMARY"; SIGNATURE_VERIFICATION="SIGNATURE_VERIFICATION"; EVIDENCE_GAP="EVIDENCE_GAP"; NEXT_READONLY_PLAN="NEXT_READONLY_PLAN"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveFinalReviewConfig:
    repo_root:str="."; output_dir:str="live_final_review_stage47"; signoff_dir:str="live_signoff_stage46"; runbook_dir:str="live_runbook_stage45"; env_snapshot_dir:str="live_env_snapshot_stage44"; signature_freeze_dir:str="live_signature_freeze_stage43"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveFinalReviewEvidence:
    evidence_id:str="stage47-evidence"; category:LiveFinalReviewCategory|str=LiveFinalReviewCategory.SYSTEM; status:LiveFinalReviewStatus|str=LiveFinalReviewStatus.SKIPPED; severity:LiveFinalReviewSeverity|str=LiveFinalReviewSeverity.WARN; path:str=""; title:str=""; summary:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class GoNoGoSummaryItem:
    item_id:str="go-no-go"; title:str=""; status:LiveFinalReviewStatus|str=LiveFinalReviewStatus.PASS; summary:str=""; confirmations:list[str]=field(default_factory=list)
    def to_dict(self): return to_plain(self)
@dataclass
class SignatureVerificationItem:
    item_id:str="signature"; role:str=""; statement:str=""; status:LiveFinalReviewStatus|str=LiveFinalReviewStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceGapItem:
    item_id:str="gap"; title:str=""; severity:LiveFinalReviewSeverity|str=LiveFinalReviewSeverity.WARN; summary:str=""; required_action:str="补齐证据后重新执行只读验收。"
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyPlanItem:
    item_id:str="plan"; title:str=""; summary:str=""; status:LiveFinalReviewStatus|str=LiveFinalReviewStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class LiveFinalReviewReport:
    report_id:str="stage47-final-readonly-go-nogo-review"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalReviewDecision|str=LiveFinalReviewDecision.NEED_MORE_EVIDENCE; config:LiveFinalReviewConfig|dict[str,Any]=field(default_factory=LiveFinalReviewConfig); evidence:list[LiveFinalReviewEvidence]=field(default_factory=list); go_no_go_summary:list[GoNoGoSummaryItem]=field(default_factory=list); signature_verification_items:list[SignatureVerificationItem]=field(default_factory=list); evidence_gaps:list[EvidenceGapItem]=field(default_factory=list); next_readonly_plan:list[NextReadonlyPlanItem]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage47 不是实盘授权","确认未来真实执行仍需单独审批","确认不调用 xttrader、不查账户、不下单、不真实通知"]); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class SignatureVerificationReport:
    report_id:str="stage47-signature-verification"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalReviewDecision|str=LiveFinalReviewDecision.NEED_MORE_EVIDENCE; items:list[SignatureVerificationItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class EvidenceGapReport:
    report_id:str="stage47-evidence-gap"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalReviewDecision|str=LiveFinalReviewDecision.NEED_MORE_EVIDENCE; items:list[EvidenceGapItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class NextReadonlyPlanReport:
    report_id:str="stage47-next-readonly-plan"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:LiveFinalReviewDecision|str=LiveFinalReviewDecision.NEED_MORE_EVIDENCE; items:list[NextReadonlyPlanItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
