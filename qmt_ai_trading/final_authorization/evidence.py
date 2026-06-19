from __future__ import annotations
from pathlib import Path
from typing import Any
from uuid import uuid4
from .models import FinalAuthorizationConfig, FinalAuthorizationDecision, FinalAuthorizationEvidence, FinalAuthorizationEvidenceStatus as S, FinalAuthorizationEvidenceType as T
from .safety import contains_forbidden_final_authorization_action, sanitize_final_authorization_metadata

def detect_final_authorization_evidence_blockers(text: str, evidence_type: T|str):
    reasons=[]; low=(text or "").lower(); typ=str(evidence_type)
    if contains_forbidden_final_authorization_action(text): reasons.append("Forbidden live execution, account query, bypass, or real-send wording detected.")
    if any(x in low for x in ["need_more_evidence","not_ready","no_go","blocked"]): reasons.append("Evidence contains NEED_MORE_EVIDENCE / NOT_READY / NO_GO / BLOCKED wording.")
    if typ.endswith("MONITORING") and ("critical" in low or "circuit breaker open" in low or "circuit_breaker_open" in low): reasons.append("Monitoring CRITICAL or Circuit Breaker OPEN detected.")
    if typ.endswith("DATA_QUALITY") and ("fail" in low or "unknown" in low): reasons.append("Data Quality FAIL/UNKNOWN detected.")
    return list(dict.fromkeys(reasons))
def classify_final_authorization_evidence_status(text: str, evidence_type: T|str):
    if not (text or "").strip(): return S.MISSING
    if detect_final_authorization_evidence_blockers(text, evidence_type): return S.FAIL
    low=text.lower(); typ=str(evidence_type)
    if typ.endswith("NOTIFICATION_DRY_RUN") and not ("no real" in low or "dry-run" in low or "dry_run" in low): return S.WARN
    if typ.endswith("DASHBOARD") and not ("read-only" in low or "readonly" in low or "no order" in low): return S.WARN
    return S.PRESENT
def summarize_final_authorization_evidence_text(text: str, evidence_type):
    one=" ".join((text or "").split()); return one[:240] if one else f"No {evidence_type} evidence text."
def collect_final_authorization_evidence_from_file(path: str|Path|None, evidence_type: T|str):
    p=Path(path) if path else None
    if not p or not p.exists(): return FinalAuthorizationEvidence(f"final-auth-evidence-{uuid4().hex[:8]}", evidence_type, S.MISSING, str(path or ""), "Evidence file is missing.", "WARN")
    text=p.read_text(encoding="utf-8", errors="replace"); status=classify_final_authorization_evidence_status(text, evidence_type); blockers=detect_final_authorization_evidence_blockers(text, evidence_type)
    return FinalAuthorizationEvidence(f"final-auth-evidence-{uuid4().hex[:8]}", evidence_type, status, str(p), summarize_final_authorization_evidence_text(text,evidence_type), "CRITICAL" if status==S.FAIL else ("WARN" if status==S.WARN else "INFO"), "; ".join(blockers), sanitize_final_authorization_metadata({"bytes":len(text)}))
def collect_final_authorization_evidence(**paths: Any):
    mapping={"live_env_check_report":T.LIVE_ENV_CHECK,"live_manual_prep_package":T.LIVE_MANUAL_PREP,"gray_decision_package":T.GRAY_DECISION_PACKAGE,"gray_rehearsal_report":T.GRAY_REHEARSAL,"live_gray_report":T.LIVE_GRAY_READINESS,"live_readiness_audit_report":T.LIVE_READINESS_AUDIT,"pipeline_report":T.RISK_GATE,"approval_file":T.HUMAN_APPROVAL,"paper_report":T.PAPER_TRADING,"monitoring_report":T.MONITORING,"data_quality_report":T.DATA_QUALITY,"agent_memo":T.AGENT_RESEARCH,"notification_dry_run_report":T.NOTIFICATION_DRY_RUN,"dashboard_path":T.DASHBOARD,"final_acceptance_report":T.FINAL_ACCEPTANCE}
    return [collect_final_authorization_evidence_from_file(paths.get(k), v) for k,v in mapping.items() if k in paths]
def aggregate_final_authorization_decision(evidence: list[FinalAuthorizationEvidence], config: FinalAuthorizationConfig):
    blocked=[e.blocked_reason for e in evidence if (getattr(e.status,"value",e.status)=="FAIL") and e.blocked_reason]
    warnings=[f"{getattr(e.evidence_type,'value',e.evidence_type)}: {e.summary}" for e in evidence if getattr(e.status,"value",e.status) in {"MISSING","WARN"}]
    if blocked: return FinalAuthorizationDecision.BLOCKED, list(dict.fromkeys(blocked)), list(dict.fromkeys(warnings))
    req=[("require_live_env_check",T.LIVE_ENV_CHECK),("require_live_manual_prep",T.LIVE_MANUAL_PREP),("require_gray_decision_package",T.GRAY_DECISION_PACKAGE),("require_gray_rehearsal",T.GRAY_REHEARSAL),("require_live_gray_readiness",T.LIVE_GRAY_READINESS),("require_live_readiness_audit",T.LIVE_READINESS_AUDIT),("require_risk_gate",T.RISK_GATE),("require_human_approval",T.HUMAN_APPROVAL),("require_paper_trading",T.PAPER_TRADING),("require_monitoring",T.MONITORING),("require_data_quality",T.DATA_QUALITY),("require_agent_research",T.AGENT_RESEARCH),("require_notification_dry_run",T.NOTIFICATION_DRY_RUN),("require_dashboard",T.DASHBOARD),("require_final_acceptance",T.FINAL_ACCEPTANCE)]
    required=[t.value for n,t in req if getattr(config,n,False)]; present={getattr(e.evidence_type,"value",e.evidence_type):getattr(e.status,"value",e.status) for e in evidence}
    missing=[r for r in required if present.get(r)!="PRESENT"]
    if missing or warnings: return FinalAuthorizationDecision.NEED_MORE_EVIDENCE, [], list(dict.fromkeys(warnings+[f"Missing or non-present required evidence: {x}" for x in missing]))
    return FinalAuthorizationDecision.READY_FOR_FINAL_SIGNOFF_REVIEW, [], []
