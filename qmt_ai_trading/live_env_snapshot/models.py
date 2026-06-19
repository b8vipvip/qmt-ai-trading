# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_ENV_SNAPSHOT 只表示环境快照材料可供人工复核。"

class LiveEnvSnapshotDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_ENV_SNAPSHOT="READY_FOR_ENV_SNAPSHOT"
class LiveEnvSnapshotStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class LiveEnvSnapshotSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveEnvSnapshotCategory(str, Enum):
    STAGE40_REDLINE_REVIEW="STAGE40_REDLINE_REVIEW"; STAGE41_LEDGER="STAGE41_LEDGER"; STAGE42_HUMAN_REVIEW="STAGE42_HUMAN_REVIEW"; STAGE43_SIGNATURE_FREEZE="STAGE43_SIGNATURE_FREEZE"; CONFIG_FREEZE="CONFIG_FREEZE"; GITIGNORE="GITIGNORE"; DRY_RUN_MODE="DRY_RUN_MODE"; LIVE_SWITCH="LIVE_SWITCH"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> Any: return v.value if isinstance(v, Enum) else v
def to_plain(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k): to_plain(x) for k,x in v.items()}
    if isinstance(v, (list, tuple)): return [to_plain(x) for x in v]
    return v

@dataclass
class LiveEnvSnapshotConfig:
    repo_root: str = "."
    output_dir: str = "live_env_snapshot_stage44"
    signature_freeze_dir: str = "live_signature_freeze_stage43"
    review_dir: str = "live_gray_review_stage42"
    ledger_dir: str = "live_gray_ledger_stage41"
    redline_review_dir: str = "redline_review_stage40"
    validation_logs_dir: str = "validation_logs"
    read_only: bool = True
    dry_run_only: bool = True
    no_trade_authorization: bool = True
    live_trading_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveEnvSnapshotEvidence:
    evidence_id: str = "stage44-evidence"
    category: LiveEnvSnapshotCategory | str = LiveEnvSnapshotCategory.SYSTEM
    status: LiveEnvSnapshotStatus | str = LiveEnvSnapshotStatus.SKIPPED
    severity: LiveEnvSnapshotSeverity | str = LiveEnvSnapshotSeverity.WARN
    path: str = ""
    title: str = ""
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class ConfigFreezeReviewItem:
    item_id: str = "config-freeze-review-item"
    category: LiveEnvSnapshotCategory | str = LiveEnvSnapshotCategory.CONFIG_FREEZE
    status: LiveEnvSnapshotStatus | str = LiveEnvSnapshotStatus.PASS
    severity: LiveEnvSnapshotSeverity | str = LiveEnvSnapshotSeverity.INFO
    name: str = ""
    value: str = ""
    summary: str = ""
    def to_dict(self): return to_plain(self)

@dataclass
class EnvironmentSnapshotItem:
    item_id: str = "environment-snapshot-item"
    category: LiveEnvSnapshotCategory | str = LiveEnvSnapshotCategory.SYSTEM
    status: LiveEnvSnapshotStatus | str = LiveEnvSnapshotStatus.PASS
    severity: LiveEnvSnapshotSeverity | str = LiveEnvSnapshotSeverity.INFO
    name: str = ""
    value: str = ""
    summary: str = ""
    def to_dict(self): return to_plain(self)

@dataclass
class ReadonlyEnvironmentSnapshotReport:
    report_id: str = "stage44-readonly-environment-snapshot"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveEnvSnapshotDecision | str = LiveEnvSnapshotDecision.NEED_MORE_EVIDENCE
    config: LiveEnvSnapshotConfig | dict[str, Any] = field(default_factory=LiveEnvSnapshotConfig)
    items: list[EnvironmentSnapshotItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)

@dataclass
class LiveEnvSnapshotReport:
    report_id: str = "stage44-live-env-snapshot-config-review"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveEnvSnapshotDecision | str = LiveEnvSnapshotDecision.NEED_MORE_EVIDENCE
    config: LiveEnvSnapshotConfig | dict[str, Any] = field(default_factory=LiveEnvSnapshotConfig)
    evidence: list[LiveEnvSnapshotEvidence] = field(default_factory=list)
    config_freeze_review: list[ConfigFreezeReviewItem] = field(default_factory=list)
    environment_snapshot: list[EnvironmentSnapshotItem] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_manual_confirmations: list[str] = field(default_factory=lambda: ["确认 Stage44 不是实盘授权", "确认 dry-run/shadow/live disabled", "确认运行产物未提交", "确认 Stage45 仍为只读演练"])
    safety_note: str = SAFETY_NOTE
    summary: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return to_plain(self)
