from __future__ import annotations
import json
from .models import LiveRunbookCategory as C, LiveRunbookReport, ManualRehearsalReport, IncidentPlaybookReport, enum_value, to_plain

def _ev_rows(items):
    return [f"| {enum_value(x.severity)} | {enum_value(x.status)} | {enum_value(x.category)} | {x.path} | {x.title} | {x.summary} |" for x in items]
def format_live_runbook_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_manual_rehearsal_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_incident_playbook_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_live_runbook_report_markdown(report: LiveRunbookReport) -> str:
    ev=report.evidence
    def cat(c): return [x for x in ev if enum_value(x.category)==enum_value(c)]
    lines=["# Stage45 Read-only Live Runbook and Manual Rehearsal","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_RUNBOOK_REVIEW 只表示运行手册材料可供人工复核，不是实盘授权。","","## Evidence Summary",json.dumps(report.summary, ensure_ascii=False),"","| Severity | Status | Category | Path | Title | Summary |","| --- | --- | --- | --- | --- | --- |"]
    lines += _ev_rows(ev) or ["| WARN | SKIPPED | SYSTEM | | None | No evidence collected |"]
    for c,t in [(C.STAGE41_LEDGER,"Stage41 Ledger Evidence"),(C.STAGE42_HUMAN_REVIEW,"Stage42 Human Review Evidence"),(C.STAGE43_SIGNATURE_FREEZE,"Stage43 Signature Freeze Evidence"),(C.STAGE44_ENV_SNAPSHOT,"Stage44 Environment Snapshot Evidence")]:
        lines += ["",f"## {t}"] + ([f"- {enum_value(x.status)} {x.path}: {x.summary}" for x in cat(c)] or ["- Not found / skipped."])
    lines += ["","## Read-only Runbook"]
    for s in report.runbook_sections: lines += [f"### {s.title}"] + [f"- {x}" for x in s.content]
    lines += ["","## Manual Rehearsal Steps"]
    for s in report.manual_steps: lines += [f"### {s.title}"] + [f"- [ ] {x}" for x in s.checklist] + [f"Expected: {s.expected_result}"]
    lines += ["","## Incident Playbook"]
    for i in report.incident_items: lines += [f"### {i.scenario}", f"- Detection: {i.detection}"] + [f"- Response: {x}" for x in i.response] + [f"- Rollback: {i.rollback}"]
    lines += ["","## Required Manual Confirmations"] + [f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage46 仍不得直接实盘；只能继续做灰度前运行手册复核、人工演练签字、配置冻结复查或更严格的只读检查。",""]
    return "\n".join(lines)
def format_manual_rehearsal_markdown(report: ManualRehearsalReport) -> str:
    lines=["# Stage45 Manual Rehearsal Package","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_RUNBOOK_REVIEW 不是实盘授权。"]
    for s in report.steps: lines += ["",f"## {s.title}"]+[f"- [ ] {x}" for x in s.checklist]+[f"Expected: {s.expected_result}"]
    return "\n".join(lines)+"\n"
def format_incident_playbook_markdown(report: IncidentPlaybookReport) -> str:
    lines=["# Stage45 Incident Playbook","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"本清单只用于只读异常演练，不是实盘授权。"]
    for i in report.items: lines += ["",f"## {i.scenario}",f"- Severity: {enum_value(i.severity)}",f"- Detection: {i.detection}"]+[f"- Response: {x}" for x in i.response]+[f"- Rollback: {i.rollback}"]
    return "\n".join(lines)+"\n"
