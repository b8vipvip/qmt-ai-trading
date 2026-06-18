"""Human approval data models for dry-run TradeIntent authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"


@dataclass
class ApprovalRequest:
    approval_id: str
    run_id: str
    created_at: str
    expires_at: str
    status: ApprovalStatus | str = ApprovalStatus.PENDING
    trade_intents: list[dict[str, Any]] = field(default_factory=list)
    risk_decisions: list[dict[str, Any]] = field(default_factory=list)
    data_source: dict[str, Any] = field(default_factory=dict)
    confidence: str | None = None
    summary: str = ""
    reason: str = ""
    requested_by: str = "pipeline"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalDecision:
    approval_id: str
    action: ApprovalAction | str
    decided_at: str
    decided_by: str
    comment: str = ""
    status_after: ApprovalStatus | str = ApprovalStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalCheckResult:
    approval_id: str
    allowed: bool
    status: ApprovalStatus | str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
