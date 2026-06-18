from __future__ import annotations
from pathlib import Path
from typing import Any
from .models import GrayDecision, GrayDecisionConfig, GrayDecisionEvidence, GrayDecisionEvidenceStatus as S, GrayDecisionEvidenceType as T
from .safety import contains_forbidden_gray_decision_action, sanitize_gray_decision_metadata
REQ={T.RISK_GATE:"require_risk_gate",T.HUMAN_APPROVAL:"require_human_approval",T.PAPER_TRADING:"require_paper_trading",T.LIVE_READINESS_AUDIT:"require_live_readiness_audit",T.MONITORING:"require_monitoring",T.DATA_QUALITY:"require_data_quality",T.AGENT_RESEARCH:"require_agent_research",T.LIVE_GRAY_READINESS:"require_live_gray_readiness",T.NOTIFICATION_DRY_RUN:"require_notification_dry_run",T.DASHBOARD:"require_dashboard",T.GRAY_REHEARSAL:"require_gray_rehearsal",T.FINAL_ACCEPTANCE:"require_final_acceptance"}
def _etype(e): return e if isinstance(e,T) else T(str(e))
def detect_evidence_blockers(text: str, evidence_type: T|str)->list[str]:
    lo=text.lower(); out=[]
    if contains_forbidden_gray_decision_action(text): out.append("forbidden live execution / notification / account query marker detected")
    if _etype(evidence_type)==T.MONITORING and ("critical" in lo or "circuit breaker open" in lo or "circuit_breaker: open" in lo): out.append("monitoring critical or circuit breaker OPEN")
    if _etype(evidence_type)==T.DATA_QUALITY and ("fail" in lo or "unknown" in lo): out.append("data quality FAIL/UNKNOWN requires more evidence")
    if _etype(evidence_type)==T.LIVE_GRAY_READINESS and ("no_go" in lo or "blocked" in lo): out.append("live gray readiness is NO_GO/BLOCKED")
    if "bypass risk" in lo or "绕过风控" in text: out.append("risk gate bypass marker detected")
    return out
def classify_evidence_status(text: str, evidence_type: T|str)->S:
    blockers=detect_evidence_blockers(text,evidence_type)
    if blockers and (contains_forbidden_gray_decision_action(text) or _etype(evidence_type)==T.MONITORING): return S.FAIL
    if blockers: return S.WARN
    if "warn" in text.lower() or "warning" in text.lower(): return S.WARN
    return S.PRESENT if text.strip() else S.MISSING
def summarize_evidence_text(text: str, evidence_type: T|str)->str:
    clean=" ".join((text or "").split())[:300]
    return clean or f"No local {getattr(evidence_type,'value',evidence_type)} evidence text."
def collect_evidence_from_file(path: str|Path|None, evidence_type: T|str)->GrayDecisionEvidence:
    et=_etype(evidence_type); sid=f"{et.value.lower()}_evidence"
    if not path or not Path(path).exists():
        return GrayDecisionEvidence(sid,et,S.MISSING,str(path or ""),"Local evidence file missing.","WARN","missing required local evidence")
    text=Path(path).read_text(encoding="utf-8", errors="replace")
    status=classify_evidence_status(text,et); blockers=detect_evidence_blockers(text,et)
    return GrayDecisionEvidence(sid,et,status,str(path),summarize_evidence_text(text,et),"CRITICAL" if status==S.FAIL else ("WARN" if status==S.WARN else "INFO"),"; ".join(blockers),{"bytes":len(text)})
def collect_gray_decision_evidence(**paths: Any)->list[GrayDecisionEvidence]:
    mapping=[("pipeline_report",T.RISK_GATE),("approval_file",T.HUMAN_APPROVAL),("paper_report",T.PAPER_TRADING),("live_readiness_audit_report",T.LIVE_READINESS_AUDIT),("monitoring_report",T.MONITORING),("data_quality_report",T.DATA_QUALITY),("agent_memo",T.AGENT_RESEARCH),("live_gray_report",T.LIVE_GRAY_READINESS),("notification_dry_run_report",T.NOTIFICATION_DRY_RUN),("dashboard_path",T.DASHBOARD),("gray_rehearsal_report",T.GRAY_REHEARSAL),("final_acceptance_report",T.FINAL_ACCEPTANCE)]
    return [collect_evidence_from_file(paths.get(k),t) for k,t in mapping]
def _status_value(status):
    return status.value if hasattr(status, "value") else str(status)

def aggregate_evidence_decision(evidence: list[GrayDecisionEvidence], config: GrayDecisionConfig):
    blocked=[]; warnings=[]; missing=[]
    by={_etype(e.evidence_type):e for e in evidence}
    for e in evidence:
        if _status_value(e.status)==S.FAIL.value: blocked.append(e.blocked_reason or f"{e.evidence_type} failed")
        if _status_value(e.status)==S.WARN.value: warnings.append(e.summary)
        if _status_value(e.status)==S.MISSING.value: missing.append(str(getattr(e.evidence_type,'value',e.evidence_type)))
    for et,attr in REQ.items():
        if getattr(config,attr,False) and (et not in by or _status_value(by[et].status)==S.MISSING.value): missing.append(et.value)
    if blocked: return GrayDecision.BLOCKED, blocked, warnings+missing
    if missing or warnings: return GrayDecision.NEED_MORE_EVIDENCE, [], warnings+missing
    return GrayDecision.READY_FOR_MANUAL_DECISION, [], []
