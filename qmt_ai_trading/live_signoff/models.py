# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_SIGNOFF_REVIEW 只表示签字封版材料可供人工复核。"
class LiveSignoffDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_SIGNOFF_REVIEW="READY_FOR_SIGNOFF_REVIEW"
class LiveSignoffStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveSignoffSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveSignoffCategory(str, Enum):
    STAGE42_HUMAN_REVIEW="STAGE42_HUMAN_REVIEW"; STAGE43_SIGNATURE_FREEZE="STAGE43_SIGNATURE_FREEZE"; STAGE44_ENV_SNAPSHOT="STAGE44_ENV_SNAPSHOT"; STAGE45_RUNBOOK="STAGE45_RUNBOOK"; RUNBOOK_REVIEW="RUNBOOK_REVIEW"; MANUAL_REHEARSAL_SIGNOFF="MANUAL_REHEARSAL_SIGNOFF"; INCIDENT_REHEARSAL="INCIDENT_REHEARSAL"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v
def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class LiveSignoffConfig:
    repo_root: str="."; output_dir: str="live_signoff_stage46"; runbook_dir: str="live_runbook_stage45"; env_snapshot_dir: str="live_env_snapshot_stage44"; signature_freeze_dir: str="live_signature_freeze_stage43"; review_dir: str="live_gray_review_stage42"; validation_logs_dir: str="validation_logs"; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; live_trading_enabled: bool=False; metadata: dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveSignoffEvidence:
    evidence_id: str="stage46-evidence"; category: LiveSignoffCategory|str=LiveSignoffCategory.SYSTEM; status: LiveSignoffStatus|str=LiveSignoffStatus.SKIPPED; severity: LiveSignoffSeverity|str=LiveSignoffSeverity.WARN; path: str=""; title: str=""; summary: str=""; metadata: dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class RunbookReviewItem:
    item_id: str="runbook-review"; title: str=""; status: LiveSignoffStatus|str=LiveSignoffStatus.PASS; summary: str=""; confirmations: list[str]=field(default_factory=list)
    def to_dict(self): return to_plain(self)
@dataclass
class ManualSignoffItem:
    item_id: str="manual-signoff"; role: str=""; statement: str=""; status: LiveSignoffStatus|str=LiveSignoffStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class IncidentRehearsalResult:
    item_id: str="incident-rehearsal"; scenario: str=""; severity: LiveSignoffSeverity|str=LiveSignoffSeverity.WARN; result: str="只读演练待人工复核"; required_action: str="记录证据并由人工确认。"
    def to_dict(self): return to_plain(self)
@dataclass
class LiveSignoffReport:
    report_id: str="stage46-runbook-review-manual-signoff"; created_at: str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveSignoffDecision|str=LiveSignoffDecision.NEED_MORE_EVIDENCE; config: LiveSignoffConfig|dict[str, Any]=field(default_factory=LiveSignoffConfig); evidence: list[LiveSignoffEvidence]=field(default_factory=list); runbook_review: list[RunbookReviewItem]=field(default_factory=list); manual_signoff_items: list[ManualSignoffItem]=field(default_factory=list); incident_results: list[IncidentRehearsalResult]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); required_manual_confirmations: list[str]=field(default_factory=lambda:["确认 Stage46 不是实盘授权", "确认未来真实执行仍需单独审批", "确认不调用 xttrader、不查账户、不下单、不真实通知"]); safety_note: str=SAFETY_NOTE; summary: dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ManualSignoffReport:
    report_id: str="stage46-manual-signoff"; created_at: str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveSignoffDecision|str=LiveSignoffDecision.NEED_MORE_EVIDENCE; items: list[ManualSignoffItem]=field(default_factory=list); safety_note: str=SAFETY_NOTE; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class IncidentRehearsalReport:
    report_id: str="stage46-incident-rehearsal"; created_at: str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveSignoffDecision|str=LiveSignoffDecision.NEED_MORE_EVIDENCE; items: list[IncidentRehearsalResult]=field(default_factory=list); safety_note: str=SAFETY_NOTE; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str, Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
