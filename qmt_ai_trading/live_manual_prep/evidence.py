from __future__ import annotations
from pathlib import Path
from typing import Any
from uuid import uuid4
from .models import LiveManualPrepConfig, LiveManualPrepDecision, LiveManualPrepEvidence, LiveManualPrepEvidenceStatus, LiveManualPrepEvidenceType
from .safety import contains_forbidden_live_manual_action, sanitize_live_manual_prep_metadata

def detect_live_manual_evidence_blockers(text: str, evidence_type: LiveManualPrepEvidenceType|str):
    reasons=[]; low=(text or "").lower()
    if contains_forbidden_live_manual_action(text): reasons.append("Forbidden live execution, account query, bypass, or real-send wording detected.")
    if "no_go" in low or "blocked" in low and str(evidence_type).endswith("LIVE_GRAY_READINESS"): reasons.append("Live Gray Readiness reports NO_GO/BLOCKED.")
    if "critical" in low or "circuit breaker open" in low or "circuit_breaker_open" in low: reasons.append("Monitoring CRITICAL or Circuit Breaker OPEN detected.")
    return list(dict.fromkeys(reasons))
def classify_live_manual_evidence_status(text: str, evidence_type: LiveManualPrepEvidenceType|str):
    if not text.strip(): return LiveManualPrepEvidenceStatus.MISSING
    if detect_live_manual_evidence_blockers(text, evidence_type): return LiveManualPrepEvidenceStatus.FAIL
    low=text.lower(); typ=str(evidence_type)
    if "need_more_evidence" in low: return LiveManualPrepEvidenceStatus.WARN
    if typ.endswith("DATA_QUALITY") and ("fail" in low or "unknown" in low): return LiveManualPrepEvidenceStatus.WARN
    if typ.endswith("NOTIFICATION_DRY_RUN") and not ("no real" in low or "dry-run" in low or "dry_run" in low): return LiveManualPrepEvidenceStatus.WARN
    if typ.endswith("DASHBOARD") and not ("read-only" in low or "readonly" in low or "no order" in low): return LiveManualPrepEvidenceStatus.WARN
    return LiveManualPrepEvidenceStatus.PRESENT
def summarize_live_manual_evidence_text(text: str, evidence_type):
    one=" ".join((text or "").split()); return one[:240] if one else f"No {evidence_type} evidence text."
def collect_live_manual_evidence_from_file(path: str|Path|None, evidence_type: LiveManualPrepEvidenceType|str):
    p=Path(path) if path else None
    if not p or not p.exists():
        return LiveManualPrepEvidence(f"live-manual-evidence-{uuid4().hex[:8]}", evidence_type, LiveManualPrepEvidenceStatus.MISSING, str(path or ""), "Evidence file is missing.", "WARN")
    text=p.read_text(encoding="utf-8", errors="replace")
    status=classify_live_manual_evidence_status(text, evidence_type); blockers=detect_live_manual_evidence_blockers(text, evidence_type)
    return LiveManualPrepEvidence(f"live-manual-evidence-{uuid4().hex[:8]}", evidence_type, status, str(p), summarize_live_manual_evidence_text(text, evidence_type), "CRITICAL" if status==LiveManualPrepEvidenceStatus.FAIL else ("WARN" if status==LiveManualPrepEvidenceStatus.WARN else "INFO"), "; ".join(blockers), sanitize_live_manual_prep_metadata({"bytes": len(text)}))
def collect_live_manual_prep_evidence(**paths: Any):
    mapping={"gray_decision_package":LiveManualPrepEvidenceType.GRAY_DECISION_PACKAGE,"live_gray_report":LiveManualPrepEvidenceType.LIVE_GRAY_READINESS,"gray_rehearsal_report":LiveManualPrepEvidenceType.GRAY_REHEARSAL,"live_readiness_audit_report":LiveManualPrepEvidenceType.LIVE_READINESS_AUDIT,"pipeline_report":LiveManualPrepEvidenceType.RISK_GATE,"approval_file":LiveManualPrepEvidenceType.HUMAN_APPROVAL,"paper_report":LiveManualPrepEvidenceType.PAPER_TRADING,"monitoring_report":LiveManualPrepEvidenceType.MONITORING,"data_quality_report":LiveManualPrepEvidenceType.DATA_QUALITY,"agent_memo":LiveManualPrepEvidenceType.AGENT_RESEARCH,"notification_dry_run_report":LiveManualPrepEvidenceType.NOTIFICATION_DRY_RUN,"dashboard_path":LiveManualPrepEvidenceType.DASHBOARD,"final_acceptance_report":LiveManualPrepEvidenceType.FINAL_ACCEPTANCE}
    return [collect_live_manual_evidence_from_file(paths.get(k), v) for k,v in mapping.items() if k in paths]
def aggregate_live_manual_prep_decision(evidence: list[LiveManualPrepEvidence], config: LiveManualPrepConfig):
    blocked=[e.blocked_reason for e in evidence if str(e.status)=="LiveManualPrepEvidenceStatus.FAIL" or str(e.status)=="FAIL" if e.blocked_reason]
    warnings=[]
    for e in evidence:
        st=e.status.value if hasattr(e.status,"value") else str(e.status)
        if st in {"MISSING","WARN"}: warnings.append(f"{e.evidence_type}: {e.summary}")
    if blocked: return LiveManualPrepDecision.BLOCKED, list(dict.fromkeys(blocked)), list(dict.fromkeys(warnings))
    required=[]
    for name, typ in [("require_gray_decision_package",LiveManualPrepEvidenceType.GRAY_DECISION_PACKAGE),("require_live_gray_readiness",LiveManualPrepEvidenceType.LIVE_GRAY_READINESS),("require_gray_rehearsal",LiveManualPrepEvidenceType.GRAY_REHEARSAL),("require_live_readiness_audit",LiveManualPrepEvidenceType.LIVE_READINESS_AUDIT),("require_risk_gate",LiveManualPrepEvidenceType.RISK_GATE),("require_human_approval",LiveManualPrepEvidenceType.HUMAN_APPROVAL),("require_paper_trading",LiveManualPrepEvidenceType.PAPER_TRADING),("require_monitoring",LiveManualPrepEvidenceType.MONITORING),("require_data_quality",LiveManualPrepEvidenceType.DATA_QUALITY),("require_agent_research",LiveManualPrepEvidenceType.AGENT_RESEARCH),("require_notification_dry_run",LiveManualPrepEvidenceType.NOTIFICATION_DRY_RUN),("require_dashboard",LiveManualPrepEvidenceType.DASHBOARD),("require_final_acceptance",LiveManualPrepEvidenceType.FINAL_ACCEPTANCE)]:
        if getattr(config,name,False): required.append(typ.value)
    present={e.evidence_type.value if hasattr(e.evidence_type,"value") else str(e.evidence_type): (e.status.value if hasattr(e.status,"value") else str(e.status)) for e in evidence}
    missing=[r for r in required if present.get(r)!="PRESENT"]
    if missing or warnings: return LiveManualPrepDecision.NEED_MORE_EVIDENCE, [], list(dict.fromkeys(warnings+[f"Missing or non-present required evidence: {x}" for x in missing]))
    return LiveManualPrepDecision.READY_FOR_SIGNOFF, [], []
aggregate_evidence_decision=aggregate_live_manual_prep_decision
