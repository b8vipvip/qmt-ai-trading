from __future__ import annotations
import json
from .models import IncidentRehearsalReport, LiveSignoffReport, ManualSignoffReport, enum_value, to_plain

def _json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2)
def format_live_signoff_report_json(report: LiveSignoffReport) -> str: return _json(report)
def format_manual_signoff_report_json(report: ManualSignoffReport) -> str: return _json(report)
def format_incident_rehearsal_report_json(report: IncidentRehearsalReport) -> str: return _json(report)
def format_live_signoff_report_markdown(report: LiveSignoffReport) -> str:
    def cat(name): return [e for e in report.evidence if enum_value(e.category)==name]
    lines=["# Stage46 Runbook Review and Manual Rehearsal Signoff","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"","## Evidence Summary",f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}",f"- read_only: {report.summary.get('read_only',True)}",f"- dry_run_only: {report.summary.get('dry_run_only',True)}"]
    for key,title in [("STAGE42_HUMAN_REVIEW","Stage42 Human Review Evidence"),("STAGE43_SIGNATURE_FREEZE","Stage43 Signature Freeze Evidence"),("STAGE44_ENV_SNAPSHOT","Stage44 Environment Snapshot Evidence"),("STAGE45_RUNBOOK","Stage45 Runbook Evidence")]:
        lines += ["",f"## {title}"] + ([f"- {enum_value(e.status)} {e.path}: {e.summary}" for e in cat(key)] or ["- Not found / skipped."])
    lines += ["","## Runbook Review"]
    for i in report.runbook_review: lines += [f"### {i.title}",f"- Status: {enum_value(i.status)}",f"- Summary: {i.summary}"]+[f"- {c}" for c in i.confirmations]
    lines += ["","## Manual Signoff Package"]
    for i in report.manual_signoff_items: lines += [f"- [ ] {i.role}: {i.statement}"]
    lines += ["","## Incident Rehearsal Results"]
    for i in report.incident_results: lines += [f"- {i.scenario}: {enum_value(i.severity)}; {i.result}; {i.required_action}"]
    lines += ["","## Required Manual Confirmations"]+[f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage47 仍不得直接实盘；只能继续做最终只读 go/no-go 材料汇总、人工签字核验或更严格的灰度前检查。",""]
    return "\n".join(lines)
def format_manual_signoff_markdown(report: ManualSignoffReport) -> str:
    lines=["# Stage46 Manual Rehearsal Signoff Package","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"每个签字项均不代表实盘授权，未来真实执行仍需单独审批。"]
    for i in report.items: lines += ["",f"## {i.role}",f"- [ ] {i.statement}","- 不代表实盘授权。","- 未来真实执行仍需单独审批。"]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    return "\n".join(lines)+"\n"
def format_incident_rehearsal_markdown(report: IncidentRehearsalReport) -> str:
    lines=["# Stage46 Incident Rehearsal Results","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note]
    for i in report.items: lines += ["",f"## {i.scenario}",f"- Severity: {enum_value(i.severity)}",f"- Result: {i.result}",f"- Required Action: {i.required_action}"]
    return "\n".join(lines)+"\n"
