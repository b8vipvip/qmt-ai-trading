# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_RUNBOOK_REVIEW 只表示运行手册材料可供人工复核。"
class LiveRunbookDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_RUNBOOK_REVIEW="READY_FOR_RUNBOOK_REVIEW"
class LiveRunbookStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveRunbookSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveRunbookCategory(str, Enum):
    STAGE41_LEDGER="STAGE41_LEDGER"; STAGE42_HUMAN_REVIEW="STAGE42_HUMAN_REVIEW"; STAGE43_SIGNATURE_FREEZE="STAGE43_SIGNATURE_FREEZE"; STAGE44_ENV_SNAPSHOT="STAGE44_ENV_SNAPSHOT"; RUNBOOK="RUNBOOK"; MANUAL_REHEARSAL="MANUAL_REHEARSAL"; INCIDENT_PLAYBOOK="INCIDENT_PLAYBOOK"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v
def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v

@dataclass
class LiveRunbookConfig:
    repo_root: str = "."; output_dir: str = "live_runbook_stage45"; env_snapshot_dir: str = "live_env_snapshot_stage44"; signature_freeze_dir: str = "live_signature_freeze_stage43"; review_dir: str = "live_gray_review_stage42"; ledger_dir: str = "live_gray_ledger_stage41"; validation_logs_dir: str = "validation_logs"; read_only: bool = True; dry_run_only: bool = True; no_trade_authorization: bool = True; live_trading_enabled: bool = False; metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class LiveRunbookEvidence:
    evidence_id: str = "stage45-evidence"; category: LiveRunbookCategory | str = LiveRunbookCategory.SYSTEM; status: LiveRunbookStatus | str = LiveRunbookStatus.SKIPPED; severity: LiveRunbookSeverity | str = LiveRunbookSeverity.WARN; path: str = ""; title: str = ""; summary: str = ""; metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class RunbookSection:
    section_id: str = "runbook-section"; title: str = ""; content: list[str] = field(default_factory=list); category: LiveRunbookCategory | str = LiveRunbookCategory.RUNBOOK; status: LiveRunbookStatus | str = LiveRunbookStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class ManualRehearsalStep:
    step_id: str = "manual-step"; title: str = ""; checklist: list[str] = field(default_factory=list); expected_result: str = ""; status: LiveRunbookStatus | str = LiveRunbookStatus.PASS
    def to_dict(self): return to_plain(self)
@dataclass
class IncidentPlaybookItem:
    item_id: str = "incident-item"; scenario: str = ""; severity: LiveRunbookSeverity | str = LiveRunbookSeverity.WARN; detection: str = ""; response: list[str] = field(default_factory=list); rollback: str = ""
    def to_dict(self): return to_plain(self)
@dataclass
class LiveRunbookReport:
    report_id: str = "stage45-readonly-runbook-manual-rehearsal"; created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveRunbookDecision | str = LiveRunbookDecision.NEED_MORE_EVIDENCE; config: LiveRunbookConfig | dict[str, Any] = field(default_factory=LiveRunbookConfig); evidence: list[LiveRunbookEvidence] = field(default_factory=list); runbook_sections: list[RunbookSection] = field(default_factory=list); manual_steps: list[ManualRehearsalStep] = field(default_factory=list); incident_items: list[IncidentPlaybookItem] = field(default_factory=list); blocking_reasons: list[str] = field(default_factory=list); warnings: list[str] = field(default_factory=list); required_manual_confirmations: list[str] = field(default_factory=lambda:["确认 Stage45 不是实盘授权", "确认不调用 xttrader、不查账户、不下单、不真实通知", "确认 READY_FOR_RUNBOOK_REVIEW 仅代表材料可复核", "确认 Stage46 仍为只读复核/签字封版"]); safety_note: str = SAFETY_NOTE; summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class ManualRehearsalReport:
    report_id: str = "stage45-manual-rehearsal"; created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveRunbookDecision | str = LiveRunbookDecision.NEED_MORE_EVIDENCE; steps: list[ManualRehearsalStep] = field(default_factory=list); safety_note: str = SAFETY_NOTE; warnings: list[str] = field(default_factory=list); blocking_reasons: list[str] = field(default_factory=list); summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class IncidentPlaybookReport:
    report_id: str = "stage45-incident-playbook"; created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision: LiveRunbookDecision | str = LiveRunbookDecision.NEED_MORE_EVIDENCE; items: list[IncidentPlaybookItem] = field(default_factory=list); safety_note: str = SAFETY_NOTE; warnings: list[str] = field(default_factory=list); blocking_reasons: list[str] = field(default_factory=list); summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
