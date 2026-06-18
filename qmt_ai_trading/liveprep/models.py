"""Models for Stage 30 live gray readiness preparation."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Live gray readiness is a preparation report only. It does not enable live trading, does not submit orders, and cannot bypass Risk Gate, Human Approval, Live Readiness Audit, Monitoring, or Circuit Breaker."

class LiveGrayDecision(str, Enum):
    NO_GO = "NO_GO"; BLOCKED = "BLOCKED"; READY_FOR_MANUAL_REVIEW = "READY_FOR_MANUAL_REVIEW"
class LiveGrayCheckStatus(str, Enum):
    PASS = "PASS"; WARN = "WARN"; FAIL = "FAIL"; SKIP = "SKIP"
class LiveGraySeverity(str, Enum):
    INFO = "INFO"; WARNING = "WARNING"; ERROR = "ERROR"; CRITICAL = "CRITICAL"
class LiveGrayScope(str, Enum):
    CONFIG = "CONFIG"; RISK = "RISK"; APPROVAL = "APPROVAL"; PAPER = "PAPER"; AUDIT = "AUDIT"; MONITORING = "MONITORING"; AGENT = "AGENT"; WHITELIST = "WHITELIST"; CAPITAL = "CAPITAL"; SYSTEM = "SYSTEM"

@dataclass
class LiveGrayConfig:
    live_enabled: bool = False
    gray_enabled: bool = False
    max_total_capital: float = 5000.0
    max_single_order_value: float = 1000.0
    max_symbol_weight: float = 0.1
    max_portfolio_weight: float = 0.2
    allowed_symbols: list[str] = field(default_factory=list)
    require_human_approval: bool = True
    require_risk_gate: bool = True
    require_paper_trading: bool = True
    require_live_readiness_audit: bool = True
    require_monitoring: bool = True
    require_agent_research: bool = True
    require_circuit_breaker_closed: bool = True
    require_quality_pass: bool = True
    allow_unknown_quality_for_review: bool = False
    operator_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class LiveGrayCheck:
    check_id: str
    scope: LiveGrayScope | str
    status: LiveGrayCheckStatus | str
    severity: LiveGraySeverity | str
    title: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        d=asdict(self); d["scope"]=getattr(self.scope,"value",self.scope); d["status"]=getattr(self.status,"value",self.status); d["severity"]=getattr(self.severity,"value",self.severity); return d

@dataclass
class LiveGrayReadinessReport:
    report_id: str = field(default_factory=lambda: f"livegray-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: LiveGrayDecision | str = LiveGrayDecision.NO_GO
    config: LiveGrayConfig = field(default_factory=LiveGrayConfig)
    checks: list[LiveGrayCheck] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    blocked_reasons: list[str] = field(default_factory=list)
    manual_review_items: list[str] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    success: bool = False
    message: str = "Default NO_GO; live gray readiness preparation only."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"report_id":self.report_id,"created_at":self.created_at,"decision":getattr(self.decision,"value",self.decision),"config":self.config.to_dict(),"checks":[c.to_dict() for c in self.checks],"summary":self.summary,"blocked_reasons":self.blocked_reasons,"manual_review_items":self.manual_review_items,"safety_note":self.safety_note,"success":self.success,"message":self.message,"metadata":self.metadata}
