"""Dataclasses for the Stage 23 live readiness audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class GoNoGoDecision(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"


def json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    return value


@dataclass
class AuditCheckResult:
    check_id: str
    name: str
    status: AuditStatus | str
    severity: AuditSeverity | str
    message: str
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass
class AuditReport:
    report_id: str
    created_at: str
    project_root: str
    decision: GoNoGoDecision | str = GoNoGoDecision.NO_GO
    summary: str = ""
    total_checks: int = 0
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    critical_count: int = 0
    checks: list[AuditCheckResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass
class LiveReadinessPolicy:
    require_roadmap: bool = True
    require_architecture: bool = True
    require_risk_gate: bool = True
    require_human_approval: bool = True
    require_paper_trading: bool = True
    require_sync_script_protected: bool = True
    require_live_disabled: bool = True
    require_no_xttrader_import: bool = True
    require_no_direct_order_call: bool = True
    require_gitignore_runtime_dirs: bool = True
    require_no_sensitive_patterns: bool = True
    allow_go: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))
