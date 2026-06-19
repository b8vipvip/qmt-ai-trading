# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_HUMAN_REVIEW 只表示材料可供人工复核。"

class LiveGrayReviewDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_HUMAN_REVIEW="READY_FOR_HUMAN_REVIEW"
class LiveGrayReviewStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveGrayReviewSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveGrayReviewCategory(str, Enum):
    STAGE39_FINAL_AUTHORIZATION="STAGE39_FINAL_AUTHORIZATION"; STAGE40_REDLINE_REVIEW="STAGE40_REDLINE_REVIEW"; STAGE41_LEDGER="STAGE41_LEDGER"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; PAPER_TRADING="PAPER_TRADING"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; DATA_QUALITY="DATA_QUALITY"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v
def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v

@dataclass
class LiveGrayReviewConfig:
    repo_root: str = "."
    output_dir: str = "live_gray_review_stage42"
    ledger_dir: str = "live_gray_ledger_stage41"
    redline_review_dir: str = "redline_review_stage40"
    final_authorization_dir: str = "final_authorization_stage40"
    validation_logs_dir: str = "validation_logs"
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveGrayReviewEvidence:
    evidence_id: str = "review-evidence"
    category: LiveGrayReviewCategory | str = LiveGrayReviewCategory.SYSTEM
    status: LiveGrayReviewStatus | str = LiveGrayReviewStatus.SKIPPED
    severity: LiveGrayReviewSeverity | str = LiveGrayReviewSeverity.WARN
    path: str = ""
    title: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveGrayReviewChecklistItem:
    item_id: str = "review-checklist-item"
    category: LiveGrayReviewCategory | str = LiveGrayReviewCategory.SYSTEM
    status: LiveGrayReviewStatus | str = LiveGrayReviewStatus.WARN
    severity: LiveGrayReviewSeverity | str = LiveGrayReviewSeverity.WARN
    path: str = ""
    line_number: int = 0
    marker: str = ""
    message: str = ""
    remediation: str = ""
    def to_dict(self): return to_plain(self)

@dataclass
class ReadOnlyRehearsalStep:
    step_id: str = "rehearsal-step"
    title: str = ""
    status: LiveGrayReviewStatus | str = LiveGrayReviewStatus.PASS
    safety_note: str = SAFETY_NOTE
    evidence_path: str = ""
    expected_result: str = "只读演练材料可供人工复核；不产生实盘授权。"
    def to_dict(self): return to_plain(self)

@dataclass
class ReadOnlyRehearsalReport:
    report_id: str = "stage42-readonly-rehearsal"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveGrayReviewDecision | str = LiveGrayReviewDecision.NEED_MORE_EVIDENCE
    steps: list[ReadOnlyRehearsalStep] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveGrayReviewReport:
    report_id: str = "stage42-live-gray-human-review-package"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveGrayReviewDecision | str = LiveGrayReviewDecision.NEED_MORE_EVIDENCE
    config: LiveGrayReviewConfig | dict[str, Any] = field(default_factory=LiveGrayReviewConfig)
    evidence: list[LiveGrayReviewEvidence] = field(default_factory=list)
    checklist: list[LiveGrayReviewChecklistItem] = field(default_factory=list)
    rehearsal: ReadOnlyRehearsalReport | dict[str, Any] | None = None
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_manual_signoffs: list[str] = field(default_factory=lambda: ["人工 go/no-go 会议主持人签字", "风险负责人签字", "最终授权人签字"])
    summary: dict[str, Any] = field(default_factory=dict)
    safety_note: str = SAFETY_NOTE
    def to_dict(self): return to_plain(self)
