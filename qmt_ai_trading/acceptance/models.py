"""Stage 32 final acceptance data models.

Documentation and dry-run validation only. No QMT, xttrader, notification, or order submission.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

class AcceptanceDecision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

@dataclass
class AcceptanceCheck:
    check_id: str
    title: str
    status: AcceptanceDecision
    message: str
    evidence: str = ""
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self); d["status"] = self.status.value; return d

@dataclass
class AcceptanceReport:
    report_id: str
    created_at: str
    decision: AcceptanceDecision
    checks: list[AcceptanceCheck] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    safety_note: str = ""
    success: bool = False
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self); d["decision"] = self.decision.value; d["checks"]=[c.to_dict() for c in self.checks]; return d
