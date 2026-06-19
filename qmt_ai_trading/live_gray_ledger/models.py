# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_MANUAL_REVIEW 只表示台账材料可供人工复核。"

class LiveGrayLedgerDecision(str, Enum):
    BLOCKED = "BLOCKED"; NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"; READY_FOR_MANUAL_REVIEW = "READY_FOR_MANUAL_REVIEW"
class LiveGrayLedgerStatus(str, Enum):
    PASS = "PASS"; WARN = "WARN"; FAIL = "FAIL"; SKIPPED = "SKIPPED"
class LiveGrayLedgerSeverity(str, Enum):
    INFO = "INFO"; WARN = "WARN"; CRITICAL = "CRITICAL"
class LiveGrayLedgerCategory(str, Enum):
    STAGE37_MANUAL_PREP="STAGE37_MANUAL_PREP"; STAGE38_ENV_CHECK="STAGE38_ENV_CHECK"; STAGE39_FINAL_AUTHORIZATION="STAGE39_FINAL_AUTHORIZATION"; STAGE40_REDLINE_REVIEW="STAGE40_REDLINE_REVIEW"; RISK_GATE="RISK_GATE"; HUMAN_APPROVAL="HUMAN_APPROVAL"; PAPER_TRADING="PAPER_TRADING"; LIVE_SWITCH="LIVE_SWITCH"; SCHEDULER="SCHEDULER"; NOTIFICATION="NOTIFICATION"; QMT_BOUNDARY="QMT_BOUNDARY"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v

def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k, x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v

@dataclass
class LiveGrayLedgerConfig:
    repo_root: str = "."
    output_dir: str = "live_gray_ledger_stage41"
    redline_review_dir: str = "redline_review_stage40"
    final_authorization_dir: str = "final_authorization_stage40"
    live_env_check_dir: str = "live_env_check_stage40"
    live_manual_prep_dir: str = "live_manual_prep_stage40"
    gray_decision_dir: str = "gray_decision_stage40"
    gray_rehearsal_dir: str = "gray_rehearsal_stage40"
    notification_dryrun_dir: str = "notification_dryrun_stage40"
    validation_logs_dir: str = "validation_logs"
    require_redline_review: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return to_plain(self)

@dataclass
class LiveGrayLedgerEvidence:
    evidence_id: str = "ledger-evidence"
    category: LiveGrayLedgerCategory | str = LiveGrayLedgerCategory.SYSTEM
    status: LiveGrayLedgerStatus | str = LiveGrayLedgerStatus.SKIPPED
    severity: LiveGrayLedgerSeverity | str = LiveGrayLedgerSeverity.WARN
    path: str = ""
    title: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return to_plain(self)

@dataclass
class LiveGrayLedgerItem:
    item_id: str = "ledger-item"
    category: LiveGrayLedgerCategory | str = LiveGrayLedgerCategory.SYSTEM
    status: LiveGrayLedgerStatus | str = LiveGrayLedgerStatus.WARN
    severity: LiveGrayLedgerSeverity | str = LiveGrayLedgerSeverity.WARN
    path: str = ""
    line_number: int = 0
    marker: str = ""
    message: str = ""
    remediation: str = ""
    def to_dict(self) -> dict[str, Any]: return to_plain(self)

@dataclass
class LiveGrayLedgerReport:
    report_id: str = "stage41-live-gray-readonly-ledger"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveGrayLedgerDecision | str = LiveGrayLedgerDecision.NEED_MORE_EVIDENCE
    config: LiveGrayLedgerConfig | dict[str, Any] = field(default_factory=LiveGrayLedgerConfig)
    evidence: list[LiveGrayLedgerEvidence] = field(default_factory=list)
    items: list[LiveGrayLedgerItem] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    safety_note: str = SAFETY_NOTE
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return to_plain(self)
