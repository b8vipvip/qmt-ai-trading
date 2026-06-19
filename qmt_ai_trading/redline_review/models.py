from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "Red-line review is review-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."


class RedlineReviewDecision(str, Enum):
    BLOCKED = "BLOCKED"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"
    READY_FOR_REDLINE_REVIEW = "READY_FOR_REDLINE_REVIEW"


class RedlineSeverity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class RedlineStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class RedlineCategory(str, Enum):
    LIVE_SWITCH = "LIVE_SWITCH"
    EXECUTE_SWITCH = "EXECUTE_SWITCH"
    REAL_NOTIFICATION = "REAL_NOTIFICATION"
    QMT_TRADING_API = "QMT_TRADING_API"
    XTTRADER = "XTTRADER"
    ACCOUNT_QUERY = "ACCOUNT_QUERY"
    ORDER_SUBMISSION = "ORDER_SUBMISSION"
    RISK_BYPASS = "RISK_BYPASS"
    APPROVAL_BYPASS = "APPROVAL_BYPASS"
    SCHEDULER = "SCHEDULER"
    DASHBOARD = "DASHBOARD"
    DOCUMENTATION = "DOCUMENTATION"
    RUNTIME_ARTIFACT = "RUNTIME_ARTIFACT"
    SENSITIVE_FILE = "SENSITIVE_FILE"
    SYSTEM = "SYSTEM"


def enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    return value


@dataclass
class RedlineReviewConfig:
    repo_root: str = "."
    include_paths: list[str] = field(default_factory=lambda: ["qmt_ai_trading", "scripts", "docs", "tests"])
    exclude_paths: list[str] = field(default_factory=lambda: [
        ".git", "__pycache__", ".pytest_cache", ".venv", "venv",
        "market_data", "data_cache", "reports", "logs", "approvals", "paper_orders",
        "final_authorization_stage39", "final_authorization_stage40",
        "redline_review_stage40", "dashboard_stage40", "monitoring_reports_stage40",
        "validation_logs",
    ])
    allowed_live_markers: list[str] = field(default_factory=list)
    allowed_dry_run_markers: list[str] = field(default_factory=lambda: ["dry-run", "dry_run", "review-only", "read-only", "preparation-only"])
    require_scheduler_dry_run: bool = True
    require_dashboard_read_only: bool = True
    require_no_sensitive_files: bool = True
    require_no_xttrader: bool = True
    require_no_qmt_trading_api: bool = True
    require_no_account_queries: bool = True
    require_no_real_notifications: bool = True
    require_no_execute_live: bool = True
    operator_name: str = ""
    reviewer_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)


@dataclass
class RedlineFinding:
    finding_id: str = "redline-finding"
    category: RedlineCategory | str = RedlineCategory.SYSTEM
    status: RedlineStatus | str = RedlineStatus.WARN
    severity: RedlineSeverity | str = RedlineSeverity.WARN
    path: str = ""
    line_number: int = 0
    marker: str = ""
    message: str = ""
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)


@dataclass
class RedlineReviewReport:
    report_id: str = "redline-review"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: RedlineReviewDecision | str = RedlineReviewDecision.NEED_MORE_EVIDENCE
    config: RedlineReviewConfig | dict[str, Any] = field(default_factory=RedlineReviewConfig)
    findings: list[RedlineFinding] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    safety_note: str = SAFETY_NOTE
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)
