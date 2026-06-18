from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Gray decision package is manual-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."
class GrayDecision(str, Enum):
    NOT_ELIGIBLE="NOT_ELIGIBLE"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_MANUAL_DECISION="READY_FOR_MANUAL_DECISION"; BLOCKED="BLOCKED"
class GrayDecisionEvidenceStatus(str, Enum):
    PRESENT="PRESENT"; MISSING="MISSING"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class GrayDecisionEvidenceType(str, Enum):
    RISK_GATE="RISK_GATE"; HUMAN_APPROVAL="HUMAN_APPROVAL"; PAPER_TRADING="PAPER_TRADING"; LIVE_READINESS_AUDIT="LIVE_READINESS_AUDIT"; MONITORING="MONITORING"; DATA_QUALITY="DATA_QUALITY"; AGENT_RESEARCH="AGENT_RESEARCH"; LIVE_GRAY_READINESS="LIVE_GRAY_READINESS"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; DASHBOARD="DASHBOARD"; GRAY_REHEARSAL="GRAY_REHEARSAL"; FINAL_ACCEPTANCE="FINAL_ACCEPTANCE"; SYSTEM="SYSTEM"
@dataclass
class GrayDecisionEvidence:
    evidence_id: str
    evidence_type: GrayDecisionEvidenceType | str
    status: GrayDecisionEvidenceStatus | str
    source_path: str = ""
    summary: str = ""
    severity: str = "INFO"
    blocked_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        d=asdict(self); d["evidence_type"]=self.evidence_type.value if isinstance(self.evidence_type,Enum) else str(self.evidence_type); d["status"]=self.status.value if isinstance(self.status,Enum) else str(self.status); return d
@dataclass
class GrayDecisionConfig:
    allowed_symbols: list[str] = field(default_factory=list)
    max_total_capital: float = 5000.0
    max_single_order_value: float = 1000.0
    max_symbol_weight: float = 0.1
    max_portfolio_weight: float = 0.2
    require_risk_gate: bool = True; require_human_approval: bool = True; require_paper_trading: bool = True; require_live_readiness_audit: bool = True; require_monitoring: bool = True; require_data_quality: bool = True; require_agent_research: bool = True; require_live_gray_readiness: bool = True; require_notification_dry_run: bool = True; require_dashboard: bool = True; require_gray_rehearsal: bool = True; require_final_acceptance: bool = True
    operator_name: str = ""; reviewer_name: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda:{"manual_only":True,"live_enabled":False,"real_send_enabled":False})
    def to_dict(self): return asdict(self)
@dataclass
class GrayDecisionPackage:
    package_id: str = field(default_factory=lambda:f"gray-decision-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: GrayDecision | str = GrayDecision.NEED_MORE_EVIDENCE
    config: GrayDecisionConfig = field(default_factory=GrayDecisionConfig)
    evidence: list[GrayDecisionEvidence] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_signature_placeholder: str = "Operator: ______ Reviewer: ______ Date: ______ Decision: ______"
    summary: str = "Manual-only gray decision package."
    safety_note: str = SAFETY_NOTE
    success: bool = True
    message: str = "Generated manual-only gray decision package."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        return {"package_id":self.package_id,"created_at":self.created_at,"decision":self.decision.value if isinstance(self.decision,Enum) else str(self.decision),"config":self.config.to_dict(),"evidence":[e.to_dict() for e in self.evidence],"checklist":list(self.checklist),"blocked_reasons":list(self.blocked_reasons),"warnings":list(dict.fromkeys(self.warnings)),"manual_signature_placeholder":self.manual_signature_placeholder,"summary":self.summary,"safety_note":self.safety_note,"success":self.success,"message":self.message,"metadata":dict(self.metadata)}
