from __future__ import annotations
import json
from .models import *
def _json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2)
def format_live_archive_report_json(report: LiveArchiveReport)->str: return _json(report)
def format_evidence_remediation_report_json(report: EvidenceRemediationReport)->str: return _json(report)
def format_human_verification_summary_report_json(report: HumanVerificationSummaryReport)->str: return _json(report)
def format_next_readonly_check_report_json(report: NextReadonlyCheckReport)->str: return _json(report)
def _ev(report, cat): return [e for e in report.evidence if enum_value(e.category)==cat]
def _ev_lines(items): return [f"- {enum_value(e.status)} {e.path}: {e.summary}" for e in items] or ["- Not found / skipped."]
def format_live_archive_report_markdown(report: LiveArchiveReport)->str:
    lines=["# Stage48 Final Read-only Archive and Evidence Remediation Plan","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_ARCHIVE_REVIEW 只表示最终只读归档材料可供人工复核，不是实盘授权。","","## Evidence Summary",f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}","- read_only: True","- dry_run_only: True"]
    for key,title in [("STAGE44_ENV_SNAPSHOT","Stage44 Environment Snapshot Evidence"),("STAGE45_RUNBOOK","Stage45 Runbook Evidence"),("STAGE46_SIGNOFF","Stage46 Signoff Evidence"),("STAGE47_FINAL_REVIEW","Stage47 Final Review Evidence")]: lines += ["",f"## {title}"]+_ev_lines(_ev(report,key))
    lines += ["","## Archive Index"]+[f"- {enum_value(i.status)} {i.title}: {i.summary}" for i in report.archive_index]
    lines += ["","## Evidence Remediation Plan"]+[f"- {enum_value(i.severity)} {i.title}: {i.summary} Required action: {i.required_action}" for i in report.evidence_remediation_plan]
    lines += ["","## Human Verification Summary"]+[f"- [ ] {i.role}: {i.statement} 不代表实盘授权；未来真实执行仍需单独审批。" for i in report.human_verification_summary]
    lines += ["","## Next Read-only Check Plan"]+[f"- {i.title}: {i.summary}" for i in report.next_readonly_check_plan]
    lines += ["","## Required Manual Confirmations"]+[f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage49 仍不得直接实盘；只能继续做补证后只读复核、人工核验复查、最终材料一致性检查或更严格的灰度前检查。",""]
    return "\n".join(lines)
def format_evidence_remediation_markdown(report: EvidenceRemediationReport)->str:
    return "\n".join(["# Stage48 Evidence Remediation Plan","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]+[f"\n## {i.title}\n- Severity: {enum_value(i.severity)}\n- Summary: {i.summary}\n- Required Action: {i.required_action}" for i in report.items])+"\n"
def format_human_verification_summary_markdown(report: HumanVerificationSummaryReport)->str:
    lines=["# Stage48 Human Verification Summary","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]
    for i in report.items: lines += ["",f"## {i.role}",f"- [ ] {i.statement}","- 不代表实盘授权。","- 未来真实执行仍需单独审批。"]
    return "\n".join(lines)+"\n"
def format_next_readonly_check_markdown(report: NextReadonlyCheckReport)->str:
    return "\n".join(["# Stage48 Next Read-only Check Plan","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]+[f"\n## {i.title}\n- {i.summary}" for i in report.items])+"\n"
