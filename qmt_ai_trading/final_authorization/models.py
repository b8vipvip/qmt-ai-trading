from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Final authorization package is review-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."

class FinalAuthorizationDecision(str, Enum):
    NOT_AUTHORIZED="NOT_AUTHORIZED"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_FINAL_SIGNOFF_REVIEW="READY_FOR_FINAL_SIGNOFF_REVIEW"; BLOCKED="BLOCKED"
class FinalAuthorizationEvidenceStatus(str, Enum):
    PRESENT="PRESENT"; MISSING="MISSING"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class FinalAuthorizationEvidenceType(str, Enum):
    LIVE_ENV_CHECK="LIVE_ENV_CHECK"; LIVE_MANUAL_PREP="LIVE_MANUAL_PREP"; GRAY_DECISION_PACKAGE="GRAY_DECISION_PACKAGE"; GRAY_REHEARSAL="GRAY_REHEARSAL"; LIVE_GRAY_READINESS="LIVE_GRAY_READINESS"; LIVE_READINESS_AUDIT="LIVE_READINESS_AUDIT"; RISK_GATE="RISK_GATE"; HUMAN_APPROVAL="HUMAN_APPROVAL"; PAPER_TRADING="PAPER_TRADING"; MONITORING="MONITORING"; DATA_QUALITY="DATA_QUALITY"; AGENT_RESEARCH="AGENT_RESEARCH"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; DASHBOARD="DASHBOARD"; FINAL_ACCEPTANCE="FINAL_ACCEPTANCE"; SYSTEM="SYSTEM"

def enum_value(v: Any) -> str:
    return v.value if isinstance(v, Enum) else str(v)

@dataclass
class FinalAuthorizationConfig:
    allowed_symbols: list[str] = field(default_factory=list)
    max_total_capital: float = 5000.0
    max_single_order_value: float = 1000.0
    max_symbol_weight: float = 0.1
    max_portfolio_weight: float = 0.2
    require_live_env_check: bool = True
    require_live_manual_prep: bool = True
    require_gray_decision_package: bool = True
    require_gray_rehearsal: bool = True
    require_live_gray_readiness: bool = True
    require_live_readiness_audit: bool = True
    require_risk_gate: bool = True
    require_human_approval: bool = True
    require_paper_trading: bool = True
    require_monitoring: bool = True
    require_data_quality: bool = True
    require_agent_research: bool = True
    require_notification_dry_run: bool = True
    require_dashboard: bool = True
    require_final_acceptance: bool = True
    operator_name: str = ""
    reviewer_name: str = ""
    risk_owner_name: str = ""
    final_approver_name: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda: {"final_authorization_dry_run": True, "live_enabled": False, "real_order_enabled": False, "real_send_enabled": False, "external_network_enabled": False})
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class FinalAuthorizationEvidence:
    evidence_id: str
    evidence_type: FinalAuthorizationEvidenceType | str
    status: FinalAuthorizationEvidenceStatus | str
    source_path: str = ""
    summary: str = ""
    severity: str = "INFO"
    blocked_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        d=asdict(self); d["evidence_type"]=enum_value(self.evidence_type); d["status"]=enum_value(self.status); return d

@dataclass
class FinalAuthorizationPackage:
    package_id: str = field(default_factory=lambda: f"final-authorization-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: FinalAuthorizationDecision | str = FinalAuthorizationDecision.NEED_MORE_EVIDENCE
    config: FinalAuthorizationConfig = field(default_factory=FinalAuthorizationConfig)
    evidence: list[FinalAuthorizationEvidence] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    forbidden_items: list[str] = field(default_factory=list)
    residual_risks: list[str] = field(default_factory=list)
    signoff_placeholders: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    future_stage_requirements: list[str] = field(default_factory=list)
    summary: str = "Final manual authorization package summary for future human review only."
    safety_note: str = SAFETY_NOTE
    success: bool = True
    message: str = "Generated review-only final authorization package."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"package_id":self.package_id,"created_at":self.created_at,"decision":enum_value(self.decision),"config":self.config.to_dict(),"evidence":[e.to_dict() for e in self.evidence],"checklist":self.checklist,"forbidden_items":self.forbidden_items,"residual_risks":self.residual_risks,"signoff_placeholders":self.signoff_placeholders,"blocked_reasons":list(dict.fromkeys(self.blocked_reasons)),"warnings":list(dict.fromkeys(self.warnings)),"future_stage_requirements":self.future_stage_requirements,"summary":self.summary,"safety_note":self.safety_note,"success":self.success,"message":self.message,"metadata":self.metadata}
