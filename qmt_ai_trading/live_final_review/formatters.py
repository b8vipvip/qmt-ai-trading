from __future__ import annotations
import json
from .models import *
def _json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2)
def format_live_final_review_report_json(report: LiveFinalReviewReport)->str: return _json(report)
def format_signature_verification_report_json(report: SignatureVerificationReport)->str: return _json(report)
def format_evidence_gap_report_json(report: EvidenceGapReport)->str: return _json(report)
def format_next_readonly_plan_report_json(report: NextReadonlyPlanReport)->str: return _json(report)
def _ev(report, cat): return [e for e in report.evidence if enum_value(e.category)==cat]
def _ev_lines(items): return [f"- {enum_value(e.status)} {e.path}: {e.summary}" for e in items] or ["- Not found / skipped."]
def format_live_final_review_report_markdown(report: LiveFinalReviewReport)->str:
    lines=["# Stage47 Final Read-only Go/No-Go Review Package","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_FINAL_REVIEW 只表示最终只读 go/no-go 材料可供人工复核，不是实盘授权。","","## Evidence Summary",f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}","- read_only: True","- dry_run_only: True"]
    for key,title in [("STAGE43_SIGNATURE_FREEZE","Stage43 Signature Freeze Evidence"),("STAGE44_ENV_SNAPSHOT","Stage44 Environment Snapshot Evidence"),("STAGE45_RUNBOOK","Stage45 Runbook Evidence"),("STAGE46_SIGNOFF","Stage46 Signoff Evidence")]: lines += ["",f"## {title}"]+_ev_lines(_ev(report,key))
    lines += ["","## Final Go/No-Go Summary"]
    for i in report.go_no_go_summary: lines += [f"### {i.title}",f"- Status: {enum_value(i.status)}",f"- Summary: {i.summary}"]+[f"- {c}" for c in i.confirmations]
    lines += ["","## Signature Verification Checklist"]+[f"- [ ] {i.role}: {i.statement}" for i in report.signature_verification_items]
    lines += ["","## Evidence Gap List"]+[f"- {enum_value(i.severity)} {i.title}: {i.summary} Required action: {i.required_action}" for i in report.evidence_gaps]
    lines += ["","## Next Read-only Plan"]+[f"- {i.title}: {i.summary}" for i in report.next_readonly_plan]
    lines += ["","## Required Manual Confirmations"]+[f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage48 仍不得直接实盘；只能继续做最终只读材料归档、缺口补证、人工核验或更严格的灰度前检查。",""]
    return "\n".join(lines)
def format_signature_verification_markdown(report: SignatureVerificationReport)->str:
    lines=["# Stage47 Signature Verification Checklist","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]
    for i in report.items: lines += ["",f"## {i.role}",f"- [ ] {i.statement}","- 不代表实盘授权。","- 未来真实执行仍需单独审批。"]
    return "\n".join(lines)+"\n"
def format_evidence_gap_markdown(report: EvidenceGapReport)->str:
    return "\n".join(["# Stage47 Evidence Gap List","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]+[f"\n## {i.title}\n- Severity: {enum_value(i.severity)}\n- Summary: {i.summary}\n- Required Action: {i.required_action}" for i in report.items])+"\n"
def format_next_readonly_plan_markdown(report: NextReadonlyPlanReport)->str:
    return "\n".join(["# Stage47 Next Read-only Plan","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]+[f"\n## {i.title}\n- {i.summary}" for i in report.items])+"\n"
