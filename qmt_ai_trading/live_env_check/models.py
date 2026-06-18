from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Live environment check is read-only. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."

class LiveEnvCheckDecision(str, Enum):
    NOT_READY = "NOT_READY"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"
    READY_FOR_ENV_REVIEW = "READY_FOR_ENV_REVIEW"
    BLOCKED = "BLOCKED"

class LiveEnvCheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"

class LiveEnvCheckScope(str, Enum):
    SYSTEM = "SYSTEM"; FILES = "FILES"; GIT = "GIT"; CONFIG = "CONFIG"; SCHEDULER = "SCHEDULER"
    RISK = "RISK"; APPROVAL = "APPROVAL"; PAPER = "PAPER"; MONITORING = "MONITORING"
    DATA_QUALITY = "DATA_QUALITY"; AGENT = "AGENT"; NOTIFICATION = "NOTIFICATION"; DASHBOARD = "DASHBOARD"
    LIVE_MANUAL_PREP = "LIVE_MANUAL_PREP"; SECURITY = "SECURITY"

@dataclass
class LiveEnvCheckConfig:
    allowed_symbols: list[str] = field(default_factory=list)
    max_total_capital: float | None = None
    max_single_order_value: float | None = None
    max_symbol_weight: float = 0.1
    max_portfolio_weight: float = 0.2
    require_git_clean: bool = False
    require_sync_script_protected: bool = True
    require_no_sensitive_files: bool = True
    require_no_live_flags: bool = True
    require_dashboard_read_only: bool = True
    require_notification_dry_run: bool = True
    require_qmt_trading_disabled: bool = True
    operator_name: str = ""
    reviewer_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class LiveEnvCheckItem:
    check_id: str
    scope: LiveEnvCheckScope | str
    status: LiveEnvCheckStatus | str
    title: str
    message: str = ""
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self); data["scope"] = self.scope.value if isinstance(self.scope, LiveEnvCheckScope) else str(self.scope); data["status"] = self.status.value if isinstance(self.status, LiveEnvCheckStatus) else str(self.status); return data

@dataclass
class LiveEnvCheckReport:
    report_id: str = field(default_factory=lambda: f"live-env-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveEnvCheckDecision | str = LiveEnvCheckDecision.NEED_MORE_EVIDENCE
    config: LiveEnvCheckConfig = field(default_factory=LiveEnvCheckConfig)
    checks: list[LiveEnvCheckItem] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = "Read-only live environment check generated for manual review."
    safety_note: str = SAFETY_NOTE
    success: bool = False
    message: str = "READY_FOR_ENV_REVIEW is not live trading authorization."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"report_id": self.report_id, "created_at": self.created_at, "decision": self.decision.value if isinstance(self.decision, LiveEnvCheckDecision) else str(self.decision), "config": self.config.to_dict(), "checks": [c.to_dict() for c in self.checks], "blocked_reasons": list(self.blocked_reasons), "warnings": list(self.warnings), "summary": self.summary, "safety_note": self.safety_note, "success": bool(self.success), "message": self.message, "metadata": dict(self.metadata)}
