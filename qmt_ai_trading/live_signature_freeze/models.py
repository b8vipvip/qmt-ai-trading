# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_SIGNATURE 只表示材料可供人工签字复核。"

class LiveSignatureFreezeDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_SIGNATURE="READY_FOR_SIGNATURE"
class LiveSignatureFreezeStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveSignatureFreezeSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveSignatureFreezeCategory(str, Enum):
    STAGE40_REDLINE_REVIEW="STAGE40_REDLINE_REVIEW"; STAGE41_LEDGER="STAGE41_LEDGER"; STAGE42_HUMAN_REVIEW="STAGE42_HUMAN_REVIEW"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; CONFIG_FREEZE="CONFIG_FREEZE"; SIGNATURE="SIGNATURE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; DATA_QUALITY="DATA_QUALITY"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v
def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v

@dataclass
class LiveSignatureFreezeConfig:
    repo_root: str = "."
    output_dir: str = "live_signature_freeze_stage43"
    review_dir: str = "live_gray_review_stage42"
    ledger_dir: str = "live_gray_ledger_stage41"
    redline_review_dir: str = "redline_review_stage40"
    validation_logs_dir: str = "validation_logs"
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveSignatureFreezeEvidence:
    evidence_id: str = "signature-freeze-evidence"
    category: LiveSignatureFreezeCategory | str = LiveSignatureFreezeCategory.SYSTEM
    status: LiveSignatureFreezeStatus | str = LiveSignatureFreezeStatus.SKIPPED
    severity: LiveSignatureFreezeSeverity | str = LiveSignatureFreezeSeverity.WARN
    path: str = ""
    title: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveSignatureChecklistItem:
    item_id: str = "signature-checklist-item"
    category: LiveSignatureFreezeCategory | str = LiveSignatureFreezeCategory.SIGNATURE
    status: LiveSignatureFreezeStatus | str = LiveSignatureFreezeStatus.WARN
    severity: LiveSignatureFreezeSeverity | str = LiveSignatureFreezeSeverity.WARN
    path: str = ""
    line_number: int = 0
    marker: str = ""
    message: str = ""
    remediation: str = ""
    title: str = ""
    summary: str = ""
    def to_dict(self): return to_plain(self)

@dataclass
class ConfigFreezeItem:
    item_id: str = "config-freeze-item"
    category: LiveSignatureFreezeCategory | str = LiveSignatureFreezeCategory.CONFIG_FREEZE
    status: LiveSignatureFreezeStatus | str = LiveSignatureFreezeStatus.PASS
    severity: LiveSignatureFreezeSeverity | str = LiveSignatureFreezeSeverity.INFO
    name: str = ""
    frozen_value: str = ""
    summary: str = ""
    def to_dict(self): return to_plain(self)

@dataclass
class ConfigFreezeReport:
    report_id: str = "stage43-config-freeze-summary"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveSignatureFreezeDecision | str = LiveSignatureFreezeDecision.NEED_MORE_EVIDENCE
    config: LiveSignatureFreezeConfig | dict[str, Any] = field(default_factory=LiveSignatureFreezeConfig)
    items: list[ConfigFreezeItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveSignatureFreezeReport:
    report_id: str = "stage43-live-signature-freeze"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveSignatureFreezeDecision | str = LiveSignatureFreezeDecision.NEED_MORE_EVIDENCE
    config: LiveSignatureFreezeConfig | dict[str, Any] = field(default_factory=LiveSignatureFreezeConfig)
    evidence: list[LiveSignatureFreezeEvidence] = field(default_factory=list)
    checklist: list[LiveSignatureChecklistItem] = field(default_factory=list)
    config_freeze_items: list[ConfigFreezeItem] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_manual_signoffs: list[str] = field(default_factory=lambda: ["会议主持人签字", "风险负责人签字", "配置冻结复核人签字", "最终授权人签字"])
    safety_note: str = SAFETY_NOTE
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
