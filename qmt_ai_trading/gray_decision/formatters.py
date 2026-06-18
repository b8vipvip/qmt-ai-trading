from __future__ import annotations
import json
from .models import GrayDecisionEvidence, GrayDecisionPackage, SAFETY_NOTE
from .checklist import format_gray_decision_checklist
def format_gray_decision_evidence(evidence: GrayDecisionEvidence)->str:
    d=evidence.to_dict(); return f"| {d['evidence_type']} | {d['status']} | {d.get('severity','')} | {d.get('source_path','')} | {d.get('summary','')} | {d.get('blocked_reason','')} |"
def format_gray_decision_package_markdown(package: GrayDecisionPackage)->str:
    p=package.to_dict(); lines=["# Gray decision package summary",f"- Package ID: {p['package_id']}",f"- Created at: {p['created_at']}",f"- Success: {p['success']}","", "## Decision", f"- Decision: {p['decision']}", f"- Message: {p['message']}","", "## Required evidence", "- Risk Gate / Human Approval / Paper Trading / Live Readiness Audit / Monitoring / Data Quality / Agent Research / Live Gray Readiness / Notification Dry Run / Dashboard / Gray Rehearsal / Final Acceptance", "", "## Evidence table", "| Type | Status | Severity | Source | Summary | Blocked reason |", "|---|---|---|---|---|---|"]
    lines += [format_gray_decision_evidence(e) for e in package.evidence]
    lines += ["", "## Blocked reasons"] + ([f"- {x}" for x in package.blocked_reasons] or ["- None"])
    lines += ["", "## Warnings"] + ([f"- {x}" for x in package.warnings] or ["- None"])
    lines += ["", "## Manual checklist", format_gray_decision_checklist(package), "", "## Manual signature placeholder", package.manual_signature_placeholder, "", "## Safety note", SAFETY_NOTE, "", "## Next separate stage", "阶段三十七：极小资金灰度实盘人工审批准备（仍默认关闭）。READY_FOR_MANUAL_DECISION is not trading authorization."]
    return "\n".join(lines)
def format_gray_decision_package_json(package: GrayDecisionPackage)->str:
    return json.dumps(package.to_dict(), ensure_ascii=False, indent=2)
